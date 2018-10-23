"""A simple handler that just writes its contents to stdout."""

import sys
from .base_handler import FileHandler


class StandardOutHandler(FileHandler):
    """A simple FileHandler that just writes all files to stdout.

    There is no separation between files, so this handler is only appropriate
    for standalone AnalysisTemplate classes that produce a single file of
    output.
    """

    def handle_file(self, path, file_contents):
        """Save or otherwise handle a file produced by an AnalysisTemplate.

        Args:
            path (str): The path of the file.
            file_contents (bytes): The raw binary contents of the file.  If these
                contents are a string it will have already been encoded as utf-8.
        """

        str_contents = file_contents.decode('utf-8')
        sys.stdout.write(str_contents)
