from ..environment import Environment
from typedargs.exceptions import InternalError


class ProgressBar(object):
    """A progress bar that automatically chooses the best display method."""

    def __init__(self, total, message=None, leave=True):
        env = Environment()
        if env.interactivity == Environment.Notebook:
            from tqdm import tqdm_notebook
            self._bar = tqdm_notebook(total=total, leave=leave)

            if message is not None:
                self._bar.set_description(message)
        else:
            from tqdm import tqdm
            self._bar = tqdm(total=total, leave=leave)

            if message is not None:
                self._bar.set_description(message)

        self.total = total

    @property
    def total(self):
        return self._bar.total

    @total.setter
    def total(self, total):
        self._bar.total = total

    def update(self, delta):
        self._bar.update(delta)

    def __enter__(self):
        self._bar.__enter__()

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._bar.__exit__(exc_type, exc_value, traceback)
