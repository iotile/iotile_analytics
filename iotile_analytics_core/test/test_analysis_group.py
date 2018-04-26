"""Make sure the analysis group works."""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import pytest
from typedargs.exceptions import ArgumentError
from iotile_analytics.core import CloudSession, AnalysisGroup
from iotile_analytics.core.stream_series import StreamSeries
from iotile_analytics.core.exceptions import AuthenticationError, CertificateVerificationError, CloudError


def test_session_login(water_meter):
    """Make sure we can login successfully."""

    domain, _cloud = water_meter

    session = CloudSession('test@arch-iot.com', 'test', domain=domain, verify=False)
    assert session.token == "JWT_USER"

    with pytest.raises(AuthenticationError):
        CloudSession('test@arch-iot.com', 'test2', domain=domain, verify=False)

def test_token_login(water_meter):
    """Make sure we can login successfully with a token"""

    domain, _cloud = water_meter

    session = CloudSession(token="JWT_USER", domain=domain, verify=False)

    assert session.token == "JWT_USER"

    with pytest.raises(AuthenticationError):
        CloudSession(token="WRONG_TOKEN", domain=domain, verify=False)

def test_ssl_verification(water_meter):
    """Make sure we default to verifying SSL partners."""

    domain, _cloud = water_meter

    with pytest.raises(CertificateVerificationError):
        CloudSession('test@arch-iot.com', 'test', domain=domain, verify=True)


def test_multiple_login(water_meter):
    """Make sure multiple logins work correctly."""

    domain, _cloud = water_meter

    CloudSession('test@arch-iot.com', 'test', domain=domain, verify=False)

    session = CloudSession(domain=domain)
    assert session.token == 'JWT_USER'


def test_device_analysis(water_meter):
    """Make sure we can create an analysis group from a device.

    Also tests to make sure we properly read in stream time series and event
    data.  We support reading stream data from json API dumps or from CSV
    files.
    """

    domain, _cloud = water_meter
    CloudSession('test@arch-iot.com', 'test', domain=domain, verify=False)

    group = AnalysisGroup.FromDevice('d--0000-0000-0000-00d2', domain=domain)

    assert group.stream_counts['s--0000-0077--0000-0000-0000-00d2--5001']['points'] == 11
    assert group.stream_counts['s--0000-0077--0000-0000-0000-00d2--5002']['points'] == 3


def test_stream_download(filter_group):
    """Make sure we can download streams from an analysis group."""

    data = filter_group.fetch_stream('5001')
    assert len(data) == 11

    assert isinstance(data, StreamSeries)
    assert set(data.available_units) == set(['Liters', 'Gallons', 'Cubic Meters', 'Acre Feet'])

    outL = data.convert('Liters')
    outG = data.convert('Gallons')

    assert data.iloc[0][0] == pytest.approx(outL.iloc[0][0])
    assert data.iloc[0][0] / 3.78541 == pytest.approx(outG.iloc[0][0])
    with pytest.raises(ArgumentError):
        data.convert('Test Unit')


def test_invalid_stream(filter_group):
    """Make sure we raise the right error if we can't find a stream."""

    with pytest.raises(ArgumentError):
        filter_group.fetch_stream('5500')


def test_raw_events(filter_group):
    """Make sure we can download raw events."""

    meta = filter_group.fetch_events('5001')
    assert meta.columns[0] == 'event_id'
    assert meta.columns[1] == 'has_raw_data'
    assert meta.columns[2] == 'meta'

    assert meta.iloc[0]['meta'] == 'hello'
    assert meta.iloc[1]['meta'] == 'goodbye'

    raw = filter_group.fetch_raw_events('5001')

    assert len(raw) == 2
    assert raw.iloc[0]['test'] == 1
    assert raw.iloc[1]['goodbye'] == 15.0


def test_channel_info(filter_group):
    """Make sure we can download raw events."""

    # Test AnalyisGroup API
    device = filter_group.source_info
    assert device['slug'] == 'd--0000-0000-0000-00d2'
    assert device['label'] == 'Filtration Flow'
    assert device['org'] == 'test_org'

    props = filter_group.properties
    assert props['CargoDescription'] == 'SO# 83469'
    assert props['Country'] == 'KOREA'


def test_hidden_streams(filter_group, with_system):
    """Make sure we can successfully download streams with and without system info."""

    nosys_group = filter_group
    withsys_group = with_system

    with pytest.raises(ArgumentError):
        nosys_group.fetch_stream('5c00')

    data = withsys_group.fetch_stream('5c00')
    assert len(data) == 4
