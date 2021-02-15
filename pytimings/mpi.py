try:
    from mpi4py import MPI

    HAVE_MPI = True
except ImportError:
    HAVE_MPI = False


if HAVE_MPI:

    class CollectiveCommunication:
        def __init__(self, mpi_communicator=None):
            self._comm = mpi_communicator or getCommunicator()
            self.rank = self._comm.rank
            self.size = self._comm.size

        def sum(self, local_value):
            lsum = self._comm.reduce(local_value, MPI.SUM)
            return lsum

        def max(self, local_value):
            lsum = self._comm.reduce(local_value, MPI.MAX)
            return lsum

    def getLocalCommunicator():
        return MPI.COMM_SELF

    def getCommunicator():
        return MPI.COMM_WORLD


else:

    class CollectiveCommunication:
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

    def getLocalCommunicator():
        return None

    def getCommunicator():
        return None
