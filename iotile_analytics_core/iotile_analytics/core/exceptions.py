"""Custom exceptions for iotile analytics."""

from typedargs.exceptions import KeyValueException


class CloudError(KeyValueException):
    """A generic error interacting with IOTile.cloud."""

    pass


class AuthenticationError(CloudError):
    """An error logging into iotile.cloud."""

    pass


class CertificateVerificationError(CloudError):
    """The iotile.cloud instance you are talking to does not have a trusted certificate.

    If you really want to talk to this cloud server, you can pass verify=False when you
    create a CloudSession in order to turn off certificate verification.
    """

    pass


class MissingPackageError(KeyValueException):
    """The operation you requested requires a packgae to be installed.

    The suggestion keyword argument should be the name of the package.
    """

    pass


class UsageError(KeyValueException):
    """A method was called in an unacceptable way.

    This exception is thrown when an API function is misused.
    """

    pass
