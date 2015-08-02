import fnmatch
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
    STOP_WATCHING = 0
    RELOAD = 1

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
        runners = Scheduler().load(self.tasks).run()
        # schedule all of the runners
        for runner in six.itervalues(runners):
            runner.schedule(self.executor)

        self.executor.wait()

    def watch(self, reload_patterns=None):
        scheduler = Scheduler().load(self.tasks)
        runners = scheduler.run()

        # schedule all of the runners
        self.by_source = {}
        for runner in six.itervalues(runners):
            runner.schedule(self.executor)
            for dep in runner.task.dependent:
                abs = os.path.abspath(dep)
                if abs not in self.by_source:
                    self.by_source[abs] = set([runner.task])
                else:
                    self.by_source[abs].add(runner.task)

        self.executor.wait()

        def change_handler(obs):
            self.changes.append(obs)
        self.watcher = Watcher(change_handler)
        log.info('Watching for changes. Control-C to cancel')

        try:
            while self.sleep():
                ret = self.process_changes(reload_patterns)
                if ret == Maker.RELOAD:
                    return Maker.RELOAD
        except KeyboardInterrupt:
            pass
        finally:
            self.close()

        return Maker.STOP_WATCHING

    def process_changes(self, reload_patterns=None):
        batch = self.changes
        self.changes = []
        for obs in set(batch):
            if obs.type in ('created', 'deleted',):
                if reload_patterns is None:
                    log.info(u'File %s: %s, reloading', obs.type, obs.path)
                    return Maker.RELOAD

                for p in reload_patterns:
                    if fnmatch.fnmatch(obs.path, p):
                        log.info(u'File %s: %s, reloading', obs.type, obs.path)
                        return Maker.RELOAD

            if obs.type != 'modified':
                continue

            for task in (self.by_source.get(os.path.abspath(obs.path)) or []):
                log.info('Detected %s: %s', obs.type, obs.path)
                runner = Runner(task)
                runner.schedule(self.executor)

        return None

    def sleep(self):
        time.sleep(.1)
        return True

    def close(self):
        try:
            if self.watcher:
                self.watcher.stop()
        except Exception:
            log.info('Failed to stop watcher', exc_info=True)

        self.executor.shutdown()


def make(*tasks, **kwargs):
    log.info('Start')

    with closing(Maker(*tasks, **kwargs)) as maker:
        maker.execute()
        return maker


def watch(func, reload_patterns=None, **kwargs):
    log.info('Start')

    while True:
        maker = Maker(*func(), **kwargs)
        ret = maker.watch(reload_patterns)

        if ret == Maker.STOP_WATCHING:
            break

    return maker
