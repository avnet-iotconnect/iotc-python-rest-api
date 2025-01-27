# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

"""This module provides IoTConnect authentication functionality."""
import datetime
import os

from . import apiurl, config
from .apirequest import Headers, request
from .error import UsageError, AuthError


def _ts_now():
    return datetime.datetime.now(datetime.timezone.utc).timestamp()


def check() -> None:
    if config.access_token is None:
        raise UsageError("No access token configured. Please configure the API.")
    else:
        if config.token_expiry < _ts_now():
            raise AuthError("Token expired")
        if should_refresh():
            # It's been longer than an hour since we refreshed the token. We should refresh it now.
            refresh()


def authenticate(username: str, password: str) -> None:
    """Record access token from IoT Connect and return it. Entrance point to this module"""
    missing_args = []
    if username is None:
        missing_args.append("Username")
    if password is None:
        missing_args.append("Password")
    if config.skey is None:
        missing_args.append("Solution Key")
    if len(missing_args):
        raise UsageError('authenticate: The following arguments are missing: %s' % ", ".join(missing_args))
    if config.api_trace_enabled:
        print(f"Solution Key: {config.skey}")
    basic_token = _get_basic_token()
    headers = {
        Headers.N_ACCEPT: Headers.V_APP_JSON,
        Headers.N_AUTHORIZATION: 'Basic %s' % basic_token,
        "Solution-key": config.skey
    }
    data = {
        "username": username,
        "password": password
    }
    response = request(apiurl.ep_auth, "/Auth/login", json=data, headers=headers)
    config.access_token = response.body.get_object_value("access_token")
    config.refresh_token = response.body.get_object_value("refresh_token")
    expires_in = response.body.get_object_value("expires_in")
    config.token_time = _ts_now()
    config.token_expiry = config.token_time + expires_in
    config.username = username
    config.write()


def should_refresh() -> bool:
    return config.token_time + 3600 < _ts_now() and os.environ.get('IOTC_API_NO_TOKEN_REFRESH') is None


def refresh() -> None:
    data = {
        "refreshtoken": config.refresh_token
    }
    response = request(apiurl.ep_auth, "/Auth/refresh-token", json=data, headers={})
    config.access_token = response.body.get_object_value("access_token")
    config.refresh_token = response.body.get_object_value("refresh_token")
    expires_in = response.body.get_object_value("expires_in")
    config.token_time = _ts_now()
    config.token_expiry = config.token_time + expires_in
    config.write()


def get_auth_headers(accept=Headers.V_APP_JSON) -> dict[str, str]:
    """  Helper: Returns a shallow copy of headers used to authenticate other API call with the access token  """
    check()
    return dict({
        Headers.N_ACCEPT: accept,
        Headers.N_AUTHORIZATION: "Bearer " + config.access_token
    })


def _get_basic_token() -> str:
    """Get basic token from the IoT Connect and return it."""
    headers = {
        Headers.N_CONTENT_TYPE: Headers.V_APP_JSON,
        Headers.N_ACCEPT: Headers.V_APP_JSON
    }
    response = request(apiurl.ep_auth, "/Auth/basic-token", headers=headers)
    basic_token = response.body.get("data")
    return basic_token
