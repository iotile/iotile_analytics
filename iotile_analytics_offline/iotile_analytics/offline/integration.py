import os
from iotile_analytics.core.exceptions import UsageError
from .database import OfflineDatabase


def hdf5_save_factory(path):
    """Generate an HDF5 saver and overwrite a previous file if exists."""

    if os.path.exists(path):
        if not os.path.isfile(path):
            raise UsageError("Path specified as location of hdf5 file exists and is not a file (so it can't be deleted)", path=path)

        os.remove(path)

    return OfflineDatabase(path)


def hdf5_load_factory(path):
    """Generate an HDF5 loader, ensuring that the path specified exists."""

    if not os.path.exists(path):
        raise UsageError("Path specified as location of hdf5 file does not exist.", path=path)

    if not os.path.isfile(path):
        raise UsageError("Path specified as location of hdf5 file exists but is not a file", path=path)

    return OfflineDatabase(path)
