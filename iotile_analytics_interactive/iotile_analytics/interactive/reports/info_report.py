"""Basic LiveReport that just prints information about an AnalysisGroup as a txt file."""

from __future__ import unicode_literals, absolute_import
import sys
from io import open
from past.builtins import basestring
from .analysis_template import AnalysisTemplate


class SourceInfoReport(AnalysisTemplate):
    """A basic AnalysisTemplate that just prints source information.

    If you pass the argument streams as True, the report will also include a
    list of all data streams in the AnalysisGroup.  This AnalysisTemplate can
    be directly viewed on stdout without needing to be saved to a file but can
    also optionally generate a text file (.txt) with the metadata that it
    prints.

    Args:
        group (AnalysisGroup): The group that we wish to analyze.
        streams (bool): Include stream summary information as well
            in the report.  This defaults to False if not passed.
    """

    def __init__(self, group, streams=False):
        self._group = group
        self.standalone = True
        self.include_streams = streams

    def run(self, output_path):
        """Render this report to output_path.

        If this report is a standalone html file, the output path will have
        .html appended to it and be a single file.

        If this report is not standalone, the output will be folder that is
        created at output_path.

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

        output_file = sys.stdout
        if output_path is not None:
            if output_path.endswith('.txt'):
                output_path = output_path[:-4]

            output_path = output_path + ".txt"

            output_file = open(output_path, 'w', encoding='utf-8')

        try:
            output_file.write("Source Info\n")
            output_file.write("-----------\n")

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

            output_file.write("\nProperties\n")
            output_file.write("----------\n")
            for key in sorted(self._group.properties):
                if len(key) > 27:
                    key = key[:27] + '...'

                val = self._group.properties[key]
                if isinstance(val, basestring):
                    val = val.encode('utf-8').decode('utf-8')
                else:
                    val = str(val)
                output_file.write('{0:30s} {1}\n'.format(key, val.replace('\n', new_line)))

            if self.include_streams:
                output_file.write("\nStream Summaries\n")
                output_file.write("----------------\n")

                for slug in sorted(self._group.streams):
                    if self._group.stream_empty(slug):
                        continue

                    name = self._group.get_stream_name(slug)

                    if len(name) > 37:
                        name = name[:37] + '...'

                    output_file.write('{:40s} {:s}\n'.format(name, slug))

                output_file.write("\nStream Counts\n")
                output_file.write("-------------\n")

                for slug in sorted(self._group.streams):
                    if self._group.stream_empty(slug):
                        continue

                    counts = self._group.stream_counts[slug]

                    output_file.write('{:s}              {: 6d} points {: 6d} events\n'.format(slug, counts.get('points'), counts.get('events')))
        finally:
            if output_path is not None:
                output_file.close()

        if output_path is None:
            return []

        return [output_path]
