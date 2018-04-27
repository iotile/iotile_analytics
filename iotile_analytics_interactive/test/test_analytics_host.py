"""Tests to make sure analytics_host works."""

from __future__ import unicode_literals
import json
import os
import zipfile
from iotile_analytics.interactive.scripts.analytics_host import main
from iotile_analytics.core import CloudSession

ARCHIVE_DATA = (
"Source Info\n"
"-----------\n"
"block                          1\n"
"created_by                     tim\n"
"created_on                     2017-10-27T21:23:36Z\n"
"description                    Test archive for analysis purposes\n"
"id                             25\n"
"org                            arch-internal\n"
"pid                            \n"
"sg                             saver-v1-0-0\n"
"slug                           b--0001-0000-0000-04e7\n"
"title                          Archive: Test Saver Device (04e7)\n"
"\nProperties\n"
"----------\n")

DEVICE_DATA = (
"Source Info\n"
"-----------\n"
"active                         True\n"
"claimed_by                     test\n"
"claimed_on                     None\n"
"created_on                     2017-01-11T03:39:14.394521Z\n"
"external_id                    \n"
"gid                            0000-0000-0000-00d2\n"
"id                             210\n"
"label                          Filtration Flow\n"
"lat                            None\n"
"lon                            None\n"
"org                            test_org\n"
"project                        1c07fdd0-3fad-4549-bd56-5af2aca18d5b\n"
"sg                             water-meter-v1-1-0\n"
"slug                           d--0000-0000-0000-00d2\n"
"template                       1d1p2bt101es-v2-0-0\n"
"\nProperties\n"
"----------\n")


def test_info_report_archive_stdout(shipping, capsys):
    """Make sure we can render info to stdout from an archive."""

    domain, _cloud = shipping
    slug = 'b--0001-0000-0000-04e7'

    CloudSession(user='test@arch-iot.com', password='test', domain=domain, verify=False)
    retval = main(['-t', 'basic_info', slug, '-d', domain, '--no-verify', '-c'])
    assert retval == 0

    out, err = capsys.readouterr()

    assert out == ARCHIVE_DATA


def test_info_report_device_stdout(water_meter, capsys):
    """Make sure we can render info to stdout from a device."""

    domain, _cloud = water_meter
    slug = 'd--0000-0000-0000-00d2'

    CloudSession(user='test@arch-iot.com', password='test', domain=domain, verify=False)
    retval = main(['-t', 'basic_info', slug, '-d', domain, '--no-verify', '-c'])
    assert retval == 0

    out, err = capsys.readouterr()

    assert out == DEVICE_DATA


def test_info_report_to_file(water_meter, tmpdir):
    """Make sure we can save basic info to a file."""

    file = str(tmpdir.join('temp_file'))

    domain, _cloud = water_meter
    slug = 'd--0000-0000-0000-00d2'

    CloudSession(user='test@arch-iot.com', password='test', domain=domain, verify=False)
    retval = main(['-t', 'basic_info', slug, '-d', domain, '--no-verify', '-o', file, '-c'])
    assert retval == 0

    with open(file + '.txt', 'r') as infile:
        out = infile.read()

    assert out == DEVICE_DATA

    # Prepare for the next test
    os.remove(file + '.txt')

    # Make sure .txt is properly stripped
    retval = main(['-t', 'basic_info', slug, '-d', domain, '--no-verify', '-o', file + '.txt', '-c'])
    assert retval == 0

    with open(file + '.txt', 'r') as infile:
        out = infile.read()

    assert out == DEVICE_DATA


def test_info_report_to_zip(water_meter, tmpdir):
    """Make sure we can bundle into a zip."""

    file = str(tmpdir.join('temp_file'))

    domain, _cloud = water_meter
    slug = 'd--0000-0000-0000-00d2'

    CloudSession(user='test@arch-iot.com', password='test', domain=domain, verify=False)
    retval = main(['-t', 'basic_info', slug, '-d', domain, '--no-verify', '-o', file, '-b', '-c'])
    assert retval == 0

    zip_obj = zipfile.ZipFile(file + '.zip', 'r')

    # Make sure we saved the file with a relative path and no root dir
    with zip_obj.open('temp_file.txt', 'r') as infile:
        out = infile.read().decode('utf-8')

    # We write different line endings on windows and linux
    assert out.splitlines() == DEVICE_DATA.splitlines()


def test_user_pass_handling(water_meter, capsys):
    """Make sure we can pass username and password on the cmdline."""

    domain, _cloud = water_meter
    slug = 'd--0000-0000-0000-00d2'

    retval = main(['-t', 'basic_info', '-u', 'test@arch-iot.com', '-p', 'test', slug, '-d', domain, '--no-verify', '-c'])
    assert retval == 0

    out, _err = capsys.readouterr()

    assert out == DEVICE_DATA


def test_local_files(water_meter, tmpdir):
    """Make sure we can run a report from a local file."""

    domain, _cloud = water_meter
    slug = 'd--0000-0000-0000-00d2'

    saved_file = str(tmpdir.join('saved_file.hdf5'))
    file = str(tmpdir.join('temp_file.txt'))

    retval = main(['-t', 'save_hdf5', slug, '-d', domain, '--no-verify', '-o', saved_file, '-c'])
    assert retval == 0
    assert os.path.isfile(saved_file)

    retval = main(['-t', 'basic_info', saved_file, '-o', file, '-c'])
    assert retval == 0

    with open(file, 'r') as infile:
        out = infile.read()

    assert out == DEVICE_DATA


def test_stream_overview_desc():
    """Make sure we can print help info for an AnalysisTemplate."""

    retval = main(['-t', 'stream_overview', '-l'])
    assert retval == 0


def test_rendering_report(water_meter, tmpdir):
    """Make sure we can render an html report."""

    domain, _cloud = water_meter
    slug = 'd--0000-0000-0000-00d2'
    stream = 's--0000-0077--0000-0000-0000-00d2--5001'

    retval = main(['-t', 'stream_overview', slug, '-d', domain, '--no-verify', '-o', str(tmpdir.join('report')), '-c', '-a', 'stream=%s' % stream])
    assert retval == 0
