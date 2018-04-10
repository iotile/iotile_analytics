"""Make sure we can use our pytables offline database."""

import pytest
import numpy as np
from iotile_analytics.offline import OfflineDatabase
from typedargs.exceptions import ArgumentError


def test_create_database(group):
    """Make sure we can initialize a database."""

    db = OfflineDatabase()

    slug = group.find_stream('5001')
    data = group.fetch_stream(slug)
    definition = group.streams[slug]
    events = group.fetch_events(slug)
    raw_events = group.fetch_raw_events(slug)
    db.save_stream(slug, definition, data, events, raw_events)

    slug = group.find_stream('5002')
    data = group.fetch_stream(slug)
    definition = group.streams[slug]
    events = group.fetch_events(slug)
    raw_events = group.fetch_raw_events(slug)
    db.save_stream(slug, definition, data, events, raw_events)

    streams = db.list_streams()
    slugs = set([x['slug'] for x in streams])

    assert len(slugs) == 2

    assert 's--0000-0077--0000-0000-0000-00d2--5001' in slugs
    assert 's--0000-0077--0000-0000-0000-00d2--5002' in slugs

    db.close()


def test_get_data(group, database):
    """Make sure we can get stream, event and raw event data from a db."""

    slug5001 = 's--0000-0077--0000-0000-0000-00d2--5001'
    slug5002 = 's--0000-0077--0000-0000-0000-00d2--5002'

    meta5001 = database.get_stream_definition(slug5001)
    assert meta5001['slug'] == slug5001

    meta5002 = database.get_stream_definition(slug5002)
    assert meta5002['slug'] == slug5002

    with pytest.raises(ArgumentError):
        database.get_stream_definition('abc')

    data5001 = database.fetch_datapoints(slug5001)
    grp5001 = group.fetch_stream(slug5001)
    data5002 = database.fetch_datapoints(slug5002)
    grp5002 = group.fetch_stream(slug5002)

    with pytest.raises(ArgumentError):
        database.fetch_datapoints('abc')

    assert np.allclose(grp5001.values, data5001.values)
    assert np.allclose(grp5002.values, data5002.values)
    assert np.allclose(grp5001.index.astype('int64'), data5001.index.astype('int64'))
    assert np.allclose(grp5002.index.astype('int64'), data5002.index.astype('int64'))

    events5001 = database.fetch_events(slug5001)
    grp5001 = group.fetch_events(slug5001)

    events5002 = database.fetch_events(slug5002)
    grp5002 = group.fetch_events(slug5002)

    assert len(events5001) == 2
    assert np.all(events5001.values == grp5001.values)
    assert np.allclose(grp5001.index.astype('int64'), events5001.index.astype('int64'))

    assert len(events5002) == 0
    assert len(grp5002) == 0
