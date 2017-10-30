"""Helper classes showing interactive timeseries."""

import bqplot
from .viewer_base import BaseViewer

class LogLogViewer(BaseViewer):
    """A simple interface to a loglog data plot.

    Internally this object wraps a bqplot Figure object and
    provides reasonable defaults for all of the settings, while
    passing through access to traits that you may want to update
    later.

    Args:
        data (Series): A pandas Series with the time series data that
            we wish to display.
        fixed_y (tuple): Either None for a dynamically scaling y-axis
            or a tuple with (min, max) that contains the fixed min and
            max values for the axis.
        xticks (bool): Whether to show the x axis tick values, ticks
            are usually shown when there is a single plot but hidden
            when there are multiple plots stacked on top of each other
            with a common x axis since you want the bottom plot to show
            the ticks for all of the others.
        xlabel (str): Optional label to display on the x axis
        ylabel (str): Optional label to display on the y axis
        size (tuple): Optional tuple of (width, height) as strings in either
            % or pixels that are passed to Figure.layout to set its width and
            height.
        margic (dict): Optional dict of margin values
    """

    def __init__(self, data=None, fixed_y=None, **kwargs):
        x_scale = bqplot.LogScale()
        y_scale = bqplot.LogScale()

        super(LogLogViewer, self).__init__(x_scale, y_scale, data=data, **kwargs)

        if fixed_y is not None:
            y_min, y_max = fixed_y
            self.y_scale.min = y_min
            self.y_scale.max = y_max
