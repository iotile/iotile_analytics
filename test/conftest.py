from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import pytest
import os.path
from pytest_localserver.http import WSGIServer
from mock_cloud import MockIOTileCloud
from iotile_analytics import CloudSession, AnalysisGroup


@pytest.fixture(scope="module")
def mock_cloud():
    """Create a mock IOTile.cloud server."""

    base = os.path.dirname(__file__)
    conf = os.path.join(base, 'data', 'basic_cloud.json')

    cloud = MockIOTileCloud(conf)
    server = WSGIServer(application=cloud)

    server.start()
    domain = server.url
    yield domain, cloud
    server.stop()


@pytest.fixture(scope="module")
def water_meter(mock_cloud):
    """Create a water meter cloud."""

    domain, cloud = mock_cloud
    base = os.path.dirname(__file__)
    conf = os.path.join(base, 'data', 'test_project_watermeter.json')

    cloud.add_data(conf)
    cloud.stream_folder = os.path.join(base, 'data', 'watermeter')

    return domain, cloud


@pytest.fixture(scope="function")
def filter_group(water_meter):
    """An AnalysisGroup from a single water meter device."""

    domain, cloud = water_meter

    CloudSession('test@arch-iot.com', 'test', domain=domain)

    group = AnalysisGroup.FromDevice('d--0000-0000-0000-00d2', domain=domain)
    return group

