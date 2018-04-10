import tables


class PropertyTable(tables.IsDescription):
    """All associated source info."""

    key = tables.StringCol(256)
    str_value = tables.StringCol(256)
    int_value = tables.Int64Col()
    bool_value = tables.BoolCol()
