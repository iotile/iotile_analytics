"""The AnalysisGroup is the main entry point for analyzing data.

It allows you to select data streams from IOTile.cloud and turn them
into Pandas time series for analysis.  You can create an AnalysisGroup
from a Project, a Device or a DataBlock.
"""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
from future.utils import viewitems

import pandas as pd
from iotile_cloud.api.connection import DOMAIN_NAME
from iotile_cloud.api.exceptions import RestHttpBaseException
from iotile_cloud.stream.data import StreamData
from typedargs.exceptions import ArgumentError
from .exceptions import CloudError
from .session import CloudSession


class AnalysisGroup(object):
    """A top level entry point for selecting and analyzing data.

    Currently AnalysisGroups must be created by passing the id
    or slug of a project in iotile.cloud and then are populated with
    all of the data streams and variables in that project.

    If you specify 'device' for source_type, the cloud_id should be
    a slug for the device that you want to fetch streams from.

    If you specify 'archive' for the source type, the cloud_id should
    be a slug for the archive that you want to fetch streams from.

    if you specify 'project' for source type, the cloud_id should be
    the UUId of the project that you want to fetch streams from.

    Args:
        cloud_id (str): An IOTile.cloud id (usually a slug) that
            selects that data streams are included in this analysis
            project.
        source_type (str): The type of iotile.cloud object that we
            are linking this AnalysisProject to.  This defaults to
            an iotile.cloud project, but finding only streams from a
            single device is also supported.  You can currently
            specify 'project' ,'device' or 'archive'.
        domain (str): Optional iotile.cloud domain to connect to (defaults to
            https://iotile.cloud).
    """

    def __init__(self, cloud_id, source_type='project', domain=DOMAIN_NAME):
        stream_finders = {
            'project': self._find_project_streams,
            'device': self._find_device_streams,
            'archive': self._find_archive_streams
        }

        stream_finder = stream_finders.get(source_type, None)
        if stream_finder is None:
            raise ArgumentError("Invalid source type", source_type=source_type, supported_sources=stream_finders.keys(), suggestion="Try using one of the convenience functions for creating an AnalysisGroup like FromDevice or FromProject")

        session = CloudSession(domain=domain)
        self._session = session
        self._api = session.get_api()

        stream_list = stream_finder(cloud_id)
        self.streams = self._parse_stream_list(stream_list)
        self.stream_counts = self._count_streams([x['slug'] for x in stream_list])

        self._stream_table = [(slug.lower(), self._get_stream_name(stream).lower()) for slug, stream in viewitems(self.streams)]

    def _count_streams(self, slugs):
        resources = [self._api.stream(x).data for x in slugs]
        ts_results = self._session.fetch_multiple(resources, message='Counting Events in Streams', page_size=1)

        event_resources = [self._api.event for x in slugs]
        event_args = [{"filter": x} for x in slugs]

        event_results = self._session.fetch_multiple(event_resources, event_args, message='Counting Data in Streams', page_size=1)

        return {slug: {'points': ts['count'], 'events': event['count']} for slug, ts, event in zip(slugs, ts_results, event_results)}

    def stream_empty(self, slug):
        """Check if a stream is empty.

        Empty streams have neither event data nor time series data.

        Args:
            slug (str): The slug of the stream tha we want to check to
                see if it empty

        Returns:
            bool: True if the stream is empty, otherwise false.
        """

        counts = self.stream_counts[slug]
        return counts['points'] == 0 and counts['events'] == 0

    def print_streams(self, include_empty=False):
        """Print a table of the streams in this AnalysisGroup.

        By default this function does not print streams that have no data
        but you can override that by passing include_empty=True.

        Args:
            include_empty (bool): Also show streams that have no data.
        """

        print("{:40s} {:s}".format("Name", "Slug"))
        print("{:40s} {:s}".format("----", "----"))

        for slug, stream in self.streams.items():
            if self.stream_empty(slug) and not include_empty:
                continue

            name = self._get_stream_name(stream)

            if len(name) > 37:
                name = name[:37] + '...'

            print('{:40s} {:s}'.format(name, slug))

    @classmethod
    def _get_stream_name(cls, stream):
        name = stream.get('data_label', '')

        if name == '':
            name = stream.get('var_name') + "(from variable)"

        if name == '':
            name = "Unnamed"

        return name

    def find_stream(self, partial, include_empty=False):
        """Find a stream by a partial identifier.

        The identifier can either be a part of its slug or its name or the
        name of the variable that it comes from.  Whatever you pass must
        uniquely match exactly one stream in this analysis project or an
        exception will be thrown.

        Matching is done in a case insensitive fashion.

        By default, only streams that are not empty are searched.  You can
        override this by passing include_empty=True.  This behavior is the
        same as the print_streams() behavior, so searching for a stream based
        on what you find in print streams will work as expected.

        Args:
            partial (str): A partial slug or identifier to use to uniquely
                find one stream.
            include_empty (bool): Also include streams that have no data in
                the search.

        Returns:
            str: The full slug of the stream that we were looking for, suitable
                for passing to an IOTile.cloud api.

        Raises:
            ArgumentError: If the partial matches no streams or if it matches
                multiple streams.
        """

        if isinstance(partial, int):
            partial = "{:x}".format(partial)

        if not isinstance(partial, str):
            partial = str(partial)

        partial = partial.lower()

        found = [slug for slug, stream in self._stream_table if (partial in slug or partial in stream) and (include_empty or not self.stream_empty(slug))]
        if len(found) == 0:
            raise ArgumentError("No stream found matching given partial identifier", partial=partial)
        elif len(found) > 1:
            raise ArgumentError("Multiple matching streams found", partial=partial, slugs=found)

        return found[0]

    def fetch_stream(self, slug_or_name):
        """Fetch data from a stream by its slug or name.

        For example say you have the following stream in this analysis project:
        s--0000-0011--0000-0000-0000-0222--5001 (Temperature)

        You could fetch it by passing any of:
         - temp
         - 5001
         - Temperature
         - s--0000-0011--0000-0000-0000-0222--5001

        Args:
            slug_or_name (str): The stream that we want to fetch.  This
                can be a partial match to a full stream slug or name so long
                as it uniquely matches.  This is passed to find_stream so anything
                that find_stream accepts will be accepted here.
        """

        slug = self.find_stream(slug_or_name)
        data = self._get_stream_data(slug)

        dt_index = pd.to_datetime([x['timestamp'] for x in data])
        return pd.Series([x['output_value'] for x in data], index=dt_index)

    def fetch_events(self, slug_or_name):
        """Fetch event metadata from a stream by its slug or name.

        This function will return a Pandas DataFrame with all of the
        events in the stream.  It will return only the extra summary
        data stored with the event itself however.  If you need access to
        any raw data uploaded with the event that was not part of the
        summary, you need to use fetch_event for each event to get
        the raw data.

        slug_or_name is passed to find_stream to convert it into a slug so
        partial stream names are accepted.

        Args:
            slug_or_name (str): The stream that we want to fetch.  This
                can be a partial match to a full stream slug or name so long
                as it uniquely matches.  This is passed to find_stream so anything
                that find_stream accepts will be accepted here.

        Returns:
            DataFrame: All of the extra_data associated with the event as a
                Pandas DataFrame.
        """

        slug = self.find_stream(slug_or_name)

        try:
            data = self._get_event_data(slug)

            dt_index = pd.to_datetime([x['timestamp'] for x in data])
            extra_data = [x['extra_data'] for x in data]

            for i, event in enumerate(data):
                extra_data[i]['event_id'] = event['id']

            return pd.DataFrame(extra_data, index=dt_index)
        except RestHttpBaseException as exc:
            raise CloudError("Error fetching events from stream", exception=exc, response=exc.response.status_code)

    def fetch_raw_events(self, slug_or_name, subkey=None, postprocess=None):
        """Fetch multiple raw events by numeric id.

        Args:
            slug_or_name (str): The stream that we want to fetch.  This
                can be a partial match to a full stream slug or name so long
                as it uniquely matches.  This is passed to find_stream so anything
                that find_stream accepts will be accepted here.
            subkey (str): Only include a single key of the event.  This is usefuly for complex
                events where you want to just focus on a portion of them.
            postprocess (callable): (Optional) function to call on each raw event before
                adding it to the dataframe.

        Returns:
            pd.DataFrame: The raw event object data fetched from iotile.cloud.
        """

        events = self.fetch_events(slug_or_name)
        event_ids = events['event_id'].values

        resources = [self._api.event(x).data for x in event_ids]
        data = self._session.fetch_multiple(resources)

        if postprocess is None:
            postprocess = lambda x: x

        if subkey is not None:
            data = [postprocess(x[subkey]) for x in data]
        else:
            data = [postprocess(x) for x in data]

        return pd.DataFrame(data, index=events.index)

    def fetch_raw_event(self, event_or_id, subkey=None):
        """Fetch associated raw data for an event.

        Args:
            event_or_id (pd.Series or int): Either an event returned as a member of the response
                of fetch_events with the event_id key set or an id for an event as an integer.
            subkey (str): Only include a single key of the event.  This is usefuly for complex
                events where you want to just focus on a portion of them.

        Returns:
            pd.DataFrame: The raw event object data fetched from iotile.cloud.
        """

        event = self._session.fetch_raw_event(event_or_id)

        if subkey is not None:
            if subkey not in event:
                raise ArgumentError("Desired key was not found in event", subkey=subkey, keys=event.keys())

            event = event[subkey]

        return pd.DataFrame.from_dict(event)

    def _find_project_streams(self, project_id):
        """Find all streams in a project by its uuid."""

        try:
            results = self._api.stream.get(project=project_id)
            return results['results']
        except RestHttpBaseException as exc:
            raise CloudError("Error calling method on iotile.cloud", exception=exc, response=exc.response.status_code)

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

    @classmethod
    def _parse_stream_list(cls, stream_list):
        return {stream['slug']: stream for stream in stream_list}

    def _get_stream_data(self, slug, start=None, end=None):
        resource = self._api.stream(slug).data
        return self._session.fetch_all(resource, page_size=1000, message="Downloading Stream Data")

    def _get_event_data(self, slug):
        resource = self._api.event
        return self._session.fetch_all(resource, page_size=1000, message="Downloading Events", filter=slug)

    @classmethod
    def FromDevice(cls, slug=None, external_id=None, domain=DOMAIN_NAME):
        """Create a new AnalysisGroup from a single device.

        The device can be found either by passing its slug or numeric
        id directly or by passing a device specific external_id.

        External ids are typically used to link a virtual IOTile device
        with a separate physical object.  If you have a POD or Arch Node
        then you don't need to worry about external ids.

        **You must pass either a slug or an external_id but not both.**

        Args:
            slug (str): the slug of the device that we want.  This can either
                 be a short slug with leading zeros omitted or long slug. It
                 should start with 'd--' since it is a device slug.
            external_id (str): The external id of the device that we want to
                search for. This external_id must be unique among all devices
                so that it matches a single device.
            domain (str): Optional iotile.cloud domain to connect to (defaults to
                https://iotile.cloud).
        """

        session = CloudSession(domain=domain)
        device = session.find_device(slug=slug, external_id=external_id)

        return AnalysisGroup(device['slug'], source_type="device", domain=domain)

    @classmethod
    def FromArchive(cls, slug=None, domain=DOMAIN_NAME):
        """Create a new AnalysisGroup from a single archive.

        The archive is found by passing its archive slug:
        b--XXXX-XXXX-XXXX-XXXX

        Args:
            slug (str): the slug of the archive that we want.  This can either
                 be a short slug with leading zeros omitted or long slug. It
                 should start with 'b--' since it is an archive slug.
            domain (str): Optional iotile.cloud domain to connect to (defaults to
                https://iotile.cloud).
        """

        return AnalysisGroup(slug, source_type="archive")
