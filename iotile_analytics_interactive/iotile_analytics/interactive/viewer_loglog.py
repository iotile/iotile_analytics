"""Helper classes showing interactive timeseries."""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
from bokeh.models import LogTicker, NumeralTickFormatter, LogTickFormatter
from .viewer_base import BaseViewer


class LogLogViewer(BaseViewer):
    """A data series viewer with a logarithmic x and y axis.

    All functionality in BaseViewer is present and there are a few
    convenience functions for setting the tick format on the axes
    easily.

    Apart from the special arguments listed below, all other arguments
    are passed through to BaseViewer.

    Args:
        x_decade_mantissa (list): The mantissa values to use for the x_axis.  If
            not specified this defaults to ticks on 1, 2 and 5 mantiss values.
        x_sciformat (bool): Whether to display the x tick values in 10^X format
            or in normal decimal.  Defaults to scientific.
        y_decade_mantissa (list): The mantissa values to use for the y_axis.  If
            not specified this defaults to ticks on 1, 2 and 5 mantiss values.
        y_sciformat (bool): Whether to display the y tick values in 10^X format
            or in normal decimal.  Defaults to scientific.
    """

    def __init__(self, x_decade_mantissa=(1, 2, 5), x_sciformat=True, y_decade_mantissa=(1, 2, 5),
                 y_sciformat=True, **kwargs):

        if 'x_type' not in kwargs:
            kwargs['x_type'] = 'log'

        if 'y_type' not in kwargs:
            kwargs['y_type'] = 'log'

        super(LogLogViewer, self).__init__(**kwargs)

        x_ticker = LogTicker(base=10, mantissas=x_decade_mantissa)
        x_ticker.num_minor_ticks = 10
        if x_sciformat is True:
            x_formatter = LogTickFormatter()
        else:
            x_formatter = NumeralTickFormatter(format="0")

        y_ticker = LogTicker(base=10, mantissas=y_decade_mantissa)
        y_ticker.num_minor_ticks = 10
        if y_sciformat is True:
            y_formatter = LogTickFormatter()
        else:
            y_formatter = NumeralTickFormatter(format="0")

        self.config_ticks('x', None, x_ticker, x_formatter)
        self.config_ticks('y', None, y_ticker, y_formatter)
