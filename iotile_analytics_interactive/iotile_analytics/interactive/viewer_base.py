"""Base viewer class for interactive plots."""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from iotile_analytics.core import Environment
from bokeh.plotting import figure
from bokeh.io import show, push_notebook
from bokeh.models import ColumnDataSource, LinearAxis, Range1d, Axis, DataRange1d
import pandas as pd
import numpy as np
from typedargs.exceptions import ArgumentError


class BaseViewer(object):
    """A simple interface to plot data.

    Internally this object wraps a bqplot Figure object and provides
    reasonable defaults for all of the settings, while passing through access
    to traits that you may want to update later.

    Args:
        size (tuple): Optional tuple of (width, height) as integers in pixels
            if you wish this viewer to have a fixed size
        x_type ('auto', 'linear', 'log', 'datetime'): Whether we should create a
            log, linear, or time viewer.
        y_type ('auto', 'linear', 'log', 'datetime'): What scaling type to use for
            the y axis.
        fixed_y (tuple): Optional tuple to use a fixed y axis.
        y_name (str): Optional name for the default y axis so that we can refer to it
            if there are multiple axes included in the plot.
        x_label (str): The label for the x axis
        y_label (str): The label for the default y axis
        tools (list): A list of tools to be added to the toolbar.  If these are passed then
            the toolbar is shown by default above the plot. If no tools are passed the default
            behavior is to associate no tools wtih the viewer.
    """

    def __init__(self, size=None, x_type='auto', y_type='auto', fixed_y=None, y_name=None, x_label=None, y_label=None, y_color=None, **kwargs):
        if size is not None:
            width, height = size
            kwargs['plot_width'] = width
            kwargs['plot_height'] = height

        if fixed_y is not None:
            y_min, y_max = fixed_y
            kwargs['y_range'] = (y_min, y_max)

        if kwargs.get('tools') is None:
            kwargs['toolbar_location'] = None

        self.figure = figure(x_axis_type=x_type, y_axis_type=y_type, logo=None, **kwargs)
        self._notebook_handle = None
        self._in_notebook = False
        self._default_y_name = y_name

        env = Environment()
        if env.interactivity == env.Notebook:
            self._in_notebook = True

        self.sources = {}

        if y_label is not None:
            self.label_axis(y_name, y_label)

        if x_label is not None:
            self.figure.xaxis.axis_label = x_label

        if y_color is not None:
            self.color_axis(y_name, y_color)

    def _find_axis(self, name):
        if name == self._default_y_name:
            axis = self.figure.yaxis
            if not isinstance(axis, Axis):
                return axis[0]

            return axis

        axes = self.figure.yaxis
        if isinstance(axes, Axis):
            raise ArgumentError("Named axis could not be found", name=name)

        for axis in axes:
            if axis.y_range_name == name:
                return axis

        raise ArgumentError("Named axis could not be found", name=name)

    def config_ticks(self, axis_type, axis_name, ticker, formatter):
        """Configure the ticker and formatter for an axis.

        Args:
            axis_type (str): Either x or y for an x or y axis
            axis_name (str): The name of the axis if there are multiple
                axis choices.  If you want the default axis, pass None.
            ticker (bokey.models.tickers.Ticker): The ticker to use
                to generate ticks.
            formatter (bokeh.models.formatters.TickFormatter): The formatter
                to use to generate names for major ticks.
        """

        if axis_name is None:
            axis_name = self._default_y_name

        if axis_type not in ('x', 'y'):
            raise ArgumentError("Unknown axis type that is not x or y", axis_type=axis_type)

        if axis_type == 'x':
            axis = self.figure.xaxis
        else:
            axis = self._find_axis(axis_name)

        axis.ticker = ticker
        axis.formatter = formatter

    def label_axis(self, name, label):
        """Set the label of an axis by name

        Args:
            name (str): The name of the axis that we wish to adjust.
            label (str): The axis label that we would like to set.
        """

        axis = self._find_axis(name)
        axis.axis_label = label

    def color_axis(self, name, color):
        """Set the color of one of the y axes."""

        axis = self._find_axis(name)
        axis.axis_line_color = color
        axis.axis_label_text_color = color
        axis.major_label_text_color = color
        axis.major_tick_line_color = color
        axis.minor_tick_line_color = color

    def add_yaxis(self, name, y_range=None, location="right", label=None, color=None):
        """Add another y axis to the graph.

        You must provide a name for the axis and an optional fixed range
        min/max. The name is used to refer to the axis later if you need to
        modify it. If you want to color the entire axis you can pass a color
        string in color and it will be as if you separately called
        color_yaxis.

        Args:
            name (str): A unique name for this axis.
            y_range (tuple(min, max)): A tuple with explicit min/max range for this axis.
            location (str): The location for the axis, one of left or right.
            label (str): The optional label to use for the axis.
            color (str): An optional color that is used to color all aspects of the axis.
        """

        if y_range is not None and not isinstance(y_range, Range1d):
            y_min, y_max = y_range
            y_range = Range1d(start=y_min, end=y_max)
        elif y_range is None:
            y_range = DataRange1d()

        self.figure.extra_y_ranges[name] = y_range

        axis = LinearAxis(y_range_name=name, axis_label=label)
        self.figure.add_layout(axis, location)

        if color is not None:
            self.color_axis(name, color)

    def show(self):
        """Show this figure."""

        if self._in_notebook:
            self._notebook_handle = show(self.figure, notebook_handle=True)
        else:
            show(self.figure)

    def _sync_notebook(self):
        if self._notebook_handle is not None:
            push_notebook(handle=self._notebook_handle)

    @classmethod
    def _find_axes(cls, input_data, explicit_x=None):
        """Given a pandas series or numpy array return the X and Y axes.

        This function supports extracting a single X and Y axis from the following
        input configurations:

        - 2 1D arrays
        - a single 2D array
        - a list of numbers (x is implicitly linspace(0, len(input_data)))
        - a Pandas Series
        - the first column of a Pandas DataFrame
        """

        if isinstance(input_data, pd.Series):
            if explicit_x is not None:
                raise ArgumentError("You cannot pass an explicit x axis with a pandas Series")

            return input_data.index, input_data.values
        elif isinstance(input_data, pd.DataFrame):
            if explicit_x is not None:
                raise ArgumentError("You cannot pass an explicit x axis with a pandas DataFrame")

            return input_data.index, input_data.values[:, 0]
        elif isinstance(input_data, np.ndarray):
            if len(input_data.shape) == 2 and input_data.shape[0] == 2:
                if explicit_x is not None:
                    raise ArgumentError("You cannot pass an explicit x axis with a 2D array of input data")

                return input_data[:, 0], input_data[:, 1]
            elif len(input_data.shape) == 1:
                if explicit_x is not None:
                    if len(explicit_x) != len(input_data):
                        raise ArgumentError("Your explicit x data has a different length that your y data", x_length=len(explicit_x), y_length=len(input_data))

                    return explicit_x, input_data
                else:
                    return np.linspace(0, len(input_data) - 1, len(input_data)), input_data
        elif explicit_x is not None:
            return np.array(explicit_x), np.array(explicit_x)

        return np.linspace(0, len(input_data) - 1, len(input_data)), np.array(input_data)

    def add_series(self, data, x_data=None, size=None, name=None, alpha_with_line=None, label=None, mark='line', x_name='x', y_name='y', y_axis=None, color=None, bar_width=0.1):
        """Add a new line to the plot.

        This function does not clear the data that is already there so it
        creates a new line.  If you pass an explicit column data source, that
        is used and you must pass x_name and y_name explicitly with the column
        names that should be used unless they are 'x' and 'y'.

        You can choose to add the new data to the chart as a line, scatter or
        bar

        Args:

            data (ndarray, pd.Series or ColumnDataSource): An array of values
                to plot.  If data is a Series, then it is plotted as is.  If
                it is a 1D ndarray then this is interpreted as a series of y
                values and you can pass the x values explicitly using the
                x_data argument.
            x_data (ndarray): An array of explicit x_values.  This can only be
                passed if data is a 1D ndarray that is then interpreted as y
                values.
            x_name (str): Optional explicit x column name if data is a
                ColumnDataSource, defaults to x.
            y_name (str): Optional explicit y column name is data is a
                ColumnDataSource, defaults to y.
            y_axis (str): Optional name for the y axis that should be used to
                plot this line.  If this is specified then the line is colored
                with the same color as the axis.
            name (str): Optional name for this data series.  This is used to
                name the columns in self.source and also used to stream
                updates by name.  If this is None, it defaults to series_N
                where N is incremented for each new add_series call.
            mark (str): The type of mark to add.  Valid types strings are:
                line, scatter, bars
            bar_width (int): For bar marks, the width of the bars.
            color (str): Explicitly set the color of this line to the color
                specified.  This overrides any default color that might be set
                based on the y_axis that is used.
            label (str): Show this line in the legend and use the following legend
                string for it.
            alpha_with_line (float): Make the glyphs themselves transparent with this
                alpha value and include a fully opaque outline in the same color.  This
                only applies to scatter and bars type charts.
            size (float): For scatter plots, the screen space unit size of the markers.

        Returns:
            str, Renderer: The name of the data source added for this series, in case it is
                autogenerated and the renderer of the line itself.
        """

        if name is None:
            name = "series_{}".format(len(self.sources))

        if mark not in ('line', 'scatter', 'bar'):
            raise ArgumentError("Unknown glyph type in add_series", line_type=mark, known_types=('line', 'scatter', 'bar'))

        if isinstance(data, ColumnDataSource):
            source = data
        else:
            x_set, y_set = self._find_axes(data, x_data)
            source = ColumnDataSource({x_name: x_set, y_name: y_set})

        self.sources[name] = (source, x_name, y_name)

        kwargs = {}

        if y_axis is not None:
            axis = self._find_axis(y_axis)

            if y_axis != self._default_y_name:
                kwargs['y_range_name'] = y_axis

            kwargs['color'] = axis.axis_label_text_color

        if color is not None:
            kwargs['color'] = color

        if label is not None:
            kwargs['legend'] = label

        if mark == 'line':
            render = self.figure.line(x=x_name, y=y_name, name=name, source=source, **kwargs)
        else:
            if alpha_with_line is not None:
                kwargs['fill_alpha'] = alpha_with_line

            if mark == 'scatter':
                if size is not None:
                    kwargs['size'] = size

                render = self.figure.scatter(x=x_name, y=y_name, name=name, source=source, **kwargs)
            elif mark == 'bar':
                render = self.figure.vbar(x=x_name, width=bar_width, top=y_name, name=name, source=source, **kwargs)

        self._sync_notebook()
        return name, render

    def update_series(self, name, data, x_data=None, rollover=None):
        """Stream new data to a series previously added with add_series.

        Args:
            name (str): The name of the series added previously in add_series.
                If the name was autogenerated by add_series, it would have been
                returned from that function.
            data (ndarray or pd.Series): An array of values to plot.  If data
                is a Series, then it is plotted as is.  If it is a 1D ndarray
                then this is interpreted as a series of y values and you can
                pass the x values explicitly using the x_data argument.
            x_data (ndarray): An array of explicit x_values.  This can only be
                passed if data is a 1D ndarray that is then interpreted as y
                values.
            rollover (int): An optional maximum length for the columns to grow.
                If you specify this, only the last rollover values will be kept.
                This allows you to create continously updating plots by just streaming
                new values as they become available.
        """

        source, x_name, y_name = self.sources.get(name, (None, None, None))
        if source is None:
            raise ArgumentError("Unknown source name", name=name, known_names=list(self.sources))

        x_set, y_set = self._find_axes(data, x_data)

        source.stream({x_name:x_set, y_name:y_set}, rollover=rollover)
        self._sync_notebook()
