"""Tests to make sure analytics_host works."""

from __future__ import unicode_literals
import json
import zipfile
from iotile_analytics.interactive.scripts.analytics_host import main
from iotile_analytics.core import CloudSession

ARCHIVE_DATA = (
"Source Properties\n"
"-----------------\n"
"block                          1\n"
"created_by                     tim\n"
"created_on                     2017-10-27T21:23:36Z\n"
"description                    Test archive for analysis purposes\n"
"id                             25\n"
"org                            arch-internal\n"
"pid                            \n"
"sg                             saver-v1-0-0\n"
"slug                           b--0001-0000-0000-04e7\n"
"title                          Archive: Test Saver Device (04e7)\n")

DEVICE_DATA = (
"Source Properties\n"
"-----------------\n"
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
)


def test_info_report_archive_stdout(shipping, capsys):
    """Make sure we can render info to stdout from an archive."""

    domain, _cloud = shipping
    slug = 'b--0001-0000-0000-04e7'

    CloudSession(user='test@arch-iot.com', password='test', domain=domain, verify=False)
    retval = main(['-t', 'basic_info', slug, '-d', domain, '--no-verify'])
    assert retval == 0

    out, err = capsys.readouterr()

    assert out == ARCHIVE_DATA


def test_info_report_device_stdout(water_meter, capsys):
    """Make sure we can render info to stdout from a device."""

    domain, _cloud = water_meter
    slug = 'd--0000-0000-0000-00d2'

    CloudSession(user='test@arch-iot.com', password='test', domain=domain, verify=False)
    retval = main(['-t', 'basic_info', slug, '-d', domain, '--no-verify'])
    assert retval == 0

    out, err = capsys.readouterr()

    assert out == DEVICE_DATA


def test_info_report_to_file(water_meter, tmpdir):
    """Make sure we can save basic info to a file."""

    file = str(tmpdir.join('temp_file'))

    domain, _cloud = water_meter
    slug = 'd--0000-0000-0000-00d2'

    CloudSession(user='test@arch-iot.com', password='test', domain=domain, verify=False)
    retval = main(['-t', 'basic_info', slug, '-d', domain, '--no-verify', '-o', file])
    assert retval == 0

    with open(file + '.txt', 'r') as infile:
        out = infile.read()

    assert out == DEVICE_DATA

    # Make sure .txt is properly stripped
    retval = main(['-t', 'basic_info', slug, '-d', domain, '--no-verify', '-o', file + '.txt'])
    assert retval == 0

    with open(file + '.txt', 'r') as infile:
        out = infile.read()

    assert out == DEVICE_DATA


def test_info_report_to_file(water_meter, tmpdir):
    """Make sure we can bundle into a zip."""

    file = str(tmpdir.join('temp_file'))

    domain, _cloud = water_meter
    slug = 'd--0000-0000-0000-00d2'

    CloudSession(user='test@arch-iot.com', password='test', domain=domain, verify=False)
    retval = main(['-t', 'basic_info', slug, '-d', domain, '--no-verify', '-o', file, '-b'])
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

    retval = main(['-t', 'basic_info', '-u', 'test@arch-iot.com', '-p', 'test', slug, '-d', domain, '--no-verify'])
    assert retval == 0

    out, err = capsys.readouterr()

    assert out == DEVICE_DATA
