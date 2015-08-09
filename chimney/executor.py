import threading
from concurrent.futures import _base
from concurrent.futures.thread import _WorkItem, _worker, _threads_queues
import weakref

try:
    import queue
except ImportError:
    import Queue as queue


class DelayedThreadPoolExecutor(_base.Executor):
    def __init__(self, max_workers):
        """Initializes a new ThreadPoolExecutor instance.

        Args:
            max_workers: The maximum number of threads that can be used to
                execute the given calls.
        """
        self._max_workers = max_workers
        self._work_queue = queue.Queue()
        self._threads = set()
        self._shutdown = False
        self._shutdown_lock = threading.Lock()

        self._start_queue = []

    def queue(self, runner):
        self._start_queue.append(runner)

    def start(self):
        map(self.submit, self._start_queue)
        self._start_queue = []

    def submit(self, runner, *args, **kw):
        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError('cannot schedule new futures after shutdown')

            w = _WorkItem(runner.future, runner.task, args, kw)

            def on_done(f):
                self._work_queue.task_done()
            runner.future.add_done_callback(on_done)
            self._work_queue.put(w)
            self._adjust_thread_count()
            return runner.future
    submit.__doc__ = _base.Executor.submit.__doc__

    def _adjust_thread_count(self):
        # When the executor gets lost, the weakref callback will wake up
        # the worker threads.
        def weakref_cb(_, q=self._work_queue):
            q.put(None)
        # TODO(bquinlan): Should avoid creating new threads if there are more
        # idle threads than items in the work queue.
        if len(self._threads) < self._max_workers:
            t = threading.Thread(target=_worker,
                                 args=(weakref.ref(self, weakref_cb),
                                       self._work_queue))
            t.daemon = True
            t.start()
            self._threads.add(t)
            # don't want this cleaned up on interpreter exit
            # _threads_queues[t] = self._work_queue

    def shutdown(self, wait=True):
        with self._shutdown_lock:
            self._shutdown = True
            self._work_queue.empty()
            self._work_queue.put(None)
        if wait:
            for t in self._threads:
                t.join()
    shutdown.__doc__ = _base.Executor.shutdown.__doc__

    def wait(self):
        self._work_queue.all_tasks_done.acquire()
        try:
            while self._work_queue.unfinished_tasks and not self._shutdown:
                self._work_queue.all_tasks_done.wait(timeout=1)
        finally:
            self._work_queue.all_tasks_done.release()
