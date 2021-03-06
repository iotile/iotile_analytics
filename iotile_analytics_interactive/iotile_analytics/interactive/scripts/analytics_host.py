"""A cmdline host for running AnalysisTemplates on data from iotile.cloud."""

from __future__ import absolute_import, unicode_literals, print_function
import sys
import os
from builtins import input, str
import argparse
import logging
import inspect
import pkg_resources
from future.utils import viewitems
from iotile_analytics.core.exceptions import UsageError, AuthenticationError
from iotile_analytics.core import CloudSession, AnalysisGroup, Environment
from iotile_analytics.core.channels import ChannelCaching
from iotile_analytics.interactive.reports import ReportUploader
from iotile_analytics.interactive.reports.handlers import StandardOutHandler, ZipHandler, LocalDiskHandler, WebPushHandler, StreamingWebPushHandler
from typedargs.doc_parser import ParsedDocstring
from typedargs.exceptions import ValidationError, ArgumentError
from typedargs.metadata import AnnotatedMetadata
from typedargs.terminal import get_terminal_size
from iotile_cloud.api.connection import DOMAIN_NAME


DESCRIPTION = \
"""Run precreated analysis templates against devices or archives stored locally or in iotile.cloud.

analytics-host is designed to let people quickly run precreated analysis
operatation on their data. An example would be creating a summary report that
shows high level information about all data received from a given device or
inside of a particular archive.

You do not need to have an internet connection to use analytics-host.  While
it can automatically pull your information from iotile.cloud using your login
credentials, it can also run most analyses locally using predownloaded data
that you have on your computer.

The most up-to-date reference information is always available online at:
https://iotile.github.io/iotile_analytics/

Most of the analysis templates included with analytics-host create interactive
html web pages that embed graphs, controls and tables showing the results of
the analysis performed.  These html files are designed to be opened in any
modern web browser and typically do not need an internet connection.

basic usage:

- analytics-host will ask you to confirm everything before you do it unless
  you pass the -c flag indicating that you don't want this behavior.

- you typically need to specify an output path for where the results of your
  analysis should be saved.  You do this using the -o,--output <path> flag.
  Some simple analysis templates can just print their output to the screen
  but most require a file.  Some analysis template generate many files so the
  path you pass here will be interpreted as a directory where all of the files
  should be saved.

- you need to identify the data you are looking for in the cloud by its *slug*
  which is an alphanumeric identifier that starts with d-- for a device or
  b-- for an archive.

  For example, "d--0000-0000-0000-0123" or "b--0001-0000-0000-0100".

- if your analysis generates multiple files you can have analytics-host bundle
  them into a zip file for you by using the `-b` flag.

examples:

To see what types of analysis you have installed run:
$ analytics-host -l

To see help information about a specific AnalysisTemplate, pass it by name
using -t along with -l:
$ analytics-host -l -t basic_info

To see this help information do:
$ analytics-host -h

If you have the package iotile-analytics-offline installed, you can download
all data from a specific device for offline access using:
$ analytics-host -t save_hdf5 <device slug> -o <output_path> -c

advanced usage:

Some analysis templates are configurable and require that you pass them
arguments.  You can see if any arguments are accepted by running:
$ analytics-host -l -t <template name>

If you do need to pass arguments, you must pass them using the `-a, --arg`
option in the form of `name=value` where name is the parameter name
shown in the above command and value is the value you want to pass.

For example, if you had a template named "excited_report" that took a
parameter named title as a string and show_bold as a boolean, you would
invoke it using:
$ analytics-host -t excited_report -a "title=Your Title" -a show_bold=true

Note that you need to use quote around your first argument since it contains a
space.  Quotes around an argument not containing a space are optional.
"""


