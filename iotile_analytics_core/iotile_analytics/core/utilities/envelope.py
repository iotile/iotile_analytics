"""Envelope calculation from a series of sampled functions."""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

from collections import namedtuple
import numpy as np
from typedargs.exceptions import ArgumentError
from .domain import combine_domains


EnvelopeState = namedtuple("EnvelopeState", ['data', 'mark'])


def envelope(*arrays, **kwargs):
    """Return the minimum and maximum envelopes from a series of arrays.

    All passed in arguments should be 2D arrays.  The domain of all of the
    functions is found using combine_domains() and this is then divided into
    a fixed number of buckets using the bin_count keyword parameter (that
    must be passed as a keyword).

    For each bin in the combined domain, the minimum and maximum values in
    all of the passed arrays is then found and the resulting min/max envelopes
    are returned as a (bin_count, 3) array.  The first column is the bins that
    were used.  You can either return the left side, center or right side of
    the bins using the keyword bin_mark = "left" | "right" | "center".

    The default bin_mark is "center".

    Args:
        *arrays (ndarray): A list of numpy arrays that must be 2D and are used
             to compute a min/max envelope.
        bin_count (int): An optional keyword argument that indicates the number of
            bins to divde the domain into for envelope calculation.  Default: 100
        bin_spacing (str): An optional keyword argument of either 'linear' or 'log'
            to indicate whether the bins should be generated using.  Default: linear
        bin_mark (str): How to return the bins that were used to calculate the
            envelope.  Possible options are "left", "right" or "center" causing the
            first column of the output to contain the left edge, right edge or center
            of each bin respectively. Default: "center"
    """

    mark = kwargs.get('bin_mark', 'center')
    if mark not in ('left', 'right', 'center'):
        raise ArgumentError("Invalid bin_mark, must be left, right or center", bin_mark=mark)

    d_min, d_max = combine_domains(*arrays, type="union")

    num_bins = kwargs.get('bin_count', 100)

    bin_spacing = kwargs.get('bin_spacing', 'linear')
    if bin_spacing not in ('linear', 'log'):
        raise ArgumentError("Invalid bin spacing, must be linear or log", bin_spacing=bin_spacing)

    if bin_spacing == 'linear':
        bins = np.linspace(d_min, d_max, num_bins+1)
    else:
        bins = np.geomspace(d_min, d_max, num_bins+1)

    # Make sure there are no roundoff errors so that every element in the
    # envelope domain is contained inside the bins.
    bins[0] = d_min
    bins[-1] = d_max

    env_min = np.zeros_like(bins[1:])
    env_max = np.zeros_like(bins[1:])

    env_min[:] = np.nan
    env_max[:] = np.nan

    for arr in arrays:
        indices = np.digitize(arr[:,0], bins[1:], right=True)

        for arr_i, i in enumerate(indices):
            val = arr[arr_i, 1]

            if np.isnan(env_max[i]) or val > env_max[i]:
                env_max[i] = val
            if np.isnan(env_min[i]) or val < env_min[i]:
                env_min[i] = val

    centers = (bins[1:] + bins[:-1]) / 2.0

    # Fill in empty gaps with interpolation in case there weren't any values
    # in a given bucket.  We default to a simple linear interpolation
    nan_index = np.isnan(env_min)
    if np.any(nan_index):
        nonnan = np.logical_not(nan_index)
        env_min[nan_index] = np.interp(centers[nan_index], centers[nonnan], env_min[nonnan])

    nan_index = np.isnan(env_max)
    if np.any(nan_index):
        nonnan = np.logical_not(nan_index)
        env_max[nan_index] = np.interp(centers[nan_index], centers[nonnan], env_max[nonnan])


    out = np.ndarray([num_bins, 3])
    out[:, 1] = env_min
    out[:, 2] = env_max

    if mark == 'left':
        out[:, 0] = bins[:-1]
    elif mark == 'right':
        out[:, 0] = bins[1:]
    else:
        out[:, 0] = (bins[1:] + bins[:-1]) / 2.0



    return out


