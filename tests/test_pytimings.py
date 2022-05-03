#!/usr/bin/env python

"""Tests for `pytimings` package."""
import pickle
import numpy as np
from functools import partial
from tempfile import TemporaryFile

from click.testing import CliRunner

from pytimings import cli
from pytimings.timer import scoped_timing, cummulative_scoped_timing, function_timer
from pytimings.tools import output_at_exit, busywait
from .fixtures import is_windows_platform

_DUMMY_SECTION = 'mysection'

DEFAULT_SLEEP_SECONDS = 0.1


default_sleep = partial(busywait, DEFAULT_SLEEP_SECONDS)


def _assert(delta_value, lower=DEFAULT_SLEEP_SECONDS, upper=None):
    if is_windows_platform():
        fuzzy_factor = 0.98
        lower = lower * fuzzy_factor
        if upper:
            upper = upper / fuzzy_factor
    if upper is None:
        assert delta_value > lower
    else:
        assert upper > delta_value > lower


def test_content(timings_object):
    timings_object.start(_DUMMY_SECTION)
    slept = default_sleep()
    timed = timings_object.stop(_DUMMY_SECTION)
    _assert(timed.wall, lower=slept)
    timings_object.stop()
    timings_object.output_all_measures()
    timings_object.reset(_DUMMY_SECTION)
    timings_object.reset()
    timings_object.start(_DUMMY_SECTION)
    slept = default_sleep()
    timed = timings_object.stop(_DUMMY_SECTION)
    _assert(timed.wall, lower=slept, upper=1.1 * slept)
    timings_object.stop()
    timings_object.output_all_measures()


def test_nesting(timings_object):
    scope = partial(scoped_timing, timings=timings_object)
    sleeps = []
    with scope("root_section"):
        sleeps.append(default_sleep())
        with scope("root_section.nested_1"):
            sleeps.append(default_sleep())
            with scope("root_section.nested_1.leaf_section"):
                sleeps.append(default_sleep())
            timed = timings_object.delta("root_section.nested_1.leaf_section")
            _assert(timed.wall, lower=sum(sleeps[-1:]), upper=1.1 * sum(sleeps[-2:]))
        timed = timings_object.delta("root_section.nested_1")
        _assert(timed.wall, lower=sum(sleeps[-2:]), upper=1.1 * sum(sleeps[-3:]))
    timed = timings_object.delta("root_section")
    _assert(timed.wall, lower=sum(sleeps), upper=1.1 * sum(sleeps))


def test_pickling(pickled_timings_object):
    with TemporaryFile() as out:
        dump = partial(pickle.dump, pickled_timings_object, out)
        dump(protocol=0)
        dump(protocol=pickle.HIGHEST_PROTOCOL)
        dump(protocol=pickle.DEFAULT_PROTOCOL)


def test_context(timings_object):
    timings_object.start(_DUMMY_SECTION)
    default_sleep()
    timings_object.stop(_DUMMY_SECTION)
    delta_before = timings_object.delta(_DUMMY_SECTION)
    with scoped_timing(_DUMMY_SECTION, timings=timings_object):
        default_sleep()
    delta_after = timings_object.delta(_DUMMY_SECTION)
    _assert(delta_after.wall, lower=delta_before.wall)
    _assert(delta_after.user, lower=delta_before.user)

    # use the global timings object default
    delta_before = timings_object.delta(_DUMMY_SECTION)
    with scoped_timing(_DUMMY_SECTION):
        default_sleep()
    delta_after = timings_object.delta(_DUMMY_SECTION)
    assert delta_after == delta_before


def test_decorator(timings_object):
    @function_timer(section_name=_DUMMY_SECTION, timings=timings_object)
    def decorated():
        default_sleep()

    assert _DUMMY_SECTION not in timings_object._known_timers_map.keys()
    decorated()
    delta_before = timings_object.delta(_DUMMY_SECTION)
    decorated()
    delta_after = timings_object.delta(_DUMMY_SECTION)
    _assert(delta_after.wall, lower=delta_before.wall)
    _assert(delta_after.user, lower=delta_before.user)


def test_decorator_default_name(timings_object):
    @function_timer(timings=timings_object)
    def my_decorated_name():
        default_sleep()

    class OuterClass:
        @function_timer(timings=timings_object)
        def my_inner_name(self):
            default_sleep()

    section = "test_decorator_default_name.<locals>.my_decorated_name"
    assert section not in timings_object._known_timers_map.keys()
    my_decorated_name()
    delta_before = timings_object.delta(section)
    my_decorated_name()
    delta_after = timings_object.delta(section)
    _assert(delta_after.wall, lower=delta_before.wall)
    _assert(delta_after.user, lower=delta_before.user)

    section = "test_decorator_default_name.<locals>.OuterClass.my_inner_name"
    assert section not in timings_object._known_timers_map.keys()
    obj = OuterClass()
    obj.my_inner_name()
    delta_before = timings_object.delta(section)
    obj.my_inner_name()
    delta_after = timings_object.delta(section)
    _assert(delta_after.wall, lower=delta_before.wall)
    _assert(delta_after.user, lower=delta_before.user)


def test_simple_output(timings_object):
    # simple output with optional format specifier
    with scoped_timing("time", print, timings=timings_object, format='.5f'):
        default_sleep()
    with scoped_timing("a much longer section name", print, timings=timings_object):
        busywait(1)
    scoped_sleepy_time = timings_object.walltime("time")
    timings_object.output_console()

    # add a known walltime to the timings object
    timings_object.add_walltime('sleepy_time', DEFAULT_SLEEP_SECONDS)
    sleepy_time = timings_object.walltime("sleepy_time")
    np.isclose(scoped_sleepy_time, sleepy_time)


def test_cummulative_scoped_timings(timings_object):
    # 'scoped_timing' and 'cummulative_scoped_timing' only differ in terms of their output, but not in terms
    # of their way of storing deltas
    with scoped_timing("time", print, timings=timings_object, format='.5f'):
        default_sleep()
    with scoped_timing("time", print, timings=timings_object, format='.5f'):
        # printout will be default_sleep()
        default_sleep()

    with cummulative_scoped_timing("another time", print, timings=timings_object, format='.5f'):
        default_sleep()
    with cummulative_scoped_timing("another time", print, timings=timings_object, format='.5f'):
        # printout will be 2 * default_sleep()
        default_sleep()

    # but this doesn't matter for the objects
    np.isclose(timings_object.walltime("time"), timings_object.walltime("another time"))


def test_atexit(timings_object):
    """This only tests if the setup function can be called"""
    output_at_exit(timings=timings_object)


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'pytimings.cli.main' in result.output
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output
