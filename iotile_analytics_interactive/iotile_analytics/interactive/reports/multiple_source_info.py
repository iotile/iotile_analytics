"""An extension of 'basic_info' template that prints information for multiple AnalysisGroup"""

from __future__ import unicode_literals, absolute_import
import sys
from io import open, StringIO
from past.builtins import basestring
from .analysis_template import AnalysisTemplate


class MultipleSourceInfoReport(AnalysisTemplate):
    """Extension of 'basic_info' AnalysisTemplate that just prints info for multiple sources

    If you pass the argument streams as True, the report will also include a
    list of all data streams in the AnalysisGroup.  This AnalysisTemplate can
    be directly viewed on stdout without needing to be saved to a file but can
    also optionally generate a text file (.txt) with the metadata that it
    prints.

    Args:
        group (list): A list of AnalysisGroups we wish to analyze
        streams (bool): Include stream summary information as well
            in the report.  This defaults to False if not passed.
    """

    def __init__(self, groups, streams=False):
        self._groups = groups
        self.standalone = True
        self.include_streams = streams

    def run(self, output_path, file_handler=None):
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

        out = StringIO()

        if output_path is not None:
            if output_path.endswith('.txt'):
                output_path = output_path[:-4]

            output_path = output_path + ".txt"

        for _group in self._groups:
            out.write("Source Info\n")
            out.write("-----------\n")

            new_line = '\n' + ' ' * 31
            for key in sorted(_group.source_info):
                if len(key) > 27:
                    key = key[:27] + '...'

                val = _group.source_info[key]
                if isinstance(val, basestring):
                    val = val.encode('utf-8').decode('utf-8')
                else:
                    val = str(val)
                out.write('{0:30s} {1}\n'.format(key, val.replace('\n', new_line)))

            out.write("\nProperties\n")
            out.write("----------\n")
            for key in sorted(_group.properties):
                if len(key) > 27:
                    key = key[:27] + '...'

                val = _group.properties[key]
                if isinstance(val, basestring):
                    val = val.encode('utf-8').decode('utf-8')
                else:
                    val = str(val)
                out.write('{0:30s} {1}\n'.format(key, val.replace('\n', new_line)))

            if self.include_streams:
                out.write("\nStream Summaries\n")
                out.write("----------------\n")

                for slug in sorted(_group.streams):
                    if _group.stream_empty(slug):
                        continue

                    name = _group.get_stream_name(slug)

                    if len(name) > 37:
                        name = name[:37] + '...'

                    out.write('{:40s} {:s}\n'.format(name, slug))

                out.write("\nStream Counts\n")
                out.write("-------------\n")

                for slug in sorted(_group.streams):
                    if _group.stream_empty(slug):
                        continue

                    counts = _group.stream_counts[slug]

                    out.write('{:s}              {: 6d} points {: 6d} events\n'.format(slug, counts.get('points'), counts.get('events')))

        encoded = out.getvalue().encode('utf-8')

        if file_handler is None:
            with open(output_path, "wb") as outfile:
                outfile.write(output_path, encoded)
        else:
            file_handler(output_path, encoded)

        return [output_path]
