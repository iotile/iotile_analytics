"""Basic file handler that just saves files to disk."""

import os
import logging
from iotile_analytics.core.exceptions import UsageError


class LocalDiskHandler(object):
    """Base class for all FileHandlers supported by analytics-host.

    A FileHandler subclass just needs to implement the handle_file method and
    can optionally also implement the start() and finish() methods in case
    they need to do additional setup before and after the report has been run.

    The default implementation of handle_file just saves it to disk.
    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.files = []

    def start(self):
        """Perform any necessary actions before the AnalysisTemplate starts."""
        pass

    def finish(self, paths):
        """Perform any necessary actions after the AnalysisTemplate has finished."""
        pass

    def handle_file(self, path, file_contents):
        """Save or otherwise handle a file produced by an AnalysisTemplate.

        Args:
            path (str): The path of the file.
            file_contents (bytes): The raw binary contents of the file.  If these
                contents are a string it will have already been encoded as utf-8.
        """

        basedir = os.path.dirname(os.path.abspath(path))

        if os.path.exists(basedir) and not os.path.isdir(basedir):
            raise UsageError("Cannot create directory %s, it already exists and is not a directory.  Trying to save %s", basedir, path)

        if not os.path.exists(basedir):
            self._logger.debug("Creating folder %s in handle_file", basedir)
            os.makedirs(basedir)  # This cannot have .. in it, see https://docs.python.org/2/library/os.html#os.makedirs

        with open(path, "wb") as outfile:
            self._logger.debug("Saving file %s", path)
            outfile.write(file_contents)

        self.files.append(path)
