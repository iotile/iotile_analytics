"""Base viewer class for interactive plots."""

import bqplot
from IPython.display import display
import pandas as pd
import numpy as np


class BaseViewer(object):
    """A simple interface to plot data.

    Internally this object wraps a bqplot Figure object and
    provides reasonable defaults for all of the settings, while
    passing through access to traits that you may want to update
    later.

    Args:
        data (Series): A pandas Series with the time series data that
            we wish to display.
        x_scale (bqplot.Scale): A scale for the x axis
        y_scale (bqplot.Scale): A scale for the y axis
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
        margin (dict): Optional margin values for the plot
    """

    def __init__(self, x_scale, y_scale, data=None, size=None, ylabel=None, xlabel=None, xticks=True, margin=None):
        self.x_scale = x_scale
        self.y_scale = y_scale

        x_ax = bqplot.Axis(scale=self.x_scale)
        if xticks is False:
            x_ax.num_ticks = 0
        if xlabel is not None:
            x_ax.label = xlabel

        y_ax = bqplot.Axis(scale=self.y_scale, orientation="vertical")
        if ylabel is not None:
            y_ax.label = ylabel

        if margin is None:
            margin = {
                'top': 30, 'bottom': 0, 'left': 50, 'right': 0
            }

            if xlabel is not None or xticks:
                margin['bottom'] = 50

        self.figure = bqplot.Figure(axes=[x_ax, y_ax], fig_margin=margin)

        if size is not None:
            width, height = size
            self.figure.layout.width = width
            self.figure.layout.height = height

        if data is not None:
            x_data, y_data = self._find_axes(data)

            line = bqplot.Lines(x=x_data, y=y_data, scales={'x': self.x_scale, 'y': self.y_scale})
            self.figure.marks = [line]

        self.x_axis = x_ax
        self.y_axis = y_ax

    @property
    def x_min(self):
        return self.x_scale.min

    @x_min.setter
    def x_min(self, value):
        self.x_scale.min = value

    @property
    def x_max(self):
        return self.x_scale.max

    @x_max.setter
    def x_max(self, value):
        self.x_scale.max = value

    def display(self):
        display(self.figure)

    def _find_axes(self, input_data):
        """Given a pandas series or numpy array return the X and Y axes."""

        if isinstance(input_data, pd.Series):
            return input_data.index, input_data.values
        elif isinstance(input_data, np.ndarray):
            return input_data[:, 0], input_data[:, 1]

        return np.linspace(0, len(input_data) - 1, len(input_data)), np.array(input_data)
