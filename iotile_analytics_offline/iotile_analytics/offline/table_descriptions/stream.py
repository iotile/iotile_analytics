import tables


class Stream(tables.IsDescription):
    """An IOTile Stream (timeseries data)."""

    internal_value = tables.Float64Col()
    timestamp = tables.Int64Col()
    device_timestamp = tables.Int64Col()
    reading_id = tables.Int64Col()
