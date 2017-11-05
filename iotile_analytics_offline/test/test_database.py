"""Make sure we can use our pytables offline database."""

from iotile_analytics.offline import OfflineDatabase


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

    slugs = db.list_streams()
    assert len(slugs) == 2
    assert 's--0000-0077--0000-0000-0000-00d2--5001' in slugs
    assert 's--0000-0077--0000-0000-0000-00d2--5002' in slugs
