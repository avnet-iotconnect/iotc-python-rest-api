"""This module provides IoTConnect authentication functionality."""
import datetime
import os
from typing import Optional

from . import apiurl, config
from .apirequest import Headers, request
from .error import UsageError, AuthError


def _ts_now():
    return datetime.datetime.now(datetime.timezone.utc).timestamp()


access_token: Optional[str] = None
refresh_token = None
_token_expiry = 0  # just initialize for "sense" purposes
_token_time = 0


def check() -> None:
    if access_token is None:
        raise UsageError("No access token configured")
    else:
        if _token_expiry < _ts_now():
            raise AuthError("Token expired")
        if should_refresh():
            # It's been longer than an hour since we refreshed the token. We should refresh it now.
            refresh()
            _save_config()


def authenticate(username: str, password: str, solution_key: str) -> None:
    global access_token, refresh_token, _token_time, _token_expiry
    """Record access token from IoT Connect and return it. Entrance point to this module"""
    missing_args = []
    if username is None:
        missing_args.append("Username")
    if password is None:
        missing_args.append("Password")
    if solution_key is None:
        missing_args.append("Solution Key")
    if len(missing_args):
        raise UsageError('authenticate: The following arguments are missing: %s' % ", ".join(missing_args))
    if config.api_trace_enabled:
        print(f"Solution Key: {solution_key}")
    basic_token = _get_basic_token()
    headers = {
        Headers.N_ACCEPT: Headers.V_APP_JSON,
        Headers.N_AUTHORIZATION: 'Basic %s' % basic_token,
        "Solution-key": solution_key
    }
    data = {
        "username": username,
        "password": password
    }
    response = request(apiurl.ep_auth, "/Auth/login", json=data, headers=headers)
    access_token = response.body.get_object_value("access_token")
    refresh_token = response.body.get_object_value("refresh_token")
    expires_in = response.body.get_object_value("expires_in")
    _token_time = _ts_now()
    _token_expiry = _token_time + expires_in
    _save_config()


def should_refresh() -> bool:
    return _token_time + 100 < _ts_now() and os.environ.get('IOTC_NO_TOKEN_REFRESH') is None


def refresh() -> None:
    global access_token, refresh_token, _token_time, _token_expiry
    data = {
        "refreshtoken": refresh_token
    }
    response = request(apiurl.ep_auth, "/Auth/refresh-token", json=data, headers={})
    access_token = response.body.get_object_value("access_token")
    refresh_token = response.body.get_object_value("refresh_token")
    expires_in = response.body.get_object_value("expires_in")
    _token_time = _ts_now()
    _token_expiry = _token_time + expires_in
    # print("refresh token: " + refresh_token)
    print("Token refreshed successfully.")
    # print(access_token)
    _save_config()


def get_auth_headers(accept=Headers.V_APP_JSON) -> dict[str, str]:
    """  Helper: Returns a shallow copy of headers used to authenticate other API call with the access token  """
    check()
    return dict({
        Headers.N_ACCEPT: accept,
        Headers.N_AUTHORIZATION: "Bearer " + access_token
    })


def _get_basic_token() -> str:
    """Get basic token from the IoT Connect and return it."""
    headers = {
        Headers.N_CONTENT_TYPE: Headers.V_APP_JSON,
        Headers.N_ACCEPT: Headers.V_APP_JSON
    }
    response = request(apiurl.ep_auth, "/Auth/basic-token", headers=headers)
    basic_token = response.body.get("data")
    # print("Basic token: " + basic_token)
    return basic_token


def _save_config() -> None:
    section = config.get_section(config.SECTION_AUTH)
    section['access_token'] = access_token
    section['refresh_token'] = refresh_token
    section['token_time'] = str(round(_token_time))
    section['token_expiry'] = str(round(_token_expiry))
    config.write()


def _load_config() -> None:
    global access_token, refresh_token, _token_time, _token_expiry
    section = config.get_section(config.SECTION_AUTH)
    if section.get('access_token') is not None:
        access_token = section['access_token']
        refresh_token = section['refresh_token']
        _token_time = int(section['token_time'])
        _token_expiry = int(section['token_expiry'])


_load_config()
