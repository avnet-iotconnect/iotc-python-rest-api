# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

import os
from dataclasses import dataclass, field
from http import HTTPMethod
from typing import Optional, Dict, List, BinaryIO, Tuple

from . import apiurl, credentials, util
from .apirequest import request, Headers
from .error import UsageError, NotFoundResponseError

# use these types as "type" query parameter when querying firmwares
TYPE_RELEASED = "released"
TYPE_DRAFT = "draft"
TYPE_BOTH = "both"  # either released or draft firmware
FORM_FIELD_FILE_DATA = 'fileData' # Defines the form field that all files must be uploaded as when uploading firmware. Use this for upload_raw()

@dataclass
class Url:
    name: str  # file name associated with this URL (original file name during upload)
    url: str  # file name associated with this URL (original file name during upload)


@dataclass
class Upgrade:
    guid: str
    software: str  # software version
    description: str
    isDraft: str

    # metadata:
    createdDate: str  # ISO string
    createdBy: str  # User GUID
    updatedDate: str  # ISO string
    updatedBy: str  # User GUID

    # not used
    fileName: str  # not used? (probably compatibility with some old API version)
    fileUrl: str  # not used? (probably compatibility with some old API version)

    # urls=[{'url': 'https://pociotconnectblobstorage.blob.core.windows.net/firmware/B1EF896C-77CF-4A5E-A8DF-3F6EEA36B4C8.zip?sv=2020-04-08&se=2025-03-14T20%3A08%3A00Z&sr=b&sp=r&sig=cPwAU5deWCq30jsYflbrXhR1CzCdPiZvwKju6V8q6PM%3D'
    # 'name': 'test.zip'}]))
    urls: List[Url]

    # these fields relate to the Firmware object and are not present when we just create a blank Upgrade
    firmwareguid: str = field(default=None)  # guid of the Firmware object
    name: str = field(default=None)  # name of the firmware object associated with this upgrade
    hardware: str = field(default=None)  # hardware of the firmware object associated with this upgrade
    firmwareUpgradeDescription: str = field(default=None)

    # shortcuts
    def is_draft(self):
        return self.isDraft.lower() == TYPE_DRAFT

    def is_released(self):
        return self.isDraft.lower() ==  TYPE_RELEASED

    def __post_init__(self):
        if self.urls is not None:
            # noinspection PyTypeChecker
            # - complains about item, Url
            self.urls = [Url(**util.normalize_keys(util.filter_dict_to_dataclass_fields(item, Url))) for item in self.urls]
        else:
            self.urls = []


@dataclass
class UpgradeCreateResult:
    newId: str


@dataclass
class UploadResult:
    guid: str


def _validate_version(version: str, what: str):
    if version is None:
        raise UsageError(f'"{what}" parameter must not be None')
    elif len(version) > 20 or len(version) == 0:
        raise UsageError(f'"{what}" parameter must be between 1 and 20 characters')
    elif all(x.isalnum() for x in version.split('.')):
        raise UsageError(f'"{what}" parameter must contain only alphanumeric characters or periods')


def query(query_str: str = '[*]', params: Optional[Dict[str, any]] = None) -> list[Upgrade]:
    response = request(apiurl.ep_firmware, '/firmware-upgrade')
    return response.data.get(query_str=query_str, params=params, dc=Upgrade)


def get_by_guid(guid: str) -> Optional[Upgrade]:
    """ Lookup a firmware by GUID """
    if guid is None or len(guid) == 0:
        raise UsageError('get_by_guid: The firmware guid argument is missing')
    try:
        response = request(apiurl.ep_firmware, f'/firmware-upgrade/{guid}')
        return response.data.get_one(dc=Upgrade)
    except NotFoundResponseError:
        return None


