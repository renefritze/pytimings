---
kernelspec:
  display_name: Python 3
  name: python3
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
---

Basic Usage
===========

We'll start by importing the (always existing) global `Timings` object.

```{code-cell}

from pytimings.timer import global_timings
global_timings
```

To measure the execution time of a given code segment you can
start a timer with a given section name and stop it afterwards.
`stop` returns a `TimingsDelta` object with the gathered info.

```{code-cell}

global_timings.start("a_section_name")
...
global_timings.stop("a_section_name")

```

To inspect deltas of known sections at any other point
use the `delta` function.

```{code-cell}

global_timings.delta("a_section_name")
```

To get an overview over all sections you can use `output_console`.

```{code-cell}

global_timings.output_console()
```
