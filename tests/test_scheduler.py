from nose.tools import eq_
from chimney.scheduler import TaskGraph
from chimney.compilers import coffee, uglify


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
    run_plan = [s for s in graph.toposort() if not s.endswith('.coffee')]
    eq_(run_plan, ['other.js', 'combined.js', 'combined.min.js'])
