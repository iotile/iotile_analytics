"""A class that lets you compare portions of multiple timeseries datasets."""

from builtins import range
from typedargs.exceptions import ArgumentError
import pandas as pd
import numpy as np


class TimeseriesAggregator(object):
    """A utility class for aggregating and selecting data from multiple timeseries.

    All timeseries added to the aggregator automatically have their indices resampled
    to be uniform and are then concatenated into a global index.  You can easily select
    subsets of the index to to see what data is present in each of the data sets for
    that region of time.

    Args:
        granularity (str): The finest sampling granulatary that you wish to use for all
            added datasets.  This is passed to pandas dataframe.resample for all added
            data before processing so that equivalent time points are treated as equal.
        resampling_function (str): The name of the resampling function to use to resample.
            Defaults to the last data point of the period data.  This should be something
            like 'mean', 'sum', etc.
        timezone (str): The timezone to use to localize all data coming in so that days
            correspond correctly to days in that timezone.  Default: UTC.  This should be
            a timzeone value like 'US/Central'.
    """

    def __init__(self, granulatary, resampling_function='last', timezone='UTC'):
        self._granulatary = granulatary
        self._resampling_function = resampling_function
        self._timezone = timezone

        self._data = {}
        self.domain = None

    def add_data(self, name, data):
        """Add a new dataset to the aggregator.

        The data is homogenized and the underlying domain of the aggregator is
        extended if necessary.

        Args:
            name (str): A unique name for this dataset so that it can be retrieved
                later.
            data (pd.DataFrame): A dataframe to add to our aggregator.
        """

        if name in self._data:
            raise ArgumentError("Attempted to add data with the same name as an existing dataset", name=name)

        # First localize the data into the right timezone
        data = data.tz_localize('UTC').tz_convert(self._timezone)

        # Next, homogenize its index into the right granularity
        data = getattr(data.resample(self._granulatary), self._resampling_function)()

        if self.domain is None:
            self.domain = data.index
        else:
            self.domain = self.domain.union(data.index)

        self._data[name] = data

    def dates(self, mask=None):
        """Get all of the datetimes in our data domain as a multidimensional array.

        There will be 8 columns:
        - year
        - month
        - day
        - hour
        - minute
        - second
        - week
        - weekday

        Args:
            mask (tuple): Optional 8-tuple of bools that will cause parts of the dates to be masked
                out with Nones to act as a wildcard.  Place False in an entry to mask out that portion
                of the date.

        Returns:
            list of tuples: The resulting tuples for each date.
        """

        if self.domain is None:
            return []

        if mask is None:
            mask = (True,)*8

        num_dates = len(self.domain)
        out_arr = []

        year = self.domain.year
        month = self.domain.month
        day = self.domain.day
        hour = self.domain.hour
        minute = self.domain.minute
        second = self.domain.second
        week = self.domain.week
        weekday = self.domain.weekday

        for i in range(0, num_dates):
            val = [None]*8

            if mask[0]:
                val[0] = year.values[i]
            if mask[1]:
                val[1] = month.values[i]
            if mask[2]:
                val[2] = day.values[i]
            if mask[3]:
                val[3] = hour.values[i]
            if mask[4]:
                val[4] = minute.values[i]
            if mask[5]:
                val[5] = second.values[i]
            if mask[6]:
                val[6] = week.values[i]
            if mask[7]:
                val[7] = weekday.values[i]

            out_arr.append(tuple(val))

        return out_arr

    def _deduplicate_in_order(self, in_list):
        out = []
        seen = set()

        for date in in_list:
            if date in seen:
                continue

            out.append(date)
            seen.add(date)

        return out

    def months(self):
        """Get all of the unique months spanning our data domain.

        The results are returned in time order with duplicates removed.

        Returns:
            list of datemasks: The month date masks that can be used to select a subset
                of data from this aggregator.
        """

        dates = self.dates(mask=(True, True, False, False, False, False, False, False))
        return self._deduplicate_in_order(dates)

    def weeks(self):
        """Get all unique weeks spanning our data domain.

        The results are returned in time order with duplicates removed.

        Returns:
            list of datemasks: The week date masks that can be used to select a subset
                of data from this aggregator.
        """

        dates = self.dates(mask=(True, False, False, False, False, False, True, False))
        return self._deduplicate_in_order(dates)

    def days(self):
        """Get all unique days spanning our data domain.

        The results are returned in time order with duplicates removed.

        Returns:
            list of datemasks: The day date masks that can be used to select a subset
                of data from this aggregator.
        """

        dates = self.dates(mask=(True, True, True, False, False, False, False, False))
        return self._deduplicate_in_order(dates)

    def _create_mask(self, restrict):
        if len(restrict) != 8:
            raise ArgumentError("Invalid date restriction tuple")

        if self.domain is None:
            raise ArgumentError("You must add some data before creating a mask")

        mask = np.ndarray(len(self.domain), dtype=np.bool)
        mask[:] = True

        if restrict[0] is not None:
            mask &= self.domain.year == restrict[0]
        if restrict[1] is not None:
            mask &= self.domain.month == restrict[1]
        if restrict[2] is not None:
            mask &= self.domain.day == restrict[2]
        if restrict[3] is not None:
            mask &= self.domain.hour == restrict[3]
        if restrict[4] is not None:
            mask &= self.domain.minute == restrict[4]
        if restrict[5] is not None:
            mask &= self.domain.second == restrict[5]
        if restrict[6] is not None:
            mask &= self.domain.week == restrict[6]
        if restrict[7] is not None:
            mask &= self.domain.weekday == restrict[7]

        return mask

    def get(self, name, restrict=None, include_nan=False):
        """Get a portion of a dataset restricted to a given time interval."""

        if name not in self._data:
            raise ArgumentError("Unknown dataset name", name=name, datasets=self._data.keys())

        data = self._data[name]

        if restrict is not None:
            mask = self._create_mask(restrict)
            data = data[mask]

        if not include_nan:
            data = data.dropna()

        return data
