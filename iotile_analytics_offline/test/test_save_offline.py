"""Tests to make sure offline saving works with archives."""

import os
from iotile_analytics.core import AnalysisGroup

def test_save_offline(shipping_group, tmpdir):
    """Make sure we can save a shipping group."""

    outfile = str(tmpdir.join("out.hdf5"))
    shipping_group.save(outfile, 'hdf5')

    assert os.path.isfile(outfile)

    ingroup = AnalysisGroup.FromSaved(outfile, 'hdf5')
    assert ingroup.stream_counts == shipping_group.stream_counts
