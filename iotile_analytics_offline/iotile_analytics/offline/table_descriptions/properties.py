import tables

class PropertyTypes(object):
    STRING = 0
    INT = 1
    BOOL = 2
    NONE = 3


class PropertyTable(tables.IsDescription):
    """All associated source info."""

    value_type = tables.Int64Col()
    key = tables.StringCol(256)
    str_value = tables.StringCol(256)
    int_value = tables.Int64Col()
    bool_value = tables.BoolCol()
