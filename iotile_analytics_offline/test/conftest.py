"""Local pytest fixtures."""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import os.path
import pytest
from iotile_analytics.core import CloudSession, AnalysisGroup
from iotile_analytics.offline import OfflineDatabase


@pytest.fixture(scope="module")
def water_meter(mock_cloud):
    """Create a water meter cloud."""

    domain, cloud = mock_cloud
    base = os.path.dirname(__file__)
    conf = os.path.join(base, 'data', 'test_project_watermeter.json')
    cloud.add_data(conf)
    cloud.stream_folder = os.path.join(base, 'data', 'watermeter')

    return domain, cloud


@pytest.fixture(scope="module")
def group(water_meter):
    """An AnalysisGroup from a single water meter device."""

    domain, cloud = water_meter

    CloudSession('test@arch-iot.com', 'test', domain=domain, verify=False)

    group = AnalysisGroup.FromDevice('d--0000-0000-0000-00d2', domain=domain)
    return group

@pytest.fixture(scope="module")
def database(group):
    """A serialized offline database."""

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

    yield db

    db.close()
