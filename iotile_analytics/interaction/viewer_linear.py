"""Helper classes showing interactive linear plots."""

import bqplot
from .viewer_base import BaseViewer

class LinearViewer(BaseViewer):
    """A simple interface to plot linear x,y data.

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
        **kwargs: Any arguments accepted by BaseViewer may be passed to LinearViewer
            and will have the same effect
    """

    def __init__(self, data=None, fixed_y=None, **kwargs):
        x_scale = bqplot.LinearScale()
        y_scale = bqplot.LinearScale()

        super(LinearViewer, self).__init__(x_scale, y_scale, data=data, **kwargs)

        if fixed_y is not None:
            y_min, y_max = fixed_y
            self.y_scale.min = y_min
            self.y_scale.max = y_max
