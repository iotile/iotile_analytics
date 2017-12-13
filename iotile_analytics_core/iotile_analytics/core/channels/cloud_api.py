"""A wrapper around the iotile.cloud API to fetch data diretcly."""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
from future.utils import viewitems

import pandas as pd
from iotile_cloud.stream.data import StreamData
from iotile_cloud.api.exceptions import RestHttpBaseException
from typedargs.exceptions import ArgumentError
from .channel import AnalysisGroupChannel
from ..session import CloudSession
from ..stream_series import StreamSeries
from ..exceptions import CloudError


class IOTileCloudChannel(AnalysisGroupChannel):
    """An AnalysisGroupChannel that fetches data from IOTile.cloud

    Args:
        domain (str): The domain of the iotile.cloud instance that
            you want to fetch data from.
        cloud_id (str): The slug or id of the object to be enumerated to
            create this cloud channel.
        source_type (str): The type of object that we are enumerating.
            This must be one of project, device or archive.
    """

    def __init__(self, cloud_id, source_type, domain):
        super(IOTileCloudChannel, self).__init__()

        stream_finders = {
            'project': self._find_project_streams,
            'device': self._find_device_streams,
            'datablock': self._find_archive_streams
        }

        stream_finder = stream_finders.get(source_type, None)
        if stream_finder is None:
            raise ArgumentError("Invalid source type", source_type=source_type, supported_sources=stream_finders.keys(), suggestion="Try using one of the convenience functions for creating an AnalysisGroup like FromDevice or FromProject")

        self._session = CloudSession(domain=domain)
        self._api = self._session.get_api()
        self._cloud_id = cloud_id
        self._source_type = source_type
        self._stream_finder = stream_finder

    def list_streams(self):
        """Return a list of all streams.

        This is equivalent to the IOTile.cloud API method
        /api/v1/stream/

        Returns:
            list(dict): A list of dictionaries, one for each
                stream that should be part of this analysis group.
        """

        return self._stream_finder(self._cloud_id)

    def fetch_source_info(self, with_properties=False):
        """Fetch the record associated to the channel object (project, device or datablock)

        This is the object dictionary for the project, device or datablock this channel is based on

        Args:
            with_properties: If True, will also fetch object properties and add them as dictionary entries

        Returns:
            dict(<name>: <value>): A dict mapping object attribute names and values (including properties
            if with_properties=True)
        """

        resource = getattr(self._api, self._source_type)
        try:
            data = resource(self._cloud_id).get()
        except RestHttpBaseException as exc:
            raise CloudError("Error calling method on iotile.cloud", exception=exc, response=exc.response.status_code)

        if with_properties:
            try:
                property_data = self._api.property.get(target=self._cloud_id)
                if 'count' in property_data and property_data['count']:
                    for item in property_data['results']:
                        data[item['name']] = item['value']
            except RestHttpBaseException as exc:
                raise CloudError("Error calling method on iotile.cloud", exception=exc,
                                 response=exc.response.status_code)

        return data

    def count_streams(self, slugs):
        """Count the number of events and data points in a stream.

        Args:
            slug (list(str)): The slugs of the stream that we should count.

        Returns:
            dict(<slug>: {'points': int, 'events': int}): A dict mapping dicts of 2
                integers with the count of the number of events and the number of
                data points in this stream.
        """

        resources = [self._api.stream(x).data for x in slugs]
        ts_results = self._session.fetch_multiple(resources, message='Counting Events in Streams', page_size=1)

        event_resources = [self._api.event for x in slugs]
        event_args = [{"filter": x} for x in slugs]

        event_results = self._session.fetch_multiple(event_resources, event_args, message='Counting Data in Streams', page_size=1)

        return {slug: {'points': ts['count'], 'events': event['count']} for slug, ts, event in zip(slugs, ts_results, event_results)}

    def fetch_variable_types(self, slugs):
        """Fetch variable type information for a list of variable slugs.

        Args:
            slugs (list(str)): The slugs of the variable types that we should fetch.

        Returns:
            dict(<slug>: dict): A dict mapping variable slugs to variable type definitions
        """

        resources = [self._api.vartype(x) for x in slugs]
        variables = self._session.fetch_multiple(resources, message='Fetching Variable Types')

        return {x['slug']: x for x in variables}

    def fetch_events(self, slug):
        """Fetch all events for a given stream.

        These are the event metadata dictionaries, not the raw
        event data that may be stored along with the metadata.

        Args:
            slug (str): The slug of the stream that we should fetch
                events for.

        Returns:
            pd.DataFrame: A data frame with all of the events in this
                stream.
        """

        try:
            resource = self._api.event
            data = self._session.fetch_all(resource, page_size=1000, message="Downloading Events", filter=slug)

            dt_index = pd.to_datetime([x['timestamp'] for x in data])
            extra_data = [x['extra_data'] for x in data]

            for i, event in enumerate(data):
                extra_data[i]['event_id'] = event['id']
                extra_data[i]['has_raw_data'] = event.get('has_raw_data', False)

            return pd.DataFrame(extra_data, index=dt_index)
        except RestHttpBaseException as exc:
            raise CloudError("Error fetching events from stream", exception=exc, response=exc.response.status_code)

    def fetch_raw_events(self, slug):
        """Fetch all raw event data for this stream.

        These are the raw json dictionaries that may be stored for
        each event.

        Args:
            slug (str): The slug of the stream that we should fetch
                raw events for.

        Returns:
            pd.DataFrame: All of the raw events.
        """

        events = self.fetch_events(slug)
        event_ids = events['event_id'].values
        # event.has_raw_data is true if there is an associated raw JSON file stored on S3 for this event
        event_has_data = events['has_raw_data'].values
        indexes = events.index
        resources = []
        new_index = []
        for index in range(len(event_ids)):
            if event_has_data[index]:
                resources.append(self._api.event(event_ids[index]).data)
                new_index.append(indexes[index])

        data = self._session.fetch_multiple(resources, message="Downloading Raw Event Data")
        # new_index includes all indexes with actual data
        new_index = pd.to_datetime(new_index)
        return pd.DataFrame(data, index=new_index)

    def fetch_datapoints(self, slug):
        """Fetch all data points for this stream.

        These are time, value data pairs stored in the stream.

        Args:
            slug (str): The slug of the stream that we should fetch
                raw events for.

        Returns:
            StreamSeries: A data fame with internal value as floating
                point data.
        """

        resource = self._api.stream(slug).data
        raw_data = self._session.fetch_all(resource, page_size=1000, message="Downloading Stream Data")

        dt_index = pd.to_datetime([x['timestamp'] for x in raw_data])
        return StreamSeries([x['value'] for x in raw_data], index=dt_index)

    def _find_device_streams(self, device_slug):
        """Find all streams for a device by its slug."""

        try:
            results = self._api.stream.get(device=device_slug)
            return results['results']
        except RestHttpBaseException as exc:
            raise CloudError("Error calling method on iotile.cloud", exception=exc, response=exc.response.status_code)

    def _find_archive_streams(self, archive_slug):
        """Find all streams for an archive by its slug."""

        try:
            results = self._api.stream.get(block=archive_slug, all=1)
            return results['results']
        except RestHttpBaseException as exc:
            raise CloudError("Error calling method on iotile.cloud", exception=exc, response=exc.response.status_code)

    def _find_project_streams(self, project_id):
        """Find all streams in a project by its uuid."""

        try:
            results = self._api.stream.get(project=project_id)
            return results['results']
        except RestHttpBaseException as exc:
            raise CloudError("Error calling method on iotile.cloud", exception=exc, response=exc.response.status_code)
