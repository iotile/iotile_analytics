import tables


class EventIndex(tables.IsDescription):
    """An IOTile Stream (timeseries data)."""

    timestamp = tables.Int64Col()
    event_id = tables.Int64Col()
    event_index = tables.Int64Col()
