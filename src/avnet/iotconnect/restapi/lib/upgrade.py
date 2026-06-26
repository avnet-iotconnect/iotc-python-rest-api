# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

import os
from dataclasses import dataclass, field
from http import HTTPMethod
from typing import Optional, List

from . import apiurl, credentials, util, entity
from .apirequest import request, Headers
from .error import UsageError, NotFoundResponseError
from .query import Query, Page, api_param, run_query, is_guid

# use these types as "type" query parameter when querying firmwares
TYPE_RELEASED = "Released"
TYPE_DRAFT = "Draft"
TYPE_BOTH = "both"  # either released or draft firmware


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


    urls: List[Url] = field(default=None)


    # these fields relate to the Firmware object and are not present when we just create a blank Upgrade
    firmwareguid: str = field(default=None)  # guid of the Firmware object
    name: str = field(default=None)  # name of the firmware object associated with this upgrade
    hardware: str = field(default=None)  # hardware of the firmware object associated with this upgrade
    firmwareUpgradeDescription: str = field(default=None)

    # not used (fileUrl only on azure)
    fileName: str = field(default=None) # not used? (probably compatibility with some old API version)
    fileUrl: str = field(default=None) # not used? (probably compatibility with some old API version)


    # shortcuts
    def is_draft(self):
        return self.isDraft== TYPE_DRAFT

    def is_released(self):
        return self.isDraft ==  TYPE_RELEASED

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


def _resolve_firmware(value: str) -> str:
    """Accept a firmware GUID or firmware name; return the GUID."""
    if is_guid(value):
        return value
    from . import firmware  # lazy: firmware imports upgrade, so import here to avoid a cycle
    fw = firmware.get_by_name(value)
    if fw is None:
        raise UsageError(f'No firmware found with name "{value}"')
    return fw.guid


@dataclass
class UpgradeQuery(Query):
    """
    Filter options for :func:`list`. All fields optional; only the ones set are sent.
    Inherits pagination (``page``/``page_size``/``sort_by``) from :class:`~.query.Query`.
    """
    firmware: Optional[str] = api_param(
        'firmwareguid', resolver=_resolve_firmware,
        description='Filter by firmware, given as its name or GUID')
    type: Optional[str] = api_param(
        'type', description='Upgrade type: "Released", "Draft", or "both" (TYPE_* constants)')
    search: Optional[str] = api_param('searchText', description='Free-text search')


def query(query: Optional[UpgradeQuery] = None) -> Page[Upgrade]:
    """
    Query firmware upgrades, with server-side filtering, sorting and pagination.

    :param query: Filter/paging options. Defaults to the first page, unfiltered.
    :return: A :class:`~.query.Page` of :class:`Upgrade`.
    """
    return run_query(apiurl.ep_firmware, '/firmware-upgrade', query or UpgradeQuery(), Upgrade)


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
    Call upload() multiple times on to assign multiple files.

    :param upgrade_guid: GUID of the firmware upgrade created by upgrade.create() or firmware.create()
    :param file_path: Path to the file to upload.
    :param file_name: Optional file name what will be used instead of the file name provided in file_path. This file name will be presented to the device with OTA update.
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
    Publishes the upgrade. In effect, it changes the Upgrade.isDraft from "Draft" to "Released".

    :param upgrade_guid: GUID of the firmware upgrade.
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
