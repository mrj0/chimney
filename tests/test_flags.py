from nose.tools import eq_, assert_raises
from chimney.flags import Arguments, Flag, InvalidFlagValueError
from chimney.compilers import Compiler, uglify


def test_args():
    a = Arguments(
        source_map=Flag('--source-map')
    )

    assert 'source_map' in a.args
    eq_(a.args['source_map'].name, 'source_map')

    a = Arguments(
        source_map=Flag()
    )

    assert 'source_map' in a.args
    eq_(a.args['source_map'].name, 'source_map')


def test_arg_required():
    a = Arguments(
        source_map=Flag(required=True)
    )

    with assert_raises(InvalidFlagValueError):
        a.args['source_map'].validate(None)

    with assert_raises(InvalidFlagValueError):
        a.args['source_map'].validate('')

    with assert_raises(InvalidFlagValueError):
        a.args['source_map'].validate(' ')
