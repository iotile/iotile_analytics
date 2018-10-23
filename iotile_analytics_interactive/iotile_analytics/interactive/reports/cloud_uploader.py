"""Helper class that manages uploading a series of report files to iotile.cloud."""

from __future__ import unicode_literals, print_function, absolute_import
import logging
import os
import json
import string
import random
from queue import Queue
from iotile_analytics.core.interaction import ProgressBar
from iotile_analytics.core.utilities.url_routines import pack_url, post_url
from iotile_analytics.core import CloudSession
from iotile_analytics.core.exceptions import UsageError, CloudError
from typedargs.exceptions import ArgumentError


class ReportUploader(object):
    """Upload a series of files to S3 using signed URLs.

    There are two ways to use this class.  You can use the synchronous
    all-in-one upload_report function that takes in a list of files, and
    uploads them in one shot, or you can use the a-la-cart interface.

    The synchronous interface is to just call `upload_report` and pass
    it a list of paths to the files to upload.  It will synchronously
    create a report object on iotile.cloud, upload all files and then
    notify the cloud about our success.

    The a-la-carte interface lets you perform these three steps yourself:

    - create_report(): starts the report upload process, returning a report id.
    - upload_file(): queues a file for background uploading and starts uploading
      it immediately.  This function does not wait for the file upload to finish
      but returns as soon as it has been queued.
    - finish_report(): Waits for all outstanding file uploads to finish and
      then tells iotile.cloud that we have finished uploading the report.


    Args:
        domain (str): The iotile.cloud instance that we should use. If
            not passed, this defaults to https://iotile.cloud
    """

    def __init__(self, domain=None):
        self._session = CloudSession(domain=domain)
        self._api = self._session.get_api()
        self._in_progress = Queue()
        self._logger = logging.getLogger(__name__)
        self._progress = None
        self._managed_progress = False

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

        self._progress = ProgressBar(total=len(files) + 2, message="Uploading report to iotile.cloud")

        try:
            if report_id is None:
                report_id = self.create_report(label, group=group, slug=slug)
            else:
                self._logger.debug("Reusing report id: %s", report_id)
                self._progress.update(1)

            keys = self._clean_file_paths(files)

            for i, (key, path) in enumerate(zip(keys, files)):
                public = i != 0

                with open(path, "rb") as infile:
                    data = infile.read()

                self.upload_file(report_id, key, data, public)

            self.finish_report(report_id, keys[0])
        finally:
            self._progress.close()
            self._progress = None

    def create_report(self, label, group=None, slug=None):
        """Create a report record on iotile.cloud.

        This synchronously notifies that cloud that we are going to be
        uploading a report.  After this function returns you can call
        upload_file repeatedly to upload each file in the report and then
        after you are finished you can call finish_report() to finish the
        report.

        Args:
            label (str): The human readable label for the report that you
                are uploading.
            group (AnalysisGroup): The analysis group that was used to generate
                this report.  If this is not specified then you must explicitly
                specify the slug of the object used to generate the report and
                the slug of the organization that it should be uploaded for.
            slug (str): Optional string to override the slug that would be inferred
                from group.

        Returns:
            str: The report id of the report that was created.
        """

        if self._progress is not None:
            self._progress.set_description("Creating report object")

        if group is not None:
            slug = group.source_info.get('slug')

            if slug is None:
                raise ArgumentError("The group provided did not have source slug information in its source_info",
                                    slug=slug)
        elif slug is None:
            raise UsageError("If you do not specify an AnalysisGroup you must pass an org and a slug to this function",
                             slug=slug)

        org = self._get_org_slug(slug)
        report_id = self._create_report(label, slug, org)
        self._logger.debug("Created report id: %s", report_id)

        if self._progress is not None:
            self._progress.update(1)

        return report_id

    def finish_report(self, report_id, index_path):
        """Notify the cloud that we have successfully finished uploading all files for a report.

        The report should have been created by a previous call to create_report().

        Args:
            report_id (str): The report id returned from the call to create_report()
            index_path (str): The file path passed to a previous call to upload_file()
                that should be treated as the main entry point to this report.
                This path is not cleaned in any way except that \\ characters are
                converted to /.

        Returns:
            str: A URL where the uploaded report can be accessed.
        """

        # Wait for all in_progress files to finish being uploaded
        # call get to rethrow any exceptions.

        if self._progress:
            self._progress.set_description("Waiting for file uploads to finish")

        while not self._in_progress.empty():
            result = self._in_progress.get()
            result.get()

        if self._progress:
            self._progress.set_description("Finalizing report on iotile.cloud")

        key = self._clean_file_path(index_path)
        index_url = self._notify_upload_success(report_id, key)

        if self._progress:
            self._progress.update(1)

        return index_url

    def upload_file(self, report_id, file_path, file_data, public=True):
        """Upload a file asynchronously as part of this report.

        This function will return immediately and queue the file for
        background uploading.  All files are guaranteed to be uploaded
        by the time a call to finish_report() returns.

        Args:
            report_id (str): The report id returned from the call to create_report()
            file_path (str): The key that should be used for this file on s3.
                This path is not cleaned in any way except that \\ characters are
                converted to /.
            file_data (bytes): The data that should be uploaded for this file.
            public (bool): Whether this file should be protected or public.
        """

        result = self._session.pool.apply_async(self._upload_file, (report_id, file_path, file_data, public))
        self._in_progress.put(result)

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

        basedir = os.path.dirname(files[0])
        return [cls._clean_file_path(x, basedir=basedir) for x in files]

    @classmethod
    def _clean_file_path(cls, path, basedir=None):
        """Turn a local file path into an s3 key."""

        if basedir is not None:
            path = os.path.relpath(path, basedir)

        return path.replace('\\', '/')

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

    def _get_signature_url_payload(self, report_id, file_name, public=True):

        payload = {
            'name': file_name,
            'acl': 'public-read' if public is True else 'private',
            'content_type': self._get_mime_type(file_name)
        }

        resource = self._api.report.generated(report_id).uploadurl

        payload_str = json.dumps(payload)
        payload_bytes = payload_str.encode('utf-8')

        return resource.url(), payload_bytes

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

    def _upload_file(self, report_id, file_path, file_data, public):
        """Upload a file to s3.

        This function will ask for a signed s3 url from iotile.cloud and
        then immediately use it to upload a file to s3.  It is designed
        to be called from a background thread using the CloudSession.pool
        thread pool so that many uploads can proceed in parallel.
        """

        key = self._clean_file_path(file_path)
        url, payload = self._get_signature_url_payload(report_id, key, public)

        request = pack_url(url, token=self._api.token, token_type=self._api.token_type, json=True)

        try:
            encoded_resp = post_url(request, payload)
            decoded_resp = json.loads(encoded_resp)
            upload_url = decoded_resp['url']
            upload_fields = decoded_resp['fields']
        except:
            self._logger.exception("Error posting payload URL")
            raise

        file_info = {
            'filename': key,
            'mimetype': self._get_mime_type(key),
            'content': file_data
        }

        self._logger.debug("Uploading file to %s with key %s", upload_url, key)
        body, headers = encode_multipart(upload_fields, {'file': file_info})

        request = pack_url(upload_url, headers=headers)
        post_url(request, body)

        if self._progress is not None:
            self._progress.update(1)

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
