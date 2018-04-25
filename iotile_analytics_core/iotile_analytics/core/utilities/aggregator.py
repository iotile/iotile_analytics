"""A class that lets you compare portions of multiple timeseries datasets."""

from builtins import range, str
from typedargs.exceptions import ArgumentError
from iotile_analytics.core.exceptions import UsageError
import pandas as pd
import numpy as np


class TimeseriesSelector(object):
    """A utility class for aggregating and selecting data from multiple timeseries.

    The selector keeps track of the first and last timestamp that was added and lets
    you restrict data to only a given day, week or month while iterating through every
    such segment of the data.

    This is particularly useful for producing coherent views and reports of data that
    may cover different intersecting but not identical time spans.


    Args:
        timezone (str): The timezone to use to localize all data coming in so that days
            correspond correctly to days in that timezone.  Default: UTC.  This should be
            a timzeone value like 'US/Central'.
    """

    def __init__(self, timezone='UTC'):
        self._timezone = timezone

        self.oldest_point = None
        self.newest_point = None

    def add_data(self, data):
        """Add a new dataset to the aggregator.

        The data is homogenized and the underlying domain of the aggregator is
        extended if necessary.  The data itself is not stored.

        Args:
            data (pd.DataFrame): A dataframe to add to our aggregator.
        """

        # First localize the data into the right timezone
        if self._check_tz_naive(data):
            data = data.tz_localize('UTC', copy=False)

        data = data.tz_convert(self._timezone, copy=False)

        oldest = data.index.min()
        newest = data.index.max()

        if self.oldest_point is None or oldest < self.oldest_point:
            self.oldest_point = oldest
        if self.newest_point is None or newest > self.newest_point:
            self.newest_point = newest

    def _check_tz_naive(self, data):
        return data.index.tzinfo is None

    def _generate_index(self, freq):
        if self.oldest_point is None or self.newest_point is None:
            raise UsageError("You must add at least one dataset to the selector first before trying to generate an index.")

        return pd.PeriodIndex(start=self.oldest_point, end=self.newest_point, freq=freq)

    def months(self):
        """Get all of the unique months spanning our data domain.

        The results are returned in time order with duplicates removed.

        Returns:
            pd.PeriodIndex
        """

        return self._generate_index('M')

    def weeks(self):
        """Get all unique weeks spanning our data domain.

        The results are returned in time order with duplicates removed.

        Returns:
            pd.PeriodIndex
        """

        return self._generate_index('W')

    def days(self):
        """Get all unique days spanning our data domain.

        The results are returned in time order with duplicates removed.

        Returns:
            list of datemasks: The day date masks that can be used to select a subset
                of data from this aggregator.
        """

        return self._generate_index('D')

    def divide_period(self, period, freq):
        """Turn a single period into a PeriodIndex with a given frequency.

        For example you could subdivide a month into days or a week into hours.
        The subdivision will be performed down to second precision by default.

        Args:
            period (pd.Period): The period that we wish to subdivide.  If this is None
                we default to subdividing the entire domain of this object.
            freq (str): A Pandas frequency string to use to determine how big the
                chunks are that we are going to subdivid period into.

        Returns:
            pd.DatetimeIndex: The subdivided period.
        """

        if self.oldest_point is None or self.newest_point is None:
            raise UsageError("You must add at least one dataset to the selector first before trying to generate an index.")

        if period is not None:
            start = period.to_timestamp(freq, 'S')
            end = period.to_timestamp(freq, 'E')
        else:
            start = self.oldest_point.to_period(freq).to_timestamp(freq, 'S')
            end = self.newest_point.to_period(freq).to_timestamp(freq, 'E')

        return pd.DatetimeIndex(start=start, end=end, freq=freq, tz=self._timezone)

    def resample(self, data, period, freq, resample='last'):
        """Convenience function to restrict and resample a data set.

        The data set is restricted to the indicated period and if necessary
        resampled to appropriate frequency.  If the data is already sampled
        at the correct frequency then no resampling occurs and NaNs are used
        to fill in any gaps in the indicated period.

        Naive timestamps in data are assumed to be in UTC and localized to
        the configured timezone of this selector before resampling.

        Args:
            data (pd.DataFrame): The data that we would like to sample.
            period (pd.Period): The period that we want to look at.
            freq (str): The sampling frequency that we would like to use.
            resample (str): An optional resampling function in case we need to
                resample the data we are given.
        """

        # First localize the data into the right timezone
        if self._check_tz_naive(data):
            data = data.tz_localize('UTC', copy=False)

        data = data.tz_convert(self._timezone, copy=False)

        # Create the final period index we will return
        index = self.divide_period(period, freq)

        # If the data sampling frequency does not match our desired
        # final sampling frequency, we need to resample it before
        # we can reindex it.
        if data.index.freq != index.freq:
            resampler = data.resample(freq)

            if isinstance(resample, str):
                data = getattr(resampler, resample)()
            else:
                data = resampler.apply(resample)

        return data.reindex(index)
