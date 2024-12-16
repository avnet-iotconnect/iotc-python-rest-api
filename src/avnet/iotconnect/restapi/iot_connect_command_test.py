"""This module performs partial IoTConnect OTA FW Update."""

import argparse
import requests
import json

from common.authentication import authenticate
from common.constants import (
    API_DEVICE_URL,
    DEVICE_SOUND_CLASS,
    COMMAND_SEND,
    S3_ENDPOINT_HEADER,
    S3_APIKEY_HEADER
)
from common.check_status import check_status, BadHttpStatusException
from common.common import (
    get_template_guid,
    get_entity_guid,
    get_command_guid
)


def iot_connect_rule():
    """Create webhook rule in IoTConnect"""
    endpoint_url = "https://ycla29ntre.execute-api.us-west-2.amazonaws.com/prod/webhook"
    api_key = "A5A5A5A5A5A5-A5A5A5A5A5A5-A5A5A5A5A5A5"
    args = parse_arguments()
    access_token = authenticate(args.username, args.password, args.solution_key)
    print(f"Successful login - send command to the device {DEVICE_SOUND_CLASS}")
    template_guid = get_template_guid(DEVICE_SOUND_CLASS, access_token)
    entity_guid = get_entity_guid(args.entity_name, access_token)
    command_guid = get_command_guid(template_guid, access_token)
    send_command(command_guid, endpoint_url, api_key, entity_guid, access_token)


def parse_arguments() -> argparse.Namespace:
    """
    Parse CLI arguments - 4 obligatory positional argiments
     - username
     - password
     - solution key
     - entity name
    """
    print("Parse command line arguments")
    parser=argparse.ArgumentParser()
    parser.add_argument("username")
    parser.add_argument("password")
    parser.add_argument("solution_key")
    parser.add_argument("entity_name")
    return parser.parse_args()

def send_command(command_guid: str, endpoint_url: str, api_key: str, entity_guid: str, access_token: str):
    """Create device in IoTConnect from given data"""

    parameter_value = {
        S3_ENDPOINT_HEADER: endpoint_url,
        S3_APIKEY_HEADER: api_key,
    }

    parameter_value_json = json.dumps(parameter_value) 

    data = {
        "commandGuid": command_guid,
        "entityGuid": entity_guid,
        "applyTo": 1,
        "isRecursive": False,
        "parameterValue": parameter_value_json
    }

    headers = {
        "Content-type": "application/json",
        "Accept": "*/*",
        "Authorization": access_token
    }
    response = requests.post(API_DEVICE_URL + COMMAND_SEND, json = data, headers = headers)

    check_status(response)
    print(f"Command sent")

def get_rule_guid_from_response(response: requests.Response) -> str:
    """Returns template guid from the response"""
    response_json = response.json()
    # print(response_json)
    guid = response_json["data"][0]["ruleGuid"]
    return guid

if __name__ == "__main__":
    iot_connect_rule()
