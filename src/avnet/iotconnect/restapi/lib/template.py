# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

import io
import json
from dataclasses import dataclass, field
from http import HTTPMethod
from typing import Optional, List

from . import apiurl, command, util
from .apirequest import request
from .error import UsageError, ConflictResponseError, NotFoundResponseError
from .query import Query, Page, api_param, run_query


@dataclass
class Template:
    guid: str
    templateCode: str = field(metadata={'aliases': ['code']})
    templateName: str = field(metadata={'aliases': ['name']})
    isEdgeSupport: bool
    isIotEdgeEnable: bool
    authType: int
    tag: str
    messageVersion: str

    # tying to firmware
    firmwareGuid: str = field(default=None)
    firmwareName: str = field(default=None)

    # metadata:
    createdDate: str = field(default=None) # ISO string
    createdBy: str = field(default=None) # User GUID
    updatedDate: str = field(default=None) # ISO string
    updatedBy: str = field(default=None) # User GUID

    # other information
    isValidateTemplate: int = field(default=None)
    isValidEdgeSupport: int = field(default=None)
    isValidType2Support: int = field(default=None)
    isAttachedWithDevice: bool = field(default=None)
    greenGrass: bool = field(default=None)

    commands: List[command.Command] = field(default=None)

    def __post_init__(self):
        if self.commands is not None:
            # noinspection PyTypeChecker
            # - complains about item, upgrade.Upgrade
            self.commands = [command.Command(**util.normalize_keys(util.filter_dict_to_dataclass_fields(item, command.Command))) for item in self.commands]
        else:
            self.commands = []



@dataclass
class TemplateAttribute:
    """A telemetry attribute (data point) of a device template. Fetch with :func:`get_attributes`."""
    guid: str

    localName: str = field(default=None)  # name as it appears in telemetry payloads
    displayName: str = field(default=None)
    description: str = field(default=None)

    dataTypeName: str = field(default=None)  # STRING, NUMBER, BOOLEAN, DECIMAL, OBJECT, ...
    dataTypeGuid: str = field(default=None)
    unit: str = field(default=None)
    dataValidation: str = field(default=None)

    sequence: int = field(default=None)
    tag: str = field(default=None)
    parentTemplateAttributeGuid: str = field(default=None)  # set on children of an OBJECT attribute

    createdDate: str = field(default=None)
    updatedDate: str = field(default=None)

    def normalized(self) -> dict:
        """
        Compact view for "what telemetry can I send": GUIDs, timestamps and ordering
        dropped, ``None``/empty values omitted, keys renamed to the device-template
        JSON vocabulary, e.g. ``{'name': 'temperature', 'type': 'NUMBER', 'unit': 'C'}``.
        """
        out: dict = {}
        if self.localName:
            out['name'] = self.localName
        if self.dataTypeName:
            out['type'] = self.dataTypeName
        if self.unit:
            out['unit'] = self.unit
        if self.description:
            out['description'] = self.description
        if self.displayName and self.displayName != self.localName:
            out['displayName'] = self.displayName
        if self.dataValidation:
            out['validation'] = self.dataValidation
        if self.tag:
            out['tag'] = self.tag
        return out



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

@dataclass
class TemplateQuery(Query):
    """
    Filter options for :func:`list`. All fields optional; only the ones set are sent.
    Inherits pagination (``page``/``page_size``/``sort_by``) from :class:`~.query.Query`.
    """
    name: Optional[str] = api_param(
        'DeviceTemplateName', description='Device template name', examples=['My Template'])
    auth_type: Optional[int] = api_param(
        'AuthType', description='Authentication type (see authtype.AT_* constants)')
    message_version: Optional[str] = api_param(
        'MessageVersion', description='Template message version', examples=['2.1'])
    is_edge: Optional[bool] = api_param('EdgeSupport', description='Only edge templates')
    is_gateway: Optional[bool] = api_param('GatewaySupport', description='Only gateway templates')
    is_low_bandwidth: Optional[bool] = api_param('IsLowBandwidth', description='Only low-bandwidth templates')
    green_grass: Optional[bool] = api_param('greenGrass', description='Only Greengrass templates')
    wireless: Optional[bool] = api_param('wireless', description='Only wireless templates')


def query(query: Optional[TemplateQuery] = None) -> Page[Template]:
    """
    Query device templates, with server-side filtering, sorting and pagination.

    :param query: Filter/paging options. Defaults to the first page, unfiltered.
    :return: A :class:`~.query.Page` of :class:`Template`.
    """
    return run_query(apiurl.ep_device, '/device-template', query or TemplateQuery(), Template)


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


def get_attributes(template_guid: str) -> List[TemplateAttribute]:
    """
    Telemetry attribute schema of a template, ordered by ``sequence``; empty if the
    template has none or does not exist. Complements :func:`get_by_guid`, which
    returns metadata and ``commands`` but not attributes.
    """
    if template_guid is None:
        raise UsageError('get_attributes: the template_guid argument is required')

    try:
        # large pageSize so the schema is not truncated on big templates
        response = request(apiurl.ep_device, f'/template-attribute/{template_guid}', params={'pageSize': 1000})
        attrs = response.data.get(dc=TemplateAttribute)
        # endpoint rejects sortBy, so order client-side; attributes without a sequence sort last
        attrs.sort(key=lambda a: a.sequence if a.sequence is not None else float('inf'))
        return attrs
    except ConflictResponseError:
        return []


def get_attributes_normalized(template_guid: str) -> List[dict]:
    """:func:`get_attributes` passed through :func:`normalize_attributes`."""
    return normalize_attributes(get_attributes(template_guid))

def normalize_attributes(attributes: List[TemplateAttribute]) -> List[dict]:
    """
    :meth:`TemplateAttribute.normalized` applied across a template, with children of
    ``OBJECT`` attributes nested under their parent's ``attributes`` list. Input order
    is preserved.
    """
    nodes = {a.guid: a.normalized() for a in attributes}
    roots: List[dict] = []
    for a in attributes:
        parent = nodes.get(a.parentTemplateAttributeGuid)
        if parent is not None:
            parent.setdefault('attributes', []).append(nodes[a.guid])
        else:
            roots.append(nodes[a.guid])
    return roots

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
