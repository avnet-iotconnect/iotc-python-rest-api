"""This module provides IoTConnect authentication functionality."""

from typing import MutableMapping

import requests

from . import apiurl
from .apirequest import Headers
from .apirequest import Response

access_token = None
refresh_token = None

def _get_basic_token() -> str:
    """Get basic token from the IoT Connect and return it."""
    print(apiurl.ep_auth + "/Auth/basic-token")
    response = Response(requests.get(apiurl.ep_auth + "/Auth/basic-token"))
    response.ensure_success()
    basic_token = response.get_value("data")
    print("Basic token: " + basic_token)
    return basic_token

def is_authenticated() -> bool:
    return access_token is not None

def authenticate(username: str, password: str, solution_key: str) -> str:
    global access_token, refresh_token
    """Record access token from IoT Connect and return it. Entrance point to this module"""
    basic_token = _get_basic_token()
    headers = {
        Headers.N_CONTENT_TYPE: Headers.V_APP_JSON,
        Headers.N_ACCEPT: Headers.V_APP_JSON,
        Headers.N_AUTHORIZATION: 'Basic %s' % basic_token,
        "Solution-key": solution_key
    }
    data = {
        "username": username,
        "password": password
    }
    response = Response(requests.post(apiurl.ep_auth + "/Auth/login", json=data, headers=headers))
    response.ensure_success()
    access_token = str('Bearer %s' % response.get_value_or_raise("access_token"))
    refresh_token = response.get_value_or_raise("refresh_token")
    print("refresh token: " + refresh_token)
    print("Successful authentication. Access Token:")
    print(access_token)
    return access_token

def refresh():
    global access_token, refresh_token

    data = {
        "refreshtoken": refresh_token
    }

    response = Response(requests.post(apiurl.ep_auth + "/Auth/refresh-token", json=data, headers=get_auth_headers()))
    response.ensure_success()
    access_token = response.get_value_or_raise("access_token")
    refresh_token = response.get_value_or_raise("refresh_token")
    print("refresh token: " + refresh_token)
    print("Successful refresh. Access Token:")
    print(access_token)

def get_auth_headers(content_type=Headers.V_APP_JSON, accept=Headers.V_APP_JSON) -> MutableMapping[str, str]:
    """  Helper: Returns a shallow copy of headers used to authenticate other API call with the access token  """
    return dict({
        "Content-type": content_type,
        "Accept": accept,
        "Authorization": access_token
    })

