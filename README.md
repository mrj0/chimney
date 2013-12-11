Chimney
=======

You may need a coffeescript compile, a browserify transform and then
want to run uglify to minimize the source for production javascript
files. Or a maybe a SASS compile and minimization.

Chimney is a simple build system primarily intended for web
assets. There are many build systems and most asset compilers are
capable of watching for changes, but it becomes difficult to manage
when more steps are added to the pipeline.

Compilers
---------

At each step of the process, there is some input, some output and a
transformation process. Chimney simply calls these "compilers" for
simplicity, but they can be any kind of Python code.

To declare a new type of compiler, define a subclass of ``Compiler``:

```python
from chimney.compilers import Compiler

class coffee(Compiler):
    def run(self):
        # perform compile
```

Targets
-------

Targets are the goal of compilation. This might be a final executable
or an combined javascript file for a page.

Here is an example of a javascript target that needs to be built from
several coffee files (this is using the above compiler):

```python
import chimney

chimney.make(
    coffee('smoke.js', ['wood.coffee', 'fire.coffee']),
)
```

This will compile each of the .coffee dependencies to their .js output
forms using the ``coffee`` compiler defined above, then combine those
files into ``smoke.js``.

Next, there should be a step to minify ``smoke.js`` if needed. That's
easy with chimney, simply add another task to the above definition:

```python
chimney.make(
    coffee('smoke.js', ['wood.coffee', 'fire.coffee']),
    uglify('smoke.min.js', 'smoke.js'),
)
```

Chimney already provides compilers for the most popular web
assets. Others can easily be added to your script by extending the
Compiler class.

Watching for changes
--------------------

To automatically re-execute tasks when their dependencies change,
the function ``chimney.watch`` will first execute all tasks normally
but then it will watch for any filesystem changes.

To get this functionality, the api is slightly different. Instead of
expecting a list of tasks, the function ``chimney.watch`` requires
a function. This is called when new files are added so the dependencies
can be recalculated. For example:

```python
def create_tasks():
    return [
        coffee('smoke.js', ['wood.coffee', 'fire.coffee']),
        uglify('smoke.min.js', 'smoke.js'),
    ]

chimney.watch(create_tasks)
```

Whenever the coffee files are changed, ``smoke.js`` will be re-created
using the ``coffee`` compiler. Then ``smoke.min.js`` will be created, too.
When new files are added, the function ``create_tasks`` will be re-executed
to build a new set of tasks. This is useful for dynamically building
tasks.

By default, the reload will start chimney on all new files, which may
be too often. You can provide a list of (shell) patterns to match
to limit reloading:

```python
def create_tasks():
    return [
        coffee('smoke.js', ['wood.coffee', 'fire.coffee']),
        uglify('smoke.min.js', 'smoke.js'),
    ]

chimney.watch(create_tasks, reload_patterns=['*.coffee'])
```
