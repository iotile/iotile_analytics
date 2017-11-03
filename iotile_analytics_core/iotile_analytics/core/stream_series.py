"""A Pandas DataFrame subclass for dealing with TimeSeries data from IOTile.cloud streams."""

import pandas as pd


class StreamSeries(pd.DataFrame):
    """A DataFrame subclass for handle stream timeseries data.

    All arguemnts are passed through to the underlying dataframe
    except for the optional stream and variable arguments that let
    you set associated metadata and units for this stream.
    """

    _metadata = ['_stream', '_variable']

    def __init__(self, *args, **kwargs):
        self._stream = None
        self._variable = None

        if 'stream' in kwargs:
            self.set_stream(kwargs['stream'])
            del kwargs['stream']

        if 'variable' in kwargs:
            self.set_variable(kwargs['variable'])
            del kwargs['variable']

        super(StreamSeries, self).__init__(*args, **kwargs)

    @property
    def _constructor(self):
        return StreamSeries

    def set_stream(self, stream):
        """Set the stream metadata for this data series.

        This data is what is returned by the iotile.cloud
        API /api/v1/stream/<slug>/

        It contains the stream slug, some metadata and the list
        of available output units for conversion.

        Args:
            stream (dict): Stream metadata returned from iotile.cloud
        """

        self._stream = stream

    def set_variable(self, variable):
        """Set the variable metadata for this data series.

        This data is what is returned by the iotile.cloud API
        /api/v1/variable/<var_slug>
        """

        self._variable = variable

    @property
    def available_units(self):
        """Get the available output units for this data stream.

        Returns:
            list: A list of unit names that this stream can be
                converted to.
        """

        if self._stream is None:
            return []

        #FIXME: pull in variable information with available units
        return [self._stream['output_unit']['unit_full']]

    def convert(self, units):
        """Convert this stream to another set of supported units.

        Args:
            units (str): The desired output units for this stream.

        Returns:
            pd.DataFrame: The converted data stream.
        """

        out = pd.DataFrame(self.values, index=self.index)

        #FIXME: Actually do the conversion
        return out
