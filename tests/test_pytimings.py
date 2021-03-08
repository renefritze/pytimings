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


def test_content(timings_object):
    timings_object.start(_DUMMY_SECTION)
    time.sleep(0.1)
    timings_object.stop(_DUMMY_SECTION)
    timings_object.stop()
    timings_object.output_all_measures()
    timings_object.reset(_DUMMY_SECTION)
    timings_object.reset()
    timings_object.start(_DUMMY_SECTION)
    time.sleep(0.1)
    timings_object.stop(_DUMMY_SECTION)
    timings_object.stop()
    timings_object.output_all_measures()


def test_nesting(timings_object):
    scope = partial(scoped_timing, timings=timings_object)
    with scope("root_section"):
        time.sleep(0.1)
        with scope("root_section.nested_1"):
            time.sleep(0.2)
            with scope("root_section.nested_1.leaf_section"):
                time.sleep(0.3)


def test_pickling(pickled_timings_object):
    with TemporaryFile() as out:
        dump = partial(pickle.dump, pickled_timings_object, out)
        dump(protocol=0)
        dump(protocol=pickle.HIGHEST_PROTOCOL)
        dump(protocol=pickle.DEFAULT_PROTOCOL)


def test_context(timings_object):
    timings_object.start(_DUMMY_SECTION)
    time.sleep(0.1)
    timings_object.stop(_DUMMY_SECTION)
    delta_before = timings_object.delta(_DUMMY_SECTION)
    with scoped_timing(_DUMMY_SECTION, timings=timings_object):
        time.sleep(0.1)
    delta_after = timings_object.delta(_DUMMY_SECTION)
    assert delta_after.wall > delta_before.wall

    # use the global timings object default
    delta_before = timings_object.delta(_DUMMY_SECTION)
    with scoped_timing(_DUMMY_SECTION):
        time.sleep(0.1)
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
