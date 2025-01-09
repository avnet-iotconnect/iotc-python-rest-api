from http import HTTPStatus


class ApiException(Exception):
    def __init__(self, message: str, http_status: int):
        super().__init__(message, http_status)
        self.message = message
        self.status = http_status


class AuthError(ApiException):
    """ Authentication related error """

    def __init__(self, message: str, http_status: int =HTTPStatus.UNAUTHORIZED):
        super().__init__(message, http_status)


class ResponseError(ApiException):
    """ Custom exception for bad HTTP response status code """

    def __init__(self, message: str, http_status: int):
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
