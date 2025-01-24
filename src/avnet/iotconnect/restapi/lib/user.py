# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

from dataclasses import dataclass
from http import HTTPStatus
from typing import Optional

from . import apiurl
from .apirequest import request
from .error import UsageError


@dataclass
class User:
    guid: str
    userId: str
    companyGuid: str

def query(query_str: str = '[*]') -> list[User]:
    response = request(apiurl.ep_user, '/User')
    return response.data.get(query_str, dc=User)


def query_expect_one(query_str: str = '[*]') -> Optional[User]:
    response = request(apiurl.ep_user, '/User')
    return response.data.get_one(query_str, dc=User)


def get_by_email(email: str) -> Optional[User]:
    """ Lookup a user by their email (username) """
    if email is None or len(email) == 0:
        raise UsageError('get_by_email: The email parameter is missing')
    response = request(apiurl.ep_user, f'/User/{email}/availability', codes_ok=[HTTPStatus.NO_CONTENT])
    return response.data.get_one(dc=User)


def get_by_guid(guid: str) -> Optional[User]:
    """ Lookup a template by GUID """
    response = request(apiurl.ep_user, f'/User/{guid}')
    return response.data.get_one(dc=User)


