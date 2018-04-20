"""Table of metadata about this database including version and creation time."""

import tables


class DatabaseInfoTable(tables.IsDescription):
    major_version = tables.Int64Col()
    minor_version = tables.Int64Col()
    patch_version = tables.Int64Col()
