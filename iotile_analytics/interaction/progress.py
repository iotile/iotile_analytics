from ..environment import Environment
from typedargs.exceptions import InternalError


class ProgressBar(object):
    """A progress bar that automatically chooses the best display method."""

    def __init__(self, total, message=None, leave=True):
        env = Environment()
        if env.interactivity == Environment.Notebook:
            from tqdm import tqdm_notebook
            self._bar = tqdm_notebook(total, leave=leave)

            if message is not None:
                self._bar.set_description(message)

        #FIXME: Handle other display environments

    @property
    def total(self):
        return self._bar.total

    @total.setter
    def set_total(self, total):
        self._bar.total = total

    def update(self, delta):
        self._bar.update(delta)

    def __enter__(self):
        self._bar.__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        self._bar.__exit__(exc_type, exc_value, traceback)
