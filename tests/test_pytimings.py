#!/usr/bin/env python

"""Tests for `pytimings` package."""
import time

import pytest
from click.testing import CliRunner

from pytimings import cli, mpi
from pytimings.timer import scoped_timing

USE_MPI = [False]
if mpi.HAVE_MPI:
    USE_MPI.append(True)

@pytest.fixture(params=USE_MPI)
def use_mpi(request, monkeypatch):
    use_mpi = request.param
    if (not use_mpi) and mpi.HAVE_MPI:
        monkeypatch.delattr('mpi4py.MPI')
        monkeypatch.setattr('pytimings.mpi.HAVE_MPI', False)

@pytest.fixture
def timings_object(request, use_mpi):
    from pytimings.timer import Timings
    return Timings()


DUMMY_SECTION = 'mysection'

def test_content(timings_object):
    timings_object.start(DUMMY_SECTION)
    time.sleep(0.1)
    timings_object.stop(DUMMY_SECTION)
    timings_object.stop()
    timings_object.output_all_measures()
    timings_object.reset(DUMMY_SECTION)
    timings_object.reset()
    timings_object.start(DUMMY_SECTION)
    time.sleep(0.1)
    timings_object.stop(DUMMY_SECTION)
    timings_object.stop()
    timings_object.output_all_measures()

def test_context(timings_object):
    timings_object.start(DUMMY_SECTION)
    time.sleep(0.1)
    timings_object.stop(DUMMY_SECTION)
    delta_before = timings_object.delta(DUMMY_SECTION)
    with scoped_timing(DUMMY_SECTION, timings=timings_object):
        time.sleep(0.1)
    delta_after = timings_object.delta(DUMMY_SECTION)
    assert delta_after.wall > delta_before.wall

    # use the global timings object default
    delta_before = timings_object.delta(DUMMY_SECTION)
    with scoped_timing(DUMMY_SECTION):
        time.sleep(0.1)
    delta_after = timings_object.delta(DUMMY_SECTION)
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
