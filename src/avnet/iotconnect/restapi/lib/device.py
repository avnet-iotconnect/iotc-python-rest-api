# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from http import HTTPMethod
from typing import Optional, Union

from . import apiurl, entity, template
from .apirequest import request
from .error import UsageError, NotFoundResponseError, ConflictResponseError
from .query import Query, Page, api_param, run_query

# Sortable fields for DeviceQuery.sort_by (append a direction, e.g. "lastCommunication desc").
# Only these are honored; other fields 412 and displayName is silently ignored.
SORT_DUID = 'uniqueId'
SORT_LAST_CONNECTION = 'lastConnection'        # last MQTT connect
SORT_LAST_COMMUNICATION = 'lastCommunication'  # last message - best proxy for "last telemetry"


@dataclass
class Device:
    guid: str
    uniqueId: str
    displayName: str
    isActive: bool
    deviceTemplateGuid: str
    messageVersion: str
    isAcquired: Optional[int] = field(default=None)
    isEdgeSupport: Optional[bool] = field(default=None)
    isParentAcquired: Optional[bool] = field(default=None)

    # Connectivity/recency from the list endpoint (None on single-get). ISO-8601 strings.
    isConnected: Optional[bool] = field(default=None)
    lastConnection: Optional[str] = field(default=None)
    lastCommunication: Optional[str] = field(default=None)


@dataclass
class DeviceCreateResult:
    # noinspection SpellCheckingInspection
    newid: str
    entityGuid: str
    uniqueId: str
    activeDeviceCount: int = field(default=None)
    inActiveDeviceCount: int = field(default=None)
    ggDeviceScript: Optional[str] = field(default=None)
    parentUniqueId: Optional[str] = field(default=None)


# --- Status enums ----------------------------------------------------------
# The API takes these filter values as lowercase strings; modelling them as enums
# makes the legal values discoverable and validated (and gives a clean JSON-Schema
# 'enum' when these query objects are surfaced as MCP tool parameters).

class DeviceStatus(Enum):
    """Device connectivity status, as accepted by the /Device 'Status' filter."""
    ACTIVE = 'active'
    INACTIVE = 'inactive'


class Acquired(Enum):
    """Device acquire status, as accepted by the /Device 'Acquired' filter."""
    ACQUIRED = 'acquired'
    RELEASED = 'released'
    IN_PROGRESS = 'inprogress'


# --- Query options ---------------------------------------------------------

@dataclass
class DeviceQuery(Query):
    """
    Filter options for :func:`list`. All fields are optional; only the ones set are
    sent to the server. Inherits pagination (page, page_size, sort_by)
    from :class:`~.query.Query`.
    """
    duid_contains: Optional[str] = api_param(
        'UniqueId',
        description='Search devices whose DUID contains this text (case-insensitive substring). '
                    'For an exact device, use get_by_duid() instead.',
        examples=['psoc-'])
    # No name filter: the /Device 'Name' query param is ignored by the server (returns the
    # full set for any value), so it is intentionally not exposed. Narrow by duid_contains instead.
    # resolvers are wrapped in lambdas so they can be defined lower in the file
    # (field defaults are evaluated now, but the lambda body is not).
    template: Optional[str] = api_param(
        'TemplateGuid', resolver=lambda v: _resolve_template(v),
        description='Filter by device template, given as its template code or GUID',
        examples=['mytmpl01'])
    entity: Optional[str] = api_param(
        'EntityGuid', resolver=lambda v: _resolve_entity(v),
        description='Filter by entity, given as its name or GUID')
    status: Optional[DeviceStatus] = api_param(
        'Status', description='Filter by connectivity status', examples=['active'])
    acquired: Optional[Acquired] = api_param(
        'Acquired', description='Filter by acquire status')
    is_edge: Optional[bool] = api_param('isEdge', description='Only edge devices')
    is_gateway: Optional[bool] = api_param('isGateway', description='Only gateway devices')
    wireless: Optional[bool] = api_param('wireless', description='Only wireless devices')

# --- Friendly-value resolvers ---------------------------------------------
# These convert a meaningful user/agent input (a template code, an entity name)
# into the GUID the API expects. They accept a GUID too, so callers never have to
# care which they are holding - and an LLM can pass the name it actually knows
# instead of fabricating a GUID. Lookups only happen when the value isn't a GUID.

_GUID_RE = re.compile(
    r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
)


def query(query: Optional[DeviceQuery] = None) -> Page[Device]:
    """
    Query devices, with server-side filtering, sorting and pagination.

    sort_by is a "field direction" string built from the SORT_* constants,
    e.g. f'{device.SORT_LAST_COMMUNICATION} desc'.

    :param query: Filter/paging options. Defaults to the first page, unfiltered.
    :return: A :class:`~.query.Page` of :class:`Device`. Iterate it for the current
        page, or call .all() to walk every page transparently. Unlike most list
        endpoints, /Device does not report a total, so total_count is None and
        has_next falls back to page fullness.
    """
    return run_query(apiurl.ep_device, '/Device', query or DeviceQuery(), Device)


def get_by_guid(guid: str) -> Optional[Device]:
    """Lookup a device by device GUID"""
    if guid is None:
        raise UsageError('get_by_guid: The device GUID argument is missing')
    try:
        response = request(apiurl.ep_device, f'/Device/{guid}')
        return response.data.get_one(dc=Device)
    except ConflictResponseError:
        return None


