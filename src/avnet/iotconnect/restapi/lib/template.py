# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

import io
import json
from dataclasses import dataclass
from http import HTTPMethod
from typing import Optional, Dict

from . import apiurl
from .apirequest import request
from .error import UsageError, ConflictResponseError, NotFoundResponseError

# Authentication types. See https://docs.iotconnect.io/iotconnect/sdk/message-protocol/device-message-2-1/reference-table/#authtypes
AT_CA_SIGNED = 2
AT_SELF_SIGNED = 3
AT_TPM = 4
AT_SYMMETRIC_KEY = 5
AT_CA_INDIVIDUAL = 7


@dataclass
class Template:
    guid: str
    templateCode: str
    templateName: str
    isEdgeSupport: bool
    isIotEdgeEnable: bool
    authType: int
    tag: str
    messageVersion: str
    greenGrass: bool


@dataclass
class TemplateCreateResult:
    deviceTemplateGuid: str


def _validate_template_code(code: str):
    if code is None:
        raise UsageError('"code" parameter must not be None')
    elif len(code) > 10 or len(code) == 0:
        raise UsageError('"code" parameter must be between 1 and 10 characters')
    elif not code.isalnum():
        raise UsageError('"code" parameter must contain only alphanumeric characters')

def query(query_str: str = '[*]', params: Optional[Dict[str,any]] = None) -> list[Template]:
    response = request(apiurl.ep_firmware, '/device-template')
    return response.data.get(query_str=query_str, params=params, dc=Template)

def get(params: dict[str, any]) -> Optional[Template]:
    try:
        response = request(apiurl.ep_device, '/device-template', params=params)
        return response.data.get_one(dc=Template)
    except ConflictResponseError:
        return None


def get_by_template_code(template_code: str) -> Optional[Template]:
    """ Lookup an template by template code - unique template ID supplied during creation """
    _validate_template_code(template_code)
    try:
        response = request(apiurl.ep_device, f'/device-template/template-code/{template_code}')
        return response.data.get_one(dc=Template)
    except ConflictResponseError:
        return None


def get_by_guid(guid: str) -> Optional[Template]:
    """ Lookup a template by GUID """
    try:
        response = request(apiurl.ep_device, f'/device-template/{guid}')
        return response.data.get_one(dc=Template)
    except NotFoundResponseError:
        return None


def create(
        template_json_path: str,
        new_template_code: Optional[str] = None,
        new_template_name: Optional[str] = None

) -> TemplateCreateResult:
    """
    Same as create_from_json_str(), but reads a file from the filesystem located at template_json_path

    :param template_json_path: Path to the template definition file.
    :param new_template_code: Optional new template code to use. This code must be alphanumeric an up to 10 characters in length.
    :param new_template_name: Optional new template name to use.

    :return: TemplateCreateResult with newId populated with guid of the newly created template
    """
    try:
        with open(template_json_path, 'r') as template_file:
            json_data = template_file.read()
            return create_from_json_str(json_data, new_template_code, new_template_name)
    except OSError:
        raise UsageError(f'Could not open file {template_json_path}')


def create_from_json_str(
        template_json_string: str,
        new_template_code: Optional[str] = None,
        new_template_name: Optional[str] = None
) -> TemplateCreateResult:
    """
    Create a device template by using a device template json definition as string.
    This variant of the create method allows the user to select a new template code and/or name.
    The user can pass standard query parameters and fields to obtain the new template guid or other fields.

    :param template_json_string: Template definition json as string.
    :param new_template_code: Optional new template code to use. This code must be alphanumeric an up to 10 characters in length.
    :param new_template_name: Optional new template name to use.

    :return: TemplateCreateResult with newId populated with guid of the newly created template
    """

    try:
        template_obj = json.loads(template_json_string)
    except json.JSONDecodeError as ex:
        raise UsageError(ex)

    if new_template_code is not None:
        _validate_template_code(new_template_code)
        template_obj["code"] = new_template_code
    if new_template_name is not None:
        template_obj["name"] = new_template_name

    # now back to converting it into a file for the upload
    with io.StringIO() as string_file:
        # separators = compress the json
        new_template_str = json.dumps(template_obj, separators=(',', ':'))
        # try fix the template delete issue with some invalid xml when deleting by forcing windows newlines
        string_file.write(new_template_str.replace('\r\n', '\n').replace('\n', '\r\n'))
        string_file.seek(0)  # reset the file pointer after writing
        f = {"file": string_file}
        response = request(apiurl.ep_device, '/device-template/quick', files=f)
    res = response.data.get_one(dc=TemplateCreateResult)
    if res is not None and res.deviceTemplateGuid is not None:
        res.deviceTemplateGuid = res.deviceTemplateGuid.upper()
    return res


def delete_match_guid(guid: str) -> None:
    """
    Delete the template with given template guid.

    :param guid: GUID of the template to delete.
    """
    if guid is None:
        raise UsageError('delete_match_guid: The template guid argument is missing')

    response = request(apiurl.ep_device, f'/device-template/{guid}', method=HTTPMethod.DELETE)
    response.data.get_one()  # we expect data to be empty -- 'data': [] on success


def delete_match_code(code: str) -> None:
    """
    Delete the template with given template code.

    :param code: Template code of the template to delete.
    """
    if code is None:
        raise UsageError('delete_match_code: The template code argument is missing')
    _validate_template_code(code)
    t = get_by_template_code(code)
    if t is None:
        raise NotFoundResponseError(f'delete_match_code: Template with code "{code}" not found')
    delete_match_guid(t.guid)
