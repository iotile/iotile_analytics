"""Determine the domain of a group of data series."""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import pandas as pd
import numpy as np
from typedargs.exceptions import ArgumentError


def combine_domains(*args, **kwargs):
    """Determine the combined domain of a set of series.

    This function will return an interval that either contains
    the union of all domains passed in args, or the intersection,
    depending on whether type is "union" or "intersection".

    For example, if you pass in the following series:

    0, x1
    5, x2

    and

    -10, y1
    2, y2

    then the output with type="union" would be [-10, 5]
    with type="intersection", the output would be [2, 5]
    """

    domains = [find_domain(x) for x in args]

    ag_type = kwargs.get('type', 'union')
    if ag_type not in ('union', 'intersection'):
        raise ArgumentError("Unknown domain combination, must be union or intersection", type=ag_type)

    if ag_type == 'union':
        return (min([x[0] for x in domains]), max([x[1] for x in domains]))

    # We're asked for an intersection, keep a running intersection
    # and if there is not overlap among all of the intervals, throw an exception
    int_start, int_end = domains[0]

    for d_min, d_max in domains[1:]:
        if d_max < int_start or d_min > int_end:
            raise ArgumentError("Not all domains intersect in listed domains", running_intersection=(int_start, int_end), next_domain=(d_min, d_max))

        int_start = max(int_start, d_min)
        int_end = min(int_end, d_max)

    return (int_start, int_end)


def find_domain(input_data):
    """Find the min and max value of the domain of an input series.

    The input can either be a Pandas Series in which case the index
    is used if set, otherwise the first column is used.  If the input
    is a Numpy array, then the first column is used.

    Args:
        input_data (Series or ndarray): The input data that we want to
        find the domain of.

    Returns:
        (min, max): A tuple with the minimum and maximum values of the
            domain of the passed input_data.
    """

    axis = input_data

    if isinstance(input_data, pd.Series):
        if input_data.index is not None:
            axis = input_data.index.values
        else:
            axis = input_data.values

    if not isinstance(axis, np.ndarray):
        raise ArgumentError("Unknown input array in find_domain, expected numpy array", input_data=input_data, extracted_axis=axis)

    if len(axis.shape) == 2:
        axis = axis[:, 0]
    elif len(axis.shape) != 1:
        raise ArgumentError("Attempted to call find_domain on an array with more than 2 dimensions", input_data=input_data, shape=axis.shape)

    dmin = np.min(axis)
    dmax = np.max(axis)

    return (dmin, dmax)
