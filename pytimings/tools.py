import atexit
import os
import time
from functools import partial
from pathlib import Path
from typing import Union


def ensure_directory_exists(dirname):
    """create dirname if it doesn't exist"""
    try:
        os.makedirs(dirname)
    except FileExistsError:
        pass


def output_at_exit(output_dir: Union[str, Path] = None, csv_base='timings', timings=None) -> None:
    from pytimings.timer import global_timings

    output_dir = output_dir or os.getcwd()
    output_dir = Path(output_dir)
    ensure_directory_exists(output_dir)
    timings = timings or global_timings
    output = partial(timings.output_files, output_dir=output_dir, csv_base=csv_base)
    atexit.register(output)


def busywait(secs):
    """busywait simulates load, so user time won't be 0 in timings"""
    init_time = time.time()
    while time.time() < init_time + secs:
        pass
    return time.time() - init_time


def generate_example_data(output_dir, number_of_runs=10):
    from pytimings.timer import Timings, scoped_timing

    files = []
    for i in range(1, number_of_runs):
        timings = Timings()
        timings.add_extra_data({'run': i})
        with scoped_timing("linear", timings=timings):
            busywait(number_of_runs / 10 / i)
        with scoped_timing("quadratic", timings=timings):
            busywait(number_of_runs / 10 / i ** 2)
        files.append(timings.output_files(output_dir=output_dir, csv_base=f'example_speedup_{i:05}', per_rank=False))
    return files
