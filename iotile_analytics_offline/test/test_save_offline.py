"""Tests to make sure offline saving works with archives."""

import os
from iotile_analytics.core import AnalysisGroup, CloudSession
from iotile_analytics.interactive.scripts.analytics_host import main


def test_save_offline(shipping_group, tmpdir):
    """Make sure we can save a shipping group."""

    outfile = str(tmpdir.join("out.hdf5"))
    shipping_group.save(outfile, 'hdf5')

    assert os.path.isfile(outfile)

    ingroup = AnalysisGroup.FromSaved(outfile, 'hdf5')
    assert ingroup.stream_counts == shipping_group.stream_counts


def test_livereport_saving(shipping, shipping_group, tmpdir):
    """Make sure we can save an hdf5 file using analytics-host."""

    outfile = str(tmpdir.join("out.hdf5"))

    domain, _cloud = shipping
    slug = 'b--0001-0000-0000-04e7'

    CloudSession(user='test@arch-iot.com', password='test', domain=domain, verify=False)
    retval = main(['-t', 'save_hdf5', slug, '-d', domain, '-o', outfile, '--no-verify'])
    assert retval == 0

    assert os.path.isfile(outfile)

    ingroup = AnalysisGroup.FromSaved(outfile, 'hdf5')
    assert ingroup.stream_counts == shipping_group.stream_counts
