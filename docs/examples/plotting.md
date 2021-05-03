---
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

Plotting
===========


Let us first generate some example data with CSV output files.

```{code-cell}

from os import getcwd
from pytimings.tools import generate_example_data

filenames = generate_example_data(getcwd())

```

We'll then read those example files.

```{code-cell}

from pytimings.processing import csv_to_dataframe

dataframe = csv_to_dataframe(filenames, sort=True)
dataframe.plot(x='pytimings::data::run', y=['quadratic_max_wall', 'linear_max_wall'], logy=True)
```
