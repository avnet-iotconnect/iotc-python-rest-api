"""This module performs IoTConnect rule creation Update."""

import argparse
import requests

from common.authentication import authenticate
from common.constants import (
    API_DEVICE_URL,
    API_EVENT_URL,
    DEVICE_SOUND_CLASS,
    RULE,
    USER,
    SEVERETY_LOOKUP,
    API_USER_URL
)
from common.check_status import check_status, BadHttpStatusException
from common.common import (
    get_template_guid,
    get_rule_guid,
    get_entity_guid
)


def iot_connect_rule():
    """Create webhook rule in IoTConnect"""
    webhook_url = "https://0ozzw8hv4e.execute-api.us-west-2.amazonaws.com/prod/webhook"
    args = parse_arguments()
    access_token = authenticate(args.username, args.password, args.solution_key)
    print("Successful login - now create webhook Rule.")
    template_guid = get_template_guid(DEVICE_SOUND_CLASS, access_token)
    entity_guid = get_entity_guid(args.entity_name, access_token)
    delete_rule_if_exists(DEVICE_SOUND_CLASS, access_token)
    creat_rule(DEVICE_SOUND_CLASS, webhook_url, template_guid, entity_guid, args.entity_name, access_token)


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

def delete_rule_if_exists(rule_name: str, access_token: str):
    # Delete rule if exists
    guid = get_rule_guid(rule_name, access_token)
    if (len(guid) == 0):
        print("Rule does not exist")
        return
    else:
        print(f"Found rule with guid {guid}.\r\nNow delete it.")
        delete_rule(guid, access_token)

def delete_rule(guid: str, access_token: str):
    # Delete rule
    headers = {
        "Content-type": "application/json",
        "Accept": "*/*",
        "Authorization": access_token
    }
    response = requests.delete(API_DEVICE_URL + RULE + "/" + guid, headers = headers)
    check_status(response)
    print("Rule deleted")

def get_user_role(entity_name: str, access_token: str) -> dict:
    """Get first role and user guids from the IoTConnect"""
    headers = {
        "Authorization": access_token
    }
    params = {
        "Entity": entity_name
    }
    response = requests.get(API_USER_URL + USER, headers = headers, params = params)
    check_status(response)
    response_json = response.json()
    

    user = response_json["data"][0]["guid"]
    role = response_json["data"][0]["roleGuid"]

    user_role = {
        "user": user,
        "role": role
    }
    print("user = " + user)
    print("role = " + role)
    return user_role


def creat_rule(rule_name: str, webhook_url: str, template_guid: str, entity_guid: str, entity_name: str, access_token: str):
    """Create device in IoTConnect from given data"""
    major_guid = get_major_guid(access_token)
    user_role = get_user_role(entity_name, access_token)

    data = {
        "ruleType": 1,
        "templateGuid": template_guid,
        "name": rule_name,
        "severityLevelGuid": major_guid,
        "conditionText": 'requests3 = "True"',
        "ignorePreference": False,
        "applyTo": 1,
        "entityGuid": entity_guid,
        "deliveryMethod": ["WebHook"],
        "url": webhook_url,
        "webhookMsgFormat": 2,
        "roles": [user_role["role"]],
        "users": [user_role["user"]],
    }

    headers = {
        "Content-type": "application/json",
        "Accept": "*/*",
        "Authorization": access_token
    }
    response = requests.post(API_DEVICE_URL + RULE, json = data, headers = headers)

    check_status(response)
    rule_guid = get_rule_guid_from_response(response)
    print(f"Rule {rule_name} created with guid {rule_guid}")

def get_rule_guid_from_response(response: requests.Response) -> str:
    """Returns template guid from the response"""
    response_json = response.json()
    # print(response_json)
    guid = response_json["data"][0]["ruleGuid"]
    return guid

def get_major_guid(access_token: str) -> str:
    """Returns major severty level guid from the IoTConnect"""
    headers = {
        "Authorization": access_token
    }
    response = requests.get(API_EVENT_URL + SEVERETY_LOOKUP, headers = headers)
    check_status(response)
    response_json = response.json()
    # print(response_json)

    for sev_level in response_json["data"]:
        if sev_level["SeverityLevel"] == "Major":
            print(f"Found Major severety level guid {sev_level["guid"]}")
            return sev_level["guid"]

    print("Major severety level guid was not found")
    return ""

if __name__ == "__main__":
    iot_connect_rule()
