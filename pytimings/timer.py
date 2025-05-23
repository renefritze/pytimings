"""Main module."""

from __future__ import annotations

import csv
import functools
import shutil
import sys
import time
from collections import defaultdict, namedtuple
from contextlib import contextmanager
from datetime import timedelta
from io import StringIO
from pathlib import Path

import psutil

import pytimings
from pytimings.tools import ensure_directory_exists

try:
    PERF_COUNTER_FUNCTION = time.perf_counter_ns
    THREAD_TIME_FUNCTION = time.time_ns
    TO_SECONDS_FACTOR = 1e-9
except AttributeError:
    PERF_COUNTER_FUNCTION = time.perf_counter
    try:
        THREAD_TIME_FUNCTION = time.thread_time
    except AttributeError:
        # TODO Log warning
        THREAD_TIME_FUNCTION = time.process_time
    TO_SECONDS_FACTOR = 1

THREAD_TIME = "thread"
WALL_TIME = "wall"
SYS_TIME = "sys"
USER_TIME = "user"

TimingDelta = namedtuple("TimingDelta", [WALL_TIME, SYS_TIME, USER_TIME])


class NoTimerError(Exception):
    def __init__(self, section, timings=None):
        self.section = section
        self.timings = timings or global_timings
        avail = "Available sections: " + ",".join(self.timings._known_timers_map.keys())
        super().__init__(f"trying to access timer for unknown section '{section}'\n{avail}")


class TimingData:
    def __init__(self, name):
        self.name = name
        self._end_resources = None
        self._end_times = None
        self._process = psutil.Process()
        self._start_times = self._get()

    def _get(self):
        ps_times = self._process.cpu_times()
        return {
            USER_TIME: ps_times.user,
            SYS_TIME: ps_times.system,
            WALL_TIME: PERF_COUNTER_FUNCTION(),
            THREAD_TIME: THREAD_TIME_FUNCTION(),
        }

    def stop(self):
        self._end_times = self._get()

    def delta(self):
        delta_times = self._end_times or self._get()

        wall = (delta_times[WALL_TIME] - self._start_times[WALL_TIME]) * TO_SECONDS_FACTOR
        # kernel resource usage already is in seconds
        return TimingDelta(
            wall,
            delta_times[SYS_TIME] - self._start_times[SYS_TIME],
            delta_times[USER_TIME] - self._start_times[USER_TIME],
        )


def _default_timer_dict_entry():
    return (False, None)


