"""Base class for all file handlers supported by analytics-host."""

class FileHandler(object):
    """Base class for all FileHandlers supported by analytics-host.

    A FileHandler subclass just needs to implement the handle_file method and
    can optionally also implement the start() and finish() methods in case
    they need to do additional setup before and after the report has been run.
    """

    def start(self):
        """Perform any necessary actions before the AnalysisTemplate starts."""
        pass

    def finish(self, paths):
        """Perform any necessary actions after the AnalysisTemplate has finished.

        This method will be called after run() returns on the AnalysisTemplate
        and the paths argument will contain whatever run() returned.

        Args:
            paths (list of str): The list of strings returned from the call to
                run().
        """
        pass

    def handle_file(self, path, file_contents):
        """Save or otherwise handle a file produced by an AnalysisTemplate.

        Args:
            path (str): The path of the file.
            file_contents (bytes): The raw binary contents of the file.  If these
                contents are a string it will have already been encoded as utf-8.
        """

        raise NotImplementedError()
