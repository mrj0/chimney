import os
from mock import MagicMock
import time
import chimney
from nose.tools import eq_

# test stuff from README.md
from chimney.api import Maker
from chimney.watch import Observation


def test_smoke():
    class compiler(chimney.compilers.Compiler):
        ran = False

        def run(self):
            compiler.ran = True

    chimney.make(
        compiler('smoke.js', ['wood.coffee', 'fire.coffee']),
    )

    assert compiler.ran, 'compiler not executed'


def test_combine():
    class coffee(chimney.compilers.Compiler):
        pass

    class uglify(chimney.compilers.Compiler):
        pass

    coffee.run = MagicMock()
    uglify.run = MagicMock()

    chimney.make(
        coffee('smoke.js', ['wood.coffee', 'fire.coffee']),
        uglify('smoke.min.js', 'smoke.js'),
    )

    assert coffee.run.called
    assert uglify.run.called


def test_watch():
    class coffee(chimney.compilers.Compiler):
        pass

    class uglify(chimney.compilers.Compiler):
        pass

    coffee.run = MagicMock()
    uglify.run = MagicMock()
    Maker.sleep = MagicMock()
    Maker.sleep.return_value = False

    def create_tasks():
        return [
            coffee('smoke.js', ['wood.coffee', 'fire.coffee']),
            uglify('smoke.min.js', 'smoke.js'),
        ]

    maker = chimney.watch(create_tasks)

    eq_(coffee.run.call_count, 1)
    eq_(uglify.run.call_count, 1)

    maker.watcher.change_handler(Observation('wood.coffee', 'modified'))
    maker.process_changes()
    maker.executor.wait()
    eq_(coffee.run.call_count, 2)
    eq_(uglify.run.call_count, 1)

    maker.watcher.change_handler(Observation('smoke.js', 'modified'))
    maker.process_changes()
    maker.executor.wait()
    eq_(uglify.run.call_count, 2)

    maker.watcher.stop()
