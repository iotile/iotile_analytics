"""Base class for all analysis operations that can be called from analytics-host."""


#pylint: disable=too-few-public-methods;This is a base class that is meant to be overriden
class AnalysisTemplate(object):
    """Base class for all objects that can be invoked by analytics-host.

    This class has a single method run(output_location, bundle=False) that
    takes a string identifying where the results of the analysis should be
    saved and a bool identifying whether to zip up the output.

    All subclasses need to implement the run function.  The must also define
    an __init__(self, group) function that accepts as its first parameter an
    AnalysisGroup object which is to be taken as the target of whatever
    operation needs to be performed.

    If the AnalysisTemplate also needs direct access to a running iotile.cloud
    instance, i.e. it cannot complete fully offline using just the AnalysisGroup,
    then it can take a parameter in its __init__ function named domain which will
    be filled with the domain of the iotile.cloud server that it should ask for
    additional information.
    """

    standalone = True
    """Whether running this AnalysisTemplate produces a single or multiple files."""

    def run(self, output_path):
        """Run whatever analysis this class implements.

        The analysis should be saved in the location specified by output_path.
        The output_path parameter should not be taken as the literal location
        to save the output but rather suggestive of where it should be saved,
        you may decide to append an extension or remove one and create a
        directory containing your results, for example.

        If you are only creating a single file then you can use output_path as
        you see fit to generate your output file name as described above.  If
        you generate multiple files then those files **must** be all contained
        inside a directory at ``output_path`` that you generate.  This is very
        important so that your caller can easily bundle your files into a zip
        and remove the originals if necessary.

        If output_path is None then you are expected to write your output to
        stdout.  If that is not possible for the analysis you are performing,
        e.g. you are creating multiple files, then you should raise
        UsageError().

        Args:
            output_path (str): A location specifying where we should save the
                output of the analysis.

        Returns:
            list(str): A list of all of the files generated during the running of this analysis.

            The first file in the list should be considered the "main
            entry point" of the analysis.  For example, if you are rendering an
            html file with supporting data in a directory, you should return the
            html file first and either a list of all the data files or the data
            directory itself.  Returning a directory from this function will be
            interpreted as returning all files recursively contained in that directory.

            If running this report generates no files you should return an empty
            list.
        """

        raise NotImplementedError()
