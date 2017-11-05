"""Overall class for creating and managing offline data."""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import uuid
import os.path
import tables
import pandas as pd
import numpy as np
from iotile_analytics.core.stream_series import StreamSeries
from typedargs.exceptions import ArgumentError
from .table_descriptions import Stream, EventIndex


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
        elif os.path.isfile(path):
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
        self._file.create_vlarray(meta, 'archive_defintions', tables.ObjectAtom())
        self._file.create_vlarray(meta, 'device_definitions', tables.ObjectAtom())
        self._file.create_vlarray(meta, 'vartype_definitions', tables.ObjectAtom())

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

        if raw_events is not None and len(raw_events) != len(events):
            raise ArgumentError("If you pass raw events, you must pass the same number as the number of events")

        filters = tables.Filters(complevel=1)

        group = self._file.create_group('/streams', slug)

        arr_def = self._file.create_vlarray(group, 'definition', tables.ObjectAtom(), filters=filters)
        arr_events = self._file.create_vlarray(group, 'events', tables.ObjectAtom(), filters=filters)
        arr_rawevents = self._file.create_vlarray(group, 'raw_events', tables.ObjectAtom(), filters=filters)
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

                if raw_events is not None:
                    arr_rawevents.append(raw_events.iloc[i].values)

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

    @classmethod
    def _to_timecol(cls, value):
        return np.datetime64(value).astype('float64') / 1e6

    def list_streams(self):
        """List all stream slugs defined in this OfflineDatabase.

        Returns:
            set(str): A set of all of the stream slugs defined in this database.
        """

        return set([x._v_name.replace('_', '-') for x in self._file.root.streams._f_iter_nodes()])

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

    def get_datapoints(self, slug):
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

        dt_index = pd.to_datetime(index*1e9)
        return StreamSeries(values, index=dt_index)

    def _get_event_index(self, name):
        data = getattr(self._file.root.streams, name).event_index
        return data.read()

    def get_events(self, slug):
        """Get all events for a stream.

        Args:
            slug (str): The stream slug to query

        Returns:
            pd.DataFrame: All of the events.
        """

        name = slug.replace('-', '_')

        if name not in self._file.root.streams:
            raise ArgumentError("Stream slug not found in OfflineDatabase", slug=slug)

        events = self._get_event_index(name)

        event_data = getattr(self._file.root.streams, name).events.read()

        index = pd.to_datetime([x['timestamp']*1e9 for x in events])
        return pd.DataFrame(event_data, index=index)
