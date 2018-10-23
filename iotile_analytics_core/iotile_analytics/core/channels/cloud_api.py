"""A wrapper around the iotile.cloud API to fetch data diretcly."""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
from future.utils import viewitems

import pandas as pd
from iotile_cloud.api.exceptions import RestHttpBaseException
from typedargs.exceptions import ArgumentError
from .channel import AnalysisGroupChannel, ChannelCaching
from ..session import CloudSession
from ..interaction import ProgressBar
from ..stream_series import StreamSeries
from ..exceptions import CloudError


class IOTileCloudChannel(AnalysisGroupChannel):
    """An AnalysisGroupChannel that fetches data from IOTile.cloud

    Args:
        domain (str): The domain of the iotile.cloud instance that
            you want to fetch data from.
        cloud_id (str): The slug or id of the object to be enumerated to
            create this cloud channel.  If you do not want to enumerate
            any object, you can pass None here.
        include_system (bool): Include hidden system streams when query device
            objects.  This defaults to False.
    """

    def __init__(self, cloud_id, domain, include_system=False):
        super(IOTileCloudChannel, self).__init__()

        stream_finders = {
            'project': self._find_project_streams,
            'device': self._find_device_streams,
            'datablock': self._find_archive_streams
        }

        stream_counters = {
            'device': self._count_device_streams
        }

        stream_finder = None
        source_type = None
        if cloud_id is not None:
            source_type = self._classify_object(cloud_id)
            stream_finder = stream_finders.get(source_type, None)

        self._cache_policy = ChannelCaching.UNLIMITED
        self._session = CloudSession(domain=domain)
        self._api = self._session.get_api()
        self._cloud_id = cloud_id
        self._include_system = include_system
        self._source_type = source_type
        self._stream_finder = stream_finder
        self._stream_counter = stream_counters.get(source_type, self._count_generic_streams)

    @classmethod
    def _classify_object(cls, cloud_id):
        if cloud_id.startswith('p--'):
            return 'project'

        if cloud_id.startswith('d--'):
            return 'device'

        if cloud_id.startswith('b--'):
            return 'datablock'

        raise ArgumentError("Invalid source type", cloud_id=cloud_id, supported_sources=('project', 'device', 'datablock'),
                            suggestion="Try using one of the convenience functions for creating an AnalysisGroup like FromDevice or FromProject")

    def list_streams(self):
        """Return a list of all streams.

        This is equivalent to the IOTile.cloud API method
        /api/v1/stream/

        for datablocks and projects.  For devices, this calls the
        api:
        /api/v1/device/<cloud_id>/extra/

        to also get information on system streams that do not show
        up in the normal stream API.

        Returns:
            list(dict): A list of dictionaries, one for each
                stream that should be part of this analysis group.
        """

        if self._cloud_id is None:
            return []

        return self._stream_finder(self._cloud_id)

    def fetch_source_info(self):
        """Fetch the record associated to the channel object (project, device or datablock)

        This is the object dictionary for the project, device or datablock
        this channel is based on

        Args:
            with_properties: If True, will also fetch object properties and
                add them as dictionary entries

        Returns:
            dict: The raw source object that our analytics group was generated from.
        """

        if self._cloud_id is None:
            return {}

        resource = getattr(self._api, self._source_type)
        try:
            data = resource(self._cloud_id).get()
        except RestHttpBaseException as exc:
            raise CloudError("Error calling method on iotile.cloud", exception=exc, response=exc.response.status_code)

        return data

    def fetch_properties(self):
        """Fetch all properties for a given object (project, device or datablock).

        Returns:
            dict: A dict of property names and values.
        """

        data = {}

        if self._cloud_id is None:
            return {}

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

        return self._stream_counter(slugs)

    def _count_device_streams(self, slugs):
        info = self._api.device(self._cloud_id).extra.get()

        stream_table = info.get('stream_counts', {})

        # Note the specific logic here of is not False.  We explictly want to exclude has_streamid is True and is None
        # since those corresponds with normal streams like app only streams.
        normal_streams = [slug for slug in slugs if stream_table.get(slug, {}).get('has_streamid') is not False]

        normal_counts = self._count_generic_streams(normal_streams)

        results = {}
        for slug in slugs:
            if slug in normal_counts:
                results[slug] = normal_counts[slug]
            elif slug in stream_table:
                results[slug] = {'points': stream_table[slug].get('data_cnt', 0), 'events': stream_table[slug].get('event_cnt', 0)}
            else:
                raise CloudError("Could not find stream to perform a count", slug=slug)

        return results

    def _count_generic_streams(self, slugs):
        resources = [self._api.stream(x).data for x in slugs]
        ts_results = self._session.fetch_multiple(resources, message='Counting Data in Streams', page_size=1)

        event_resources = [self._api.event for x in slugs]
        event_args = [{"filter": x} for x in slugs]

        event_results = self._session.fetch_multiple(event_resources, event_args, message='Counting Events in Streams', page_size=1)
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
            data = self._session.fetch_all(resource, page_size=1000, message="Downloading Events", filter=slug, mask=1)

            dt_index = pd.to_datetime([x['timestamp'] for x in data])
            extra_data = [x['extra_data'] for x in data]

            for i, event in enumerate(data):
                extra_data[i]['event_id'] = event['id']
                extra_data[i]['has_raw_data'] = event.get('has_raw_data', False)

            return pd.DataFrame(extra_data, index=dt_index)
        except RestHttpBaseException as exc:
            raise CloudError("Error fetching events from stream", exception=exc, response=exc.response.status_code)

    def fetch_raw_events(self, slug, postprocess=None):
        """Fetch all raw event data for this stream.

        These are the raw json dictionaries that may be stored for
        each event.

        Args:
            slug (str): The slug of the stream that we should fetch
                raw events for.
            postprocess (callable): Function that should be applied to each
                raw event before adding to the dataframe.  This should
                take in a dict and return a dict.  The signature is
                postprocess(i, data) where i is the index of the row in
                the output dataframe.

        Returns:
            pd.DataFrame: All of the raw events.  This will be empty if
                there are no raw events.
        """

        events = self.fetch_events(slug)
        if len(events) == 0:
            return pd.DataFrame()

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

        data = self._session.fetch_multiple(resources, postprocess=postprocess, message="Downloading Raw Event Data")
        # new_index includes all indexes with actual data
        new_index = pd.to_datetime(new_index)
        return pd.DataFrame(data, index=new_index)

    def fetch_datapoints(self, slug):
        """Fetch all data points for this stream.

        These are time, value data pairs stored in the stream. Internal
        metadata about those data points is not returned. The result is a norm
        pandas Series subclass with additional functionality to support unit
        conversion.

        Args:
            slug (str): The slug of the stream that we should fetch
                raw data points for.

        Returns:
            StreamSeries: A data fame with internal value as floating
                point data.
        """

        use_data_api = False

        with ProgressBar(1, "Fetching %s" % slug, leave=False) as prog:
            raw_data = self._api.df.get(filter=slug, format='csv')

            str_data = raw_data.decode('utf-8')
            rows = str_data.splitlines()
            data = [x.split(',') for x in rows]
            data = data[1:]  # There is a single header line

            # FIXME: Hack to work around issue returning int_value for these objects
            if len(data) > 0 and data[0][1] == '':
                use_data_api = True
            else:
                dt_index = pd.to_datetime([x[0] for x in data])

            prog.update(1)

        if not use_data_api:
            return StreamSeries([float(x[1]) for x in data], index=dt_index)

        resource = self._api.data
        raw_json = self._session.fetch_all(resource, page_size=10000, message="Downloading Data", filter=slug, mask=1)

        dt_index = pd.to_datetime([x['timestamp'] for x in raw_json])
        data = [x['int_value'] for x in raw_json]

        return StreamSeries(data, index=dt_index)

    def _find_device_streams(self, device_slug):
        """Find all streams for a device by its slug."""

        try:
            results = self._api.stream.get(device=device_slug)
            streams = results['results']

            if self._include_system:
                hidden_results = self._api.device(device_slug).extra.get()
                hidden_streams = [slug for slug, data in viewitems(hidden_results.get('stream_counts', {})) if data.get('has_streamid') is False]

                streams += hidden_streams

            return streams
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

    def set_caching(self, policy, param=None):
        """Configure how this channel handling caching data that has been fetched.

        Args:
            policy (int): One of UNLIMITED_CACHE, LRU_CACHE or NO_CACHE.
            param (object): Optional parameter that can configure the behavior of
                the caching mode chosen.
        """

        if policy not in (ChannelCaching.UNLIMITED, ChannelCaching.NONE):
            raise ArgumentError("Unsupported cache policy type", policy=policy)

        self._cache_policy = policy

        if policy == ChannelCaching.UNLIMITED:
            self._session.enable_cache = True
        else:
            self._session.enable_cache = False
