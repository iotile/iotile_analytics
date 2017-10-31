"""Tests to make sure domain union/intersection and finding works."""

from iotile_analytics.core.utilities import find_domain, combine_domains
from typedargs.exceptions import ArgumentError
import pandas as pd
import numpy as np
import pytest


def test_find_domain():
    """Make sure we can find domains."""

    arr1 = np.linspace(0, 10, 10)

    arr2 = np.ndarray([10, 2])
    arr2[:, 0] = arr1
    arr2[:, 1] = 1

    arr3 = pd.Series(np.zeros_like(arr1), index=arr1)

    dom1 = find_domain(arr1)
    dom2 = find_domain(arr2)
    dom3 = find_domain(arr3)

    assert dom1 == (0, 10)
    assert dom2 == dom1
    assert dom3 == dom2


def test_combine_domains():
    """Make sure out domain combination works."""

    arr1 = np.linspace(0, 10)
    arr2 = np.linspace(5, 15)
    arr3 = np.linspace(-5, 5)
    arr4 = np.linspace(-10, -5)

    assert combine_domains(arr1, arr2) == (0, 15)
    assert combine_domains(arr1, arr2, type="intersection") == (5, 10)

    with pytest.raises(ArgumentError):
        combine_domains(arr1, arr4, type="intersection")

    assert combine_domains(arr1, arr2, arr3, arr4) == (-10, 15)
