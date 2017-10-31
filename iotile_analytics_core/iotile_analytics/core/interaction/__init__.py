"""Interactivity primitives that work across environments.

In particular, we need a way to ask a user a question if needed
and show the user progress.  However, the best way to do this
varies depending on whether the user's sesion is running in a
shell script, a jupyter notebook, a jupyter console or on
an unattended background worker.
"""

from .progress import ProgressBar

__all__ = ['ProgressBar']
