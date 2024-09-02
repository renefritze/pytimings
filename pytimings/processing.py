from collections.abc import Iterable
from logging import getLogger
from pathlib import Path
from typing import Union

import pandas as pd


def csv_to_dataframe(filenames: Iterable[Union[str, Path]], sort=False):
    """Read csv files into a Pandas.DataFrame"""
    if sort:
        filenames = sorted(filenames)
    tbls = [pd.read_csv(fn, index_col=0, header=0, names=[fn]) for fn in filenames]
    timings_cols = [s for s in tbls[0].T.columns if "pytimings::data" not in s]
    dataframe = pd.concat(tbls, axis=1).T
    assert all(dataframe["pytimings::data::_sections"] == dataframe["pytimings::data::_sections"].iloc[0])
    if not all(dataframe["pytimings::data::_version"] == dataframe["pytimings::data::_version"].iloc[0]):
        getLogger("").warning("input csv files created from different pytimings versions")
    for col in timings_cols:
        dataframe[col] = pd.to_numeric(dataframe[col])

    return dataframe
