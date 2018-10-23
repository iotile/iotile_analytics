"""Report File Handler that streams each file to the cloud as generated."""

import logging
from ..cloud_uploader import ReportUploader
from .base_handler import FileHandler


class StreamingWebPushHandler(FileHandler):
    """Asynchronous handler that pushes each file to the cloud as generated.

    This class has a background thread that manages the upload process and
    waits synchronously in the finish() routine until all uploads are done.
    """

    def __init__(self, label, slug, domain, report_id=None):
        super(StreamingWebPushHandler, self).__init__()

        self._label = label
        self._slug = slug
        self._domain = domain
        self._logger = logging.getLogger(__name__)
        self._uploader = None
        self._last_path = None
        self._report_id = report_id

    def start(self):
        """Perform any necessary actions before the AnalysisTemplate starts."""

        self._logger.info("Streaming files to cloud as they are generated")
        self._uploader = ReportUploader(self._domain)

        if self._report_id is None:
            self._report_id = self._uploader.create_report(self._label, slug=self._slug)
            self._logger.debug("Created report id: %s", self._report_id)
        else:
            self._logger.debug("Using existing report id: %s", self._report_id)

    def finish(self, paths):
        """Perform any necessary actions after the AnalysisTemplate has finished.

        This method will be called after run() returns on the AnalysisTemplate
        and the paths argument will contain whatever run() returned.

        Args:
            paths (list of str): The list of strings returned from the call to
                run().
        """

        if self._last_path != "index.html":
            self._logger.error("Unexpected final path from report: %s, expected index.html", self._last_path)

        self._uploader.finish_report(self._report_id, "index.html")

    def handle_file(self, path, file_contents):
        """Save or otherwise handle a file produced by an AnalysisTemplate.

        Args:
            path (str): The path of the file.
            file_contents (bytes): The raw binary contents of the file.  If these
                contents are a string it will have already been encoded as utf-8.
        """

        # We are called with index.html for the main report and data/* for all of the data files
        # The data files need to be public so that index.html can fetch them using ajax calls
        self._logger.debug("Uploading file %s with length %d", path, len(file_contents))
        self._uploader.upload_file(self._report_id, path, file_contents, public=path.startswith("data"))

        self._last_path = path
