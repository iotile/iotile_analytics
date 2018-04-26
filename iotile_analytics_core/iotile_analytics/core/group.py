"""The AnalysisGroup is the main entry point for analyzing data.

It allows you to select data streams from IOTile.cloud and turn them
into Pandas time series for analysis.  You can create an AnalysisGroup
from a Project, a Device or a DataBlock.
"""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
from future.utils import viewitems, viewvalues
from past.builtins import basestring
import pkg_resources
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
        self.source_info = channel.fetch_source_info()
        self.properties = channel.fetch_properties()
        self.streams = self._parse_stream_list(stream_list)
        self.stream_counts = channel.count_streams([x for x in self.streams])

        var_type_slugs = set([x['var_type'] for x in viewvalues(self.streams) if x is not None and x.get('var_type') is not None])

        self.variable_types = channel.fetch_variable_types(var_type_slugs)
        self._stream_table = [(slug.lower(), self.get_stream_name(slug).lower()) for slug in self.streams]

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

        for slug in self.streams:
            if self.stream_empty(slug) and not include_empty:
                continue

            name = self.get_stream_name(slug)

            if len(name) > 37:
                name = name[:37] + '...'

            print('{:40s} {:s}'.format(name, slug))

    def get_stream_name(self, slug):
        """Extract a user-friendly name from a stream.

        Args:
            slug (str): The slug that we wish to get the name of.
        Returns:
            str: The name of the stream
        """

        stream = self.streams.get(slug)
        if stream is None:
            return "System Data %s" % (slug[-4:].upper())

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

        if stream is not None:
            raw.set_stream(stream)

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
        out_streams = {}

        for obj in stream_list:
            if isinstance(obj, basestring):
                out_streams[obj] = None
            else:
                out_streams[obj['slug']] = obj

        return out_streams

    @classmethod
    def FromDevice(cls, slug=None, external_id=None, domain=DOMAIN_NAME, include_system=False):
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
            include_system (bool): Also include hidden system streams when fetching data
                for this device.  System streams are not generally useful so this defaults
                to False.
        """

        session = CloudSession(domain=domain)
        device = session.find_device(slug=slug, external_id=external_id)

        channel = IOTileCloudChannel(device['slug'], domain=domain, include_system=include_system)
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

        channel = IOTileCloudChannel(slug, domain=domain)
        return AnalysisGroup(channel)

    @classmethod
    def FromSaved(cls, identifier, format_name):
        """Load a saved AnalysisGroup.

        You must have previously called save on an AnalysisGroup
        and passed it a known format_name and identifier.  Passing
        that same identifier and format_name will reload that same
        AnalysisGroup without needing online access to IOTile.cloud.

        Args:
            identifier (str): The format specific identifier that we will
                use to name this saved AnalysisGroup.  The meaning of this
                parameter depends on the format but, for example, it could
                be the file name.
            format_name (str): An identifier for the format we wish to use to
                save our data.  You can find the list of available formats
                by calling list_formats().

        Returns:
            AnalysisGroup: The saved AnalysisGroup
        """

        loader = cls._find_load_format(format_name)

        channel = loader(identifier)
        return AnalysisGroup(channel)

    def save(self, identifier, format_name):
        """Save this AnalysisGroup.

        You can then load this analysis group again by calling
        AnalysisGroup.FromSaved(identifier, format)

        with the same identifier and format information.

        Args:
            identifier (str): The format specific identifier that we will
                use to name this saved AnalysisGroup.  The meaning of this
                parameter depends on the format but, for example, it could
                be the file name.
            format_name (str): An identifier for the format we wish to use to
                save our data.  You can find the list of available formats
                by calling list_formats().
        """

        saver_factory = self._find_save_format(format_name)
        with saver_factory(identifier) as saver:
            for slug, stream in viewitems(self.streams):
                data = None
                events = None
                raw_events = None

                if not self.stream_empty(slug):
                    data = self.fetch_stream(slug)
                    events = self.fetch_events(slug)
                    raw_events = self.fetch_raw_events(slug)

                saver.save_stream(slug, stream, data, events, raw_events)

            for slug, vartype in viewitems(self.variable_types):
                saver.save_vartype(slug, vartype)

            saver.save_source_info(self.source_info, self.properties)

    @classmethod
    def _find_save_format(cls, format_name):
        for entry in pkg_resources.iter_entry_points('iotile_analytics.save_format', format_name):
            return entry.load()

        raise ArgumentError("Could not find output format by name", available_formats=cls.list_formats())

    @classmethod
    def _find_load_format(cls, format_name):
        for entry in pkg_resources.iter_entry_points('iotile_analytics.load_format', format_name):
            return entry.load()

        raise ArgumentError("Could not find output format by name", available_formats=cls.list_formats())

    @classmethod
    def list_formats(cls):
        """List the installed formats in which we can save an AnalysisGroup.

        Returns:
            list(str): A list of the names that can be passed to save or FromSaved.
        """

        return [x.name for x in pkg_resources.iter_entry_points('iotile_analytics.save_format')]
