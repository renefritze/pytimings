from io import StringIO
from pytest_regressions import file_regression
import pytest

from .fixtures import timings_object, use_mpi, pickled_timings_object, mpi_file_regression


def test_output_all_measures(pickled_timings_object, mpi_file_regression):
    timing = pickled_timings_object
    with StringIO() as out:
        timing.output_all_measures(out)
        out.seek(0)
        mpi_file_regression.check(out.read())


def test_output_simple(pickled_timings_object, file_regression):
    timing = pickled_timings_object
    with StringIO() as out:
        timing.output_all_measures(out)
        out.seek(0)
        file_regression.check(out.read())


def test_output_per_rank(pickled_timings_object, file_regression, tmp_path):
    fn = pickled_timings_object.output_per_rank(output_dir=tmp_path, csv_base='per_rank')

    if fn is not None:
        # we're rank 0 and have written the summary file
        file_regression.check(open(fn).read())
