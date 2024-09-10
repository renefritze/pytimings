import pickle
import sys

import pytest


@pytest.fixture
def timings_object(request):
    from pytimings.timer import Timings

    return Timings()


@pytest.fixture
def pickled_timings_object(request, shared_datadir):
    filename = "nested.pickle"
    obj = pickle.loads((shared_datadir / filename).read_bytes())
    obj.extra_data = {}
    return obj


def is_windows_platform():
    return sys.platform == "win32" or sys.platform == "cygwin"


def is_mac_platform():
    return sys.platform == "darwin"
