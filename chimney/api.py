import multiprocessing
import os
from contextlib import closing
import logging
import six
from chimney.scheduler import Scheduler
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
        for runner in six.itervalues(runners):
            runner.schedule(self.executor)

        #self.executor.wait()
        #print 'done waiting'

        def change_handler(obs):
            print 'got an observation!!', obs
            print runners
        self.watcher = Watcher(change_handler)
        log.info('Watching for changes. Control-C to cancel')

    #def on_task_finished(self, task):
    #    pass

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
