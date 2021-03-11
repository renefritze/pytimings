#!/usr/bin/env python

"""Tests for `pytimings` package."""
import pickle
import time
from functools import partial
from tempfile import TemporaryFile

from click.testing import CliRunner

from pytimings import cli, mpi
from pytimings.timer import scoped_timing
from .fixtures import timings_object, use_mpi, pickled_timings_object


_DUMMY_SECTION = 'mysection'

DEFAULT_SLEEP_SECONDS = 0.1
default_sleep = partial(time.sleep, DEFAULT_SLEEP_SECONDS)


def test_content(timings_object):
    timings_object.start(_DUMMY_SECTION)
    default_sleep()
    slept = timings_object.stop(_DUMMY_SECTION)
    assert slept.wall >= DEFAULT_SLEEP_SECONDS
    timings_object.stop()
    timings_object.output_all_measures()
    timings_object.reset(_DUMMY_SECTION)
    timings_object.reset()
    timings_object.start(_DUMMY_SECTION)
    default_sleep()
    slept = timings_object.stop(_DUMMY_SECTION)
    assert 2 * DEFAULT_SLEEP_SECONDS > slept.wall >= DEFAULT_SLEEP_SECONDS
    timings_object.stop()
    timings_object.output_all_measures()


def test_nesting(timings_object):
    scope = partial(scoped_timing, timings=timings_object)
    with scope("root_section"):
        default_sleep()
        with scope("root_section.nested_1"):
            default_sleep()
            with scope("root_section.nested_1.leaf_section"):
                default_sleep()
            slept = timings_object.delta("root_section.nested_1.leaf_section")
            assert 2 * DEFAULT_SLEEP_SECONDS > slept.wall >= DEFAULT_SLEEP_SECONDS
        slept = timings_object.delta("root_section.nested_1")
        assert 3 * DEFAULT_SLEEP_SECONDS > slept.wall >= 2 * DEFAULT_SLEEP_SECONDS
    slept = timings_object.delta("root_section")
    assert 4 * DEFAULT_SLEEP_SECONDS > slept.wall >= 3 * DEFAULT_SLEEP_SECONDS


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
    assert delta_after.wall > delta_before.wall
    assert delta_after.user > delta_before.user

    # use the global timings object default
    delta_before = timings_object.delta(_DUMMY_SECTION)
    with scoped_timing(_DUMMY_SECTION):
        default_sleep()
    delta_after = timings_object.delta(_DUMMY_SECTION)
    assert delta_after == delta_before


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'pytimings.cli.main' in result.output
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output
