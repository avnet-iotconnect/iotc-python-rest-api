# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

from http import HTTPStatus


class ApiException(Exception):
    def __init__(self, message: str, http_status: int):
        super().__init__(message, http_status)
        self.message = message
        self.status = http_status


class ResponseError(ApiException):
    """ Custom exception for bad HTTP response status code """

    def __init__(self, message: str, http_status: int):
        super().__init__(message, http_status)


class AuthError(ApiException):
    """ Authentication related error """

    def __init__(self, message: str, http_status: int = HTTPStatus.UNAUTHORIZED):
        super().__init__(message, http_status)

class InvalidActionError(ApiException):
    """
    The REST API seems to have a flaw where when attempting to delete a resource of one type, for example,
    returns Not Found but deleting a different resource type will result in Conflict.
    This error wraps NotFound and Conflict together for invalid attempts to for example delete a device or template and such
    in order to make it easier for the application to catch these errors with some consistency.
    """

    def __init__(self, message: str, http_status):
        super().__init__(message, http_status)


class ConflictResponseError(InvalidActionError):
    """
    This error is returned when attempt to create a resource that already exists
    or delete a resource that has other resources associated with it (eg. a template
    that has device associated).
    Can also occur under other conditions that prevent data modification.
    It is also used internally by out API interface GET functions, but will be handled
    internally and the user should be getting None for the requested resource.
    """

    def __init__(self, message: str, http_status: int = HTTPStatus.CONFLICT):
        super().__init__(message, http_status)


class NotFoundResponseError(InvalidActionError):
    """
    These errors should be internally handled in most cases of get() functions b returning None to the user.
    """

    def __init__(self, message: str, http_status: int = HTTPStatus.NOT_FOUND):
        super().__init__(message, http_status)


class UsageError(ValueError):
    """ Incorrect usage. Missing argument etc. """
    pass


class ConfigError(UsageError):
    """ Custom exception for client configuration errors """
    pass


class SingleValueExpected(UsageError):
    """ Incorrect usage. We expected a single value to be returned by the API, but got more than one. """
    pass


class ValueExpected(UsageError):
    """ Incorrect usage. We expected a value to be obtainable from the response. """
    pass
