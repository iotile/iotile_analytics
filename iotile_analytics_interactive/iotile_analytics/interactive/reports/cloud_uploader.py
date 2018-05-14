"""Helper class that manages uploading a series of report files to iotile.cloud."""

from __future__ import unicode_literals, print_function, absolute_import
import logging
import os
import json
import string
import random
from iotile_analytics.core import CloudSession
from iotile_analytics.core.exceptions import UsageError, CloudError
from typedargs.exceptions import ArgumentError


class ReportUploader(object):
    """Upload a series of files to S3 using signed URLs.

    Args:
        domain (str): The iotile.cloud instance that we should use. If
            not passed, this defaults to https://iotile.cloud
    """

    def __init__(self, domain=None):
        self._session = CloudSession(domain=domain)
        self._api = self._session._api
        self._logger = logging.getLogger(__name__)

    def upload_report(self, label, files, report_id=None, group=None, slug=None):
        """Upload a report to iotile.cloud to attach to a device or archive.

        The report will be attached to the given AnalysisGroup, or you can
        specify the slug of the object to attach the report to explicitly. You
        must specify EITHER group OR slug and the currently logged in user
        must have permission to upload reports for org that owns the object
        that you are attaching the report to.

        You must give the report a human readable label that will be shown
        in lists where users may select to view the report.

        Args:
            label (str): The human readable label for the report that you
                are uploading.
            report_id (int): The ID of a GeneratedUserReport instance, if one
                was given. Report files will be attached to this existing report.
                If this is not specified, a new report record will be created.
            files (list of str): A list of all of the files that should
                be uploaded for this report including the main entrypoint
                file that should be listed first.
            group (AnalysisGroup): The analysis group that was used to generate
                this report.  If this is not specified then you must explicitly
                specify the slug of the object used to generate the report and
                the slug of the organization that it should be uploaded for.


        Returns:
            str: A URL where the uploaded report can be accessed.
        """

        if report_id == None:
            if group is not None:
                slug = group.source_info.get('slug')

                if slug is None:
                    raise ArgumentError("The group provided did not have source slug information in its source_info",
                                        slug=slug)
            elif slug is None:
                raise UsageError(
                    "If you do not specify an AnalysisGroup you must pass an org and a slug to this function",
                    slug=slug)

            org = self._get_org_slug(slug)
            report_id = self._create_report(label, slug, org)
            self._logger.debug("Created report id: %s", report_id)
        else:
            self._logger.debug("Reusing report id: %s", report_id)

        keys = self._clean_file_paths(files)

        urls, fields = self._get_signed_urls(report_id, keys)
        self._upload_files_to_s3(urls, fields, keys, files)
        self._notify_upload_success(report_id, keys[0])

    def _get_org_slug(self, dev_or_block_slug):
        """Look up the org for a device or block."""

        if dev_or_block_slug.startswith('b--'):
            obj = self._api.datablock(dev_or_block_slug).get()
        elif dev_or_block_slug.startswith('d--'):
            obj = self._api.device(dev_or_block_slug).get()
        else:
            raise UsageError("You can only attach reports to devices or archives, unknown slug type passed", slug=dev_or_block_slug)

        org = obj.get('org', None)
        if org is None:
            raise ArgumentError("Could not obtain org information from passed slug", slug=dev_or_block_slug, retrieved_object=obj)

        return org

    @classmethod
    def _clean_file_paths(cls, files):
        """Return a suitable s3 keys for all files."""

        first = files[0]
        basedir = os.path.dirname(first)
        if basedir is not None:
            keys = [os.path.relpath(x, basedir) for x in files]
        else:
            keys = [x for x in files]

        keys = [x.replace('\\', '/') for x in keys]
        return keys

    def _create_report(self, label, slug, org):
        payload = {
            'org': org,
            'label': label,
            'source_ref': slug
        }

        resp = self._api.report.generated.post(payload)
        self._logger.debug("Create generated report record api response: %s", resp)

        report_id = resp.get('id')
        if report_id is None:
            raise CloudError("No report id returned by cloud", response=resp)

        return report_id

    def _get_signed_urls(self, report_id, files):
        url_infos = [self._get_signature_url_payload(report_id, x, i > 0) for i, x in enumerate(files)]

        urls = [x[0] for x in url_infos]
        payloads = [x[1] for x in url_infos]

        resp_list = self._session.post_multiple(urls, payloads, message="Getting file upload authorization", include_auth=True)
        decoded_resps = [json.loads(resp) for resp in resp_list]
        urls = [x['url'] for x in decoded_resps]
        fields = [x['fields'] for x in decoded_resps]
        return urls, fields

    def _get_signature_url_payload(self, report_id, file_name, public=True):

        payload = {
            'name': file_name,
            'acl': 'public-read' if public is True else 'private',
            'content_type': self._get_mime_type(file_name)
        }

        resource = self._api.report.generated(report_id).uploadurl

        return resource.url(), payload

    @classmethod
    def _get_mime_type(cls, filename):
        _name, ext = os.path.splitext(filename)

        if ext == "":
            return 'application/octet-stream'

        # Remove the .
        ext = ext[1:]

        if ext in ('jsonp', 'js'):
            return "application/javascript"
        elif ext in ('html', 'htm'):
            return "text/html"
        elif ext in ('csv',):
            return "text/csv"
        elif ext in ('json',):
            return "application/json"

        return "application/octet-stream"

    def _upload_files_to_s3(self, urls, fields, keys, files):
        bodies = []
        headers = []
        for key, field, file_path in zip(keys, fields, files):
            with open(file_path, "rb") as infile:
                file_data = infile.read()

            file_info = {
                'filename': key,
                'mimetype': self._get_mime_type(key),
                'content': file_data
            }

            body, header = encode_multipart(field, {'file': file_info})
            bodies.append(body)
            headers.append(header)

        self._session.post_multiple(urls, bodies, headers, message="Uploading report files", include_auth=False)

    def _notify_upload_success(self, report_id, file_path):
        payload = {
            'name': file_path
        }

        resp = self._api.report.generated(report_id).uploadsuccess.post(payload)
        self._logger.info("Successfully uploaded report: id=%s, main_file=%s", report_id, file_path)
        self._logger.info("Upload success signed url: %s", resp.get('url'))

        return resp.get('url')


