"""Methods by which AnalysisGroup objects can find and download streams."""


class AnalysisGroupChannel(object):
    """A delegate object that can find and download streams.

    AnalysisGroupChannels must provide ways to locate streams, download time
    series data and event data for them as well as a few other routines.
    AnalysisGroups delegate requests for streams to their internal
    AnalysisGroupChannel so that you can access IOTile data that is either
    stored locally or remotely.
    """

    def list_streams(self):
        """Return a list of all streams.

        This is equivalent to the IOTile.cloud API method
        /api/v1/stream/

        Returns:
            list(dict): A list of dictionaries, one for each
                stream that should be part of this analysis group.
        """

        raise NotImplementedError()

    def count_streams(self, slugs):
        """Count the number of events and data points in a stream.

        Args:
            slugs (list(str)): The slugs of the stream that we should count.

        Returns:
            dict(<slug>: {'points': int, 'events': int}): A dict mapping dicts of 2
                integers with the count of the number of events and the number of
                data points in this stream.
        """

        raise NotImplementedError()

    def fetch_variable_types(self, slugs):
        """Fetch variable type information for a list of variable slugs.

        Args:
            slugs (list(str)): The slugs of the variable types that we should fetch.

        Returns:
            dict(<slug>: dict): A dict mapping variable slugs to variable type definitions
        """

        raise NotImplementedError()

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

        raise NotImplementedError()

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

        raise NotImplementedError()

    def fetch_source_info(self):
        """Fetch the record associated to the channel object (project, device or datablock)

        This is the object dictionary for the project, device or datablock this channel is based on

        Returns:
            dict(<name>: <value>): A dict mapping object attribute names and values.
        """

        raise NotImplementedError()

    def fetch_properties(self):
        """Fetch all properties for a given object (project, device or datablock).

        Returns:
            dict: A dict of property names and values.
        """

        raise NotImplementedError()

    def fetch_datapoints(self, slug, direct=False):
        """Fetch all data points for this stream.

        These are time, value data pairs stored in the stream.

        Args:
            slug (str): The slug of the stream that we should fetch
                raw events for.
            direct (bool): Access the data directly without needing a
                stream object to perform unit conversion.

        Returns:
            StreamSeries: A data fame with internal value as floating
                point data.
        """

        raise NotImplementedError()
