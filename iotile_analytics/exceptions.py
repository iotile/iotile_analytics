"""Custom exceptions for iotile analytics."""

from typedargs.exceptions import KeyValueException


class CloudError(KeyValueException):
    """A generic error interacting with IOTile.cloud."""

    pass

class AuthenticationError(CloudError):
    """An error logging into iotile.cloud."""

    pass
