import os
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class Observation(object):
    __slots__ = ['path', 'type']

    def __init__(self, path, event_type):
        self.path = path
        self.type = event_type

    def __repr__(self):
        return u'<Observation>("{}", "{}")'.format(self.path, self.type)

    def __str__(self):
        return u'<Observation>("{}", "{}")'.format(self.path, self.type)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return self.path == other.path and self.type == other.type

    def __ne__(self, other):
        return self.path != other.path or self.type != other.type


class Watcher(FileSystemEventHandler):
    def __init__(self, change_handler, path=os.curdir):
        self.change_handler = change_handler

        self.observer = Observer()
        self.observer.schedule(self, path, recursive=True)
        self.observer.start()

        super(Watcher, self).__init__()

    def on_modified(self, event):
        self.change_handler(Observation(event.src_path, event.event_type))

    def stop(self):
        self.observer.stop()
