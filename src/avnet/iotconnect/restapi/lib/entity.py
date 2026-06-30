# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

from dataclasses import dataclass, field
from http import HTTPStatus
from typing import List, Optional

from . import apiurl
from .apirequest import request
from .error import UsageError, SingleValueExpected, ConflictResponseError


@dataclass
class Entity:
    """
    An entity (a node in the account's entity tree). Fields mirror the /Entity list
    model; the root entity is the one whose ``parentEntityGuid`` is None.
    """
    guid: str
    name: str
    parentEntityGuid: Optional[str] = field(default=None)
    parentName: Optional[str] = field(default=None)
    description: Optional[str] = field(default=None)
    childEntityLabel: Optional[str] = field(default=None)
    createdDate: Optional[str] = field(default=None)
    updatedDate: Optional[str] = field(default=None)
    activeUserCount: Optional[int] = field(default=None)
    inActiveUserCount: Optional[int] = field(default=None)
    deviceCount: Optional[int] = field(default=None)


@dataclass
class EntityDetail:
    """
    Address fields from the by-GUID detail endpoint that the /Entity list model
    (:class:`Entity`) does not carry. Tree/name/count fields are available from
    :func:`query`; geo (state/country/timezone) is omitted as it is returned only
    as opaque GUIDs.
    """
    guid: str
    address: Optional[str] = field(default=None)
    address2: Optional[str] = field(default=None)
    city: Optional[str] = field(default=None)
    zipCode: Optional[str] = field(default=None)


def query() -> List[Entity]:
    """
    Query all entities.

    Unlike the other endpoints, the /Entity endpoint exposes no query parameters in the
    API (no filtering, sorting or pagination), so it returns the full set in a single
    response and this function returns a plain list rather than a Page. Filter in Python,
    e.g. ``[e for e in entity.query() if e.parentEntityGuid is None]``.
    """
    response = request(apiurl.ep_user, '/Entity', codes_ok=[HTTPStatus.NO_CONTENT])
    return response.data.get(dc=Entity)


def get_by_name(name: str) -> Optional[Entity]:
    """
    Lookup an entity by name.

    Returns None if not found; raises if the name is ambiguous. The /Entity endpoint has
    no name filter, so the match is done client-side over the full entity list.
    """
    if name is None or len(name) == 0:
        raise UsageError('get_by_name: The entity name argument is missing')
    matches = [e for e in query() if e.name == name]
    if len(matches) == 0:
        return None
    if len(matches) > 1:
        raise SingleValueExpected
    return matches[0]


def get_root_entity() -> Entity:
    """
    Find the account's root entity: the single entity that has no parent.

    The /Entity endpoint has no filter for this, so it is derived client-side from the
    full entity list (the one with ``parentEntityGuid`` None).
    """
    roots = [e for e in query() if e.parentEntityGuid is None]
    if len(roots) == 0:
        raise UsageError('get_root_entity: No root entity found for this account')
    if len(roots) > 1:
        raise SingleValueExpected
    return roots[0]


def get_detail_by_guid(guid: str) -> Optional[EntityDetail]:
    """Address detail for an entity by GUID; None if it does not exist."""
    if guid is None or len(guid) == 0:
        raise UsageError('get_detail_by_guid: The entity guid argument is missing')
    try:
        response = request(apiurl.ep_user, f'/Entity/{guid}')
        return response.data.get_one(dc=EntityDetail)
    except ConflictResponseError:
        return None
