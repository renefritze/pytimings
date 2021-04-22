"""Main module."""
import functools
import shutil
import sys
import time
from contextlib import contextmanager
from datetime import timedelta
from io import StringIO
from collections import namedtuple, defaultdict
from pathlib import Path
import psutil
from typing import Dict, Tuple, Optional

from pytimings.mpi import get_communication_wrapper, get_local_communicator, get_communicator
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

TimingDelta = namedtuple("TimingDelta", [WALL_TIME, SYS_TIME, USER_TIME], defaults=[0, 0, 0])


class NoTimerError(Exception):
    def __init__(self, section, timings=None):
        self.section = section
        self.timings = timings or global_timings
        avail = 'Available sections: ' + ','.join(self.timings._known_timers_map.keys())
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
        self._commited_deltas: Dict[str, TimingDelta] = {}
        self._known_timers_map: Dict[str, Tuple[bool, Optional[TimingData]]] = defaultdict(_default_timer_dict_entry)
        self._csv_sep = ","
        self.reset()

    def start(self, section_name: str) -> None:
        """set this to begin a named section"""
        if section_name in self._known_timers_map.keys():
            running, data = self._known_timers_map[section_name]
            if running:
                # TODO log info
                return
        self._known_timers_map[section_name] = (True, TimingData(section_name))

    def stop(self, section_name: str = None) -> int:
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

    def reset(self, section_name: str = None) -> None:
        """set elapsed time back to 0 for a given section or all of them if section_name is None"""
        if section_name is None:
            for section in self._known_timers_map.keys():
                self.reset(section)
            return
        try:
            self.stop(section_name)
        except NoTimerError:
            pass  # not stopping no timer is not an error
        self._commited_deltas[section_name] = TimingDelta()

    def walltime(self, section_name: str) -> int:
        """get runtime of section in milliseconds"""
        return self.delta(section_name)[0]

    def add_walltime(self, section_name: str, time: int) -> None:
        self._commited_deltas[section_name] = TimingDelta(time)

    def delta(self, section_name: str) -> Dict[str, int]:
        """get the full delta dict"""
        try:
            return self._commited_deltas[section_name]
        except KeyError:
            raise NoTimerError(section_name, self)

    def output_per_rank(self, output_dir: Path, csv_base: str) -> None:
        """
             creates one file local to each MPI-rank (no global averaging)
        *  one single rank-0 file with all combined/averaged measures
        """
        communication = get_communication_wrapper()
        rank = communication.rank

        ensure_directory_exists(output_dir)
        filename = output_dir / f"{csv_base}_p{rank:08d}.csv"
        with open(filename, "wt") as outfile:
            self.output_all_measures(outfile, get_local_communicator())
        tmp_out = StringIO()
        # all ranks have to participate in the data generation
        self.output_all_measures(tmp_out, get_communicator())
        # but only rank 0 needs to write it
        if rank == 0:
            a_filename = output_dir / f"{csv_base}.csv"
            tmp_out.seek(0)
            open(a_filename, "wt").write(tmp_out.read())
            return a_filename

    def output_console(self):
        """outputs walltime only w/o MPI-rank averaging"""
        from rich import console, table, box

        csl = console.Console()
        tbl = table.Table(show_header=True, header_style="bold magenta", box=box.SIMPLE_HEAVY)
        tbl.add_column("Section")
        tbl.add_column(
            "Walltime (HH:MM:SS)",
            justify="right",
        )
        for section, delta in self._commited_deltas.items():
            tbl.add_row(section, str(timedelta(seconds=delta[0])))
        csl.print(tbl)

    def output_all_measures(self, out=None, mpi_comm=None) -> None:
        """output all recorded measures
        * \note outputs average, min, max over all MPI processes associated to mpi_comm **/"""
        out = out or sys.stdout
        mpi_comm = mpi_comm or get_communicator()
        comm = get_communication_wrapper(mpi_comm)
        stash = StringIO()
        sep = self._csv_sep
        stash.write(f"threads{sep}ranks")
        for section in self._commited_deltas.keys():
            stash.write(
                f'{sep}{section}_avg_usr{sep}{section}_max_usr{sep}{section}_avg_wall{sep}{section}_max_wall{sep}{section}_avg_sys{sep}{section}_max_sys'
            )

        weight = 1 / comm.size

        # threadManager().max_threads() {sep} comm.size()
        stash.write(f"\n1{sep}{comm.size}")

        for section, delta in self._commited_deltas.items():
            delta = delta._asdict()
            wall = delta[WALL_TIME]
            usr = delta[USER_TIME]
            syst = delta[SYS_TIME]
            wall_sum = comm.sum(wall)
            wall_max = comm.max(wall)
            usr_sum = comm.sum(usr)
            usr_max = comm.max(usr)
            sys_sum = comm.sum(syst)
            sys_max = comm.max(syst)
            stash.write(
                f"{sep}{usr_sum * weight}{sep}{usr_max}{sep}{wall_sum * weight}{sep}{wall_max}{sep}{sys_sum * weight}{sep}{sys_max}"
            )

        stash.write("\n")
        stash.seek(0)
        if comm.rank == 0:
            shutil.copyfileobj(stash, out)


global_timings = Timings()


@contextmanager
def scoped_timing(section_name, log_function=None, timings=None, format=''):
    timings = timings or global_timings
    timings.start(section_name)
    try:
        yield
    finally:
        delta = timings.stop(section_name)
        if log_function:
            log_function(f"Executing {section_name} took {delta.wall:^{format}}s\n")


def function_timer(section_name, log_function=None, timings=None):
    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            with scoped_timing(section_name=section_name, log_function=log_function, timings=timings):
                return function(*args, **kwargs)

        return wrapper

    return decorator
