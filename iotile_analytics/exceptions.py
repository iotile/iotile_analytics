"""Custom exceptions for iotile analytics."""

from typedargs.exceptions import KeyValueException


class CloudError(KeyValueException):
    """A generic error interacting with IOTile.cloud."""

    pass


class AuthenticationError(CloudError):
    """An error logging into iotile.cloud."""

    pass


class MissingPackageError(KeyValueException):
    """The operation you requested requires a packgae to be installed.

    The suggestion keyword argument should be the name of the package.
    """

    pass
