"""A cmdline host for running LiveReports on data from iotile.cloud."""

from __future__ import absolute_import, unicode_literals, print_function
import sys
import os
from future.utils import viewitems
from builtins import input
import argparse
import logging
import inspect
from typedargs.doc_parser import ParsedDocstring
from typedargs.exceptions import ValidationError, ArgumentError
from typedargs.metadata import AnnotatedMetadata
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
    parser.add_argument('-a', '--arg', action="append", default=[], help="Pass an argument to the livereport you are generating, should be in the form name=value")
    parser.add_argument('-c', '--no-confirm', action="store_true", help="Do not confirm the report that you are about to generate and prompt for parameters")
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

    logger = logging.getLogger()
    reports = find_live_reports()

    print("Installed Report Count: %d\n" % len(reports))
    print("Known Reports:")
    for name, obj in viewitems(reports):
        desc = 'No description given.'

        docstring = inspect.getdoc(obj)
        try:
            if docstring is not None:
                doc = ParsedDocstring(docstring)
                desc = doc.short_desc
        except ValidationError:
            logger.exception("Error parsing docstring for report type %s, class %s", name, obj)
            desc = 'Error parsing docstring for report class.'

        print(" - %s: %s" % (name, desc))

    print("")


def print_report_details(report):
    """Print detailed usage information for a report class."""

    docstring = inspect.getdoc(report)
    try:
        if docstring is not None:
            doc = ParsedDocstring(docstring)
            print(doc.wrap_and_format(include_params=True, include_return=False, excluded_params=['group']))
        else:
            print("Report has no usage information.")
    except ValidationError:
        print("Error parsing docstring for report.")


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

    if not args.no_confirm:
        if is_cloud:
            print("Running report %s against object %s in the cloud" % (args.report, group))
            print("You will need to provide your iotile.cloud login credentials.")
        else:
            print("Running report %s against local file %s" % (args.report, group))

        resp = input(" - Are you sure you wish to continue (y/n)? ")
        if resp.lower() != 'y':
            print("Aborting because the user did not confirm.")
            sys.exit(1)

    if is_cloud:
        CloudSession(user=args.user, password=args.password, domain=args.domain, verify=not args.no_verify)

    return generator(group)


def check_arguments(report, args, confirm=False):
    """Check and optionally explicitly confirm the arguments that will be used."""

    metadata = AnnotatedMetadata(report)
    metadata.load_from_doc = True

    try:
        conv_args = {name: metadata.convert_argument(name, val) for name, val in viewitems(args)}
    except ValidationError as exc:
        print("ERROR: %s" % exc.msg)
        print("Argument: %s" % exc.params['argument'])
        print("Value: %s" % exc.params['arg_value'])

    try:
        if 'domain' in metadata.arg_names:
            args = args.copy()
            args.update({'domain': None})

        metadata.check_spec([None], args)
    except ArgumentError as exc:
        print("ERROR: Missing or excessive argument.")
        print(exc.msg)
        sys.exit(1)
    except ValidationError as exc:
        print("ERROR: %s" % exc.msg)

    if not confirm:
        return

    if len(args) == 0:
        print("Passing no arguments to report generator.")
    else:
        print("Passing the following arguments to report generator:")

    for arg, value in viewitems(conv_args):
        print(" - %s: %s" % (arg, value))

    resp = input(" - Are you sure you wish to continue (y/n)? ")
    if resp.lower() != 'y':
        print("Aborting because the user did not confirm arguments.")
        sys.exit(1)


def split_args(args):
    """Split name=value in a dictionary."""

    split_args = {}

    for comb in args:
        name, _, value = comb.partition('=')
        split_args[name] = value

    return split_args


def render_report(report_class, group, output_path=None, args=None, bundle=False, domain=None):
    """Render a report to an output path or the console."""

    if args is None:
        args = {}


    metadata = AnnotatedMetadata(report_class)
    metadata.load_from_doc = True

    if 'domain' in args:
        raise ValueError("You cannot explicitly pass a domain argument to a report.")

    if 'domain' in metadata.arg_names:
        args['domain'] = domain

    conv_args = {name: metadata.convert_argument(name, val) for name, val in viewitems(args)}

    report_obj = report_class(group, **conv_args)

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

    if args.list and args.report is None:
        list_known_reports()
        return 0

    reports = find_live_reports()
    report_obj = reports.get(args.report)
    if report_obj is None:
        print("ERROR: could not find report by name: %s\n" % args.report)
        list_known_reports()
        return 1

    if args.list:
        print_report_details(report_obj)
        return 0

    try:
        report_args = split_args(args.arg)
        group = find_analysis_group(args)

        check_arguments(report_obj, report_args, confirm=not args.no_confirm)

        rendered_path = render_report(report_obj, group, args.output, args=report_args, bundle=args.bundle, domain=args.domain)
        if args.output is not None:
            print("Rendered report to: %s" % rendered_path)
    except ValueError as exc:
        print("ERROR: %s" % exc.message)
        return 1

    return 0
