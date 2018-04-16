"""Local pytest fixtures."""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import os.path
import pytest
from iotile_analytics.core import CloudSession, AnalysisGroup
from iotile_analytics.offline import OfflineDatabase


@pytest.fixture(scope="function")
def water_meter(mock_cloud_private):
    """Create a water meter cloud."""

    domain, cloud = mock_cloud_private
    base = os.path.dirname(__file__)
    conf = os.path.join(base, 'data', 'test_project_watermeter.json')
    cloud.add_data(conf)
    cloud.stream_folder = os.path.join(base, 'data', 'watermeter')

    return domain, cloud


@pytest.fixture(scope="function")
def shipping(mock_cloud_private):
    """Create a water meter cloud."""

    domain, cloud = mock_cloud_private
    base = os.path.dirname(__file__)
    conf = os.path.join(base, 'data', 'mock_archive', 'shipping.json')
    cloud.add_data(conf)
    cloud.stream_folder = os.path.join(base, 'data', 'mock_archive')

    return domain, cloud


@pytest.fixture(scope="function")
def shipping_group(shipping):
    domain, cloud = shipping

    CloudSession('test@arch-iot.com', 'test', domain=domain, verify=False)

    group = AnalysisGroup.FromArchive('b--0001-0000-0000-04e7', domain=domain)
    return group


@pytest.fixture(scope="function")
def group(water_meter):
    """An AnalysisGroup from a single water meter device."""

    domain, cloud = water_meter

    CloudSession('test@arch-iot.com', 'test', domain=domain, verify=False)

    group = AnalysisGroup.FromDevice('d--0000-0000-0000-00d2', domain=domain)
    return group
