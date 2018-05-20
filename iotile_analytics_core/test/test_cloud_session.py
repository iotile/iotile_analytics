"""Tests to make sure low level CloudSession functions work as expected."""

import os
import json
import pytest
from iotile_analytics.core import CloudSession


@pytest.fixture(scope='function')
def cloud_session(mock_cloud):
    """A base cloud session for testing low level url operations."""
    domain, cloud = mock_cloud
    base = os.path.dirname(__file__)
    conf = os.path.join(base, 'data', 'test_project_watermeter.json')

    cloud.add_data(os.path.join(base, 'data', 'basic_cloud.json'))
    cloud.add_data(conf)
    cloud.stream_folder = os.path.join(base, 'data', 'watermeter')

    session = CloudSession('test@arch-iot.com', 'test', domain=domain, verify=False)
    return session, domain


def test_url_posting(cloud_session):
    """Make sure the bulk url poster works."""

    session, domain = cloud_session

    url = domain + "/api/v1/auth/login/"

    json_data = {
        'email': "test@arch-iot.com",
        'password': "test"
    }

    str_data = json.dumps(json_data)
    bytes_data = json.dumps(json_data)

    header = {b'content-type': b'application/json'}

    results = session.post_multiple([url, url, url], [json_data, str_data, bytes_data],
                                    [{}, header, header], include_auth=False)

    for result in results:
        data = json.loads(result)
        assert data == {"username": "test@arch-iot.com", "jwt": "JWT_USER"}


def test_post_behavior(cloud_session, httpserver):
    """Make sure we send identical headers/content on python 2/3."""

    url = httpserver.url
    json_data = {
        'email': "test@arch-iot.com",
        'password': "test"
    }

    session, _domain = cloud_session

    str_data = json.dumps(json_data)
    bytes_data = json.dumps(json_data)

    header = {b'Content-type': b'application/json'}

    results = session.post_multiple([url], [json_data],
                                    [{}], include_auth=False)

    req1 = httpserver.requests[0]

