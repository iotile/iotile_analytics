"""Envelope calculation from a series of sampled functions."""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
import numpy as np
from scipy.interpolate import interp1d
from typedargs.exceptions import ArgumentError
from .domain import combine_domains


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
        min_interp = interp1d(centers[nonnan], env_min[nonnan], assume_sorted=True)
        env_min[nan_index] = min_interp(centers[nan_index])

    nan_index = np.isnan(env_max)
    if np.any(nan_index):
        nonnan = np.logical_not(nan_index)
        max_interp = interp1d(centers[nonnan], env_max[nonnan], assume_sorted=True)
        env_max[nan_index] = max_interp(centers[nan_index])


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
