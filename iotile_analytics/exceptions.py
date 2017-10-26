"""Custom exceptions for iotile analytics."""

from typedargs.exceptions import KeyValueException


class CloudError(KeyValueException):
    """A generic error interacting with IOTile.cloud."""

    pass
