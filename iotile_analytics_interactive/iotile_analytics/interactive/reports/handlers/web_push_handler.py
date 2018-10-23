"""A basic web push handler that pushes a report to the cloud after it has been written locally."""

from .file_handler import LocalDiskHandler
from ..cloud_uploader import ReportUploader


class WebPushHandler(LocalDiskHandler):
    """Push a report from local disk to the cloud.

    The report will be saved to local disk like a LocalDiskHandler
    but it will also be pushed to the cloud in the finish() method.
    """

    def __init__(self, label, slug, domain, report_id=None):
        super(WebPushHandler, self).__init__()

        self._label = label
        self._slug = slug
        self._domain = domain
        self._report_id = report_id

    def finish(self, paths):
        """Push this entire report up to the cloud."""

        uploader = ReportUploader(self._domain)
        uploader.upload_report(self._label, paths, slug=self._slug, report_id=self._report_id)