_BOUNDARY_CHARS = string.digits + string.ascii_letters


def encode_multipart(fields, files, boundary=None):
    """Standalone multipart form encoder.

    Taken from:
    http://code.activestate.com/recipes/578668-encode-multipart-form-data-for-uploading-files-via/

    Licensed under MIT, Written by: Ben Hoyt
    """

    def _escape_quote(indata):
        return indata.replace('"', '\\"')

    if boundary is None:
        boundary = ''.join(random.choice(_BOUNDARY_CHARS) for i in range(30))
    lines = []

    for name, value in fields.items():
        lines.extend((
            '--{0}'.format(boundary),
            'Content-Disposition: form-data; name="{0}"'.format(_escape_quote(name)),
            '',
            str(value),
        ))

    for name, value in files.items():
        filename = value['filename']
        mimetype = value.get('mimetype', 'application/octet-stream')
        lines.extend((
            '--{0}'.format(boundary),
            'Content-Disposition: form-data; name="{0}"; filename="{1}"'.format(_escape_quote(name), _escape_quote(filename)),
            'Content-Type: {0}'.format(mimetype),
            'Content-Transfer-Encoding: binary',
            '',
            value['content'],
        ))

    lines.extend((
        '--{0}--'.format(boundary),
        '',
    ))

    for i, line in enumerate(lines):
        if not isinstance(line, bytes):
            lines[i] = line.encode('utf-8')

    body = b'\r\n'.join(lines)

    headers = {
        b'Content-Type': 'multipart/form-data; boundary={0}'.format(boundary).encode('utf-8')
    }

    return (body, headers)
