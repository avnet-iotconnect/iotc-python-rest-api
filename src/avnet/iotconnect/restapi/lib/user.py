# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

from dataclasses import dataclass
from http import HTTPStatus
from typing import Optional, Dict

from . import apiurl, config, token
from .apirequest import request
from .error import UsageError, ConflictResponseError, NotFoundResponseError


@dataclass
class User:
    userGuid: str
    userId: str
    companyCpid: str # It is recommended to use the token module to decode the access token to get this info


def query(query_str: str = '[*]', params: Optional[Dict[str, any]] = None) -> list[User]:
    response = request(apiurl.ep_firmware, '/User')
    return response.data.get(query_str=query_str, params=params, dc=User)


def get_own_user() -> Optional[User]:
    """ Lookup the currently logged-in user """
    at = token.decode_access_token()
    if at is None:
        raise UsageError('get_by_email: The user is not logged in. Please configure the API first.')
    return get_by_guid(at.user.id)


def get_by_email(email: str) -> Optional[User]:
    """ Lookup a user by their email (username) """
    if email is None or len(email) == 0:
        raise UsageError('get_by_email: The email parameter is missing')
    try:
        response = request(apiurl.ep_user, f'/User/{email}/availability', codes_ok=[HTTPStatus.NO_CONTENT])
        u = response.data.get_one(dc=User)
        if u is None:
            return None
        # we have to re-fetch because the availability result is missing the CPID!
        # also availability returns a different model, so convert u.guid to u.userGuid
        response = request(apiurl.ep_user, f'/User/{u.guid}', codes_ok=[HTTPStatus.NO_CONTENT])
        return response.data.get_one(dc=User)
    except ConflictResponseError:
        return None


def get_by_guid(guid: str) -> Optional[User]:
    """ Lookup a template by GUID """
    try:
        response = request(apiurl.ep_user, f'/User/{guid}')
        return response.data.get_one(dc=User)
    except NotFoundResponseError:
        return None
