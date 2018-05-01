"""Tests to make sure we can save and load HDF5 groups."""

import pytest
import os
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

    assert loaded.source_info == group.source_info
    assert loaded.properties == group.properties


def test_python2_3_compat():
    """Make sure archives saved on python 2 and 3 load identically."""

    py2_path = os.path.join(os.path.dirname(__file__), 'data', 'archive_py2.hdf5')
    py3_path = os.path.join(os.path.dirname(__file__), 'data', 'archive_py3.hdf5')

    py2_grp = AnalysisGroup.FromSaved(py2_path, format_name='hdf5')
    py3_grp = AnalysisGroup.FromSaved(py3_path, format_name='hdf5')

    slug5020 = 's--0000-0114--0005-0000-0000-0533--5020'

    data1 = py2_grp.fetch_stream(slug5020)
    data2 = py3_grp.fetch_stream(slug5020)

    assert np.allclose(data1.values, data2.values)
    assert np.allclose(data1.index.astype('int64'), data2.index.astype('int64'))

    events1 = py2_grp.fetch_events(slug5020)
    events2 = py3_grp.fetch_events(slug5020)

    assert len(events1) == len(events2)
    assert np.all(events1.values == events2.values)
    assert np.allclose(events1.index.astype('int64'), events2.index.astype('int64'))

    rawevents1 = py2_grp.fetch_raw_events(slug5020)
    rawevents2 = py3_grp.fetch_raw_events(slug5020)

    assert len(rawevents1) == len(rawevents2)
    assert np.all(rawevents1.values == rawevents2.values)
    assert np.allclose(rawevents1.index.astype('int64'), rawevents2.index.astype('int64'))

    assert py2_grp.source_info == py3_grp.source_info
    assert py2_grp.properties == py3_grp.properties
