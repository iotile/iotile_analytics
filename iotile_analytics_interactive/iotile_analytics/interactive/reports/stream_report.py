from __future__ import absolute_import, unicode_literals
from bokeh.layouts import row, layout
from bokeh.models import BoxZoomTool, PanTool, ResetTool, WheelZoomTool
from iotile_analytics.core.exceptions import UsageError
from iotile_analytics.interactive import BaseViewer, TimeSelectViewer
from .report import LiveReport

HEADER_TEMPLATE = r"""

<div class="before-content">
    <h2 class='title'>Stream Overview ({{ stream_name }})</h2>
    <ul>
        <li> Slug: {{ stream_slug }} </li>
        <li> Point Count: {{ stream_count }} </li>
        <li> First Point: {{ stream_first }} </li>
        <li> Last Point: {{ stream_last }} </li>
        <li> Display Units: {{ stream_units }}</li>
        {% if mdo is not none %}
        <li> Custom Transformation: multiply={{ mdo[0] }}, divide={{ mdo[1] }}, offset={{ mdo[2] }}</li>
        {% endif %}
    </ul>
</div>
"""

class StreamOverviewReport(LiveReport):
    """Display histogram and time series information about a stream.

    This report generates two plots.  The first is a bar graph that shows how many
    data points were received in this stream every X hours/weeks/days etc.  This is
    particularly useful for diagnosing issue where data should be received regularly but
    is not.  It can also help you orient yourself when looking through a stream with
    data collected over widely separated time intervals like data for 2 months then a 3 month
    gap then 1 month of data, etc.

    The second plot is just a graph of the data in the stream over time.  You units of the
    graph are whatever the internal units of the stream are unless you override them by
    passing the name of your desired units as a parameter.  If you do choose to override
    the units, you must specify a units name that has a known conversion from the internal
    stream units.

    Args:
        stream (str): A unique identifier for the stream that we wish to download
            and display.  This can be anything that could be passed to AnalysisGroup.fetch_stream
            including a 4-character variable ID, a partial string that matches the label of the
            stream, etc.
        window (str): The aggregation period for showing when there is data in a stream.  You can
            pass a value like 'days', 'hours', 'weeks', 'months'.  This will be given to TimeSelectViewer
            so any valid value there is acceptable here.  Defaults to days.
        units (str): The desired units in which you want to see the data.  This must be defined as an
            available output unit on the stream.  If not passed, the default is to use whatever the
            internal units are of the stream.  You can see what output unit options are by passing
            a random string here and looking at the error message.
        mdo (list(float)): An optional MDO to use to convert the data stored in this stream.  If passed
            this must be 3 float values that define a linear transformation of the data stored in the stream.
            The values are interpreted as m/d*value + o where the argument is specified as [m, d, o].
    """

    def __init__(self, group, stream, window='days', units=None, mdo=None):
        super(StreamOverviewReport, self).__init__(self.UNHOSTED)

        self.stream_data = group.fetch_stream(stream)
        self.units = units
        self.mdo = mdo
        if units is not None:
            if units not in self.stream_data.available_units:
                raise UsageError("Unknown output units specified", known_units=self.stream_data.available_units)

            self.stream_data = self.stream_data.convert(units)
        if mdo is not None:
            if len(mdo) != 3:
                raise UsageError("When specifying a fixed MDO, you must specify 3 float values for the multiple, divide and offset", mdo=mdo)

            self.stream_data = self.stream_data.apply_mdo(*mdo)

        self.before_content = self._render_info(group, stream)

        self._selector = TimeSelectViewer([self.stream_data], window, width=960, height=150, y_label="Point Count", toolbar_location="right",
                                          tools=[BoxZoomTool(dimensions='width'), WheelZoomTool(dimensions="width"), PanTool(dimensions='width'), ResetTool()])
        self._data = BaseViewer(width=960, height=400, x_type='datetime', y_label="Stream Value (%s)" % self._unit_name(), toolbar_location="right",
                                tools=[BoxZoomTool(), PanTool(dimensions='width'), WheelZoomTool(dimensions="width"), ResetTool()])
        self._data.add_series(self.stream_data)

        self.models = [self._selector.figure, self._data.figure]

    def _unit_name(self):
        if self.units is not None:
            return self.units
        elif self.mdo is not None:
            return "Custom Transformation"

        return 'Internal Units'

    def _render_info(self, group, stream):
        slug = group.find_stream(stream)

        first = None
        last = None
        if len(stream) > 0:
            first = self.stream_data.index.values[0]
            last = self.stream_data.index.values[-1]

        args = {
            'stream_name': group.get_stream_name(slug),
            'stream_slug': slug,
            'stream_count': group.stream_counts.get(slug, {}).get('points', 'Unknown'),
            'stream_units': self._unit_name(),
            'stream_first': first,
            'stream_last': last,
            'mdo': self.mdo
        }

        return self.render_string_template(HEADER_TEMPLATE, args)
