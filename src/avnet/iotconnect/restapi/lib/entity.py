"""This module provides IoTConnect authentication functionality."""
import datetime

from . import apiurl, config
from .apirequest import Headers, request
from .error import UsageError
from . import credentials as credentials


def get_guid(name: str) -> None:
    """Record access token from IoT Connect and return it. Entrance point to this module"""
    missing_args = []
    if name is None:
        raise UsageError('get_guid: The entity name argument is missing')

    credentials.check()

    headers = credentials.get_auth_headers()
    response = request(apiurl.ep_user, "/Entity/lookup", data=None, headers=headers)
    response.ensure_success()
    # print(response.get_values('*'))
    ret = response.get_values('$.data[?(@.name = "' + name + '")]')
    print(ret)
    return ret