def get_by_duid(duid: str) -> Optional[Device]:
    """Lookup a device by uniqueId"""
    if duid is None:
        raise UsageError('get_by_duid: The device Unique ID (DUID) argument is missing')
    try:
        response = request(apiurl.ep_device, f'/Device/uniqueId/{duid}')
        return response.data.get_one(dc=Device)
    except ConflictResponseError:
        return None


def create(
        template_guid: str,
        duid: str,
        device_certificate: Optional[Union[str, bytes]] = None,
        name: Optional[str] = None,
        is_ca_auth=False,
        entity_guid: Optional[str] = None
) -> DeviceCreateResult:
    """
    Create an IoTConnect device using x509 authentication (either Self Signed or CA signed).

    This is the single, curated path for device creation. The template and entity
    arguments accept either a GUID or a friendly identifier (template code / entity
    name); they are resolved to GUIDs automatically.

    :param template_guid: Device's template, given as its GUID or template code.
    :param duid: Device Unique ID.
    :param device_certificate: Device certificate as a PEM string or a path to the device PEM cert file. If not provided and CA Certificate auth type is not used an error will be raised.
    :param name: Name of the device. If not provided, DUID will be used.
    :param is_ca_auth: Set this to true if template AT (auth type) is authtype.AT_CA_SIGNED.
    :param entity_guid: Entity under which the device will be created, given as its GUID or name. If not supplied, the account root entity will be used.
    """
    if template_guid is None:
        raise UsageError('cert create: Template GUID argument is missing')
    if duid is None:
        raise UsageError('cert create: The device Unique ID (DUID) argument is missing')
    if device_certificate is None and not is_ca_auth:
        raise UsageError('create_self_signed: Device certificate argument is missing')

    cert_str = None
    if device_certificate is not None:
        if '-----BEGIN CERTIFICATE' in device_certificate:
            cert_str = device_certificate
        else:
            try:
                with open(device_certificate, 'r') as cert_file:
                    cert_str = cert_file.read()
                    if '-----BEGIN CERTIFICATE' not in cert_str:
                        raise UsageError(f'Device certificate at what ought to be a path "{device_certificate}" does not appear to be valid')
            except OSError:
                raise UsageError(f'Could not open file at what ought to be a path at "{device_certificate}"')

    template_guid = _resolve_template(template_guid)

    # assign entity guid to root entity if not provided, else resolve a name/GUID
    if entity_guid is None:
        entity_guid = entity.get_root_entity().guid
    else:
        entity_guid = _resolve_entity(entity_guid)

    data = {
        "deviceTemplateGuid": template_guid,
        "uniqueId": duid,
        "displayName": name or duid,
        "entityGuid": entity_guid
    }

    if cert_str is not None:
        data['certificateText'] = cert_str

    response = request(apiurl.ep_device, '/Device', json=data)
    return response.data.get_one(dc=DeviceCreateResult)  # we expect data to be empty -- 'data': [] on success


def set_active_match_guid(guid: str, active: bool = True) -> None:
    """
    Activate or deactivate the device with the given GUID.

    A focused, intent-revealing update (rather than a generic patch) for the one
    device field that is commonly toggled.

    :param guid: GUID of the device.
    :param active: True to activate, False to deactivate.
    """
    if guid is None:
        raise UsageError('set_active_match_guid: The device guid argument is missing')
    response = request(
        apiurl.ep_device, f'/Device/{guid}/status',
        json={'isActive': active}, method=HTTPMethod.PUT
    )
    response.data.get_one()  # we expect data to be empty -- 'data': [] on success


def set_active_match_duid(duid: str, active: bool = True) -> None:
    """
    Activate or deactivate the device with the given DUID.

    :param duid: Device unique ID.
    :param active: True to activate, False to deactivate.
    """
    if duid is None:
        raise UsageError('set_active_match_duid: The device duid argument is missing')
    d = get_by_duid(duid)
    if d is None:
        raise NotFoundResponseError(f'set_active_match_duid: Device with DUID "{duid}" not found')
    set_active_match_guid(d.guid, active)


def delete_match_guid(guid: str) -> None:
    """
    Delete the device with given guid.

    :param guid: GUID of the device to delete.
    """
    if guid is None:
        raise UsageError('delete_match_guid: The device guid argument is missing')
    response = request(apiurl.ep_device, f'/Device/{guid}', method=HTTPMethod.DELETE)
    response.data.get_one()  # we expect data to be empty -- 'data': [] on success


def delete_match_duid(duid: str) -> None:
    """
    Delete the device with given DUID.

    :param duid: Device unique ID.
    """
    if duid is None:
        raise UsageError('delete_match_duid: The device duid argument is missing')
    d = get_by_duid(duid)
    if d is None:
        raise NotFoundResponseError(f'delete_match_duid: Device with DUID "{duid}" not found')
    response = request(apiurl.ep_device, f'/Device/{d.guid}', method=HTTPMethod.DELETE)
    response.data.get_one()  # we expect data to be empty -- 'data': [] on success


def _is_guid(value: str) -> bool:
    return isinstance(value, str) and bool(_GUID_RE.match(value.strip()))

# --- Helpers ---------------------------------------------------------


def _resolve_template(value: str) -> str:
    """Accept a device template GUID or template code; return the GUID."""
    if _is_guid(value):
        return value
    t = template.get_by_template_code(value)
    if t is None:
        raise UsageError(f'No device template found with code "{value}"')
    return t.guid


def _resolve_entity(value: str) -> str:
    """Accept an entity GUID or entity name; return the GUID."""
    if _is_guid(value):
        return value
    return entity.get_by_name(value).guid