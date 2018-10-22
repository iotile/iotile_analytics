"""Helper classes to manage saving report output.

The classes in this package are used by analytics-host to properly save the
files produced by an AnalysisTemplate either locally, as part of a zip file or
by pushing them directly to a remote cloud server.
"""

from .base_handler import FileHandler
from .stdout_handler import StandardOutHandler
from .zip_handler import ZipHandler
from .file_handler import LocalDiskHandler
from .web_push_handler import WebPushHandler
from .streaming_web_push_handler import StreamingWebPushHandler

__all__ = ['FileHandler', 'StandardOutHandler', 'ZipHandler', 'LocalDiskHandler', 'WebPushHandler', 'StreamingWebPushHandler']
