"""A widget showing when in time a StreamSeries has data.

This graph shows a horizontally scrollable "minimap" style view with a
selection rectangle that allows you to pick a given day, week, or month of
data to look at.  It is best used when combined with another graph that
actually shows the selected data in detail.
"""

from __future__ import unicode_literals, absolute_import

from iotile_analytics.core.exceptions import UsageError
from iotile_analytics.core.utilities import TimeseriesSelector
from .viewer_base import BaseViewer



class TimeSelectViewer(BaseViewer):
    """A graph showing a high level overview of one or more StreamSeries.

    You need to pass a list of StreamSeries objects.  These are turned into
    a bar chart that contains the number of readings in any of the series
    at each aggregation interval in the data set.

    Args:
        series_list (list of StreamSeries): The streams that you want to build
            a TimeSelectViewer from.
        interval (str): One of hours, days, weeks or months.  This is the aggregation
            level where you will get one bar containing a number of readings in
            each of these intervals in the combined (union) domain of all of the
            series that you passed in series_list.
        timezone (str): The timezone to use to localize all data coming in so that days
            correspond correctly to days in that timezone.  Default: UTC.  This should be
            a timzeone value like 'US/Central'.
        **kwargs: Additional keyword arguments that you wish passed to the BaseViewer instance to configure
            it.
    """

    DEFAULT_HEIGHT = 100

    def __init__(self, series_list, interval="days", timezone="UTC", width=None, height=None, **kwargs):
        if height is None:
            height = TimeSelectViewer.DEFAULT_HEIGHT

        valid_intervals = ('days', 'months', 'weeks', 'hours')
        if interval not in valid_intervals:
            raise UsageError("You must pass a valid interval string", valid_intervals=valid_intervals, interval=interval)

        if len(series_list) == 0:
            raise UsageError("You must pass in at least one StreamSeries to set the domain of the TimeSelectViewer")

        super(TimeSelectViewer, self).__init__(width=width, height=height, x_type="datetime", **kwargs)

        self.domain = TimeseriesSelector(timezone=timezone)

        for series in series_list:
            self.domain.add_data(series)

        self.counts = self._build_bars(series_list, interval)
        self.add_series(self.counts, bar_width=self._interval_to_ms(interval), mark='bar', alpha_with_line=0.7)

    def _build_bars(self, series_list, interval):
        freq_map = {
            'days': 'D',
            'weeks': 'W',
            'months': 'M',
            'hours': 'H'
        }

        freq = freq_map.get(interval)
        accum = self.domain.resample(series_list[0], None, freq, resample='count')

        for series in series_list[1:]:
            accum += self.domain.resample(series, None, freq, resample='count')

        return accum

    def _interval_to_ms(self, interval):
        ms_map = {
            'hours': 60*60*1000,
            'days': 24*60*60*1000,
            'weeks': 7*24*60*60*1000,
            'months': 30*24*60*60*1000
        }

        return ms_map[interval]
