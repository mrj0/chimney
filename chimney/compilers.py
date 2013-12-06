from __future__ import print_function
import os
import six
import subprocess
import logging
import sys


log = logging.getLogger(__name__)


class CompilerError(Exception):
    def __init__(self, args, returncode, stdout, stderr):
        self.command_args = args
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        super(CompilerError, self).__init__()

    def __repr__(self):
        ret = u'Returned exit code {0} for command: "{1}"'.format(
            self.returncode, self.command_args,
        )

        if self.stdout:
            ret += u'\nOutput:\n{0}'.format(self.stdout.strip())
        if self.stderr:
            ret += u'\nErrors:\n{0}'.format(self.stderr.strip())
        return ret


def local(*args, **kw):
    """
    Run a local command
    """
    if log.isEnabledFor(logging.INFO):
        log.info(' '.join(args[0]))
    p = subprocess.Popen(
        *args,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **kw
    )

    stdout, stderr = p.communicate()
    if p.returncode != 0:
        raise CompilerError(args, p.returncode, stdout, stderr)
    return stdout, stderr


class Compiler(object):

    def __init__(self, output_file, dependent, maker=None):
        """
        A base class for compilers

        ``output_file`` - the output file relative to the project directory
        ``dependent`` - dependent files. Expects a list of glob patterns or functions.
            dependent functions will be called with no arguments to get a list of files.
            If ``dependent`` is a string, it will be converted to a list.
        """

        # the maker instance. this will be set when this instance is used by a Maker
        self.output_file = output_file
        self._output_file = output_file
        self.output_directory = None
        self._maker = None
        self.maker = maker

        if isinstance(dependent, six.string_types):
            dependent = [dependent]
        self.dependent = dependent
        super(Compiler, self).__init__()

    @property
    def maker(self):
        return self._maker

    @maker.setter
    def maker(self, v):
        self._maker = v
        if self._maker:
            self.output_directory = os.path.abspath(
                os.path.join(self.maker.directory, os.path.dirname(self.output_file)))
            #self.output_file = os.path.abspath(os.path.join(self.maker.directory, self._output_file))

    def sources(self):
        for source in self.dependent:
            yield os.path.join(self.maker.directory, source)

    def __call__(self, *args, **kwargs):
        try:
            self.run()
        except CompilerError as c:
            log.error('Task failed')
            print(
                u'========================================\n'
                u'Task failed: {}'.format(repr(c)) +
                u'\n========================================',
                file=sys.stderr
            )
        except Exception:
            log.exception('Task failed')

    def run(self):
        raise NotImplementedError()

    def __repr__(self):
        return u'<{} -> [{}]>'.format(self.output_file, ', '.join(self.dependent))


class coffee(Compiler):
    def run(self):
        # ensure the destination directory exists
        try:
            os.makedirs(self.output_directory)
        except OSError as e:
            if e.errno != 17:
                # the directory might already exist (because another thread created it)
                raise

        # stupid coffee compiler expects a directory and you can't just give it an output file _name_
        stdout, stderr = local(['coffee', '--print'] + list(self.sources()))
        log.info('writing {0}'.format(self.output_file))
        with open(self.output_file, 'wb') as f:
            f.write(stdout)


class uglify(Compiler):
    def run(self):
        if not os.path.exists(self.output_directory):
            log.info('mkdir -p {0}'.format(self.output_directory))
            os.makedirs(self.output_directory)

        local([
            'uglifyjs',
            '-o',
            self.output_file,
        ] + list(self.sources()))


class compass(Compiler):
    """
    The Compass compiler for sass projects
    """
    def run(self):
        # this assumes you have most project settings defined in config.rb
        local(['compass', 'compile'] + list(self.sources()))
