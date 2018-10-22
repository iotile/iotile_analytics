import time
from ..environment import Environment


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
            disable = None
            if env.interactivity == Environment.Unattended:
                disable = True

            from tqdm import tqdm
            self._bar = tqdm(total=total, leave=leave, disable=disable)

            if message is not None:
                self._bar.set_description(message)

        self.total = total
        self._start = time.time()
        self._print_summary = env.interactivity == Environment.Unattended
        self._message = message

    @property
    def total(self):
        return self._bar.total

    @total.setter
    def total(self, total):
        self._bar.total = total

    def update(self, delta):
        self._bar.update(delta)

    def close(self):
        self._bar.close()
        self._print_summary_line()

    def set_description(self, message):
        self._bar.set_description(message)

    def __enter__(self):
        self._bar.__enter__()
        self._start = time.time()

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._bar.__exit__(exc_type, exc_value, traceback)
        self._print_summary_line()

    def _print_summary_line(self):
        if self._print_summary:
            message = self._message
            if message is None:
                message = "Unnamed"

            end = time.time()
            total = end - self._start
            print("Operation '%s' took %.1f seconds" % (message, total))
