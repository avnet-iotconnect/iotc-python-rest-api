"""This module provides IoTConnect authentication functionality."""

from . import apiurl
from .apirequest import request
from .error import UsageError


def get_guid(name: str) -> None:
    """Record access token from IoT Connect and return it. Entrance point to this module"""
    if name is None:
        raise UsageError('get_guid: The entity name argument is missing')

    response = request(apiurl.ep_user, "/Entity/lookup")
    return response.data.get_or_raise('[?name == `' + name + '`].guid')


