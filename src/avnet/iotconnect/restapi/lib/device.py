"""This module provides IoTConnect authentication functionality."""
from dataclasses import dataclass
from http import HTTPMethod
from typing import Optional, Union

from . import apiurl, entity
from .apirequest import request
from .error import UsageError


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


def query(query_str: str = '[*]') -> list[Device]:
    response = request(apiurl.ep_device, "/Device/lookup")
    return response.data.get(query_str, dc=Device)


def query_expect_one(query_str: str = '[*]') -> Device:
    response = request(apiurl.ep_device, '/Device/lookup')
    return response.data.get_one(query_str, dc=Device)


def get_by_duid(duid) -> Device:
    """Lookup a device by uniqueId"""
    if duid is None:
        raise UsageError('get_by_duid: The device Unique ID (DUID) argument is missing')
    return query_expect_one(f"[?uniqueId==`{duid}`]")


def create(
        template_guid: str,
        duid: str,
        device_certificate: Optional[Union[str,bytes]],
        name: Optional[str] = None,
        is_ca_auth=False,
        entity_guid: Optional[str] = None
) -> str:
    """
    Create an IoTConnect device using x509 authentication (either Self Signed or CA signed)

    :param template_guid: GUID of the device's template.
    :param duid: Device Unique ID.
    :param device_certificate: Device certificate to use. If not provided and CA Certificate auth type is not used an error will be raised.
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

    # assign entity guid to root entity if not provided
    if entity_guid is None:
        entity_guid = entity.get_root_entity().guid

    data = {
        "deviceTemplateGuid": template_guid,
        "uniqueId": duid,
        "displayName": name or duid,
        "entityGuid": entity_guid
    }

    # if auto_generate:
    #    data['autoGenerate'] = True

    response = request(apiurl.ep_device, '/Device', data=data)
    ret = response.data.get_one()
    # use upper() case because the returned guid is lower case, but it should be upper. Causes lookups to fail.
    return ret.get('newid').upper() if ret is not None else None


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
    response = request(apiurl.ep_device, f'/Device/{device.guid}', method=HTTPMethod.DELETE)
    response.data.get_one()  # we expect data to be empty -- 'data': [] on success
