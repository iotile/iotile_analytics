"""Overall class for creating and managing offline data."""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from future.utils import viewitems
from builtins import int
from past.builtins import basestring
import uuid
import os.path
import tables
import pandas as pd
import numpy as np
from iotile_analytics.core.stream_series import StreamSeries
from typedargs.exceptions import ArgumentError
from .table_descriptions import Stream, EventIndex, PropertyTable

try:
    import cPickle as pickle
except ImportError:
    import pickle


class CompatibleObjectAtom(tables.ObjectAtom):
    """An object atom with a lower cpickle protocol.

    This enables sharing hdf5 files between python 2 and python 3.
    """

    def _tobuffer(self, object_):
        return pickle.dumps(object_, 2)

    def fromarray(self, array):
        # We have to check for an empty array because of a possible
        # bug in HDF5 which makes it claim that a dataset has one
        # record when in fact it is empty.
        if array.size == 0:
            return None
        return pickle.loads(array.tostring())


class OfflineDatabase(object):
    """An offline database.

    If you pass an existing file, this database will open that
    file.  If you pass a non-existing file, this database will
    create a new database.  If you pass nothing, a new in-memory
    database will be created that will not be backed by file
    storage.

    Args:
        path (str): The path to the database file that we want
            to create or open.  If None if passed (the default),
            a new, in-memory database is created that will be
            lost when the program is exited.
    """

    def __init__(self, path=None):
        if path is None:
            self._file = tables.open_file(str(uuid.uuid4()), "w", driver="H5FD_CORE", driver_core_backing_store=0)
            self._initialize_database()
            self.read_only = False
            return

        # NB. It is important that this is a real str object and not a future.newstr
        # otherwise pytables will throw an exception when it tries to open the file.
        path = str(path)
        if os.path.isfile(path):
            self._file = tables.open_file(path, mode="r")
            self.read_only = True
        else:
            self._file = tables.open_file(path, mode="w")
            self._initialize_database()
            self.read_only = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._file.close()

    def _initialize_database(self):
        """Create all necessary tables."""

        root = self._file.root
        self._file.create_group(root, 'streams')

        meta = self._file.create_group(root, 'meta')
        self._file.create_vlarray(meta, 'archive_definitions', CompatibleObjectAtom())
        self._file.create_vlarray(meta, 'device_definitions', CompatibleObjectAtom())
        self._file.create_vlarray(meta, 'vartype_definitions', CompatibleObjectAtom())
        self._file.create_table(meta, 'source_info', PropertyTable)

    def save_stream(self, slug, definition, data=None, events=None, raw_events=None):
        """Save a stream with timeseries and event data.

        Args:
            slug (str): The stream slug to save
            definition (dict): The stream metadata dictionary that comes
                from the /api/v1/stream/<slug>/ API
            data (StreamData): The raw stream timeseries data to save.
            events (pandas.DataFrame): Any event summary data to save.
            raw_events (pandas.DataFrame): The raw event data to save.
        """

        if self.read_only:
            raise ArgumentError("Attemping to save a stream in a read only database", slug=slug)

        # Create a natural name for ease of access
        slug = slug.replace('-', '_')

        node_path = '/streams/%s' % slug

        if node_path in self._file:
            raise ArgumentError("Stream already exists in file, cannot save", slug=slug)

        has_raw_events = raw_events is not None and len(raw_events) > 0
        if has_raw_events and len(raw_events) != len(events):
            raise ArgumentError("If you pass raw events, you must pass the same number as the number of events")

        filters = tables.Filters(complevel=1)

        group = self._file.create_group('/streams', slug)

        arr_def = self._file.create_vlarray(group, 'definition', CompatibleObjectAtom(), filters=filters)
        arr_events = self._file.create_vlarray(group, 'events', CompatibleObjectAtom(), filters=filters)
        arr_rawevents = self._file.create_vlarray(group, 'raw_events', CompatibleObjectAtom(), filters=filters)
        table_data = self._file.create_table(group, 'data', Stream)
        table_events = self._file.create_table(group, 'event_index', EventIndex)

        arr_def.append(definition)

        row = table_events.row

        if events is not None:
            for i, (timestamp, event) in enumerate(events.iterrows()):
                row['timestamp'] = self._to_timecol(timestamp)
                row['event_id'] = event['event_id']
                row['event_index'] = i

                row.append()

                arr_events.append(event)

                if has_raw_events:
                    arr_rawevents.append(raw_events.iloc[i].to_dict())

            table_events.flush()

        row = table_data.row
        if data is not None:
            for timestamp, point in data.iterrows():
                row['timestamp'] = self._to_timecol(timestamp)
                row['internal_value'] = point[0]

                row.append()

            table_data.flush()

    def save_vartype(self, _slug, vartype):
        """Save a vartype into the database.

        Args:
            _slug (str): The variable type slug to save.
            vartype (dict): The variable type data to save.
        """

        if self.read_only:
            raise ArgumentError("Attempted to save variable type in read only file")

        table = self._file.root.meta.vartype_definitions
        table.append(vartype)

    def save_source_info(self, info):
        """Save analysis group source metadata including properties if set.

        Args:
            info (dict): A dict of string -> string with the properties and data
                about the analysis group source.
        """

        if self.read_only:
            raise ArgumentError("Attempted to save source info in read only file")

        table = self._file.root.meta.source_info

        for key, value in viewitems(info):
            entry = table.row
            entry['key'] = key.encode('utf-8')

            if isinstance(value, basestring):
                entry['str_value'] = value.encode('utf-8')
            elif isinstance(value, int):
                entry['int_value'] = value
            elif isinstance(value, bool):
                entry['bool_value'] = value
            elif value is None:
                pass # Store a None as nothing
            else:
                raise ArgumentError("Unsupported data type in source_info", key=key, value=value, type=type(value))

            entry.append()

    def fetch_source_info(self, with_properties=False):
        """Fetch presaved source info.

        Args:
            with_properties (bool): Include properties attached to
                the object or not.  Support for this is currently
                not implemented since there is no distinction between
                property and non-property info.

        Returns:
            dict: A string -> string key-value store of source information.
        """

        table = self._file.root.meta.source_info

        out_data = {}
        for row in table.iterrows():
            key = row['key'].decode('utf-8')

            if row['str_value'] is not None:
                value = row['str_value'].decode('utf-8')
            elif row['int_value'] is not None:
                value = int(row['int_value'])
            elif row['bool_value'] is not None:
                value = bool(row['bool_value'])
            else:
                value = None

            out_data[key] = value

        return out_data

    @classmethod
    def _to_timecol(cls, value):
        return value.to_datetime64().astype(np.int64)

    def list_streams(self):
        """Return a list of all streams.

        This is equivalent to the IOTile.cloud API method
        /api/v1/stream/

        Returns:
            list(dict): A list of dictionaries, one for each
                stream that should be part of this analysis group.
        """

        return [x.definition[0] for x in self._file.root.streams._f_iter_nodes()]

    def close(self):
        self._file.close()

    def get_stream_definition(self, slug):
        """Get the stream definitions for a stream.

        Args:
            slug (str): The stream slug to query

        Returns:
            dict: The stream metadata
        """

        name = slug.replace('-', '_')

        if name not in self._file.root.streams:
            raise ArgumentError("Stream slug not found in OfflineDatabase", slug=slug)

        group = getattr(self._file.root.streams, name)
        return group.definition[0]

    def fetch_datapoints(self, slug):
        """Get all timeseries data for a stream.

        Args:
            slug (str): The stream slug to query

        Returns:
            StreamSeries: The stream data.
        """

        name = slug.replace('-', '_')

        if name not in self._file.root.streams:
            raise ArgumentError("Stream slug not found in OfflineDatabase", slug=slug)

        data = getattr(self._file.root.streams, name).data

        index = data.read(field='timestamp')
        values = data.read(field='internal_value')

        dt_index = pd.to_datetime(index, unit='ns')
        return StreamSeries(values, index=dt_index)

    def _get_event_index(self, name):
        data = getattr(self._file.root.streams, name).event_index
        return data.read()

    def fetch_events(self, slug):
        """Fetch all events for a given stream.

        These are the event metadata dictionaries, not the raw
        event data that may be stored along with the metadata.

        Args:
            slug (str): The slug of the stream that we should fetch
                events for.

        Returns:
            pd.DataFrame: All of the events.
        """

        name = slug.replace('-', '_')

        if name not in self._file.root.streams:
            raise ArgumentError("Stream slug not found in OfflineDatabase", slug=slug)

        events = self._get_event_index(name)

        event_data = getattr(self._file.root.streams, name).events.read()

        index = pd.to_datetime([x['timestamp'] for x in events], unit='ns')
        return pd.DataFrame(event_data, index=index)

    def _count_stream(self, slug):
        """Count the number of data points and events in a stream."""

        name = slug.replace('-', '_')

        if name not in self._file.root.streams:
            raise ArgumentError("Stream slug not found in OfflineDatabase", slug=slug)

        stream = getattr(self._file.root.streams, name)
        data_count = len(stream.data)
        event_count = len(stream.events)

        return {'points': data_count, 'events': event_count}

    def fetch_raw_events(self, slug):
        """Fetch all raw event data for this stream.

        These are the raw json dictionaries that are stored for
        each event.

        Args:
            slug (str): The slug of the stream that we should fetch
                raw events for.

        Returns:
            pd.DataFrame: All of the raw events.
        """

        name = slug.replace('-', '_')

        if name not in self._file.root.streams:
            raise ArgumentError("Stream slug not found in OfflineDatabase", slug=slug)

        events = self._get_event_index(name)

        event_data = getattr(self._file.root.streams, name).raw_events.read()

        index = pd.to_datetime([x['timestamp'] for x in events], unit='ns')
        return pd.DataFrame(event_data, index=index)

    def count_streams(self, slugs):
        """Count the number of events and data points in a stream.

        Args:
            slugs (list(str)): The slugs of the stream that we should count.

        Returns:
            dict(<slug>: {'points': int, 'events': int}): A dict mapping dicts of 2
                integers with the count of the number of events and the number of
                data points in this stream.
        """

        return {slug: self._count_stream(slug) for slug in slugs}

    def fetch_variable_types(self, slugs):
        """Fetch variable type information for a list of variable slugs.

        Args:
            slugs (list(str)): The slugs of the variable types that we should fetch.

        Returns:
            dict(<slug>: dict): A dict mapping variable slugs to variable type definitions
        """

        slugs = set(slugs)
        vartypes = self._file.root.meta.vartype_definitions.read()

        return {x['slug']: x for x in vartypes if x['slug'] in slugs}


# Register hook to silently close files at process exit
# From: http://www.pytables.org/cookbook/tailoring_atexit_hooks.html
def _silently_close_open_files(verbose):
    open_files = tables.file._open_files

    are_open_files = len(open_files) > 0

    if verbose and are_open_files:
        sys.stderr.write("Closing remaining open files:")

    if StrictVersion(tables.__version__) >= StrictVersion("3.1.0"):
        # make a copy of the open_files.handlers container for the iteration
        handlers = list(open_files.handlers)
    else:
        # for older versions of pytables, setup the handlers list from the
        # keys
        keys = open_files.keys()
        handlers = []
        for key in keys:
            handlers.append(open_files[key])

    for fileh in handlers:
        if verbose:
            sys.stderr.write("%s..." % fileh.filename)

        fileh.close()

        if verbose:
            sys.stderr.write("done")

    if verbose and are_open_files:
        sys.stderr.write("\n")

import sys, atexit
from distutils.version import StrictVersion
atexit.register(_silently_close_open_files, False)
