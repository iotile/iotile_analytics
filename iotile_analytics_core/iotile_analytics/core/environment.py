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
        """Configure iotile_analytics for a Jupyter Notebook.

        This changes the way input is requested and progress is
        displayed to be appropriate for an interactive notebook
        environment.  It also sets up matplotlib for inline
        graphics display.
        """

        try:
            import ipywidgets  # pylint:disable=W0612; We just want to test importability
        except ImportError:
            raise MissingPackageError("Missing required package ipywidgets", package="ipywidgets", suggestion="pip install ipywidgets")

        try:
            import tqdm  # pylint:disable=W0612; We just want to test importability
        except ImportError:
            raise MissingPackageError("Missing required package tqdm", package="tqdm", suggestion="pip install tqdm")

        try:
            from IPython import get_ipython

            ipython = get_ipython()
            ipython.magic("matplotlib inline")
        except ImportError:
            raise MissingPackageError("Missing required package IPython", package="IPython")

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
