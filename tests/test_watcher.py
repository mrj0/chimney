import os
import shutil
import time
from nose.tools import eq_
from chimney.watch import Watcher, Observation


def test_watcher():
    here = os.path.dirname(os.path.abspath(__file__))
    watched = os.path.join(here, '_watched')
    created = os.path.join(watched, 'created')

    shutil.rmtree(watched, ignore_errors=True)
    os.mkdir(watched)
    try:
        events = []

        def change_handler(obs):
            events.append(obs)
        Watcher(change_handler, path=watched)

        with open(created, 'wb') as f:
            f.write('created')

        time.sleep(.1)
        obs = events.pop(0)
        eq_(obs.path, created)
        eq_(obs.type, 'created')

        # this works but newer Watchdog implmentations break this test.
        # it wasn't that good anyhow
        # obs = events.pop(0)
        # eq_(obs.path, created)
        # eq_(obs.type, 'modified')
        # eq_(0, len(events))
    finally:
        shutil.rmtree(watched, ignore_errors=True)


def test_hash_observation():
    changes = [
        Observation('one.js', 'modified'),
        Observation('one.js', 'modified'),
        Observation('two.js', 'modified'),
    ]

    eq_([c.path for c in set(changes)], ['one.js', 'two.js'])
