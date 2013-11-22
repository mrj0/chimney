import os
import six
import subprocess
import logging


log = logging.getLogger(__name__)


def local(*args, **kw):
    """
    Run a local command
    """
    if log.isEnabledFor(logging.INFO):
        log.info(str(args))
    p = subprocess.Popen(
        *args,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **kw
    )

    return p.communicate()


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
            self.output_file = os.path.abspath(os.path.join(self.maker.directory, self._output_file))

    def sources(self):
        for source in self.dependent:
            yield os.path.join(self.maker.directory, source)

    def __call__(self, *args, **kwargs):
        try:
            self.run()
        except Exception:
            log.exception('Task failed')

    def run(self):
        raise NotImplementedError()

    def __repr__(self):
        return u'<{} -> [{}]>'.format(self.output_file, ', '.join(self.dependent))


class coffee(Compiler):
    def run(self):
        # ensure the destination directory exists
        if not os.path.exists(self.output_directory):
            log.info('mkdir -p {0}'.format(self.output_directory))
            os.makedirs(self.output_directory)

        local(
            # stupid coffee compiler expects a directory and you can't just give it an output file _name_
            'coffee --print "{0}" > "{1}"'.format(' '.join(self.sources()), self.output_file),
            shell=True,
        )


class uglify(Compiler):
    def run(self):
        if not os.path.exists(self.output_directory):
            log.info('mkdir -p {0}'.format(self.output_directory))
            os.makedirs(self.output_directory)

        local([
            'uglifyjs2',
            '--no-copyright',
            '-o',
            self.output_file,
        ] + list(self.sources())
        )


class compass(Compiler):
    """
    The Compass compiler for sass projects
    """
    def run(self):
        # this assumes you have most project settings defined in config.rb
        local(
            'compass compile "{0}"'.format(' '.join(self.sources())),
            shell=True,
        )
