"""Basic configuration for interactive vs script environments."""
from .exceptions import MissingPackageError


class Environment(object):
    """Configuration class for better interactive computing experience."""

    Console = 0
    Notebook = 1
    Script = 2
    Unattended = 3

    _settings = {}

    def __init__(self):
        self.interactivity = Environment._settings.get('interactivity', Environment.Script)

    @classmethod
    def SetupNotebook(cls):
        """Configure iotile_analytics for a Jupyter Notebook."""

        try:
            import tqdm  # pylint:disable=W0612; We just want to test importability
        except ImportError:
            raise MissingPackageError("Missing required package tqdm", package="tqdm", suggestion="pip install tqdm")

        # If we are using bokeh, make sure we set it up for notebook output
        try:
            from bokeh.io import output_notebook
            output_notebook(hide_banner=True)
        except ImportError:
            pass

        cls._settings['interactivity'] = Environment.Notebook

    @classmethod
    def SetupScript(cls):
        """Configure iotile_analytics to run in an attended script.

        Attended scripts are those that are watched by a user in the
        command line but not run using jupyter-console.  They are run
        as normal python scripts.

        No graphical plotting is allowed since the shell doesn't allow
        it and progress bars are displayed in an ascii format.
        """

        try:
            import tqdm  # pylint:disable=W0612; We just want to test importability
        except ImportError:
            raise MissingPackageError("Missing required package tqdm", package="tqdm", suggestion="pip install tqdm")

        cls._settings['interactivity'] = Environment.Script

    @classmethod
    def SetupUnattended(cls):
        """Configure iotile_analytics to run in an unattended script.

        Unattended scripts are those that are run on a server producing a log
        and not watched interactively on a tty.  Choosing Unattended mode
        causes progress bars not to dynamically update and instead just prints
        a message with the total runtime of each step.
        """

        try:
            import tqdm  # pylint:disable=W0612; We just want to test importability
        except ImportError:
            raise MissingPackageError("Missing required package tqdm", package="tqdm", suggestion="pip install tqdm")

        cls._settings['interactivity'] = Environment.Unattended
