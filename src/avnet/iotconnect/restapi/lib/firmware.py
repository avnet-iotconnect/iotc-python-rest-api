# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

from dataclasses import dataclass
from http import HTTPMethod, HTTPStatus
from typing import Optional, Dict

from . import apiurl, upgrade
from .apirequest import request
from .error import UsageError, ConflictResponseError, NotFoundResponseError


@dataclass
class Firmware:
    guid: str
    name: str
    hardware: str
    isDeprecated: bool


@dataclass
class FirmwareCreateResult:
    newId: str
    firmwareUpgradeGuid: str


def _validate_firmware_name(firmware_name: str):
    if firmware_name is None:
        raise UsageError('"firmware_name" parameter must not be None')
    elif len(firmware_name) > 10 or len(firmware_name) == 0:
        raise UsageError('"firmware_name" parameter must be between 1 and 10 characters')
    elif not firmware_name.isalnum() or firmware_name.upper() != firmware_name:
        raise UsageError('"firmware_name" parameter must be upper case and contain only alphanumeric characters')


def query(query_str: str = '[*]', params: Optional[Dict[str, any]] = None) -> list[Firmware]:
    response = request(apiurl.ep_firmware, '/Firmware')
    return response.data.get(query_str=query_str, params=params, dc=Firmware)


def get_by_name(name: str) -> Optional[Firmware]:
    """ Lookup a firmware name - unique template ID supplied during creation """
    if name is None or len(name) == 0:
        raise UsageError('get_by_name: The firmware name is missing')
    response = request(apiurl.ep_firmware, '/Firmware', params={"Name": name}, codes_ok=[HTTPStatus.NO_CONTENT])
    return response.data.get_one(dc=Firmware)


def get_by_guid(guid: str) -> Optional[Firmware]:
    """ Lookup a firmware by GUID """
    if guid is None or len(guid) == 0:
        raise UsageError('get_by_guid: The firmware guid argument is missing')
    try:
        response = request(apiurl.ep_device, f'/Firmware/{guid}')
        return response.data.get_one(dc=Firmware)
    except NotFoundResponseError:
        return None


def create(
        template_guid: str,
        name: str,
        hw_version: str,
        initial_sw_version: str,
        description: Optional[str] = None,
        upgrade_description: Optional[str] = None,
) -> FirmwareCreateResult:
    """
    Creates a firmware entry in IoTconnect. Firmware is associated with a template and can have different versions of
    firmware upgrades that can be uploaded and that are associated with it.
    When creating a firmware entry, an initial firmware upgrade version is required.

    :param template_guid: GUID of the device template.
    :param name: Name of this template. This code must be uppercase alphanumeric an up to 10 characters in length.
    :param hw_version: Hardware Version of the firmware.
    :param initial_sw_version: Hardware Version of the software.
    :param description: Optional description that can be added to the firmware.
    :param upgrade_description: Optional description that can be added to the firmware upgrade.

    :return: FirmwareCreateResult with new Firmware GUID and Firmware Upgrade GUID that was newly created.
    """

    _validate_firmware_name(name)
    if hw_version is not None:
        # noinspection PyProtectedMember
        upgrade._validate_version('hw_version', hw_version)
    if initial_sw_version is not None:
        # noinspection PyProtectedMember
        upgrade._validate_version('initial_sw_version', initial_sw_version)
    data = {
        "deviceTemplateGuid": template_guid,
        "firmwareName": name,
        "hardware": hw_version,
        "software": initial_sw_version
    }
    if description is not None:
        data["FirmwareDescription"] = description
    if upgrade_description is not None:
        data["firmwareUpgradeDescription"] = description

    response = request(apiurl.ep_firmware, '/Firmware', json=data)
    return response.data.get_one(dc=FirmwareCreateResult)


def deprecate_match_guid(guid: str) -> None:
    """
    Delete the firmware with given template guid.

    :param guid: GUID of the firmware to delete.
    """
    if guid is None:
        raise UsageError('delete_match_guid: The template guid argument is missing')
    response = request(apiurl.ep_firmware, f'/Firmware/{guid}/deprecate', method=HTTPMethod.PUT)
    response.data.get_one()  # we expect data to be empty -- 'data': [] on success


def deprecate_match_name(name: str) -> None:
    """
    Delete the firmware with given the name.

    :param name: Name of the firmware to delete.
    """
    if name is None:
        raise UsageError('delete_match_name: The firmware name argument is missing')
    _validate_firmware_name(name)
    fw = get_by_name(name)
    if fw is None:
        raise NotFoundResponseError(f'delete_match_name: Firmware with name "{name}" not found')
    deprecate_match_guid(fw.guid)
