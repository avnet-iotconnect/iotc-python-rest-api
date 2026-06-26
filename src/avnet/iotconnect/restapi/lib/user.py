# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Optional

from . import apiurl, accesstoken
from .apirequest import request
from .error import UsageError, ConflictResponseError, NotFoundResponseError
from .query import Query, Page, api_param, run_query


@dataclass
class User:
    """
    A user account. The fields the server populates depend on which endpoint produced
    the object: the single-user lookup uses ``userGuid``/``companyCpid``, while the
    list and availability endpoints use ``guid``/``companyGuid``. Use :attr:`id` to get
    the user's GUID regardless of source.
    """
    userId: str  # email / username; present in every user response
    guid: Optional[str] = field(default=None)        # GUID from list & availability responses
    userGuid: Optional[str] = field(default=None)    # GUID from the single-user lookup
    companyGuid: Optional[str] = field(default=None)
    companyCpid: Optional[str] = field(default=None)  # prefer decoding the access token for this
    firstName: Optional[str] = field(default=None)
    lastName: Optional[str] = field(default=None)
    roleName: Optional[str] = field(default=None)
    entityName: Optional[str] = field(default=None)
    entityGuid: Optional[str] = field(default=None)
    isActive: Optional[bool] = field(default=None)
    contactNo: Optional[str] = field(default=None)

    @property
    def id(self) -> Optional[str]:
        """The user's GUID, regardless of which endpoint produced this object."""
        return self.userGuid or self.guid


@dataclass
class UserQuery(Query):
    """
    Filter options for :func:`list`. All fields optional; only the ones set are sent.
    Inherits pagination (``page``/``page_size``/``sort_by``) from :class:`~.query.Query`.
    """
    first_name: Optional[str] = api_param('FirstName', description='First name')
    last_name: Optional[str] = api_param('LastName', description='Last name')
    email: Optional[str] = api_param('Email', description='Email / username')
    contact_no: Optional[str] = api_param('ContactNo', description='Contact number')
    role: Optional[str] = api_param('Role', description='Role name')
    entity: Optional[str] = api_param('Entity', description='Entity name')
    status: Optional[str] = api_param('Status', description='User status, e.g. active or inactive')


def query(query: Optional[UserQuery] = None) -> Page[User]:
    """
    Query users, with server-side filtering, sorting and pagination.

    :param query: Filter/paging options. Defaults to the first page, unfiltered.
    :return: A :class:`~.query.Page` of :class:`User`.
    """
    return run_query(apiurl.ep_user, '/User', query or UserQuery(), User)


def get_own_user() -> Optional[User]:
    """ Lookup the currently logged-in user """
    at = accesstoken.decode_access_token()
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
        # Re-fetch by GUID: the availability response uses `guid` and omits the CPID,
        # so we fetch the full single-user record (which populates userGuid/companyCpid).
        response = request(apiurl.ep_user, f'/User/{u.id}', codes_ok=[HTTPStatus.NO_CONTENT])
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
