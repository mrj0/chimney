from pprint import pprint
from concurrent.futures import _base
from mock import MagicMock
from mock import Mock
from nose.tools import eq_
from chimney.api import Maker
from chimney.scheduler import TaskGraph, Runner, Scheduler
from chimney.compilers import coffee, uglify, Compiler


class MockExecutor(_base.Executor):
    def __init__(self):
        self.executed = []

    def submit(self, runner, *args, **kwargs):
        runner.task()
        self.executed.append(runner)
        runner.future.set_result('finished')

    def wait(self):
        pass


def test_graph_sort():
    graph = TaskGraph()

    tasks = [
        coffee('combined.js', ['one.coffee', 'two.coffee']),
        coffee('other.js', ['three.coffee', 'four.coffee']),
        uglify('combined.min.js', ['combined.js', 'other.js']),
    ]

    for task in tasks:
        graph.arc(task)

    run_plan = list(graph.toposort())
    eq_(run_plan, [tasks[1], tasks[0], tasks[2]])


def test_base():
    graph = TaskGraph()

    class coffee(Compiler):
        run = MagicMock()

    class uglify(Compiler):
        run = MagicMock()

    tasks = [
        uglify('static/js-c/home/signed_in.min.js', [
            'static/js-c/home/index.js',
            'static/js-lib/jquery-ui-1.8.23.custom-min.js',
            'static/js-lib/jquery.carousel.js',
            'static/js-c/common/tooltip.js',
            'static/js-c/common/carousel/carousel.js',
            'static/js-c/common/event_list/event_list.js',
            'static/js-c/home/signed_in.js',
        ]),
        coffee('static/js-c/home/index.js', ['static/js-c/home/index.coffee']),
        coffee('static/js-c/common/tooltip.js', ['static/js-c/common/tooltip.coffee']),
        coffee('static/js-c/common/carousel/carousel.js', ['static/js-c/common/carousel/carousel.coffee']),
        coffee('static/js-c/common/event_list/event_list.js', ['static/js-c/common/event_list/event_list.coffee']),
        coffee('static/js-c/home/signed_in.js', ['static/js-c/home/signed_in.coffee']),
    ]

    for task in tasks:
        graph.arc(task)

    run_plan = list(graph.toposort())
    eq_(run_plan[-1], tasks[0])

    runners = Scheduler().load(tasks).run()
    eq_(len(runners['static/js-c/home/signed_in.min.js'].waiting_for), 5)

    maker = Maker(*tasks)
    maker.executor = MockExecutor()
    maker.execute()

    eq_(len(maker.executor.executed), 6)
    # the last task executed should be uglify
    eq_(maker.executor.executed[-1].task, tasks[0])


def test_runner():
    """
    verify that runners depending on other runners works as expected
    """
    executor = MockExecutor()
    runner_a = Runner(Mock())
    runner_b = Runner(Mock())
    runner_c = Runner(Mock())

    runner_b.waiting_for.append(runner_a)
    runner_c.waiting_for.append(runner_a)
    runner_c.waiting_for.append(runner_b)

    runner_c.schedule(executor)
    assert not runner_c.future.done(), 'c should not have run yet'

    runner_b.schedule(executor)
    assert not runner_b.future.done(), 'b should not have run yet'

    runner_a.schedule(executor)
    assert runner_a.future.done(), 'a should have run'
    runner_b.schedule(executor)
    assert runner_b.future.done(), 'b should have run'
    runner_c.schedule(executor)
    assert runner_c.future.done(), 'c should have run'
