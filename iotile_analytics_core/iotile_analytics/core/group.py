"""The AnalysisGroup is the main entry point for analyzing data.

It allows you to select data streams from IOTile.cloud and turn them
into Pandas time series for analysis.  You can create an AnalysisGroup
from a Project, a Device or a DataBlock.
"""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
from future.utils import viewitems, viewvalues

import pandas as pd
from iotile_cloud.api.connection import DOMAIN_NAME
from iotile_cloud.api.exceptions import RestHttpBaseException
from iotile_cloud.stream.data import StreamData
from typedargs.exceptions import ArgumentError
from .exceptions import CloudError
from .session import CloudSession
from .channels import IOTileCloudChannel


class AnalysisGroup(object):
    """A top level entry point for selecting and analyzing data.

    Currently AnalysisGroups must be created by passing the id
    or slug of a project in iotile.cloud and then are populated with
    all of the data streams and variables in that project.

    You should use one of the static methods FromDevice, FromArchive,
    FromProject or FromFile.

    If you use FromDevice, you should pass a slug for the device that you want
    to fetch streams from.

    If you use FromArchive you should pass a slug for the archive
    that you want to fetch streams from.

    If you use FromProject, you should pass the UUID of the project
    that you want to fetch streams from.

    Args:
        channel (AnalysisGroupChannel): The channel by which we can
            find and download streams.
    """

    def __init__(self, channel):
        self._channel = channel

        stream_list = channel.list_streams()
        self.source_info = channel.fetch_source_info(with_properties=True)
        self.streams = self._parse_stream_list(stream_list)
        self.stream_counts = channel.count_streams([x['slug'] for x in stream_list])

        var_type_slugs = set([x['var_type'] for x in viewvalues(self.streams) if x['var_type'] is not None])

        self.variable_types = channel.fetch_variable_types(var_type_slugs)
        self._stream_table = [(slug.lower(), self._get_stream_name(stream).lower()) for slug, stream in viewitems(self.streams)]

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

    def print_source_info(self):
        """Print a table with source object info

        The source object is the Project, Device or DataBlock this channel was created from

        Args:
            None
        """

        print("{:30s} {:s}".format("Name", "Value"))
        print("{:30s} {:s}".format("----", "----"))
        new_line = '\n' + ' ' * 31
        for key in self.source_info.keys():
            if len(key) > 37:
                key = key[:37] + '...'

            print('{0:30s} {1}'.format(key, str(self.source_info[key]).replace('\n', new_line)))

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

        Returns:
            StreamSeries: A pandas DataFrame subclass containing the data points as columns.
                The index of the dataframe is time in UTC.
        """

        slug = self.find_stream(slug_or_name)
        stream = self.streams[slug]
        raw = self._channel.fetch_datapoints(slug)
        raw.set_stream(self.streams[slug])

        vartype_slug = stream['var_type']

        if vartype_slug is not None:
            vartype = self.variable_types[stream['var_type']]
            raw.set_vartype(vartype)

        return raw

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
        return self._channel.fetch_events(slug)

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

        slug = self.find_stream(slug_or_name)

        raw_events = self._channel.fetch_raw_events(slug)

        if postprocess is None:
            return raw_events

        if subkey is not None:
            data = [postprocess(x[subkey]) for _i, x in raw_events.iterrows()]
        else:
            data = [postprocess(x) for _i, x in raw_events.iterrows()]

        return pd.DataFrame(data, index=raw_events.index)

    @classmethod
    def _parse_stream_list(cls, stream_list):
        return {stream['slug']: stream for stream in stream_list}

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

        channel = IOTileCloudChannel(device['slug'], source_type="device", domain=domain)
        return AnalysisGroup(channel)

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

        channel = IOTileCloudChannel(slug, source_type="datablock", domain=domain)
        return AnalysisGroup(channel)
