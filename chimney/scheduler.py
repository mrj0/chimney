from concurrent.futures._base import Future, CANCELLED_AND_NOTIFIED, CANCELLED
import six
import logging
from collections import OrderedDict

try:
    from functools import reduce
except ImportError:
    pass


log = logging.getLogger(__name__)


class TaskFuture(Future):
    """Represents the result of an asynchronous computation."""

    def failed(self):
        """Return True of the future was cancelled or otherwise failed."""
        with self._condition:
            return self._state in [CANCELLED, CANCELLED_AND_NOTIFIED] or self._exception is not None


class DiGraph(OrderedDict):
    def __init__(self, roots=None):
        super(DiGraph, self).__init__()
        if roots:
            map(self.arc, roots)

    def arc(self, task):
        key = task.output_file
        if key not in self:
            self[key] = set()

        sources = set(task.dependent)
        self[key] = self[key].union(sources)

        for source in sources:
            # ensure there's a key for this dependency
            if not source in self:
                self[source] = set()


class TaskGraph(object):
    def __init__(self, roots=None):
        super(TaskGraph, self).__init__()
        self.graph = DiGraph(roots=roots)
        self.tasks = {}

    def arc(self, task):
        self.graph.arc(task)
        self.tasks[task.output_file] = task

    def toposort(self):
        if self.graph:
            data = DiGraph()
            map(data.__setitem__, self.graph.keys(), self.graph.values())

            for k, v in data.items():
                v.discard(k)   # Ignore self dependencies
            extra_items_in_deps = reduce(set.union, data.values()) - set(data.keys())
            data.update(dict([(k, set()) for k in extra_items_in_deps]))
            while True:
                ordered = set(output_file for output_file, dep in six.iteritems(data) if not dep)
                if not ordered:
                    break
                for el in ordered:
                    task = self.tasks.get(el)
                    if task:
                        yield task
                data = dict([(item, (dep - ordered)) for item, dep in six.iteritems(data)
                            if item not in ordered])
            assert not data, "Data has a cyclic dependency"


class Runner(object):
    """
    This class waits for dependencies to finish and submits itself to the job scheduler
    """

    def __init__(self, task):
        self.future = Future()
        # a list of Runners to wait for
        self.waiting_for = []

        # the callable to run
        self.task = task

        super(Runner, self).__init__()

    def schedule(self, executor, _reschedule=False):
        """
        Try to schedule this Runner with the executor or wait for dependencies
        """
        if self.future.done():
            return

        if False not in [r.future.done() for r in self.waiting_for]:
            executor.submit(self)
            return

        def dep_finished_callback(future):
            self.schedule(executor, _reschedule=True)

        if not _reschedule:
            for runner in self.waiting_for:
                runner.future.add_done_callback(dep_finished_callback)


class Scheduler(object):
    """
    An abstraction for a single run. Tracks the run status of compiler tasks and their dependencies.
    """

    def __init__(self):
        # the dependency graph of all tasks stored by target (string path) and a set of tasks depending on the target
        self.targets = TaskGraph()

        super(Scheduler, self).__init__()

    def load(self, compilers):
        """
        Load tasks and calculate dependencies
        """
        # make an arc from every dependent file to the task that creates it
        for c in compilers:
            self.targets.arc(c)

        return self

    def run(self):
        """
        Get runners for the scheduled tasks
        """

        # create runners for all of the compiler tasks
        runners = {}

        # build dependency lists for each runner
        for task in self.targets.toposort():
            runner = Runner(task)
            runners[task.output_file] = runner

            for dep in task.dependent:
                wait_for = runners.get(dep)
                # if not present there's nothing in the schedule that produces this file. that's normal
                if wait_for:
                    runner.waiting_for.append(wait_for)

        return runners
