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

To get this functionality, simply change the above example to:

```python
chimney.watch(
    coffee('smoke.js', ['wood.coffee', 'fire.coffee']),
    uglify('smoke.min.js', 'smoke.js'),
)
```

Whenever the coffee files are changed, ``smoke.js`` will be re-created
using the ``coffee`` compiler. Then ``smoke.min.js`` will be created, too.


About
-----

Why the name Chimney?

Well, these web projects are busy solving lots of problems. They're on
fire. And you can't bring a fire in-house unless you have a
chimney. Something like that. (And the pypi name was available.)
