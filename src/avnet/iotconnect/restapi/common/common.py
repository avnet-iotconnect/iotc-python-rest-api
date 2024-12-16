"""This module provides some useful commands for IoTConnect REST API."""

import requests

from .constants import (
    API_DEVICE_URL,
    DEVICE_TEMPLATE_LIST,
    API_USER_URL,
    ENTITY_LIST,
    DEVICE_CREATE,
    RULE,
    COMMAND,
    CREDS_S3_COMMAND,
    API_FW_URL,
    FW_ADD
)
from .check_status import check_status


def get_template_guid(template_name: str, access_token: str) -> str:
    """Returns template guid from the IoTConnect"""
    headers = {
        "Authorization": access_token
    }
    params = {
        "DeviceTemplateName": template_name
    }
    response = requests.get(API_DEVICE_URL + DEVICE_TEMPLATE_LIST, headers = headers, params = params)
    check_status(response)
    response_json = response.json()
    template_guid = response_json["data"][0]["guid"]
    return template_guid

def get_device_guid(device_name: str, access_token: str) -> str:
    """Returns device guid from the IoTConnect"""
    headers = {
        "Authorization": access_token
    }
    params = {
        "UniqueId": device_name
    }
    response = requests.get(API_DEVICE_URL + DEVICE_CREATE, headers = headers, params = params)
    check_status(response)
    response_json = response.json()
    device_guid = response_json["data"][0]["guid"]
    return device_guid

def get_entity_guid(entity_name: str, access_token: str) -> str:
    """Returns entity guid for the provided entity name"""
    headers = {
        "Authorization": access_token
    }
    response = requests.get(API_USER_URL + ENTITY_LIST, headers = headers)
    check_status(response)
    response_json = response.json()
    entities = response_json["data"]

    entity_guid = ""
    for entity in entities:
        if entity["name"] == entity_name:
            entity_guid = entity["guid"]
            break
    
    print(f"Entity guid for {entity_name} entity is {entity_guid}")

    return entity_guid

def get_rule_guid(device_name: str, access_token: str) -> str:
    """Returns device guid from the IoTConnect"""
    headers = {
        "Authorization": access_token
    }
    params = {
        "name": device_name
    }
    response = requests.get(API_DEVICE_URL + RULE, headers = headers, params = params)
    check_status(response)
    response_json = response.json()
    # print(response_json)
    rule_guid = ""

    if (len(response_json["data"]) > 0):
        rule_guid = response_json["data"][0]["guid"]

    return rule_guid

def get_command_guid(template_guid: str, access_token: str) -> str:
    """Returns device guid from the IoTConnect"""
    headers = {
        "Authorization": access_token
    }
    params = {
        "deviceTemplateGuid": template_guid
    }
    response = requests.get(API_DEVICE_URL + COMMAND + template_guid, headers = headers, params = params)
    check_status(response)
    response_json = response.json()
    # print(response_json)
    command_guid = ""

    for commands in response_json["data"]:
        if commands["command"] == CREDS_S3_COMMAND:
            command_guid = commands["guid"]
            print(f"S3 creds command guid {command_guid}")
            return command_guid

    print("Command not found")

    return command_guid

def get_firmware_guid(template_name: str, access_token: str) -> str:
    """Returns firmware guid from the IoTConnect"""
    headers = {
        "Authorization": access_token
    }
    params = {
        "TemplateName": template_name
    }
    response = requests.get(API_FW_URL + FW_ADD, headers = headers, params = params)
    check_status(response)
    response_json = response.json()
    print(response_json)

    fw_guid = ""

    if (len(response_json["data"]) > 0):
        fw_guid = response_json["data"][0]["guid"]

    return fw_guid
