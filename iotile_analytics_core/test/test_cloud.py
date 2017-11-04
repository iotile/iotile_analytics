"""Tests for interacting with IOTile.cloud."""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import os.path
from iotile_cloud.api.connection import Api


def config_path(filename):
    """Create a config path."""

    base = os.path.dirname(__file__)
    return os.path.join(base, 'data', filename)


def test_mock_cloud_login(water_meter):
    """Make sure the mock cloud is working."""

    domain, cloud = water_meter
    api = Api(domain=domain, verify=False)

    res = api.login('test', 'test@arch-iot.com')
    assert res

    res = api.login('test2', 'test@arch-iot.com')
    assert not res

    res = api.login('test', 'test@arch-iot.com1')
    assert not res


def test_data_access(water_meter):
    """Make sure we can load and access data."""

    domain, _cloud = water_meter

    api = Api(domain=domain, verify=False)
    api.login('test', 'test@arch-iot.com')

    data = api.device('d--0000-0000-0000-00d2').get()
    assert data['slug'] == 'd--0000-0000-0000-00d2'

    stream = api.stream('s--0000-0077--0000-0000-0000-00d2--5002').get()
    assert stream['slug'] == 's--0000-0077--0000-0000-0000-00d2--5002'

    proj = api.project('1c07fdd0-3fad-4549-bd56-5af2aca18d5b').get()
    assert proj['slug'] == 'p--0000-0077'

    events = api.event.get(filter="s--0000-0077--0000-0000-0000-00d2--5001")
    res = events['results']
    assert len(res) == 2

    raw1 = api.event(1).data.get()
    assert raw1 == {"test": 1, "hello": 2}

    raw2 = api.event(2).data.get()
    assert raw2 == {"test": 1, "goodbye": 15}

    vartype = api.vartype('water-meter-volume').get()
