from mock import MagicMock
import chimney
from nose.tools import eq_

# test stuff from README.md


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
