"""A file handler that zips up all of the files."""

from zipfile import ZipFile, ZIP_DEFLATED
import os
from .base_handler import FileHandler


class ZipHandler(FileHandler):
    """A file handler that zips up all of the files."""

    def __init__(self, zip_path, base_dir=None):
        if not zip_path.endswith('.zip'):
            zip_path += '.zip'

        self._path = zip_path
        self._zip_file = None
        self._base_dir = base_dir

    def start(self):
        """Create the output zip file."""

        self._zip_file = ZipFile(self._path, mode='w', compression=ZIP_DEFLATED)

    def handle_file(self, path, file_contents):
        if self._base_dir is not None:
            path = os.path.join(self._base_dir, path)

        self._zip_file.writestr(path, file_contents)

    def finish(self, paths):
        self._zip_file.close()
