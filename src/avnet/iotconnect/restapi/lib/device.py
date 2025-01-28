# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

from dataclasses import dataclass, field
from http import HTTPMethod
from typing import Optional, Union, Dict

from . import apiurl, entity
from .apirequest import request
from .error import UsageError, NotFoundResponseError, ConflictResponseError


@dataclass
class Device:
    guid: str
    uniqueId: str
    displayName: str
    isAcquired: int
    isActive: bool
    isEdgeSupport: bool
    isParentAcquired: bool
    deviceTemplateGuid: str
    messageVersion: str


@dataclass
class DeviceCreateResult:
    # noinspection SpellCheckingInspection
    newid: str
    entityGuid: str
    uniqueId: str
    activeDeviceCount: int
    inActiveDeviceCount: int
    ggDeviceScript: Optional[str] = field(default=None)
    parentUniqueId: Optional[str] = field(default=None)


def query(query_str: str = '[*]', params: Optional[Dict[str, any]] = None) -> list[Device]:
    response = request(apiurl.ep_firmware, '/Device')
    return response.data.get(query_str=query_str, params=params, dc=Device)


def get_by_guid(guid:str) -> Optional[Device]:
    """Lookup a device by device GUID"""
    if guid is None:
        raise UsageError('get_by_duid: The device Unique ID (DUID) argument is missing')
    try:
        response = request(apiurl.ep_device, f'/Device/{guid}')
        return response.data.get_one(dc=Device)
    except ConflictResponseError:
        return None


def get_by_duid(duid:str) -> Optional[Device]:
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
) -> str:
    """
    Create an IoTConnect device using x509 authentication (either Self Signed or CA signed)

    :param template_guid: GUID of the device's template.
    :param duid: Device Unique ID.
    :param device_certificate: Device certificate to use as MEP string or path to the device PEM cert file. If not provided and CA Certificate auth type is not used an error will be raised.
    :param name: Name of the device. If not provided, DUID will be used.
    :param is_ca_auth: Set this to true if template AT (auth type) is AT_CA_SIGNED.
    :param entity_guid: Specify GUID of the entity under which the device will be created. If not supplied, the account root entity will be used.
    """
    if template_guid is None:
        raise UsageError('create_self_signed: Template GUID argument is missing')
    if duid is None:
        raise UsageError('create_self_signed:The device Unique ID (DUID) argument is missing')
    if device_certificate is None:
        if not is_ca_auth:
            raise UsageError('create_self_signed: Device certificate argument is missing')

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

    # assign entity guid to root entity if not provided
    if entity_guid is None:
        entity_guid = entity.get_root_entity().guid

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
    Delete the device with given guid.

    :param duid: Device unique ID.
    """
    if duid is None:
        raise UsageError('delete_match_duid: The device duid argument is missing')
    device = get_by_duid(duid)
    if device is None:
        raise NotFoundResponseError(f'delete_match_duid: Device with DUID "{duid}" not found')
    response = request(apiurl.ep_device, f'/Device/{device.guid}', method=HTTPMethod.DELETE)
    response.data.get_one()  # we expect data to be empty -- 'data': [] on success
