from nose.tools import eq_, assert_raises
from chimney import flags
from chimney.compilers import Compiler, uglify


def test_extra_flags():
    c = Compiler('b', 'a')
    eq_(c.extra_flags, {})

    c = Compiler('b', 'a', extra_flags={'--map': 'b.map'})
    eq_(c.extra_flags['--map'], 'b.map')


def test_uglify_flags():
    with assert_raises(flags.InvalidFlagError):
        c = uglify('b', 'a', asdf='b.map')

    c = uglify('b', 'a', source_map='b.map')
    eq_(c.extra_flags['--source-map'], 'b.map')

    eq_(c.get_flags(), ['--source-map b.map'])
