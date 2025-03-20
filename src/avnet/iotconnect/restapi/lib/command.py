# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

from dataclasses import dataclass, field
from typing import List, Any, Optional

from . import apiurl
from .apirequest import request
from .error import UsageError, ConflictResponseError


@dataclass
class Command:
    guid: str
    command: str
    name: str
    requiredParam: bool
    requiredAck: bool
    isOTACommand: bool
    isTemplateCommandUsed: bool
    updatedDate: str
    createdDate: str
    tag: str = field(default=None)
    devices: Any = field(default=None)


def get_all(template_guid: str) -> List[Command]:
    """
    Returns all commands associated with a specified template (GUID).

    :param template_guid: GUID od the template that defines this command.
    """
    if template_guid is None:
        raise UsageError('get_by_template_guid: get_by_template_guid argument is required')

    try:
        response = request(apiurl.ep_device, f'/template-command/{template_guid}')
        ret = response.data.get()
        return [Command(**x) for x in ret]
    except ConflictResponseError:
        return []


def get_with_name(template_guid: str, command: str) -> Optional[Command]:
    """
    Returns a command with given command name (not command "custom name" named just "name" in the device template.json) but the actual command
    name named "command" in template.json.

    :param template_guid: GUID od the template that defines this command.
    :param command: Unique command name (not the descriptive name)
    :return:
    """
    for cmd in get_all(template_guid):
        if cmd.command == command:
            return cmd
    return None


def send(command_guid: str, device_guid: str, parameters: str = None) -> None:
    """
    Sends a command to sa specific device with provided (optional) command parameters/arguments.

    :param command_guid: GUID of the command obtained by get_*() functions.
    :param device_guid: GUID of the device to send the command to.
    :param parameters: Command parameters or "command arguments".
    """

    if command_guid is None:
        raise UsageError('command_guid: device_guid argument is required')
    if device_guid is None:
        raise UsageError('execute: device_guid argument is required')

    if parameters is None:
        parameters = ""

    data = {
        "commandGuid": command_guid,
        "parameterValue": parameters
    }
    response = request(apiurl.ep_device, f'/template-command/device/{device_guid}/send', json=data)
    return response.data.get_one()
