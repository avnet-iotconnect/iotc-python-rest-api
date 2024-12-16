"""
This module provides funtionality to check https request status.
If status is bad it raises custom BadHttpStatusException
"""

import requests
from .constants import STATUS_OK


class BadHttpStatusException(BaseException):
    """Custom exception for bad HTTP response status code"""
    pass

def check_status(response: requests.Response):
    """If status is bad - raise exception"""
    if response.status_code != STATUS_OK:
        response_status = ""
        try:
            response_status = response.json()
        except requests.exceptions.JSONDecodeError:
            response_status = f"Code {response.status_code}"

        raise BadHttpStatusException("Bad HTTP response status: " + str(response_status))
