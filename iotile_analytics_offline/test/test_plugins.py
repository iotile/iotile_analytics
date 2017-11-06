"""Tests to make sure we can save and load HDF5 groups."""

import pytest
import numpy as np
from iotile_analytics.core import AnalysisGroup


def test_plugins():
    """Make sure our save plugin is registered."""

    formats = AnalysisGroup.list_formats()
    assert 'hdf5' in formats

def test_save_and_load(group, tmpdir):
    """Make sure we can save our analysis group."""

    outfile = str(tmpdir.join('out.hdf5'))
    group.save(outfile, format_name='hdf5')

    loaded = AnalysisGroup.FromSaved(outfile, format_name='hdf5')

    slug5001 = 's--0000-0077--0000-0000-0000-00d2--5001'
    slug5002 = 's--0000-0077--0000-0000-0000-00d2--5002'

    data5001 = loaded.fetch_stream(slug5001)
    grp5001 = group.fetch_stream(slug5001)
    data5002 = loaded.fetch_stream(slug5002)
    grp5002 = group.fetch_stream(slug5002)

    assert np.allclose(grp5001.values, data5001.values)
    assert np.allclose(grp5002.values, data5002.values)
    assert np.allclose(grp5001.index.astype('int64'), data5001.index.astype('int64'))
    assert np.allclose(grp5002.index.astype('int64'), data5002.index.astype('int64'))

    events5001 = loaded.fetch_events(slug5001)
    grp5001 = group.fetch_events(slug5001)

    events5002 = loaded.fetch_events(slug5002)
    grp5002 = group.fetch_events(slug5002)

    assert len(events5001) == 2
    assert np.all(events5001.values == grp5001.values)
    assert np.allclose(grp5001.index.astype('int64'), events5001.index.astype('int64'))

    assert len(events5002) == 0
    assert len(grp5002) == 0