def create(
        firmware_guid: str,
        sw_version: Optional[str] = None,
        description: Optional[str] = None,
) -> UpgradeCreateResult:
    """
    Creates a firmware upgrade for IoTconnect. A firmware upgrade has a version and a firmware file that will be
    associated with a "Firmware" entry.

    :param firmware_guid: GUID of the firmware for which to post this upgrade.
    :param sw_version: Optional Software Version of the upgrade. If not provided, a unique "build version" will be generated based on current time like 250317.185311.483.
    :param description: Optional description that can be added to the firmware upgrade.

    :return: GUID of the newly created upgrade.
    """

    if sw_version is None:
        sw_version = util.generate_unique_timestamp_string()

    _validate_version('sw_version', sw_version)

    data = {
        "firmwareGuid": firmware_guid,
        "software": sw_version
    }
    if description is not None:
        data["description"] = description

    response = request(apiurl.ep_firmware, '/firmware-upgrade', json=data)
    return response.data.get_one(dc=UpgradeCreateResult)


def upload(upgrade_guid: str, file_path: str, file_name: Optional[str] = None, file_open_mode='rb') -> None:
    """
    Uploads the update file that can be pushed to device.
    Call upgrade.create() or firmware.create() first to obtain the firmware upgrade GUID.

    :param upgrade_guid: GUID of the firmware upgrade created by upgrade.create() or firmware.create()
    :param file_path: Path to the file to upload.
    :param file_name: Optional file name what will be used instead of the file name provided in file_path. This file name will be presented to the device with OTA update.
    :param file_open_mode: The mode to pen the file in. Binary by default. Using text mode could eliminate platform dependent newline encoding.

    """

    if file_name is None:
        file_name = os.path.basename(file_path)

    with open(file_path, file_open_mode) as f:
        fw_file = {
            FORM_FIELD_FILE_DATA: (file_name, f)
        }
        data = {
            'fileRefGuid': upgrade_guid,
            'ModuleType': 'firmware',
        }
        headers = credentials.get_auth_headers()
        del headers[Headers.N_ACCEPT]
        response = request(apiurl.ep_file, '/File', method=HTTPMethod.POST, files=fw_file, data=data)
        return response.data.get_one(dc=UploadResult)

def upload_raw(upgrade_guid: str, fw_files: List[Tuple[str, Tuple[str, BinaryIO, str]]]) -> None:
    """
    Uploads the update files that can be pushed to device directly by using the native "requests" python library's
    list of files.
    See https://requests.readthedocs.io/en/latest/user/advanced/#post-multiple-multipart-encoded-files
    When providing the form field name, ensure that it is named "fileData" (replace "images" with "fileData" in the example).
    Call upgrade.create() or firmware.create() first to obtain the firmware upgrade GUID.
    Basic Example:
        ota_files = [
            (upgrade.FORM_FIELD_FILE_DATA', ('firmware.zip', open('../build/output.zip', 'rb'), 'application/octet-stream')), # recommended to octet-stream for any binary file or images (png, jpg and such)
            (upgrade.FORM_FIELD_FILE_DATA', ('models/model.tar.gz', open('models/model.tar.gz', 'rb'), 'application/octet-stream')),
            (upgrade.FORM_FIELD_FILE_DATA', ('config.json', open('config.json', 'rb'), 'application/json')) # recommended to use binary as well for json
        ]
        upload_raw("4695660d-bd7b-492b-be88-4381eaa97659, ota_files)
    IMPORTANT: The caller should NOT close opened files upon exception. Each file will be automatically closed upon exception or success.

    :param upgrade_guid: GUID of the firmware upgrade created by upgrade.create() or firmware.create().
    :param fw_files: Python "requests" package compatible files object. See the function description comment block.

    """

    # validate input ....
    # Ensure at least one file is provided
    if fw_files is None or not isinstance(fw_files, list) or len(fw_files) < 1:
        raise UsageError("At least one file element.")

    # ensure that each entry had form field name called 'fileData' and that each entry has at least 2 elements.
    for entry in fw_files:
        if len(entry) != 2:
            raise UsageError("Each entry must have form field and file data.")
        if entry[0] != FORM_FIELD_FILE_DATA:
            raise UsageError("Each entry's form filed must be named fileData.")

    try:
        data = {
            'fileRefGuid': upgrade_guid,
            'ModuleType': 'firmware',
        }
        headers = credentials.get_auth_headers()
        del headers[Headers.N_ACCEPT]
        response = request(apiurl.ep_file, '/File', method=HTTPMethod.POST, files=fw_files, data=data)
        return response.data.get_one(dc=UploadResult)
    finally:
        # close all opened files
        for entry in fw_files:
            entry[1][1].close()


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
