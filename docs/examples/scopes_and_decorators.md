---
jupytext:
  text_representation:
   format_name: myst
jupyter:
  jupytext:
    cell_metadata_filter: -all
    formats: ipynb,myst
    main_language: python
    text_representation:
      format_name: myst
      extension: .md
      format_version: '1.3'
      jupytext_version: 1.11.2
kernelspec:
  display_name: Python 3
  name: python3
---


Scopes and Decorators
=====================

Instead of manually starting and stopping timers, you can
automate this by putting a decorator on a function.

```{code-cell}

from pytimings.timer import function_timer

@function_timer()
def mysleep(seconds=1):
    import time
    init_time = time.time()
    while time.time() < init_time + seconds:
        pass

mysleep(1)
```

By default the section name will be the decorated function's `__qualname__`.
You can customize this
```{code-cell}
@function_timer(section_name="not_sleepy")
def mysleep(seconds=1):
    import time
    init_time = time.time()
    while time.time() < init_time + seconds:
        pass
```

This will accumulate the time spent in all calls to `mysleep`.
To demonstrate that, we'll use another automatic timing option:
a context manager called {meth}`pytimings.timer.scoped_timing` which starts a timer
on entering the scope and stops it on leaving.

```{code-cell}

from pytimings.timer import scoped_timing

with scoped_timing(section_name="my_scope"):
    mysleep(0.5)
```

Both the decorator and the context manager use the {attr}`pytimings.timer.global_timings`
object by default, but you can pass in a custom one too.

```{code-cell}

from pytimings.timer import Timings

with scoped_timing(section_name="my_scope", timings=Timings()):
    mysleep(0.5)
```

Now let us take a look at the output for the `global_timings` object.

```{code-cell}

from pytimings.timer import global_timings

global_timings.output_console()
```

You can see that the `my_function` timer recorded all 4 calls,
while the `my_scope` only contains one `0.5` call.
The custom timings object does not interact with the `my_scope` section
of `global_timings`.
