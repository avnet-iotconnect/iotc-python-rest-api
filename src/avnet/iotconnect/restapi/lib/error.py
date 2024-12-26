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
    pass

class UsageError(ValueError):
    """ Incorrect usage. Missing argument etc. """
    pass

class MissingValueError(ValueError):
    """ Value is missing (typically from the response). """
    pass
