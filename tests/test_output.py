from io import StringIO

import pytimings
from pytimings.processing import csv_to_dataframe
from pytimings.tools import generate_example_data


def _content(fd):
    # last line is the version field which is ever changing
    # compare files are stored with unix lf and git set to not modify
    return "".join(fd.readlines()[:-1])


def test_output_all_measures(pickled_timings_object, file_regression):
    timing = pickled_timings_object
    with StringIO() as out:
        timing.output_all_measures(out)
        out.seek(0)
        file_regression.check(_content(out))


def test_output_simple(pickled_timings_object, file_regression):
    timing = pickled_timings_object
    with StringIO() as out:
        timing.output_all_measures(out)
        out.seek(0)
        file_regression.check(_content(out))


def test_output_per_rank(pickled_timings_object, file_regression, tmp_path):
    fn = pickled_timings_object.output_files(output_dir=tmp_path, csv_base="per_rank")

    if fn is not None:
        # we're rank 0 and have written the summary file
        file_regression.check(_content(open(fn)))  # noqa: PTH123


def test_csv_to_dataframe(tmpdir):
    files = generate_example_data(tmpdir)
    assert all(f is not None for f in files), files
    assert all(f.is_file() for f in files), files
    frame = csv_to_dataframe(files)
    assert all(frame["pytimings::data::_version"] == pytimings.__version__)
