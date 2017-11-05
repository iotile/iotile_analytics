from iotile_analytics.core import AnalysisGroup


def test_plugins():
    """Make sure our save plugin is registered."""

    formats = AnalysisGroup.list_formats()
    assert 'hdf5' in formats

def test_save_and_load(group, tmpdir):
    """Make sure we can save our analysis group."""

    outfile = str(tmpdir.join('out.hdf5'))
    group.save(outfile, format_name='hdf5')

