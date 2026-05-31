"""Main module."""

from __future__ import annotations

import csv
import functools
import logging
import shutil
import sys
import time
from collections import defaultdict
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import timedelta
from io import StringIO
from pathlib import Path
from typing import NamedTuple

import psutil

import pytimings
from pytimings.tools import ensure_directory_exists

logger = logging.getLogger(__name__)

PERF_COUNTER_FUNCTION = time.perf_counter_ns
THREAD_TIME_FUNCTION = time.time_ns
TO_SECONDS_FACTOR = 1e-9

THREAD_TIME = "thread"
WALL_TIME = "wall"
SYS_TIME = "sys"
USER_TIME = "user"


class TimingDelta(NamedTuple):
    """Elapsed wall/system/user time for a section, all in seconds."""

    wall: float
    sys: float
    user: float


__all__ = [
    "SYS_TIME",
    "THREAD_TIME",
    "USER_TIME",
    "WALL_TIME",
    "NoTimerError",
    "TimingData",
    "TimingDelta",
    "Timings",
    "cummulative_scoped_timing",
    "function_timer",
    "global_timings",
    "scoped_timing",
]


class NoTimerError(Exception):
    def __init__(self, section: str, timings: Timings | None = None, is_unstopped: bool = False) -> None:
        self.section = section
        self.timings = timings or global_timings
        self.is_unstopped = is_unstopped
        if is_unstopped:
            super().__init__(f"trying to access timer for section '{section}' that has not been stopped yet")
        else:
            avail = "Available sections: " + ",".join(self.timings._known_timers_map)
            super().__init__(f"trying to access timer for unknown section '{section}'\n{avail}")


class TimingData:
    def __init__(self, name: str) -> None:
        self.name = name
        self._end_resources = None
        self._end_times: dict[str, float] | None = None
        self._process = psutil.Process()
        self._start_times = self._get()

    def _get(self) -> dict[str, float]:
        ps_times = self._process.cpu_times()
        return {
            USER_TIME: ps_times.user,
            SYS_TIME: ps_times.system,
            WALL_TIME: PERF_COUNTER_FUNCTION(),
            THREAD_TIME: THREAD_TIME_FUNCTION(),
        }

    def stop(self) -> None:
        self._end_times = self._get()

    def delta(self) -> TimingDelta:
        delta_times = self._end_times or self._get()

        wall = (delta_times[WALL_TIME] - self._start_times[WALL_TIME]) * TO_SECONDS_FACTOR
        # kernel resource usage already is in seconds
        return TimingDelta(
            wall,
            delta_times[SYS_TIME] - self._start_times[SYS_TIME],
            delta_times[USER_TIME] - self._start_times[USER_TIME],
        )


def _default_timer_dict_entry() -> tuple[bool, TimingData | None]:
    return (False, None)


class Timings:
    def __init__(self) -> None:
        self._commited_deltas: dict[str, TimingDelta] = {}
        self._known_timers_map: dict[str, tuple[bool, TimingData | None]] = defaultdict(_default_timer_dict_entry)
        self.extra_data: dict = dict()
        self.reset()

    def start(self, section_name: str) -> None:
        """set this to begin a named section"""
        if section_name in self._known_timers_map:
            running, _data = self._known_timers_map[section_name]
            if running:
                logger.info("timer for section '%s' is already running, ignoring start()", section_name)
                return
        self._known_timers_map[section_name] = (True, TimingData(section_name))

    def stop(self, section_name: str | None = None) -> TimingDelta | None:
        """stop named section's counter or all of them if section_name is None"""
        if section_name is None:
            for section in self._known_timers_map:
                self.stop(section)
            return None
        if section_name not in self._known_timers_map:
            raise NoTimerError(section_name, self)
        self._known_timers_map[section_name] = (
            False,
            self._known_timers_map[section_name][1],
        )  # mark as not running
        timing = self._known_timers_map[section_name][1]
        timing.stop()
        delta = timing.delta()
        if section_name not in self._commited_deltas:
            self._commited_deltas[section_name] = delta
        else:
            previous_delta = self._commited_deltas[section_name]
            new_delta = TimingDelta(*tuple(map(sum, zip(delta, previous_delta))))
            self._commited_deltas[section_name] = new_delta
        return self._commited_deltas[section_name]

    def reset(self, section_name: str | None = None) -> None:
        """set elapsed time back to 0 for a given section or all of them if section_name is None"""
        if section_name is None:
            for section in self._known_timers_map:
                self.reset(section)
            return
        try:
            self.stop(section_name)
        except NoTimerError:
            pass  # not stopping no timer is not an error
        self._commited_deltas[section_name] = TimingDelta(0, 0, 0)

    def walltime(self, section_name: str) -> float:
        """get runtime of section in seconds"""
        return self.delta(section_name)[0]

    def add_walltime(self, section_name: str, time: float) -> None:
        self._commited_deltas[section_name] = TimingDelta(time, 0, 0)

    def delta(self, section_name: str) -> TimingDelta:
        """get the full delta tuple"""
        try:
            return self._commited_deltas[section_name]
        except KeyError:
            # Check if the timer was started but not stopped
            is_unstopped = section_name in self._known_timers_map
            raise NoTimerError(section_name, self, is_unstopped=is_unstopped) from None

    def output_files(self, output_dir: Path, csv_base: str) -> Path:
        """output all recorded measures to a csv file"""
        output_dir = Path(output_dir)
        ensure_directory_exists(output_dir)
        outfile = output_dir / f"{csv_base}.csv"
        with outfile.open("w") as out:
            self.output_all_measures(out)
        return outfile

    def output_console(self) -> None:
        """output the recorded walltime per section to the console"""
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
        """output all recorded measures"""
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

    def add_extra_data(self, data: dict) -> None:
        """Use this for configuration data that makes the csv more informative.

        The data is also rendered in the console output.
        """
        self.extra_data.update(data)


global_timings = Timings()


@contextmanager
def scoped_timing(
    section_name: str,
    log_function: Callable[[str], None] | None = None,
    timings: Timings | None = None,
    format: str = "",
) -> Iterator[None]:
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
        except NoTimerError:
            previous_wall = 0
        delta = timings.stop(section_name)
        if log_function:
            log_function(f"Executing {section_name} took {delta.wall - previous_wall:^{format}}s")


@contextmanager
def cummulative_scoped_timing(
    section_name: str,
    log_function: Callable[[str], None] | None = None,
    timings: Timings | None = None,
    format: str = "",
) -> Iterator[None]:
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


def function_timer(
    section_name: str | None = None,
    log_function: Callable[[str], None] | None = None,
    timings: Timings | None = None,
) -> Callable:
    def decorator(function: Callable) -> Callable:
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
