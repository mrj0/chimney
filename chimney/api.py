import multiprocessing
import os
from contextlib import closing
import logging
import six
import time
from chimney.scheduler import Scheduler, Runner
from chimney.watch import Watcher
from executor import DelayedThreadPoolExecutor


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class Maker(object):
    """
    Main class of chimney. Executes compilers and stuff.
    """

    def __init__(self, *tasks, **kw):
        """
        ``tasks`` - A list of Compiler instances to run
        ``directory`` - Must be the top level of the project. All files will be relative to this path.
            Defaults to the current directory.
        """
        self.tasks = tasks
        self.directory = kw.pop('directory', None) or os.path.abspath(os.path.curdir)
        self.jobs = int(kw.pop('jobs', multiprocessing.cpu_count() * 1.5))
        # observed changes
        self.changes = []

        if kw:
            raise TypeError('Unknown keyword arguments: {0}'.format(', '.join(kw.keys())))

        for task in self.tasks:
            task.maker = self

        self.executor = DelayedThreadPoolExecutor(self.jobs)
        super(Maker, self).__init__()

    def execute(self):
        runners = Scheduler().load(self.tasks).run(self.executor)
        # schedule all of the runners
        for runner in six.itervalues(runners):
            runner.schedule(self.executor)
    #        runner.future.add_done_callback(self.on_task_finished)

    def watch(self):
        scheduler = Scheduler().load(self.tasks)
        runners = scheduler.run(self.executor)

        # schedule all of the runners
        self.by_source = {}
        for runner in six.itervalues(runners):
            runner.schedule(self.executor)
            for dep in runner.task.dependent:
                self.by_source[os.path.abspath(dep)] = runner.task

        self.executor.wait()

        def change_handler(obs):
            self.changes.append(obs)
        self.watcher = Watcher(change_handler)
        log.info('Watching for changes. Control-C to cancel')

        try:
            while self.sleep():
                self.process_changes()
        except KeyboardInterrupt:
            self.close()

    def process_changes(self):
        batch = self.changes
        self.changes = []
        for obs in set(batch):
            task = self.by_source.get(os.path.abspath(obs.path))
            if task:
                log.info('Detected %s: %s', obs.type, obs.path)
                runner = Runner(task)
                runner.schedule(self.executor)

    def sleep(self):
        time.sleep(.1)
        return True

    def close(self):
        self.executor.shutdown()


def make(*tasks):
    log.info('Start')

    with closing(Maker(*tasks)) as maker:
        maker.execute()
        return maker


def watch(*tasks):
    log.info('Start')

    maker = Maker(*tasks)
    maker.watch()
    return maker
