"""Thread-safe and parallelizable URL fetch and post routines based on urllib."""

from __future__ import absolute_import, division, print_function, unicode_literals

import json
import ssl
import sys
from collections import namedtuple

try:
    #python2
    from urllib2 import urlopen, Request
    from urllib import urlencode
except ImportError:
    #python3
    from urllib.request import urlopen, Request
    from urllib.parse import urlencode

from future.utils import iteritems
from typedargs.exceptions import ArgumentError


RequestInfo = namedtuple("RequestInfo", ['url', 'query_string', 'request_key', 'headers', 'verify'])

#pylint:disable=too-many-arguments;These are all necessary, have sane defaults and will not all need to be specified together.
def pack_url(url, query_args=None, token=None, token_type="jwt", headers=None, verify=True, json=False):
    """Create a RequestInfo object for passing to {get, post}_url.

    This function must be called before calling get_url or post_url.
    It encodes the query string and any required headers for the call.

    Args:
        url (str): The URL that we want to access.
        query_args (dict): A map of string: string for the query arguments that should
            be packed into the query string.
        token (str): Optional iotile.cloud token to include as an authentication header.
            This should be set if you are making an API call on iotile.cloud and not
            set if you are not interacting with iotile.cloud.
        token_type (str): The type of token you have.  This is normally 'jwt' (the default),
            but if you have a permanent machine token you should specify 'a-jwt' instead.
        headers (dict): An optional dict of str->str for any additional headers that should
            be included in this request.
        verify (bool): Whether to verify the SSL certificate of the https request being made.
        json (bool): Whether there are posted contents that are JSON type.  This will add a
            Content-Type header.

    Returns:
        RequestInfo: An encoded object that can be used to make a call to get_url or post_url.
    """

    if query_args is not None:
        query_string = urlencode(query_args)
        request_key = "%s?%s" % (url, query_string)
    else:
        query_string = ""
        request_key = url

    if headers is None:
        headers = {}

    if token is not None:
        headers[b'Authorization'] = '{} {}'.format(token_type, token).encode('utf-8')

    if json:
        headers[b'Content-Type'] = b'application/json'

    return RequestInfo(url, query_string, request_key, headers, verify)


def get_url(request_info, progress=None):
    """Method for fetching a url in a worker thread.

    This function will do an HTTP(s) GET.  This method assumes that the
    URL contents will be a JSON blob that it automatically decodes into
    a dict.

    It works correctly on python 2.7 and python 3 and has proper support for
    TLS with an option to disable verification of the TLS certificate for
    testing purposes.

    Args:
        request_info (RequestInfo): The result of a previous call to pack_url
            to produce a RequireInfo object.
        progress (tqdm): An optional progress bar that will be updated when this
            function completes.

    Returns:
        dict: The decoded dictionary from the JSON response of this GET.
    """

    if not isinstance(request_info, RequestInfo):
        raise ArgumentError("You must call get_url with a RequestInfo object from a call to pack_url", request_info=request_info)

    req = Request(request_info.request_key, headers=request_info.headers)

    if request_info.verify is False:
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3

        resp = urlopen(req, context=context)
    else:
        resp = urlopen(req)

    data = resp.read()
    result = json.loads(data.decode('utf-8'))

    if progress is not None:
        progress.update(1)

    return result


def post_url(request_info, data, progress=None):
    """Method for posting to an arbitrary URL with data.

    This function will do an HTTP(s) post with data.

    It works correctly on python 2.7 and python 3 and has proper support for
    TLS with an option to disable verification of the TLS certificate for
    testing purposes.

    Args:
        request_info (RequestInfo): The result of a previous call to pack_url
            to produce a RequireInfo object.
        data (bytes): The raw data that we would like to post.
        progress (tqdm): An optional progress bar that will be updated when this
            function completes.

    Returns:
        str or unicode: The utf-8 decoded response of the POST.

        This will be a str on python 3 and a unicode object on python 2.
    """

    if not isinstance(request_info, RequestInfo):
        raise ArgumentError("You must call post_url with a RequestInfo object from a call to pack_url", request_info=request_info)

    url = request_info.url

    # We must encode the URL to bytes rather than unicode otherwise:
    # https://stackoverflow.com/a/8715815 will cause a unicode decode
    # error on our *data*
    # However, we must pass a normal string on python 3
    # See: https://github.com/iotile/iotile_analytics/issues/47
    if sys.version_info.major < 3:
        url = url.encode('utf-8')
        headers = request_info.headers
    else:
        headers = {key.decode('utf-8'): val.decode('utf-8') for key, val in iteritems(request_info.headers)}

    req = Request(url, data, headers=headers)

    if request_info.verify is False:
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3

        resp = urlopen(req, context=context)
    else:
        resp = urlopen(req)

    resp_data = resp.read().decode('utf-8')

    if progress is not None:
        progress.update(1)

    return resp_data
