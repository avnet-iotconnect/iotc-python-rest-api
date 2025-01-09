"""This module provides IoTConnect authentication functionality."""
import os
from dataclasses import dataclass
from http import HTTPMethod
from typing import Optional

from . import apiurl
from .apirequest import request
from .error import UsageError


@dataclass
class Upgrade:
    guid: str


@dataclass
class Upload:
    guid: str


@dataclass
class UpgradeCreateResult:
    newId: str


@dataclass
class UploadResult:
    newId: str


def _validate_version(version: str, what: str):
    if version is None:
        raise UsageError(f'"{what}" parameter must not be None')
    elif len(version) > 20 or len(version) == 0:
        raise UsageError(f'"{what}" parameter must be between 1 and 20 characters')
    elif all(x.isalnum() for x in version.split('.')):
        raise UsageError(f'"{what}" parameter must contain only alphanumeric characters or periods')


def query(query_str: str = '[*]') -> list[Upgrade]:
    response = request(apiurl.ep_firmware, '/firmware-upgrade')
    return response.data.get(query_str, dc=Upgrade)


def query_expect_one(query_str: str = '[*]') -> Optional[Upgrade]:
    response = request(apiurl.ep_firmware, '/firmware-upgrade')
    return response.data.get_one(query_str, dc=Upgrade)


def get_by_name(name: str) -> Optional[Upgrade]:
    """ Lookup a firmware name - unique template ID supplied during creation """
    if name is None or len(name) == 0:
        raise UsageError('get_by_name: The firmware name is missing')
    return query_expect_one(f"[?name==`{name}`]")


def get_by_guid(guid: str) -> Optional[Upgrade]:
    """ Lookup a firmware by GUID """
    if guid is None or len(guid) == 0:
        raise UsageError('get_by_guid: The firmware guid argument is missing')
    return query_expect_one(f"[?guid==`{guid}`]")


def create(
        firmware_guid: str,
        sw_version: str,
        description: Optional[str] = None,
) -> UpgradeCreateResult:
    """
    Creates a firmware upgrade for IoTconnect. A firmware upgrade has a version and a firmware file that will be
    associated with a "Firmware" entry.

    :param firmware_guid: GUID of the firmware for which to post this upgrade.
    :param sw_version: Software version of the upgrade.
    :param description: Optional description that can be added to the firmware upgrade.

    :return: GUID of the newly created upgrade.
    """

    _validate_version('sw_version', sw_version)
    data = {
        "firmwareGuid": firmware_guid,
        "software": sw_version
    }
    if description is not None:
        data["description"] = description

    response = request(apiurl.ep_firmware, '/firmware-upgrade', data=data)
    return response.data.get_one(dc=UpgradeCreateResult)


def upload(upgrade_guid: str, file_path: str, file_name: Optional[str] = None, file_open_mode='rb') -> None:
    """
    Uploads the update file that can be pushed to device.
    Call upgrade.create() or firmware.create() first to obtain the firmware upgrade GUID.

    :param upgrade_guid: GUID of the firmware upgrade created by upgrade.create() or firmware.create()
    :param file: Path to the file to upload.
    :param file_open_mode: The mode to pen the file in. Binary by default. Using text mode could eliminate platform dependent newline encoding.

    """

    if file_name is None:
        file_name = os.path.basename(file_path)

    with open(file_path, file_open_mode) as f:
        fw_file = {
            'fileData': (file_name, f)
        }

        data = {
            'fileRefGuid': upgrade_guid,
            'ModuleType': 'firmware',
        }
        response = request(apiurl.ep_file, '/File', method=HTTPMethod.POST, files=fw_file, data=data)
        return response.data.get_one(dc=UploadResult)

def publish(upgrade_guid: str) -> None:
    """
    Uploads the update file that can be pushed to device.
    Call upgrade.create() or firmware.create() first to obtain the firmware upgrade GUID.

    :param upgrade_guid: GUID of the firmware upgrade created by upgrade.create() or firmware.create()
    :param file: Path to the file to upload.
    :param file_open_mode: The mode to pen the file in. Binary by default. Using text mode could eliminate platform dependent newline encoding.

    """

    request(apiurl.ep_firmware, f'/firmware-upgrade/{upgrade_guid}/publish', method=HTTPMethod.PUT)


def delete_match_guid(guid: str) -> None:
    """
    Delete the firmware with given template guid.

    :param guid: GUID of the firmware to delete.
    """
    if guid is None:
        raise UsageError('delete_match_guid: The template guid argument is missing')
    response = request(apiurl.ep_firmware, f'/firmware-upgrade/{guid}', method=HTTPMethod.DELETE)
    response.data.get_one()  # we expect data to be empty -- 'data': [] on success
