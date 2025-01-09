from requests import HTTPError

class ApiException(BaseException):
    pass

class ConfigError(ApiException):
    """ Custom exception for client configuration errors """
    pass

class AuthError(ApiException):
    """ Authentication related error """
    pass

class ResponseError(ApiException):
    """ Custom exception for bad HTTP response status code """
    # def __init__(self, code, message):
    pass

class UsageError(ApiException):
    """ Incorrect usage. Missing argument etc. """
    pass

class SingleValueExpected(UsageError):
    """ Incorrect usage. We expected a single value to be returned by the API, but got more than one. """
    pass

class ValueExpected(UsageError):
    """ Incorrect usage. We expected a value to be obtainable from the response. """
    pass