def build_args():
    """Create a command line parser."""

    parser = argparse.ArgumentParser(description=DESCRIPTION, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-v', '--verbose', action="count", default=0, help="Increase logging level (goes error, warn, info, debug)")
    parser.add_argument('-u', '--user', default=None, type=str, help="Your iotile.cloud user name.")
    parser.add_argument('-n', '--no-verify', action="store_true", help="Do not verify the SSL certificate of iotile.cloud")
    parser.add_argument('-p', '--password', default=None, type=str, help="Your iotile.cloud password.  If not specified it will be prompted when needed.")
    parser.add_argument('-o', '--output', type=str, default=None, help="The output path that you wish to save the report at.")
    parser.add_argument('-t', '--template', type=str, help="The name of the analysis template to run")
    parser.add_argument('-s', '--include-system', action="store_true", help="Also include hidden system streams.  This only affects reports created from device objects, not projects or datablocks/archives")
    parser.add_argument('-a', '--arg', action="append", default=[], help="Pass an argument to the template you are running, should be in the form name=value")
    parser.add_argument('-c', '--no-confirm', action="store_true", help="Do not confirm the analysis that you are about to perforn and prompt for parameters")
    parser.add_argument('-l', '--list', action="store_true", help="List all known analysis types without running one")
    parser.add_argument('-b', '--bundle', action="store_true", help="Bundle the rendered output into a zip file")
    parser.add_argument('-w', '--web-push', action="store_true", help="Push the resulting report to iotile.cloud.")
    parser.add_argument('--unattended', action="store_true", help="Hint that we are running as an unattended script to not print dynamic progress bars")
    parser.add_argument('--web-push-id', type=str, default=None, help="Use this report id when uploading rather than creating a new report record")
    parser.add_argument('--web-push-label', type=str, default=None, help="Set the label used when pushing a report to iotile.cloud (otherwise you are prompted for it)")
    parser.add_argument('--web-push-slug', type=str, default=None, help="Override the source slug given in the analysisgroup and force it to be this")
    parser.add_argument('--token', type=str, default=None, help="Token for authentication to iotile cloud (instead of a password)")
    parser.add_argument('-d', '--domain', default=DOMAIN_NAME, help="Domain to use for remote queries, defaults to https://iotile.cloud")
    parser.add_argument('analysis_group', default=None, nargs='*', help="The slug or path of the object you want to perform analysis on")

    return parser


def find_live_reports():
    """Find all installed live reports."""

    reports = {}

    for entry in pkg_resources.iter_entry_points('iotile_analytics.live_report'):
        name = entry.name
        obj = entry.load()

        if name in reports:
            print("WARNING: AnalysisTemplate added twice with the same name %s, replacing older version" % name)

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

    print("Installed AnalysisTemplate Count: %d\n" % len(reports))
    print("Known Analysis Templates:")
    for name, obj in viewitems(reports):
        desc = 'No description given.'

        docstring = inspect.getdoc(obj)
        try:
            if docstring is not None:
                doc = ParsedDocstring(docstring)
                desc = doc.short_desc
        except ValidationError:
            logger.exception("Error parsing docstring for AnalysisTemplate type %s, class %s", name, obj)
            desc = 'Error parsing docstring for AnalysisTemplate class.'

        print(" - %s: %s" % (name, desc))

    print("")


def print_report_details(report):
    """Print detailed usage information for a report class."""

    docstring = inspect.getdoc(report)
    try:
        if docstring is not None:
            doc = ParsedDocstring(docstring)
            width, _height = get_terminal_size()

            # Workaround terminals that do not support getting their width
            # such as Travis CI's build server
            if width is None or width <= 0:
                width = 80

            print(doc.wrap_and_format(include_params=True, width=width, include_return=False, excluded_params=['group']))
        else:
            print("Report has no usage information.")
    except ValidationError:
        print("Error parsing docstring for report.")

def find_analysis_groups(args):
    """Parse through the list of options for analysis_group and build a list"""
    groups = args.analysis_group

    all_groups = []
    all_logins = True
    for _group in groups:
        logged_in, group = find_analysis_group(args, _group)
        all_groups.append(group)
        all_logins = all_logins and logged_in

    if len(all_groups) == 1:
        return all_logins, all_groups[0]

    return all_logins, all_groups

def find_analysis_group(args, group_in):
    """Find an analysis group by name."""

    group = group_in
    is_cloud = False

    if group.startswith('d--'):
        is_cloud = True
        generator = lambda x: AnalysisGroup.FromDevice(x, domain=args.domain, include_system=args.include_system)
    elif group.startswith('b--'):
        is_cloud = True
        generator = lambda x: AnalysisGroup.FromArchive(x, domain=args.domain)
    elif os.path.exists(group):
        _name, ext = os.path.splitext(group)
        if ext != '.hdf5':
            raise UsageError("Only hdf5 formatted local analysis group files are supported")

        generator = lambda x: AnalysisGroup.FromSaved(x, 'hdf5')
    else:
        raise UsageError("Could not find object specified for report source: %s" % group)

    if not args.no_confirm:
        if is_cloud:
            print("Running report %s against object %s in the cloud" % (args.template, group))
            print("You will need to provide your iotile.cloud login credentials.")
        else:
            print("Running report %s against local file %s" % (args.template, group))

        resp = input(" - Are you sure you wish to continue (y/n)? ")
        if resp.lower() != 'y':
            print("Aborting because the user did not confirm.")
            sys.exit(1)

    if is_cloud:
        CloudSession(user=args.user, password=args.password, token=args.token, domain=args.domain, verify=not args.no_verify)

    group_obj = generator(group)

    try:
        group_obj.set_caching(ChannelCaching.NONE)
    except NotImplementedError:
        pass

    return is_cloud, generator(group)


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


def check_output_settings(report_class, output_path, bundle, web_push):
    """Verify that the combination of output settings is valid."""

    if bundle and web_push:
        raise UsageError("You cannot currently bundle and push a report.")

    if bundle and output_path is None:
        raise UsageError("You must specify an output path using -o for the bundle (-b)")

    if not report_class.standalone and output_path is None and not web_push:
        raise UsageError("The chosen AnalysisTemplate produces more than one file, you must specify an output path using -o if you are not pushing diretly to the cloud")


def build_file_handler(output_path, standalone, bundle, web_push, label, group, slug, domain, report_id=None):
    """Build the appropriate file handler for the AnalysisTemplate's output."""

    if output_path is None and web_push is False:
        return None, StandardOutHandler()

    if bundle:
        if standalone:
            return os.path.basename(output_path), ZipHandler(output_path)

        return None, ZipHandler(output_path, output_path)

    if web_push is False:
        return output_path, LocalDiskHandler()

    # Otherwise we are pushing directly to the web
    print("Uploading report to iotile.cloud server after completion")
    if label is None:
        label = input("Enter a label for the report: ")


    # if there are multiple AnalysisGroup, push to the first one by default
    if isinstance(group, list):
        group = group[0]

    if slug is None and group is not None:
        slug = group.source_info.get('slug')

    if slug is None:
        raise ArgumentError("The group provided did not have source slug information in its source_info", source_info=group.source_info)

    if output_path is None:
        return None, StreamingWebPushHandler(label, slug, domain, report_id=report_id)

    return output_path, WebPushHandler(label, slug, domain, report_id=report_id)


def split_args(args):
    """Split name=value in a dictionary."""

    split_args = {}

    for comb in args:
        name, _, value = comb.partition('=')
        split_args[name] = value

    return split_args


def perform_analysis(report_class, group, output_path=None, handler=None, args=None, domain=None):
    """Save the results of an AnalysisTemplate to an output path or the console."""

    if args is None:
        args = {}

    metadata = AnnotatedMetadata(report_class)
    metadata.load_from_doc = True

    if 'domain' in args:
        raise UsageError("You cannot explicitly pass a domain argument to an AnalysisTemplate.")

    if 'domain' in metadata.arg_names:
        args['domain'] = domain

    conv_args = {name: metadata.convert_argument(name, val) for name, val in viewitems(args)}

    report_obj = report_class(group, **conv_args)
    paths = report_obj.run(output_path, handler)
    if paths is None:
        paths = []

    return paths


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

    if args.unattended:
        print("Configuring unattended mode for status reporting")
        Environment.SetupUnattended()
    else:
        Environment.SetupScript()

    if args.list and args.template is None:
        list_known_reports()
        return 0

    reports = find_live_reports()
    report_obj = reports.get(args.template)
    if report_obj is None:
        print("ERROR: could not find report by name: %s\n" % args.template)
        list_known_reports()
        return 1

    if args.list:
        print_report_details(report_obj)
        return 0

    report_args = split_args(args.arg)
    logged_in, group = find_analysis_groups(args)


    check_arguments(report_obj, report_args, confirm=not args.no_confirm)
    check_output_settings(report_obj, args.output, args.bundle, args.web_push)

    # Make sure we create a cloud session now to capture the user's password
    # if they gave us a username and we haven't already logged in
    if not logged_in and args.user is not None and args.web_push:
        CloudSession(user=args.user, password=args.password, token=args.token, domain=args.domain, verify=not args.no_verify)

    output_path, handler = build_file_handler(args.output, report_obj.standalone, args.bundle, args.web_push,
                                              label=args.web_push_label, group=group, slug=args.web_push_slug,
                                              domain=args.domain, report_id=args.web_push_id)

    handler.start()
    rendered_paths = perform_analysis(report_obj, group, output_path, handler=handler.handle_file, args=report_args, domain=args.domain)
    handler.finish(rendered_paths)

    return 0


def cmdline_main(argv=None):
    """Wrapper around main that catches exceptions and prints them nicely."""

    try:
        retval = main(argv)
    except AuthenticationError:
        print('\nERROR: Could not log in to iotile cloud server using provided username and password.')
        retval = 1
    except UsageError as exc:
        print("\nUSAGE ERROR: %s" % exc.msg)
        for key, val in viewitems(exc.params):
            print("- %s: %s" % (key, str(val)))

        retval = 2

    return retval
