"""A LiveReport plugin to enable quickly saving data from iotile.cloud offline."""

class SaveOfflineReport(object):
    """Save all data locally as an HDF5 database file."""

    # Standalone reports are those that can be serialized to a single file or the console
    # since we don't support console serializaiton, we are not standalone
    standalone = False

    def __init__(self, group):
        self._group = group


    def run(self, output_path, file_handler):
        """Render this report to output_path.

        Args:
            output_path (str): the path to the folder that we wish
                to create.

        Returns:
            list(str): A list with a single entry for the hdf5 file we wrote.
        """

        if not output_path.endswith('.hdf5'):
            output_path = output_path + ".hdf5"

        self._group.save(output_path, 'hdf5')
        return [output_path]
