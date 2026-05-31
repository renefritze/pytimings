from __future__ import annotations

from collections.abc import Iterable
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

logger = getLogger(__name__)

__all__ = ["csv_to_dataframe"]


def csv_to_dataframe(filenames: Iterable[str | Path], sort: bool = False) -> pd.DataFrame:
    """Read csv files into a Pandas.DataFrame"""
    try:
        import pandas as pd
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "csv_to_dataframe requires pandas. Install the optional dependencies with 'pip install pytimings[plot]'."
        ) from e

    if sort:
        filenames = sorted(filenames)
    tbls = [pd.read_csv(fn, index_col=0, header=0, names=[fn]) for fn in filenames]
    timings_cols = [s for s in tbls[0].T.columns if "pytimings::data" not in s]
    dataframe = pd.concat(tbls, axis=1).T
    if not all(dataframe["pytimings::data::_sections"] == dataframe["pytimings::data::_sections"].iloc[0]):
        raise ValueError("input csv files do not all contain the same sections")
    if not all(dataframe["pytimings::data::_version"] == dataframe["pytimings::data::_version"].iloc[0]):
        logger.warning("input csv files created from different pytimings versions")
    for col in timings_cols:
        dataframe[col] = pd.to_numeric(dataframe[col])

    return dataframe
