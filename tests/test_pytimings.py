#!/usr/bin/env python

"""Tests for `pytimings` package."""
import time

import pytest
from click.testing import CliRunner

from pytimings import cli


@pytest.fixture(params=(True, False))
def use_mpi(request, monkeypatch):
    use_mpi = request.param
    if not use_mpi:
        monkeypatch.delattr('mpi4py.MPI')

@pytest.fixture
def timings_object(request, use_mpi):
    from pytimings.timer import Timings
    return Timings()


def test_content(timings_object):
    section = 'mysection'
    timings_object.start(section)
    time.sleep(0.1)
    timings_object.stop(section)
    timings_object.stop()
    timings_object.output_all_measures()
    timings_object.reset(section)
    timings_object.reset()
    timings_object.start(section)
    time.sleep(0.1)
    timings_object.stop(section)
    timings_object.stop()


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'pytimings.cli.main' in result.output
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output
