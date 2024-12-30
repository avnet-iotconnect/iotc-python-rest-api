"""This module provides IoTConnect authentication functionality."""
import io
import json
from http import HTTPMethod
from typing import Optional, Any

from . import apiurl, credentials
from .apirequest import request, Parser, Headers
from .error import UsageError

def _validate_template_code(what: str, code: str):
    if code is None:
        raise UsageError("%s: code parameter must not be None" % what)
    elif len(code) > 8 or len(code) < 1:
        raise UsageError("%s: code parameter must be between 1 and 8 characters" % what)

def query_all(query_str: str = '*', fields: Optional[list[str]] = None, single_record=False) -> Any:
    response = request(apiurl.ep_device, "/device-template/lookup")
    if single_record:
        return response.data.get_or_raise('[%s]%s' % (query_str, Parser.field_names_query_component(fields)))
    else:
        return response.data.get_all('[%s]%s' % (query_str, Parser.field_names_query_component(fields)))


def get_by_template_code(code: str, fields: Optional[list[str]] = None) -> str:
    """ Lookup an template by template code - unique template ID supplied during creation """
    if code is None:
        raise UsageError('get_by_template_code: The template code argument is missing')
    return query_all('?name == `%s`' % code, fields, single_record=True)

def create(
        template_json_path: str,
        new_template_code: Optional[str] = None,
        new_template_name: Optional[str] = None,
        fields: Optional[list[str]] = None

    ):
    """
    Same as create_from_json_str(), but reads a file from the filesystem located at template_json_path
    :param template_json_path: Path to the template definition file.
    :param new_template_code: Optional new template code to use.
    :param new_template_name: Optional new template name to use.
    :param fields: If provided, field values will be returned in a matching array.
    """
    try:
        with open(template_json_path, 'r') as template_file:
            json_data=template_file.read()
            return create_from_json_str(json_data, new_template_code, new_template_name, fields)
    except OSError:
        raise UsageError("Could not open file %s" % template_json_path)

def create_from_json_str(
        template_json_string: str,
        new_template_code: Optional[str] = None,
        new_template_name: Optional[str] = None,
        fields: Optional[list[str]] = None
    ):
    """
    Create a device template by using a device template json definition as string.
    This variant of the create method allows the user to select a new template code and/or name.
    The user can pass standard query parameters and fields to obtain the new template guid or other fields.

    :param template_json_string: Template definition json as string.
    :param new_template_code: Optional new template code to use.
    :param new_template_name: Optional new template name to use.
    :param fields: If provided, field values will be returned in a matching array.
    """
    try:
        template_obj = json.loads(template_json_string)
    except json.JSONDecodeError as ex:
        raise UsageError(ex)

    if new_template_code is not None:
        template_obj["code"] = new_template_code
    if new_template_name is not None:
        template_obj["name"] = new_template_name
    with io.StringIO() as string_file:
        string_file.write(json.dumps(template_obj))
        string_file.seek(0)
        print("FILEDEBUG: ", string_file.read())
        string_file.seek(0)
        headers = credentials.get_auth_headers()
        del headers[Headers.N_CONTENT_TYPE]
        # data = {"file": string_file.read()} {"file": template_obj}
        f= {'file': open("sample-device-template.json", 'rb')}
        response = request(apiurl.ep_device, "/device-template/quick", headers=headers, files=f)
    return response.data.get_or_raise('%s' % Parser.field_names_query_component(fields))


def delete(guid: str, fields: Optional[list[str]] = None):
    """
    Delete the template with given template code or guid.

    :param guid: GUID of the template to delete.
    :param fields: If provided, field values will be returned in a matching array.
    """
    if guid is None:
        raise UsageError('delete: The template guid argument is missing')
    response = request(apiurl.ep_device, "/device-template/" + guid, method=HTTPMethod.DELETE)
    return response.data.get_or_raise('%s' % Parser.field_names_query_component(fields))

def delete_with_code(code: str, fields: Optional[list[str]] = None):
    """
    Delete the template with given template code or guid.

    :param code: Code of the template to delete. This code must not contain special characters and must be up to 8 characters in length.
    :param fields: If provided, field values will be returned in a matching array.
    """
    if code is None:
        raise UsageError('delete: The template guid argument is missing')
    guid = get_by_template_code(code)
    response = request(apiurl.ep_device, "/device-template/" + guid, method=HTTPMethod.DELETE)
    return response.data.get_or_raise('%s' % Parser.field_names_query_component(fields))
