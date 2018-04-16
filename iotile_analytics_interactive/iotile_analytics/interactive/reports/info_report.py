"""Basic LiveReport that just prints information about an AnalysisGroup as a txt file."""

from __future__ import unicode_literals, absolute_import
from past.builtins import basestring
import sys
import os
from io import open
import zipfile
from iotile_analytics.core.exceptions import UsageError
from .report import LiveReport


class SourceInfoReport(object):
    """A basic LiveReport that just prints source information.

    Args:
        group (AnalysisGroup): The group that we wish to analyze.
    """

    DESCRIPTION = "Display streams, properties and record counts about the source."

    def __init__(self, group):
        self._group = group
        self.standalone = True

    def render(self, output_path, bundle=False):
        """Render this report to output_path.

        If this report is a standalone html file, the output path
        will have .html appended to it and be a single file.

        If this report is not standalone, the output will be
        folder that is created at output_path.

        If bundle is True and the report is not standalone, it will be zipped
        into a file at output_path.zip.  Any html or directory that was
        created as an intermediary before zipping will be deleted before this
        function returns.

        Args:
            output_path (str): the path to the folder that we wish
                to create.

        Returns:
            str: The path to the actual file or directory created.  This
                may differ from the file you pass in output_path by an
                extension or the addition of a subdirectory.
        """

        if output_path is None and bundle:
            raise UsageError("You cannot bundle a report if you are directing it to stdout.")

        output_file = sys.stdout
        if output_path is not None:
            if output_path.endswith('.txt'):
                output_path = output_path[:-3]

            bundle_path = output_path + ".zip"
            output_path = output_path + ".txt"

            output_file = open(output_path, 'w', encoding='utf-8')

        try:
            output_file.write("Source Properties\n")
            output_file.write("-----------------\n")

            new_line = '\n' + ' ' * 31
            for key in sorted(self._group.source_info):
                if len(key) > 27:
                    key = key[:27] + '...'

                val = self._group.source_info[key]
                if isinstance(val, basestring):
                    val = val.encode('utf-8').decode('utf-8')
                else:
                    val = str(val)
                output_file.write('{0:30s} {1}\n'.format(key, val.replace('\n', new_line)))
        finally:
            if output_path is not None:
                output_file.close()

        if bundle:
            zip_obj = zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED)
            zip_obj.write(output_path, os.path.basename(output_path))
            os.remove(output_path)
            return bundle_path

        return output_path
