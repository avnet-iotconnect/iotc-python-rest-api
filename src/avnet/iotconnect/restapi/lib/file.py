# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

from dataclasses import dataclass, field
from http import HTTPMethod
from typing import Optional, List

from . import apiurl
from .apirequest import request
from .error import UsageError, ConflictResponseError

FILE_MODULE_DEVICEIMAGE = 'deviceimage'
FILE_MODULE_COMPANYLOGO = 'companylogo'
FILE_MODULE_FIRMWARE = 'firmware'
FILE_MODULE_USERPROFILE = 'userprofile'
FILE_MODULE_IMPORTBATCH = 'importbatch'
FILE_MODULE_SOLUTIONIMAGE = 'solutionimage'
FILE_MODULE_DEVICECERTIFICATE = 'devicecertificate'
FILE_MODULE_CUSTOM = 'custom'
FILE_MODULE_MODULE = 'module'
FILE_MODULE_WIDGETIMAGE = 'widgetimage'
FILE_MODULE_DEVICEUPDATE = 'deviceupdate'
FILE_MODULE_GGCOMPONENTARTIFACT = 'ggcomponentartifact'
FILE_MODULE_GGCOMPONENTRECIPE = 'ggcomponentrecipe'

FILE_MODULE_TYPES = (
    FILE_MODULE_DEVICEIMAGE,
    FILE_MODULE_COMPANYLOGO,
    FILE_MODULE_FIRMWARE,
    FILE_MODULE_USERPROFILE,
    FILE_MODULE_IMPORTBATCH,
    FILE_MODULE_SOLUTIONIMAGE,
    FILE_MODULE_DEVICECERTIFICATE,
    FILE_MODULE_CUSTOM,
    FILE_MODULE_MODULE,
    FILE_MODULE_WIDGETIMAGE,
    FILE_MODULE_DEVICEUPDATE,
    FILE_MODULE_GGCOMPONENTARTIFACT,
    FILE_MODULE_GGCOMPONENTRECIPE,
)


@dataclass
class File:
    guid: str
    file: str
    name: str
    tag: str = field(default=None)
    createdDate: str = field(default=None)
    state: str = field(default=None)

@dataclass
class FileLookupResult:
    fileData: List[File]


def get_by_module_type_and_guid(module_type: str, file_ref_guid: str) -> List[File]:
    """
    :param module_type: Module that this file ref was associated with during creation/upload.
    :param file_ref_guid: Reference GUID of that the file object was originally created with.
    """
    if file_ref_guid is None:
        raise UsageError('get_by_module_type_and_guid: file_ref_guid argument is required')
    if module_type is None:
        raise UsageError('get_by_module_type_and_guid: module_type argument is required')
    # if module_type not in FILE_MODULE_TYPES:
    #    raise UsageError('get_by_module_type_and_guid: module_type argument is invalid')

    try:
        response = request(apiurl.ep_file, f'/File/{module_type}/{file_ref_guid}')
        ret = response.data.get(expr='fileData')
        return [File(**x) for x in ret]
    except ConflictResponseError:
        return []


def create(
        module_type: str,
        file_ref_guid: str,
        file_path: str,
):
    """

    Upload a file for a given module type with associated file_ref_guid.
    Recording the File Reference GUID (or having a known fixed value time) is the only way to obtain to a file created by create().
    Recording the returned File GUID can be used to subsequently delete this object.
    If using the "custom" module, ensure that you created one in your account. Navigate in the UI to:
    Settings -> Configurations, enable the Custom Filet Storage
    toggle if it is not already enable, give it a "Storage name" and then Save it.

    :param module_type: Module that this file ref was associated with during creation/upload.
    :param file_ref_guid: This is the File Reference GUID of an object (or your own generated guid) to which the file created will
        be associated with. This is NOT the same as the GUID of the file that will be returned by creating.

        See this list to find out what File Reference GUID may refer to:
            deviceGuid for deviceimage
            companyGuid for companylogo
            firmwareUpgradeGuid for firmware
            userGuid for userprofile
            importBatchGuid for importbatch
            solutionGuid for solutionimage
            deviceCertificateGuid for devicecertificate
            any guid for custom
            moduleGuid for module
            dashboardWidgetGuid for widgetimage
            dashboardBackgroundGuid for dashboardimage

    :param file_path: Path to the file to upload.

    """

    with open(file_path, 'rb') as f:
        fw_file = {
            'fileData': f
        }
        data = {
            ""
            "fileRefGuid": file_ref_guid,
            "ModuleType": module_type
        }
        print(data)
        response = request(apiurl.ep_file, '/File',  method=HTTPMethod.POST, files=fw_file, data=data)
        return response.data.get_one()



def delete_match_guid(module_type: str, file_guid: str) -> None:
    """
    Delete the file with given module_type and file GUID (NOT the File Reference GUID).

    :param module_type: Module that this file ref was associated with during creation/upload.
    :param file_guid: GUID the actual file (not the File Reference GUID).

    """
    if file_guid is None:
        raise UsageError('delete_match_guid: The template guid argument is missing')
    response = request(apiurl.ep_file, f'/File/{module_type}/{file_guid}', method=HTTPMethod.DELETE)
    response.data.get_one()  # we expect data to be empty -- 'data': [] on success
