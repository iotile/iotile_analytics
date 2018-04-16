"""A cmdline host for running LiveReports on data from iotile.cloud."""

from __future__ import absolute_import, unicode_literals, print_function
import sys
import os
from future.utils import viewitems
import argparse
import logging
from iotile_cloud.api.connection import DOMAIN_NAME
import pkg_resources
from builtins import str
from iotile_analytics.core import CloudSession, AnalysisGroup, Environment


DESCRIPTION = \
"""Generate a LiveReport from data stored locally or in iotile.cloud.

"""


def build_args():
    """Create a command line parser."""

    parser = argparse.ArgumentParser(description=DESCRIPTION, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-v', '--verbose', action="count", default=0, help="Increase logging level (goes error, warn, info, debug)")
    parser.add_argument('-u', '--user', default=None, type=str, help="Your iotile.cloud user name.")
    parser.add_argument('-n', '--no-verify', action="store_true", help="Do not verify the SSL certificate of iotile.cloud")
    parser.add_argument('-p', '--password', default=None, type=str, help="Your iotile.cloud password.  If not specified it will be prompted when needed.")
    parser.add_argument('-o', '--output', type=str, default=None, help="The output path that you wish to save the report at.")
    parser.add_argument('-t', '--report', type=str, help="The name of the report to generate")
    parser.add_argument('-l', '--list', action="store_true", help="List all known report types without running one")
    parser.add_argument('-b', '--bundle', action="store_true", help="Bundle the rendered output into a zip file")
    parser.add_argument('-d', '--domain', default=DOMAIN_NAME, help="Domain to use for remote queries, defaults to https://iotile.cloud")
    parser.add_argument('analysis_group', default=None, nargs='?', help="The slug or path of the object you want to generate a report on")

    return parser


def find_live_reports():
    """Find all installed live reports."""

    reports = {}

    for entry in pkg_resources.iter_entry_points('iotile_analytics.live_report'):
        name = entry.name
        obj = entry.load()

        if name in reports:
            print("WARNING: LiveReport added twice with the same name %s, replacing older version" % name)

        reports[name] = obj

    return reports


def setup_logging(args):
    """Setup log level and output."""

    should_log = args.verbose > 0
    verbosity = args.verbose

    root = logging.getLogger()

    if should_log:
        formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(levelname).3s %(name)s %(message)s', '%y-%m-%d %H:%M:%S')
        handler = logging.StreamHandler()

        handler.setFormatter(formatter)

        loglevels = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]
        if verbosity >= len(loglevels):
            verbosity = len(loglevels) - 1

        level = loglevels[verbosity]

        root.setLevel(level)
        root.addHandler(handler)
    else:
        root.addHandler(logging.NullHandler())


def list_known_reports():
    """Print a table of all known analysis report types."""

    reports = find_live_reports()

    print("Installed Report Count: %d\n" % len(reports))
    print("Known Reports:")
    for name, obj in viewitems(reports):
        desc = 'No description given.'
        if hasattr(obj, 'DESCRIPTION'):
            desc = obj.DESCRIPTION

        print(" - %s: %s" % (name, desc))

    print("")


def find_analysis_group(args):
    """Find an analysis group by name."""

    Environment.SetupScript()

    group = args.analysis_group
    is_cloud = False

    if group.startswith('d--'):
        is_cloud = True
        generator = lambda x: AnalysisGroup.FromDevice(x, domain=args.domain)
    elif group.startswith('b--'):
        is_cloud = True
        generator = lambda x: AnalysisGroup.FromArchive(x, domain=args.domain)
    elif os.path.exists(group):
        _name, ext = os.path.splitext(group)
        if ext != '.hdf5':
            raise ValueError("Only hdf5 formatted local analysis group files are supported")

        generator = lambda x: AnalysisGroup.FromSaved(x, 'hdf5')

    if is_cloud:
        CloudSession(user=args.user, password=args.password, domain=args.domain, verify=not args.no_verify)

    return generator(group)


def render_report(report_class, group, output_path=None, bundle=False):
    """Render a report to an output path or the console."""

    if hasattr(report_class, 'FromGroup'):
        report_obj = report_class.FromGroup(group)
    else:
        report_obj = report_class(group)

    if not report_obj.standalone and output_path is None:
        raise ValueError("You must specify an output path for this report type.")

    return report_obj.render(output_path, bundle=bundle)


def main(argv=None):
    """Main entry point for analytics-report script."""

    if argv is None:
        if len(sys.argv) == 0:
            argv = []
        else:
            argv = sys.argv[1:]

    parser = build_args()
    args = parser.parse_args(args=argv)

    setup_logging(args)

    if args.list:
        list_known_reports()
        return 0

    reports = find_live_reports()
    report_obj = reports.get(args.report)
    if report_obj is None:
        print("ERROR: could not find report by name: %s\n" % args.report)
        list_known_reports()
        return 1

    try:
        group = find_analysis_group(args)
        rendered_path = render_report(report_obj, group, args.output, bundle=args.bundle)
        if args.output is not None:
            print("Rendered report to: %s" % rendered_path)
    except ValueError as exc:
        print("ERROR: %s" % exc.message)
        raise
        return 1

    return 0
