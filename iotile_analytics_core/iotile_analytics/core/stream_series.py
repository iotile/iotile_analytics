"""A Pandas DataFrame subclass for dealing with TimeSeries data from IOTile.cloud streams."""

import pandas as pd
from typedargs.exceptions import ArgumentError


class StreamSeries(pd.DataFrame):
    """A DataFrame subclass for handle stream timeseries data.

    All arguemnts are passed through to the underlying dataframe
    except for the optional stream and variable arguments that let
    you set associated metadata and units for this stream.
    """

    _metadata = ['_stream', '_vartype']

    def __init__(self, *args, **kwargs):
        self._stream = None
        self._vartype = None

        if 'stream' in kwargs:
            self.set_stream(kwargs['stream'])
            del kwargs['stream']

        if 'vartype' in kwargs:
            self.set_variable(kwargs['vartype'])
            del kwargs['vartype']

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

    def set_vartype(self, vartype):
        """Set the variable type and units metadata for this data series.

        This data is what is returned by the iotile.cloud API
        /api/v1/vartype/<slug>
        """

        self._vartype = vartype

    @property
    def available_units(self):
        """Get the available output units for this data stream.

        Returns:
            list: A list of unit names that this stream can be
                converted to.
        """

        if self._vartype is not None:
            return [x['unit_full'] for x in self._vartype.get('available_output_units', [])]

        if self._stream is not None:
            return [self._stream['output_unit']['unit_full']]

        return []

    def _mdo_for_unit(self, unit):
        if unit not in self.available_units:
            raise ArgumentError("Unknown units", units=unit)

        if self._vartype is not None:
            units = {x['unit_full']: x for x in self._vartype.get('available_output_units', [])}
        else:
            units = {self._stream['output_unit']['unit_full']: self._stream['output_unit']}

        unit_data = units[unit]
        m = unit_data.get('m', 1)
        d = unit_data.get('d', 1)
        o = unit_data.get('o', 0.0)

        return (m, d, o)

    def apply_mdo(self, m, d, o):
        """Convert this stream by applying a fixed m, d, o transformation.

        Args:
            m (float): The number to multiply by.
            d (float): The number to divide by.
            o (float): The number to add as an offset.

        Returns:
            pd.DataFrame: The converted data stream.
        """

        out = pd.DataFrame(self.values, copy=True, index=self.index)

        out[0] *= float(m)
        out[0] /= float(d)
        out[0] += float(o)

        return out


    def convert(self, units):
        """Convert this stream to another set of supported units.

        Args:
            units (str): The desired output units for this stream.

        Returns:
            pd.DataFrame: The converted data stream.
        """

        m, d, o = self._mdo_for_unit(units)
        return self.apply_mdo(m, d, o)
