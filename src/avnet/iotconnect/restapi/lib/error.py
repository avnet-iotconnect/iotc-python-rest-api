class ConfigError(BaseException):
    """ Custom exception for client configuration errors """
    pass


class ResponseException(BaseException):
    """ Custom exception for bad HTTP response status code """
    pass
