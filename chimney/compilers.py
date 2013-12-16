from __future__ import print_function
import os
import six
import subprocess
import logging
import sys
from path import path
from chimney import flags
from chimney.flags import Arguments, Flag


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


def mkdirs(path, mode=0777):
    try:
        os.makedirs(path, mode=mode)
    except OSError as e:
        if e.errno != 17:
            # the directory might already exist (because another thread created it)
            raise


class Compiler(object):
    arguments = Arguments()

    def __init__(self, output_file, dependent, maker=None, extra_flags=None, **kwargs):
        """
        A base class for compilers

        ``output_file`` - the output file relative to the project directory
        ``dependent`` - dependent files. Expects a list of glob patterns or functions.
            dependent functions will be called with no arguments to get a list of files.
            If ``dependent`` is a string, it will be converted to a list.
        """

        # the maker instance. this will be set when this instance is used by a Maker
        self.output_file = path(output_file)
        self.output_directory = None
        self._maker = None
        self.maker = maker
        self.extra_flags = extra_flags or {}

        if isinstance(dependent, six.string_types):
            dependent = [dependent]
        self.dependent = map(path, dependent)
        super(Compiler, self).__init__()

        # parse the keywords into extra_flags
        if self.arguments:
            for name, value in six.iteritems(kwargs):
                flag = self.arguments.args.get(name)
                if flag is None:
                    raise flags.InvalidFlagError(u'Invalid flag: {0}'.format(name))
                flag.validate(value)
                self.extra_flags[flag.switch] = value

    @property
    def maker(self):
        return self._maker

    @maker.setter
    def maker(self, v):
        self._maker = v
        if self._maker:
            self.output_directory = self.output_file.dirname()

    def sources(self):
        """
        A generator for dependent files for use with the compiler. The path to resources
        may be adjusted to work in the compiler's execution environment.
        """
        for source in self.dependent:
            yield source

    def get_flags(self):
        """
        Return extra_flags as a list for execute()
        """
        return [u'{0} {1}'.format(n, v) for n, v in six.iteritems(self.extra_flags)]

    def __call__(self, *args, **kwargs):
        try:
            if max([d.mtime for d in self.sources()]) < self.output_file.mtime:
                return
        except OSError as e:
            # a file doesn't exist?
            pass

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

    def execute_command(self, *args, **kw):
        """
        Execute a command
        """
        return local(*args, **kw)


class ShellCompilerMixin(object):
    def execute_command(self, *args, **kw):
        # uglify run without shell=True doesn't create source maps, todo
        if log.isEnabledFor(logging.INFO):
            log.info(' '.join(args[0]))
        p = subprocess.Popen(
            ' '.join(args[0]),
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            **kw
        )

        stdout, stderr = p.communicate()
        returncode = p.poll()
        if returncode != 0:
            raise CompilerError(args, returncode, stdout, stderr)
        return stdout, stderr


class coffee(Compiler):
    def run(self):
        mkdirs(self.output_directory)

        # stupid coffee compiler expects a directory and you can't just give it an output file _name_
        stdout, stderr = self.execute_command(['coffee', '--print'] + list(self.sources()))
        log.info('writing {0}'.format(self.output_file))
        with open(self.output_file, 'wb') as f:
            f.write(stdout)


class sqwish(Compiler):
    def run(self):
        cmd = ['sqwish'] + list(self.sources()) + ['-o', self.output_file]
        self.execute_command(cmd)


class uglify(ShellCompilerMixin, Compiler):
    arguments = Arguments(
        source_map=Flag(),
        source_map_root=Flag(required=True),
        source_map_url=Flag(required=True),
        in_source_map=Flag(),
        wrap=Flag(required=True),
        export_all=Flag(),
        define=Flag(required=True),
        enclose=Flag(required=True),
        acorn=Flag(),
        screw_ie8=Flag(),
    )

    def __init__(self, output_file, dependent, maker=None, extra_flags=None, **kwargs):
        # make some default options for these source map files. uglify doesn't do anything sensible

        if 'source_map' in kwargs and kwargs['source_map'] is None:
            kwargs['source_map'] = os.path.join(os.path.dirname(output_file),
                                                os.path.basename(output_file) + u'.map')
        if 'source_map_url' in kwargs and kwargs['source_map_url'] is None:
            kwargs['source_map_url'] = os.path.basename(output_file) + u'.map'

        super(uglify, self).__init__(output_file, dependent, maker, extra_flags, **kwargs)

    def run(self):
        mkdirs(self.output_directory)

        cmd = ['uglifyjs'] + self.get_flags() + ['-o', self.output_file] + list(self.sources())
        self.execute_command(cmd)


class compass(Compiler):
    """
    The Compass compiler for sass projects
    """
    def run(self):
        # this assumes you have most project settings defined in config.rb
        self.execute_command(['compass', 'compile'] + list(self.sources()))
