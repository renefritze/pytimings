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


Extra Data
===========


{class}`pytimings.timer.Timings` objects have a supplementary
key-value storage which makes it easy to tag timings data with metadata.

```{code-cell}

from pytimings.timer import global_timings
global_timings
```

Now add any metadata you want as a dictionary:

```{code-cell}

global_timings.add_extra_data(
    {
        "program_version": 1,
        "problem_size": 9001
    }
)
```


In console output you'll see the extra data as another table. In CSV-file outputs
it is added as additional rows.

```{code-cell}

global_timings.output_console()
```
