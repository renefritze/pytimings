
try:
    import mpi4py
    DEFAULT_MPI_COMM = mpi4py.MPI.Comm_World
except ImportError:
    DEFAULT_MPI_COMM = None


class DummyMpiComm:
    pass


if DEFAULT_MPI_COMM is None:
    DEFAULT_MPI_COMM = DummyMpiComm()
