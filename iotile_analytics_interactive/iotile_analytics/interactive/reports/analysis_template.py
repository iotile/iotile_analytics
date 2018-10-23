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

    All AnalysisTemplate subclasses must announce in advance of being run
    whether they produce one or multiple files by setting the standalone property
    as appropriate.  The property defaults to True, which means only a single
    file is produced, so it only needs to be overriden by subclasses that produce
    multiple files.  The standalone property must be a class property, not an
    instance property so that it can be inspected before the class is instantiated.
    """

    standalone = True
    """Whether running this AnalysisTemplate produces a single or multiple files."""

    def run(self, output_path, file_handler=None):
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

        If output_path is None and file_handler is None then you are expected
        to write your output to stdout.  If that is not possible for the
        analysis you are performing, e.g. you are creating multiple files,
        then you should raise UsageError().

        If output_path is None but file_handler is not None then you are
        expected to hand each of your produced files to file_handler in order
        for it to save them appropriately.

        Args:
            output_path (str): A location specifying where we should save the
                output of the analysis.
            file_handler (callable): A function that will be given a bytes
                object for each file that this report generates as well as
                the relative path to that file.  If you override this function,
                it is your responsibility to save all of these files, otherwise
                no output will be generated.  The purpose of this argument is
                to allow for streaming these files to a remote server or some
                other action that is not just saving the data to a local disk.

                The default behavior is to just save to local disk, which happens
                if file_handler is None (the default value).  The signature
                of file_handler should be file_handler(path, contents) where
                contents is a bytes object.

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
