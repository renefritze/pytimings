"""Main module."""
import sys
import time
from resource import getrusage as resource_usage, RUSAGE_SELF
from typing import Dict

from pytimings.mpi import DEFAULT_MPI_COMM

try:
    PERF_COUNTER_FUNCTION = time.perf_counter_ns
    THREAD_TIME_FUNCTION = time.time_ns
    TO_SECONDS_FACTOR = 1e-6
except AttributeError:
    PERF_COUNTER = time.perf_counter
    try:
        THREAD_TIME_FUNCTION = time.thread_time
    except AttributeError:
        # TODO Log warning
        THREAD_TIME_FUNCTION = time.process_time
    TO_SECONDS_FACTOR = 1e-3

THREAD_TIME = "thread"
WALL_TIME = "wall"


class TimingData:
    def __init__(self, name):
        self.name = name
        self._end_resources = None
        self._end_times = None
        self._start_resources, self._start_times = self._get()

    def _get(self):
        return resource_usage(RUSAGE_SELF), {
            WALL_TIME: PERF_COUNTER_FUNCTION(),
            THREAD_TIME: THREAD_TIME_FUNCTION(),
        }

    def stop(self):
        self._end_resources, self._end_times = self._get()

    def delta(self):
        if self._end_times:
            delta_resources = self._start_resources
            delta_times = self._end_times
        else:
            delta_resources, delta_times = self._get()

        wall = (
            self._delta_times[WALL_TIME] - self._start_times[WALL_TIME]
        ) * TO_SECONDS_FACTOR
        # kernel resource usage already is in seconds
        return {
            WALL_TIME: wall,
            "sys": delta_resources.ru_stime - self._start_resources.ru_stime,
            "user": delta_resources.ru_utime - self._start_resources.ru_utime,
        }


class Timings:
    def __init__(self):
        self._commited_deltas: Dict[str, Dict] = {}
        self._output_dir = None
        self._known_timers_map = {}
        self._csv_sep = ","

    def stop(self) -> None:
        pass

    def start(self, section_name: str) -> None:
        """set this to begin a named section"""

    def stop(self, section_name: str) -> int:
        """stop named section's counter"""

    def reset(self, section_name: str = None) -> None:
        """set elapsed time back to 0 for a given section or all of them if section_name is NOne"""

    def walltime(self, section_name: str) -> int:
        """get runtime of section in milliseconds"""

    def delta(self, section_name: str) -> Dict[str, int]:
        """get the full delta dict"""

    def output_per_rank(csv_base: str) -> None:
        """
             creates one file local to each MPI-rank (no global averaging)
        *  one single rank-0 file with all combined/averaged measures
        """

    def output_simple(out=None):
        """outputs walltime only w/o MPI-rank averaging"""
        out = out or sys.stdout

    def output_all_measures(out=None, mpi_comm=None) -> None:
        """output all recorded measures
        * \note outputs average, min, max over all MPI processes associated to mpi_comm **/"""
        out = out or sys.stdout
        mpi_comm = mpi_comm or DEFAULT_MPI_COMM

    def set_outputdir(dirname: str) -> None:
        pass


global_timings = Timings()
