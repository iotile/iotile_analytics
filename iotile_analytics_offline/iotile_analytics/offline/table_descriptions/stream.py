import tables


class Stream(tables.IsDescription):
    """An IOTile Stream (timeseries data)."""

    internal_value = tables.Float64Col()
    timestamp = tables.Int64Col()
