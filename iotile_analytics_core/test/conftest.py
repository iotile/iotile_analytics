"""Local pytest fixtures."""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import os.path
import pytest
from iotile_analytics.core import CloudSession, AnalysisGroup


@pytest.fixture(scope="module")
def water_meter(mock_cloud):
    """Create a water meter cloud."""

    domain, cloud = mock_cloud
    base = os.path.dirname(__file__)
    conf = os.path.join(base, 'data', 'test_project_watermeter.json')

    cloud.add_data(os.path.join(base, 'data', 'basic_cloud.json'))
    cloud.add_data(conf)
    cloud.stream_folder = os.path.join(base, 'data', 'watermeter')

    return domain, cloud

@pytest.fixture(scope="function")
def filter_group(water_meter):
    """An AnalysisGroup from a single water meter device."""

    domain, _cloud = water_meter

    CloudSession('test@arch-iot.com', 'test', domain=domain, verify=False)

    group = AnalysisGroup.FromDevice('d--0000-0000-0000-00d2', domain=domain)
    return group

@pytest.fixture(scope="function")
def with_system(water_meter):
    """An AnalysisGroup from a single water meter device."""

    domain, _cloud = water_meter

    CloudSession('test@arch-iot.com', 'test', domain=domain, verify=False)

    group = AnalysisGroup.FromDevice('d--0000-0000-0000-00d2', domain=domain, include_system=True)
    return group
