"""This module provides IoTConnect authentication functionality."""
import io
import json
from dataclasses import dataclass
from http import HTTPMethod
from typing import Optional

from . import apiurl
from .apirequest import request
from .error import UsageError

# Authentication types. See https://docs.iotconnect.io/iotconnect/sdk/message-protocol/device-message-2-1/reference-table/#authtypes
AT_CA_SIGNED = 2
AT_SELF_SIGNED = 3
AT_TPM = 4
AT_SYMMETRIC_KEY = 5
AT_CA_INDIVIDUAL = 7

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

def _validate_version(version: str, what: str):
    if version is None:
        raise UsageError(f'"{what}" parameter must not be None')
    elif len(version) > 20 or len(version) == 0:
        raise UsageError(f'"{what}" parameter must be between 1 and 20 characters')
    elif all(x.isalnum() for x in version.split('.')):
        raise UsageError(f'"{what}" parameter must contain only alphanumeric characters or periods')


def query(query_str: str = '[*]') -> list[Firmware]:
    response = request(apiurl.ep_firmware, '/Firmware')
    return response.data.get(query_str, dc=Firmware)


def query_expect_one(query_str: str = '[*]') -> Optional[Firmware]:
    response = request(apiurl.ep_firmware, '/Firmware')
    return response.data.get_one(query_str, dc=Firmware)


def get_by_name(name: str) -> Optional[Firmware]:
    """ Lookup a firmware name - unique template ID supplied during creation """
    if name is None or len(name) == 0:
        raise UsageError('get_by_name: The firmware name is missing')
    return query_expect_one(f"[?name==`{name}`]")


def get_by_guid(guid: str) -> Optional[Firmware]:
    """ Lookup a firmware by GUID """
    if guid is None or len(guid) == 0:
        raise UsageError('get_by_guid: The firmware guid argument is missing')
    return query_expect_one(f"[?guid==`{guid}`]")


def create(
        template_guid: str,
        name: str,
        hw_version: str,
#        sw_version: str,
#        fw_file: str,
        description: Optional[str] = None,
) -> Optional[str]:
    """
    Creates a firmware entry in IoTconnect. Firmware is associated with a template and can have different versions of
    firmware upgrades that can be uploaded and that are associated with it.

    :param template_guid: GUID of the device template.
    :param name: Name of this template. This code must be uppercase alphanumeric an up to 10 characters in length.
    :param hw_version: Hardware Version of the firmware.
    :param hw_version: Hardware Version of the software.
    :param description: Optional description that can be added to the firmware.

    :return: GUID of the newly created template
    """

    _validate_firmware_name(name)
    _validate_version('hw_version', name)
    data = {
        "deviceTemplateGuid": template_guid,
        "firmwareName": name,
        "hardware": hw_version,
        "software": "dummy"
    }
    if description is not None:
        data["FirmwareDescription"] = description

    response = request(apiurl.ep_firmware, '/Firmware', data=data)
    return response.data.get_one(dc=FirmwareCreateResult)

def delete_match_guid(guid: str) -> None:
    """
    Delete the firmware with given template guid.

    :param guid: GUID of the firmware to delete.
    """
    if guid is None:
        raise UsageError('delete_match_guid: The template guid argument is missing')
    response = request(apiurl.ep_firmware, f'/Firmware/{guid}/deprecate', method=HTTPMethod.PUT)
    response.data.get_one()  # we expect data to be empty -- 'data': [] on success


def delete_match_name(name: str) -> None:
    """
    Delete the firmware with given template code.

    :param name: Name of the template to delete.
    """
    if name is None:
        raise UsageError('delete_match_name: The firmware name argument is missing')
    _validate_firmware_name(name)
    fw = get_by_name(name)
    if fw is None:
        raise UsageError(f'delete_match_name: Firmware with name "{name}" not found')
    delete_match_guid(fw.guid)

