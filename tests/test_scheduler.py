from pprint import pprint
from concurrent.futures import _base
from mock import Mock
from nose.tools import eq_
from chimney.scheduler import TaskGraph, Runner
from chimney.compilers import coffee, uglify


class MockExecutor(_base.Executor):
    def submit(self, runner, *args, **kwargs):
        runner.task()
        runner.future.set_result('finished')


def test_graph_sort():
    graph = TaskGraph()

    tasks = [
        coffee('combined.js', ['one.coffee', 'two.coffee']),
        coffee('other.js', ['three.coffee', 'four.coffee']),
        uglify('combined.min.js', ['combined.js', 'other.js']),
    ]

    for task in tasks:
        graph.arc(task)

    # ignore the coffee files
    run_plan = list(graph.toposort())
    eq_(run_plan, [tasks[1], tasks[0], tasks[2]])


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
