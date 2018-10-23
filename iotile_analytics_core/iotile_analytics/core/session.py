"""Simple session management system to save an iotile.cloud token."""
from __future__ import absolute_import, division, print_function, unicode_literals

from builtins import range

import getpass
import math
import json
import ssl
import sys
import logging
from threading import Lock
from multiprocessing.pool import ThreadPool
from future.utils import iteritems

# For some reason using the future input = raw_input patch in builtins
# does not work on jupyter so fall back to this manual patch.
try:
    input = raw_input
except NameError:
    pass

try:
    #python2
    from urllib2 import urlopen, Request
    from urllib import urlencode
    import urllib3
except ImportError:
    #python3
    from urllib.request import urlopen, Request
    from urllib.parse import urlencode
    import urllib3

from typedargs.exceptions import ArgumentError
from iotile_cloud.api.connection import Api, DOMAIN_NAME
from iotile_cloud.api.exceptions import HttpNotFoundError, HttpClientError, RestHttpBaseException, HttpCouldNotVerifyServerError
from .exceptions import CloudError, AuthenticationError, CertificateVerificationError
from .interaction import ProgressBar
from .utilities.url_routines import get_url, pack_url, post_url


class CloudSession(object):
    """A persistent session to IOTile.cloud.

    CloudSession internally caches results and information from iotile.cloud
    so that you don't have to login multiple times per script invocation.

    All caching is performed on a per domain basis so you can have multiple sessions
    going to different IOTile.cloud instances if needed.  If you login to the same
    domain mulitple times with different users, the cache for that domain will be
    cleared with each login.

    You can create a CloudSession instance with no arguments and it will use stored credentials
    from the last time you logged into that cloud server.  So you can do:

    CloudSession(user="Username", password="Password")

    and then later just call:
    CloudSession()

    The SSL certificate verification option is also saved with each successful login

    Args:
        user (str): The user name to login with
        password (str): The user's password
        domain (str): The complete domain name of the iotile.cloud instance to login to.
            This defaults to https://iotile.cloud
        verify (bool): If set to false, do not verify the SSL certificate of the remote
            iotile.cloud server.  This option is **NOT RECOMMENDED** but sometimes required
            if you are behind a corporate firewall that terminates SSL connections at the
            firewall and uses a self-signed certificate.  Setting this option allows your
            connection to iotile.cloud to be intercepted by third parties in a Man in the
            Middle Attack.  Obviously, the default option is True.  If you don't pass any option here
            the default is use the same verification options that were used in the last successful
            login to the domain that you are talking to.
        token (str): An optional, manually entered IOTile token.
            If valid, bypasses the user+password login, then proceeds as usual
    """

    MAX_CONCURRENCY = 10
    _login_cache = {}
    pool = None

    #pytest: disable=R0913; These arguments are all necessary and appropriate, with sane defaults
    def __init__(self, user=None, password=None, domain=DOMAIN_NAME, verify=None, token=None):
        self.logger = logging.getLogger(__name__)
        if CloudSession.pool is None:
            self.logger.debug("Creating thread pool with %d threads", CloudSession.MAX_CONCURRENCY)
            CloudSession.pool = ThreadPool(CloudSession.MAX_CONCURRENCY)
            self.logger.debug("Finished creating thread pool.")

        if domain not in CloudSession._login_cache:
            CloudSession._login_cache[domain] = {'requests': {}, 'request_lock': Lock()}

        # If we are logging in with a different user than before, clear out the old cache data.
        cache = CloudSession._login_cache[domain]
        with cache['request_lock']:
            old_user = cache.get('user')
            if user is not None and old_user is not None and old_user != user:
                CloudSession._login_cache[domain] = {'requests': {}, 'request_lock': Lock()}

        self.domain = domain
        self.enable_cache = True

        if verify is not None:
            self.verify = verify
        else:
            self.verify = cache.get('verify', True)

        if self.verify is False:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        if token is not None:
            self.token = token
            self.token_type = "jwt"
        else:
            self.token = cache.get('token', None)
            self.token_type = cache.get('token_type', None)

        self._api = Api(domain=domain, verify=self.verify)
        self._api.set_token(self.token, self.token_type)

        if token is not None:
            if self._check_token():
                with cache['request_lock']:
                    cache['token'] = self.token
                    cache['token_type'] = self.token_type
                    cache['verify'] = self.verify
            else:
                raise AuthenticationError("Could not login to IOTile.cloud", token=token, domain=domain)

        # Explictly log in if we're passed all of the right information
        # or our current token is invalid
        if self.token is not None and self.token_type is not None and user is None and password is None:
            return

        if password is None and self._check_token():
            return

        if user is None:
            # Both python 2 and 3 require native strings to be passed into getpass
            prompt_str = "Please enter your IOTile.cloud email: "
            if sys.version_info.major < 3:
                prompt_str = prompt_str.encode('utf-8')

            user = input(prompt_str)

        if password is None:
            # Both python 2 and 3 require native strings to be passed into getpass
            prompt_str = "Please enter your IOTile.cloud password: "
            if sys.version_info.major < 3:
                prompt_str = prompt_str.encode('utf-8')
            password = getpass.getpass(prompt_str)

        try:
            res = self._api.login(email=user, password=password)
        except RestHttpBaseException as err:
            self._translate_error(err, "Error logging into iotile.cloud", email=user)

        if not res:
            raise AuthenticationError("Could not login to IOTile.cloud", user=user, domain=domain)

        self.token = self._api.token
        self.token_type = self._api.token_type

        with cache['request_lock']:
            cache['user'] = user
            cache['token'] = self.token
            cache['token_type'] = self.token_type
            cache['verify'] = self.verify

    def _check_token(self):
        """Verify that we're able to log in to IOTile.cloud with our token."""

        if self.token is None:
            return False

        try:
            _info = self._api.account.get()

            return True
        except HttpClientError:
            return False

    def fetch_multiple(self, resources, per_call_kw=None, postprocess=None, message=None, **kwargs):
        """Fetch multiple resources in parallel.

        Up to concurrency max calls are in flight at a given time.  The results
        are returned in the same order as resources is passed.

        Args:
            resources (RestResource[]): Should be created from an Api object.
            per_call_kw (dict[]): An optional set of keyword arguments that should be individual
                for each fetch call.  For example, you could pass a custom filter argument for
                each call.
            message (str): Optional descriptive message that is printed with the progress bar
            **kwargs (str): Additional keyword arguments that are passed as part of
                the query string in the get request.

        Returns:
            dict[]: A list of the results for each resource.
        """

        if per_call_kw is None:
            per_call_kw = [{} for x in range(0, len(resources))]

        if len(per_call_kw) != len(resources):
            raise ArgumentError("You must pass the same number of per_call keyword arguments as resources (or none at all)", fetch_length=len(resources), kw_length=len(per_call_kw))

        try:
            with ProgressBar(total=len(resources), message=message, leave=False) as progbar:
                args = [(x, _merge_dicts(per_call_kw[i], kwargs), progbar, postprocess, i) for i, x in enumerate(resources)]
                wrapped_results = self.pool.map(self._resource_fetcher, args)

                failed = [err for result, err in wrapped_results if err is not None]
                if len(failed) > 0:
                    raise failed[0]

                return [result for result, _err in wrapped_results]
        except RestHttpBaseException as err:
            raise self._translate_error(err, msg="Error fetching resources in parallel from IOTile.cloud")

    def post_multiple(self, urls, datas, headers=None, message=None, include_auth=True):
        """Make multiple parallel posts to urls with the contents as given by datas.

        Requests will be mapped to the underlying thread pool and made in
        batches according to the pool size.  If you need to attach headers to
        the requests, you can pass a dictionary in headers, which will be
        copied and used for all requests, or you can pass a list of dicts that
        will be used one per url in urls.

        The specific encoding behavior of this function depends on what kind of object
        you pass in for each member of datas.  The following table lays out what happens
        in each case:

        - dict: The dictionary is dumped to a string using json.dumps and that string is
            encoded into bytes via the utf-8 encoding.  A content-type: application/json
            header is added.
        - str (on python 3), unicode (on python 2): The string is encoded into a bytes
            object using utf-8.  No content-type headers are added.
        - bytes (on python 3), str or bytes (on python 2): Nothing is done and the data
            is sent exactly as passed.

        This encoding happens on a per-item basis for datas so you can mix and match
        the three types to different urls in urls.

        Args:
            urls (list of str): A list of the urls that should be called including any
                query strings that they might have.  These will be passed unmodified
                to urlopen().
            datas (list of str, dict or bytes): A list of the actual payloads that should be
                included in each url post.  If this is a dict then it is encoded as a json
                string in utf-8 and the appropriate content-type header is added to each
                request.  If it is a string, it is encoded as utf-8 bytes and no header is
                added.
            headers (dict or list of dicts): Either a single dict of headers that will
                be included in every call or a list of dicts that will be used individually
                for each call.
            include_auth (bool): Whether to include an Authorization token in the headers
                for every request.
            message (str): A user-facing message that will be shown in the ProgressBar
                indicating progress for this operation.

        Returns:
            list of bytes: A list of the actual responses to each post.
        """

        if headers is None:
            headers = {}

        if isinstance(headers, dict):
            headers = [headers.copy()]*len(urls)
        elif isinstance(headers, list) and len(headers) != len(urls):
            raise ArgumentError("Number of passed headers does not agree with number of urls",
                                url_count=len(urls), header_count=len(headers))

        if len(datas) != len(urls):
            raise ArgumentError("Number of passed payloads does not agree with number of urls",
                                url_count=len(urls), payload_count=len(datas))

        for i, (in_data, in_headers) in enumerate(zip(datas, headers)):
            if isinstance(in_data, dict):
                json_data = json.dumps(in_data).encode('utf-8')
                datas[i] = json_data
                in_headers[b'Content-type'] = b"application/json"
            elif not isinstance(in_data, bytes):
                datas[i] = in_data.encode('utf-8')

            if include_auth:
                in_headers[b'Authorization'] = '{} {}'.format(self.token_type, self.token).encode('utf-8')

        with ProgressBar(total=len(urls), leave=False, message=message) as progbar:
            args = zip(urls, datas, headers, [progbar]*len(urls))
            wrapped_results = self.pool.map(self._generic_url_poster, args)

        failed = [err for _result, err in wrapped_results if err is not None]
        if len(failed) > 0:
            raise failed[0]

        return [x for x, _y in wrapped_results]

    def fetch_all(self, resource, page_size=100, message=None, **kwargs):
        """Fetch and concatenate all pages of a given resource.

        The pages are fetched in parallel using up to concurrency requests
        at a time.

        If one page request fails, the fetch fails.  A single call is made to
        figure out how many results there are and then batched calls are made
        to download the pages in parallel.

        The RestResource is accessed using get with any keyword arguments passed
        to this function.

        **You cannot pass the page keyword argument to this function explicitly since
        that keyword is generated and used internally.**

        Args:
            resource (RestResource): Should be created from an Api object.
            page_size (int): The desired page size to use for fetches.
            message (str): Optional descriptive message that is printed with the progress bar
            **kwargs (str): Additional keyword arguments that are passed as part of
                the query string in the get request.

        Returns:
            dict[]: A list of the results concatenated from all pages.
        """

        try:
            with ProgressBar(total=100, leave=False, message=message) as progbar:
                results = resource.get(page_size=page_size, **kwargs)
                total_count = results['count']
                results = results.get('results', [])

                if total_count <= page_size:
                    progbar.total = 1
                    progbar.update(1)
                    return results

                pages = int(math.ceil(total_count / float(page_size)))
                progbar.total = pages
                progbar.update(1)

                args = [(resource, x+1, page_size, kwargs, progbar) for x in range(1, pages)]

                wrapped_results = self.pool.map(self._url_fetcher, args)

                failed = [err for result, err in wrapped_results if err is not None]
                if len(failed) > 0:
                    raise failed[0]

                for result, _err in wrapped_results:
                    results.extend(result.get('results'))

                return results
        except RestHttpBaseException as err:
            raise self._translate_error(err, msg="Error fetching resource from IOTile.cloud", url=resource.url())

    def _resource_fetcher(self, args):
        resource, kwargs, progress, postprocess, i = args

        try:
            request = pack_url(resource.url(), kwargs, token=self.token, token_type=self.token_type, verify=self.verify)
            result = self._check_cache(request.request_key)

            if result is None:
                result = get_url(request)
                self._cache_result(request.request_key, result)

            if postprocess is not None:
                result = postprocess(i, result)

            progress.update(1)
            return result, None
        except Exception as err:  # pylint:disable=W0703; we do the exception processing in the calling function
            self.logger.exception("Error fetching resource")
            return None, err

    def _generic_url_poster(self, args):
        """Method for posting to an arbitrary URL with data."""

        url, data, headers, progress = args

        try:
            request = pack_url(url, headers=headers, verify=self.verify)
            resp_data = post_url(request, data, progress=progress)
            return resp_data, None
        except Exception as err:  # pylint:disable=W0703; we do the exception processing in the calling function
            self.logger.exception("Error posting to url %s, headers=%s", url, headers)
            return None, err

    def _url_fetcher(self, args):
        """Method for fetching a url page in a worker thread."""

        resource, page, page_size, kwargs, progress = args

        try:
            query = kwargs.copy()
            query['page_size'] = page_size
            query['page'] = page

            request = pack_url(resource.url(), query, token=self.token, token_type=self.token_type, verify=self.verify)
            result = self._check_cache(request.request_key)

            if result is None:
                result = get_url(request)
                self._cache_result(request.request_key, result)

            progress.update(1)
            return result, None
        except Exception as err:  # pylint:disable=W0703; we do the exception processing in the calling function
            return None, err

    def _cache_result(self, query, response):
        if not self.enable_cache:
            return

        cache = self._login_cache[self.domain]

        with cache['request_lock']:
            cache['requests'][query] = response

    def _check_cache(self, key):
        if not self.enable_cache:
            return None

        cache = self._login_cache[self.domain]

        with cache['request_lock']:
            return cache['requests'].get(key, None)

    def get_api(self):
        """Return a logged in API object to IOTile.cloud.

        Returns:
            Api
        """

        return self._api

    @classmethod
    def _translate_error(cls, error, msg="Error interacting with iotile.cloud", **kwargs):
        """Translate a raw rest error into a user friendly cloud error."""

        if isinstance(error, HttpCouldNotVerifyServerError):
            raise CertificateVerificationError(msg, raw_eror=error, **kwargs)

        return CloudError(msg, raw_error=error, **kwargs)

    def find_device(self, slug=None, external_id=None):
        """Find an IOTile device by its slug or external_id.

        The device can be found either by passing its slug or numeric
        id directly or by passing a device specific external_id.

        External ids are typically used to link a virtual IOTile device
        with a separate physical object.  If you have a POD or Arch Node
        then you don't need to worry about external ids.

        **You must pass either a slug or an external_id but not both.**

        Args:
            slug (str): the slug of the device that we want.  This can either
                 be a short slug with leading zeros omitted or long slug. It
                 should start with 'd--' since it is a device slug.
            external_id (str): The external id of the device that we want to
                search for. This external_id must be unique among all devices
                so that it matches a single device.
        """

        if slug is not None and external_id is not None:
            raise ArgumentError("You must pass either a device slug or an external_id but not both", slug=slug, external_id=external_id)

        api = self.get_api()

        if external_id is not None:
            try:
                devices = api.device.get(external_id=external_id)
                results = devices.get('results', [])

                if len(results) < 0:
                    raise ArgumentError("No device matching external_id could be found", external_id=external_id, suggestion="Make sure the external id is correct")
                elif len(results) > 1:
                    slugs = [x['slug'] for x in results]
                    raise ArgumentError("More than one device with given external id found", external_id=external_id, found_devices=slugs)

                return results[0]
            except HttpClientError as err:
                raise self._translate_error(err)

        try:
            return api.device(slug).get()
        except HttpNotFoundError:
            raise ArgumentError("No device with the given slug could be found", slug=slug)
        except HttpClientError as err:
            raise self._translate_error(err, "Error fetching device information", slug=slug)

    def fetch_raw_event(self, event_or_id):
        """Fetch associated raw data for an event.

        Args:
            event_or_id (pd.Series or int): Either an event returned as a member of the response
                of fetch_events with the event_id key set or an id for an event as an integer.

        Returns:
            dict: The raw event object data fetched from iotile.cloud.
        """

        if hasattr(event_or_id, 'event_id'):
            event_id = event_or_id['event_id']
        else:
            event_id = event_or_id

        if not isinstance(event_id, int):
            try:
                event_id = int(event_id)
            except ValueError:
                raise ArgumentError("Invalid event passed to fetch_raw_event that could not be converted to an integer", event=event_or_id, event_id=event_id)

        try:
            api = self.get_api()
            return api.event(event_id).data.get()
        except HttpNotFoundError:
            raise ArgumentError("No event with the given id could be found", event_id=event_id)
        except HttpClientError as err:
            raise self._translate_error(err, "Error fetching event data", event_id=event_id)


def _merge_dicts(dict1, dict2):
    result = dict1.copy()
    result.update(dict2)
    return result
