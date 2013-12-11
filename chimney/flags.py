import six


class InvalidFlagError(Exception):
    pass


class InvalidFlagValueError(InvalidFlagError):
    pass


class Arguments(object):
    def __init__(self, **kw):
        super(Arguments, self).__init__()

        self.args = {}
        for name, arg in six.iteritems(kw):
            arg.name = name
            self.args[name] = arg


class Flag(object):
    def __init__(self, switch=None, required=False):
        self._name = None
        self.required = required
        self.switch = switch
        super(Flag, self).__init__()

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name
        if self.switch is None:
            self.switch = u'{0}{1}'.format('-' if len(name) == 1 else '--', name.replace('_', '-'))

    def validate(self, value):
        if value:
            value = value.strip()
        if self.required and not value:
            raise InvalidFlagValueError(u'{0} requires a value'.format(self.name))
