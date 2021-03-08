import pickle
import re
import pytest
from mpi4py import MPI
from pytest_regressions.data_regression import DataRegressionFixture
from pytest_regressions.num_regression import NumericRegressionFixture
from pytest_regressions.file_regression import FileRegressionFixture


from pytimings import mpi

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


@pytest.fixture
def pickled_timings_object(request, use_mpi, shared_datadir):
    filename = f'nested.mpi_{mpi.HAVE_MPI}.pickle'
    return pickle.load(open(shared_datadir / filename, 'rb'))


def _make_regression_fixture(base_type, fname):
    def check(self, data_dict, basename=None, fullpath=None):
        """

        :param data_dict: the data to check
        :param basename: unless explicitly set, defaults to test name with rank count appended
        :param fullpath: part of the origianl API, but cannot be used (mutually exclusive in super class
            with setting basename
        """
        assert fullpath is None
        if basename is None:
            super_basename = re.sub(r"[\W]", "_", self.request.node.name)
            ranks = MPI.COMM_WORLD.Get_size()
            assert ranks > 0
            basename = f'{super_basename}_r{ranks}'
        print(f'checking basename {basename}')
        super(self.__class__, self).check(data_dict, basename=basename)

    new_type = type(f'Mpi{base_type.__name__}', (base_type,), {'check': check})

    @pytest.fixture()
    def maker(datadir, original_datadir, request):
        return new_type(datadir, original_datadir, request)

    maker.__name__ = fname
    return new_type, maker


for rtype, fname in (
    (DataRegressionFixture, 'data_regression'),
    (NumericRegressionFixture, 'num_regression'),
    (FileRegressionFixture, 'file_regression'),
):
    fname = f'mpi_{fname}'
    new_type, fixture = _make_regression_fixture(rtype, fname)
    locals()[fname] = fixture