def envelope_create(min_x, max_x, bin_count=100, bin_spacing="linear", bin_mark="center"):
    """Create a uniform sampling envelope for a domain.

    This function is used to start an incremental envelope accumulation
    process.  For example, say you have 100 sampled functions and you want to
    calculate the minimum and maximum values in a series of bins along the
    domain.

    Args:
        min_x (float): The minimum x value you are interested in.
        max_x (float): The maximum x value you are interested in.
        bin_count (int): An optional keyword argument that indicates the number of
            bins to divde the domain into for envelope calculation.  Default: 100
        bin_spacing (str): An optional keyword argument of either 'linear' or 'log'
            to indicate whether the bins should be generated using.  Default: linear
        bin_mark (str): How to return the bins that were used to calculate the
            envelope.  Possible options are "left", "right" or "center" causing the
            first column of the output to contain the left edge, right edge or center
            of each bin respectively. Default: "center"

    Returns:
        EnvelopeState: an opaque structure that you can pass to envelope_update or envelope_finish.

        This structure contains all information necessary for incrementally calculating
        the envelope of a set of sampled functions without needing to have all of those
        functions at once.
    """

    if bin_mark not in ('left', 'right', 'center'):
        raise ArgumentError("Invalid bin_mark, must be left, right or center", bin_mark=bin_mark)

    if bin_spacing not in ('linear', 'log'):
        raise ArgumentError("Invalid bin spacing, must be linear or log", bin_spacing=bin_spacing)

    if bin_count <= 0:
        raise ArgumentError("Invalid bin count, must be a positive number", bin_count=bin_count)

    state_array = np.zeros([bin_count + 1, 3])
    if bin_spacing == 'linear':
        state_array[:, 0] = np.linspace(min_x, max_x, bin_count + 1)
    else:
        state_array[:, 0] = np.geomspace(min_x, max_x, bin_count + 1)

    # Make sure there are no roundoff errors so that every element in the
    # envelope domain is contained inside the bins.
    state_array[0, 0] = min_x
    state_array[-1, 0] = max_x

    state_array[:, 1] = np.nan
    state_array[:, 2] = np.nan

    return EnvelopeState(state_array, bin_mark)


def envelope_update(state, array):
    """Update an envelope with a new array.

    This function will update every bin in the envelope currently pointed to
    by state with what was already there or the value in array.

    This function must be called with `state` being the return value from a
    previous call to envelope_create().

    The `state` parameter is modified in place.

    Args:
        state (EnvelopeState): Opaque envelope state created by a prior call
            to envelope_create().
        array (np.ndarray([N, 2])): An Nx2 array of x, y coordinates that will
            be digitized and used to update the appropriate envelope buckets.
    """

    if not isinstance(state, EnvelopeState):
        raise ArgumentError("You must pass an EnvelopeState object created by a prior call to envelope_create", state=state)

    envelope = state.data
    indices = np.digitize(array[:, 0], envelope[1:, 0], right=True)

    for arr_i, i in enumerate(indices):
        val = array[arr_i, 1]

        if i == len(envelope) - 1:
            continue

        if np.isnan(envelope[i + 1, 2]) or val > envelope[i + 1, 2]:
            envelope[i + 1, 2] = val
        if np.isnan(envelope[i + 1, 1]) or val < envelope[i + 1, 1]:
            envelope[i + 1, 1] = val


def envelope_finish(state):
    """Finish calculating an envelope and return the result.

    Args:
        state (EnvelopeState): Opaque envelope state created by a prior call
            to envelope_create().

    Returns:
        np.ndarray(N, 3): An Nx3 array with bin markers, minimum values and maximum values.

        The choice of bin marker depends on what bin_mark argument was passed
        when envelope_create was called and could be either the left edge of
        the bin, the center of the bin or the right edge.
    """

    if not isinstance(state, EnvelopeState):
        raise ArgumentError("You must pass an EnvelopeState object created by a prior call to envelope_create", state=state)

    envelope = state.data

    centers = (envelope[1:, 0] + envelope[:-1, 0]) / 2.0

    # Fill in empty gaps with interpolation in case there weren't any values
    # in a given bucket.  We default to a simple linear interpolation
    nan_index = np.isnan(envelope[1:, 1])
    if np.any(nan_index):
        nonnan = np.logical_not(nan_index)
        envelope[1:, 1][nan_index] = np.interp(centers[nan_index], centers[nonnan], envelope[1:, 1][nonnan])

    nan_index = np.isnan(envelope[1:, 2])
    if np.any(nan_index):
        nonnan = np.logical_not(nan_index)
        envelope[1:, 2][nan_index] = np.interp(centers[nan_index], centers[nonnan], envelope[1:, 2][nonnan])

    if state.mark == 'left':
        envelope[1:, 0] = envelope[:-1, 0]
    elif state.mark == 'right':
        envelope[1:, 0] = envelope[1:, 0]
    else:
        envelope[1:, 0] = centers

    return envelope[1:, :]
