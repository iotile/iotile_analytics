"""Table definitions for offline data."""

from .stream import Stream
from .event_index import EventIndex
from .info import DatabaseInfoTable
from .properties import PropertyTable, PropertyTypes

# We cannot document these objects using better-apidoc because they have a custom
# pytables metaclass that maeks them appear to be defined in tables.descriptions, which
# breaks everything since they can't be imported there.
__nodoc__ = ['Stream', 'EventIndex', 'DatabaseInfoTable', 'PropertyTable', 'PropertyTypes']
__all__ = ['Stream', 'EventIndex', 'DatabaseInfoTable', 'PropertyTable', 'PropertyTypes']
