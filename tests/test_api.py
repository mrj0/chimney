from mock import MagicMock
from nose.tools import eq_
from chimney.api import Maker, watch
from chimney.compilers import Compiler
from chimney.watch import Observation


def test_watch_multi():
    # make sure one change to a shared dependency recompiles both
    class coffee(Compiler):
        run = MagicMock()

    close = Maker.close  # don't let it shutdown yet
    Maker.close = MagicMock()
    Maker.sleep = MagicMock()
    Maker.sleep.return_value = False

    def create_tasks():
        return [
            coffee('smoke.js', ['wood.coffee', 'fire.coffee']),
            coffee('waterlog.js', ['wood.coffee', 'water.coffee']),
        ]

    maker = watch(create_tasks, reload_patterns=['*.coffee', '*.js'])

    # compiles smoke.js, waterlog.js
    eq_(coffee.run.call_count, 2)

    maker.watcher.change_handler(Observation('wood.coffee', 'modified'))
    maker.process_changes()
    maker.executor.wait()
    # had 2 already, should now compile both again
    eq_(coffee.run.call_count, 4)

    maker.watcher.change_handler(Observation('water.coffee', 'modified'))
    maker.process_changes()
    maker.executor.wait()
    # now just compiles waterlog.js
    eq_(coffee.run.call_count, 5)

    close(maker)
    maker.watcher.stop()
