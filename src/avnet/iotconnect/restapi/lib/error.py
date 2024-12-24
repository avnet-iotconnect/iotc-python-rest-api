from requests import HTTPError


class ConfigError(BaseException):
    """ Custom exception for client configuration errors """
    pass


class ResponseError(HTTPError):
    """ Custom exception for bad HTTP response status code """
    pass


class UsageError(ValueError):
    """ Incorrect usage. Missing argument etc. """
    pass
