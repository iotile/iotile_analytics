"""Test to make sure the envelope function works."""

import pytest
import numpy as np
from iotile_analytics.core.utilities import envelope, envelope_create, envelope_update, envelope_finish


def test_basic_envelope():
    """Make sure envelope works correctly."""

    x_vals = np.linspace(0, 10, 10)

    in1 = np.ndarray([10, 2])
    in1[:, 0] = x_vals
    in1[:5, 1] = 1.0
    in1[5:, 1] = -1.0

    in2 = np.ndarray([10, 2])
    in2[:, 0] = x_vals
    in2[:5, 1] = -1.0
    in2[5:, 1] = 1.0

    out = envelope(in1, in2, bin_count=10)
    assert out.shape[0] == 10
    assert out.shape[1] == 3

    assert out[:, 1] == pytest.approx(-1.0*np.ones_like(out[:, 1]))
    assert out[:, 2] == pytest.approx(np.ones_like(out[:, 1]))

    # Also test the incremental envelope calculation
    state = envelope_create(x_vals[0], x_vals[-1], bin_count=10)
    envelope_update(state, in1)
    envelope_update(state, in2)
    out2 = envelope_finish(state)

    assert out2.shape[0] == 10
    assert out2.shape[1] == 3

    assert out2[:, 1] == pytest.approx(-1.0*np.ones_like(out[:, 1]))
    assert out2[:, 2] == pytest.approx(np.ones_like(out[:, 1]))


def test_envelope_interpolation():
    """Make sure we can fill in gaps in the envelope."""

    x_vals = np.linspace(0, 10, 10)

    in1 = np.ndarray([10, 2])
    in1[:, 0] = x_vals
    in1[:5, 1] = 1.0
    in1[5:, 1] = -1.0

    in2 = np.ndarray([10, 2])
    in2[:, 0] = x_vals
    in2[:5, 1] = -1.0
    in2[5:, 1] = 1.0

    out = envelope(in1, in2, bin_count=100)
    assert out.shape[0] == 100
    assert out.shape[1] == 3

    assert out[:, 1] == pytest.approx(-1.0*np.ones_like(out[:, 1]))
    assert out[:, 2] == pytest.approx(np.ones_like(out[:, 1]))

    # Also test the incremental envelope calculation
    state = envelope_create(x_vals[0], x_vals[-1], bin_count=100)
    envelope_update(state, in1)
    envelope_update(state, in2)
    out2 = envelope_finish(state)

    assert out2.shape[0] == 100
    assert out2.shape[1] == 3

    assert out2[:, 1] == pytest.approx(-1.0*np.ones_like(out[:, 1]))
    assert out2[:, 2] == pytest.approx(np.ones_like(out[:, 1]))


def test_bin_edges():
    """Make sure we return the right bin edges in all 3 supported cases."""

    x_vals = np.linspace(0, 10, 10)

    in1 = np.ndarray([10, 2])
    in1[:, 0] = x_vals
    in1[:5, 1] = 1.0
    in1[5:, 1] = -1.0

    in2 = np.ndarray([10, 2])
    in2[:, 0] = x_vals
    in2[:5, 1] = -1.0
    in2[5:, 1] = 1.0

    out_left = envelope(in1, in2, bin_count=10, bin_mark="left")
    out_right = envelope(in1, in2, bin_count=10, bin_mark="right")
    out_center = envelope(in1, in2, bin_count=10, bin_mark="center")

    bins = bins = np.linspace(0, 10, 11)

    assert out_left[:, 0] == pytest.approx(bins[:-1])
    assert out_right[:, 0] == pytest.approx(bins[1:])
    assert out_center[:, 0] == pytest.approx((bins[1:] + bins[:-1]) / 2.0)

    state = envelope_create(x_vals[0], x_vals[-1], bin_count=10, bin_mark='left')
    envelope_update(state, in1)
    envelope_update(state, in2)
    out2_left = envelope_finish(state)

    state = envelope_create(x_vals[0], x_vals[-1], bin_count=10, bin_mark='center')
    envelope_update(state, in1)
    envelope_update(state, in2)
    out2_center = envelope_finish(state)

    state = envelope_create(x_vals[0], x_vals[-1], bin_count=10, bin_mark='right')
    envelope_update(state, in1)
    envelope_update(state, in2)
    out2_right = envelope_finish(state)

    assert out2_left[:, 0] == pytest.approx(bins[:-1])
    assert out2_right[:, 0] == pytest.approx(bins[1:])
    assert out2_center[:, 0] == pytest.approx((bins[1:] + bins[:-1]) / 2.0)

    # Make sure that data outside of the bins is rejected without error
    state = envelope_create(x_vals[0], x_vals[-1], bin_count=10, bin_mark='left')
    envelope_update(state, in1)
    envelope_update(state, in2)
    envelope_update(state, np.array([[11, 5]]))
    out2_left = envelope_finish(state)
