"""Simple session management system to save an iotile.cloud token."""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import str, range

# For some reason using the future input = raw_input patch in builtins
# does not work on jupyter so fall back to this manual patch.
try:
    input = raw_input
except NameError:
    pass

import getpass
import math
import json
import ssl

try:
    #python2
    from urllib2 import urlopen, Request
    from urllib import urlencode
    import requests.packages.urllib3 as urllib3
except ImportError:
    #python3
    from urllib.request import urlopen, Request
    from urllib.parse import urlencode
    import requests.packages.urllib3 as urllib3

from threading import Lock
from multiprocessing.pool import ThreadPool
from typedargs.exceptions import ArgumentError
from iotile_cloud.api.connection import Api, DOMAIN_NAME
from iotile_cloud.api.exceptions import HttpNotFoundError, HttpClientError, RestHttpBaseException, HttpCouldNotVerifyServerError
from .exceptions import CloudError, AuthenticationError, CertificateVerificationError
from .interaction import ProgressBar


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
        concurrence (int): The maximum number of simultaneous requests to send to iotile.cloud
            when we are requesting multiple resources at a time.  Default: CloudSession.MAX_CONCURRENCY
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

    #pytest: disable=R0913; These arguments are all necessary and appropriate, with sane defaults
    def __init__(self, user=None, password=None, domain=DOMAIN_NAME, concurrency=None, verify=None, token=None):
        if concurrency is None:
            concurrency = CloudSession.MAX_CONCURRENCY

        self.pool = ThreadPool(concurrency)

        if domain not in CloudSession._login_cache:
            CloudSession._login_cache[domain] = {'requests': {}, 'request_lock': Lock()}

        # If we are logging in with a different user than before, clear out the old cache data.
        cache = CloudSession._login_cache[domain]
        with cache['request_lock']:
            old_user = cache.get('user')
            if user is not None and old_user is not None and old_user != user:
                CloudSession._login_cache[domain] = {'requests': {}, 'request_lock': Lock()}

        self.domain = domain

        if verify is not None:
            self.verify = verify
        else:
            self.verify = cache.get('verify', True)

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
            user = input("Please enter your IOTile.cloud email: ".encode('utf-8'))

        if password is None:
            password = getpass.getpass("Please enter your IOTile.cloud password: ".encode('utf-8'))

        if self.verify is False:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

    def fetch_multiple(self, resources, per_call_kw=None, message=None, **kwargs):
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
                args = [(x, _merge_dicts(per_call_kw[i], kwargs), progbar) for i, x in enumerate(resources)]
                wrapped_results = self.pool.map(self._resource_fetcher, args)

                failed = [err for result, err in wrapped_results if err is not None]
                if len(failed) > 0:
                    raise failed[0]

                return [result for result, _err in wrapped_results]
        except RestHttpBaseException as err:
            raise self._translate_error(err, msg="Error fetching resources in parallel from IOTile.cloud")

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
        resource, kwargs, progress = args

        try:
            url = resource.url()
            query_string = urlencode(kwargs)

            cache_key = "%s?%s" % (url, query_string)
            result = self._check_cache(cache_key)

            if result is None:
                headers = {b'Authorization': '{} {}'.format(self.token_type, self.token).encode('utf-8')}
                req = Request(cache_key, headers=headers)

                if self.verify is False:
                    context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
                    context.options |= ssl.OP_NO_SSLv2
                    context.options |= ssl.OP_NO_SSLv3

                    resp = urlopen(req, context=context)
                else:
                    resp = urlopen(req)

                data = resp.read()
                result = json.loads(data.decode('utf-8'))
                self._cache_result(cache_key, result)

            progress.update(1)
            return result, None
        except Exception as err:  # pylint:disable=W0703; we do the exception processing in the calling function
            return None, err

    def _url_fetcher(self, args):
        """Method for fetching a url page in a worker thread."""

        resource, page, page_size, kwargs, progress = args

        try:
            url = resource.url()
            query = kwargs.copy()
            query['page_size'] = page_size
            query['page'] = page
            query_string = urlencode(query)

            cache_key = "%s?%s" % (url, query_string)
            result = self._check_cache(cache_key)

            if result is None:
                headers = {b'Authorization': '{} {}'.format(self.token_type, self.token).encode('utf-8')}
                req = Request(cache_key, headers=headers)

                if self.verify is False:
                    context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
                    context.options |= ssl.OP_NO_SSLv2
                    context.options |= ssl.OP_NO_SSLv3

                    resp = urlopen(req, context=context)
                else:
                    resp = urlopen(req)

                data = resp.read()
                result = json.loads(data.decode('utf-8'))

                self._cache_result(cache_key, result)

            progress.update(1)
            return result, None
        except Exception as err:  # pylint:disable=W0703; we do the exception processing in the calling function
            return None, err

    def _cache_result(self, query, response):
        cache = self._login_cache[self.domain]

        with cache['request_lock']:
            cache['requests'][query] = response

    def _check_cache(self, key):
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
