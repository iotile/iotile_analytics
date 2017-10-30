"""Helper classes showing interactive timeseries."""

import bqplot
from .viewer_base import BaseViewer

class TimeseriesViewer(BaseViewer):
    """A simple interface to plot timeseries data.

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
    """

    def __init__(self, data=None, fixed_y=None, size=None, ylabel=None, xlabel=None, xticks=True):
        x_scale = bqplot.DateScale()
        y_scale = bqplot.LinearScale()

        super(TimeseriesViewer, self).__init__(x_scale, y_scale, data=data, size=size, xlabel=xlabel, ylabel=ylabel, xticks=xticks)

        if fixed_y is not None:
            y_min, y_max = fixed_y
            self.y_scale.min = y_min
            self.y_scale.max = y_max