class Timings:
    def __init__(self):
        self._commited_deltas: dict[str, TimingDelta] = {}
        self._known_timers_map: dict[str, tuple[bool, TimingData | None]] = defaultdict(_default_timer_dict_entry)
        self.extra_data = dict()
        self.reset()

    def start(self, section_name: str) -> None:
        """set this to begin a named section"""
        if section_name in self._known_timers_map.keys():
            running, data = self._known_timers_map[section_name]
            if running:
                # TODO log info
                return
        self._known_timers_map[section_name] = (True, TimingData(section_name))

    def stop(self, section_name: str | None = None) -> int:
        """stop named section's counter or all of them if section_name is None"""
        if section_name is None:
            for section in self._known_timers_map.keys():
                self.stop(section)
            return
        if section_name not in self._known_timers_map.keys():
            raise NoTimerError(section_name, self)
        self._known_timers_map[section_name] = (
            False,
            self._known_timers_map[section_name][1],
        )  # mark as not running
        timing = self._known_timers_map[section_name][1]
        timing.stop()
        delta = timing.delta()
        if section_name not in self._commited_deltas.keys():
            self._commited_deltas[section_name] = delta
        else:
            previous_delta = self._commited_deltas[section_name]
            new_delta = TimingDelta(*tuple(map(sum, zip(delta, previous_delta))))
            self._commited_deltas[section_name] = new_delta
        return self._commited_deltas[section_name]

    def reset(self, section_name: str | None = None) -> None:
        """set elapsed time back to 0 for a given section or all of them if section_name is None"""
        if section_name is None:
            for section in self._known_timers_map.keys():
                self.reset(section)
            return
        try:
            self.stop(section_name)
        except NoTimerError:
            pass  # not stopping no timer is not an error
        self._commited_deltas[section_name] = TimingDelta(0, 0, 0)

    def walltime(self, section_name: str) -> int:
        """get runtime of section in milliseconds"""
        return self.delta(section_name)[0]

    def add_walltime(self, section_name: str, time: int) -> None:
        self._commited_deltas[section_name] = TimingDelta(time, 0, 0)

    def delta(self, section_name: str) -> dict[str, int]:
        """get the full delta dict"""
        try:
            return self._commited_deltas[section_name]
        except KeyError:
            raise NoTimerError(section_name, self)  # noqa: B904

    def output_files(self, output_dir: Path, csv_base: str) -> Path:
        """output all recorded measures to a csv file"""
        output_dir = Path(output_dir)
        ensure_directory_exists(output_dir)
        outfile = output_dir / f"{csv_base}.csv"
        with outfile.open("w") as out:
            self.output_all_measures(out)
        return outfile

    def output_console(self):
        """outputs walltime only w/o MPI-rank averaging"""
        from rich import box, console, table

        csl = console.Console()
        tbl = table.Table(show_header=True, header_style="bold blue", box=box.SIMPLE_HEAVY)
        tbl.add_column("Extra")
        tbl.add_column("Data")
        for key, value in self.extra_data.items():
            tbl.add_row(key, str(value))
        if len(self.extra_data):
            csl.print(tbl)

        tbl = table.Table(show_header=True, header_style="bold magenta", box=box.SIMPLE_HEAVY)
        tbl.add_column("Section")
        tbl.add_column(
            "Walltime (HH:MM:SS)",
            justify="right",
        )
        for section, delta in self._commited_deltas.items():
            tbl.add_row(section, str(timedelta(seconds=delta[0])))
        if len(self._commited_deltas):
            csl.print(tbl)
        else:
            csl.print("No timings were recorded")

    def output_all_measures(self, out=None) -> None:
        """output all recorded measures

        Outputs average, min, max over all MPI processes associated to mpi_comm
        """
        out = out or sys.stdout
        stash = StringIO()
        csv_file = csv.writer(stash, lineterminator="\n")
        # header
        csv_file.writerow(["section", "value"])

        # threadManager().max_threads()
        csv_file.writerow(["threads", 1])

        for section, delta in self._commited_deltas.items():
            delta = delta._asdict()  # noqa: PLW2901
            wall = delta[WALL_TIME]
            usr = delta[USER_TIME]
            syst = delta[SYS_TIME]
            csv_file.writerows(
                [
                    [f"{section}_usr", usr],
                    [f"{section}_wall", wall],
                    [f"{section}_sys", syst],
                ]
            )
        csv_file.writerows([[f"pytimings::data::{k}", v] for k, v in self.extra_data.items()])
        csv_file.writerow(
            [
                "pytimings::data::_sections",
                "||".join(sorted(self._commited_deltas.keys())),
            ]
        )
        csv_file.writerow(["pytimings::data::_version", pytimings.__version__])
        stash.seek(0)
        shutil.copyfileobj(stash, out)

    def add_extra_data(self, data: [dict]):
        """Use this for something configuration data that makes the csv more informative.

        Data is not displayed with console output.
        """
        self.extra_data.update(data)


global_timings = Timings()


@contextmanager
def scoped_timing(section_name, log_function=None, timings=None, format=""):
    """Start timer on entering block scope, stop it (and optionally output) on exiting.

    The printout will only show walltime for the current scope.
    See :py:func:`pytimings.timer.cummulative_scoped_timing` for a version with cummulative output.
    """
    timings = timings or global_timings
    timings.start(section_name)
    try:
        yield
    finally:
        try:
            previous_wall = timings.walltime(section_name)
        except:  # noqa: E722
            previous_wall = 0
        delta = timings.stop(section_name)
        if log_function:
            log_function(f"Executing {section_name} took {delta.wall - previous_wall:^{format}}s")


@contextmanager
def cummulative_scoped_timing(section_name, log_function=None, timings=None, format=""):
    """Start timer on entering block scope, stop it (and optionally output) on exiting.

    The printout will show the cummulated walltime for all scopes with this section name.
    See :py:func:`pytimings.timer.scoped_timing` for a version with non-cummulative output.
    """
    timings = timings or global_timings
    timings.start(section_name)
    try:
        yield
    finally:
        delta = timings.stop(section_name)
        if log_function:
            log_function(f"Executing {section_name} cummulatively took {delta.wall:^{format}}s")


def function_timer(section_name=None, log_function=None, timings=None):
    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            with scoped_timing(
                section_name=section_name or function.__qualname__,
                log_function=log_function,
                timings=timings,
            ):
                return function(*args, **kwargs)

        return wrapper

    return decorator
