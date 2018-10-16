"""Helper classes showing interactive histogram."""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
from .viewer_base import BaseViewer


class HistogramViewer(BaseViewer):
    """A histogram viewer based on quad() Glyph.

    All functionality in BaseViewer is present and there are a few
    convenience functions for setting the tick format on the axes
    easily.

    Apart from the special arguments listed below, all other arguments
    are passed through to BaseViewer.

    Args:

    """
    def __init__(self, **kwargs):

        if 'x_type' not in kwargs:
            kwargs['x_type'] = 'auto'

        if 'y_type' not in kwargs:
            kwargs['y_type'] = 'auto'

        super(HistogramViewer, self).__init__(**kwargs)


    def add_hist(self, left, right, top, bottom=0, label=None, color=None):
        """A method to add histogram to bokeh figure.

        Args:
            left: The x-coordinates of the left edges.
            right: The x-coordinates of the right edges.
            top: The y-coordinates of the top edges.
            bottom: The y-coordinates of the bottom edges.
                    Defaults to 0, as that is where the histogram bottom starts
            label (str): Show this line in the legend and use the following legend string for it
            color (str): Explicitly set the color of this line to the color specified.
                         This overrides any default color that might be set based on y_axis

        Returns:
            render: A rendered Glyph based on options chosen

        """
        kwargs = {}
        if label is not None:
            kwargs['legend'] = label

        if color is not None:
            kwargs['color'] = color

        render = self.figure.quad(left=left, right=right, top=top, bottom=bottom, **kwargs)

        return render

