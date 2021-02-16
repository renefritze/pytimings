try:
    from mpi4py import MPI

    HAVE_MPI = True
except ImportError:
    HAVE_MPI = False


class _SerialCommunicationWrapper:
    """Minimal no-MPI abstraction around needed collective communication operations

    This class should not be instantiated directly. Use `get_communication_wrapper instead`"""

    def __init__(self, mpi_communicator=None):
        if mpi_communicator is not None:
            # TODO log debug
            pass
        self._comm = mpi_communicator
        self.rank = 0
        self.size = 1

    def sum(self, local_value):
        return local_value

    def max(self, local_value):
        return local_value


class DummyCommunicator:
    rank = 0
    size = 1


if HAVE_MPI:

    class _MPICommunicationWrapper:
        """Minimal MPI abstraction around needed collective communication operations

        This class should not be instantiated directly. Use `get_communication_wrapper instead`"""

        def __init__(self, mpi_communicator=None):
            self._comm = mpi_communicator or get_communicator()
            self.rank = self._comm.rank
            self.size = self._comm.size

        def sum(self, local_value):
            lsum = self._comm.reduce(local_value, MPI.SUM)
            return lsum

        def max(self, local_value):
            lsum = self._comm.reduce(local_value, MPI.MAX)
            return lsum

    _CommunicationWrapper = _MPICommunicationWrapper
else:

    _CommunicationWrapper = _SerialCommunicationWrapper


def get_communication_wrapper(mpi_communicator=None):
    if HAVE_MPI:
        return _MPICommunicationWrapper(mpi_communicator)
    return _SerialCommunicationWrapper(mpi_communicator)


def get_local_communicator():
    if HAVE_MPI:
        return MPI.COMM_SELF
    return DummyCommunicator()


def get_communicator():
    if HAVE_MPI:
        return MPI.COMM_WORLD
    return DummyCommunicator()
