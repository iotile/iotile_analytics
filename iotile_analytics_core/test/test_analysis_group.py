"""Make sure the analysis group works."""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import pytest
from typedargs.exceptions import ArgumentError
from iotile_analytics.core import CloudSession, AnalysisGroup
from iotile_analytics.core.exceptions import CloudError, AuthenticationError


def test_session_login(water_meter):
    """Make sure we can login successfully."""

    domain, _cloud = water_meter

    session = CloudSession('test@arch-iot.com', 'test', domain=domain)
    assert session.token == "JWT_USER"

    with pytest.raises(AuthenticationError):
        CloudSession('test@arch-iot.com', 'test2', domain=domain)


def test_device_analysis(water_meter):
    """Make sure we can create an analysis group from a device.

    Also tests to make sure we properly read in stream time series and event
    data.  We support reading stream data from json API dumps or from CSV
    files.
    """

    domain, _cloud = water_meter
    CloudSession('test@arch-iot.com', 'test', domain=domain)

    group = AnalysisGroup.FromDevice('d--0000-0000-0000-00d2', domain=domain)

    assert group.stream_counts['s--0000-0077--0000-0000-0000-00d2--5001']['points'] == 11
    assert group.stream_counts['s--0000-0077--0000-0000-0000-00d2--5002']['points'] == 3


def test_stream_download(filter_group):
    """Make sure we can download streams from an analysis group."""

    data = filter_group.fetch_stream('5001')
    assert len(data) == 11


def test_invalid_stream(filter_group):
    """Make sure we raise the right error if we can't find a stream."""

    with pytest.raises(ArgumentError):
        filter_group.fetch_stream('5500')
