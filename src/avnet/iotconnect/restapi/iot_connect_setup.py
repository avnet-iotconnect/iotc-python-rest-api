"""This module performs partial IoTConnect solution setup for audio classification demo."""

import argparse
import requests

from common.authentication import authenticate
from common.constants import (
    DEVICE_TEMPLATES_DIR,
    TEMPLATES_TAIL,
    API_DEVICE_URL,
    DEVICE_TEMPLATE_CREATE,
    DEVICE_TEMPLATE_ALREADY_EXISTS,
    DEVICE_ALREADY_EXISTS,
    DEVICE_SOUND_GEN,
    DEVICE_SOUND_CLASS,
    DEVICE_CREATE
)
from common.check_status import check_status, BadHttpStatusException
from common.common import (
    get_template_guid,
    get_entity_guid,
    get_device_guid
)


def iot_connect_setup():
    """Perform IoTConnect solution setup"""
    args = parse_arguments()
    access_token = authenticate(args.username, args.password, args.solution_key)
    print("Successful login - now create device templates.")
    entity_guid = get_entity_guid(args.entity_name, access_token)
    soundclass_temp_guid = create_device_template(access_token, DEVICE_SOUND_CLASS)
    create_device_with_own_certificate(args.certificate, soundclass_temp_guid, entity_guid, access_token)
    soundgen_temp_guid = create_device_template(access_token, DEVICE_SOUND_GEN)
    create_device_with_aws_certificate(soundgen_temp_guid, entity_guid, access_token)

def parse_arguments() -> argparse.Namespace:
    """
    Parse CLI arguments - 4 obligatory positional argiments
     - username
     - password
     - solution key
     - device certificate
     - entity name
    """
    print("Parse command line arguments")
    parser=argparse.ArgumentParser()
    parser.add_argument("username")
    parser.add_argument("password")
    parser.add_argument("solution_key")
    parser.add_argument("entity_name")
    parser.add_argument("certificate")
    return parser.parse_args()



def get_template_guid_from_response(response: requests.Response) -> str:
    """Returns template guid from the response"""
    response_json = response.json()
    guid = response_json["data"][0]["deviceTemplateGuid"]
    return guid

def get_device_guid_from_response(response: requests.Response) -> str:
    """Returns template guid from the response"""
    response_json = response.json()
    guid = response_json["data"][0]["newid"]
    return guid

def create_device_template(access_token: str, template_name: str) -> str:
    """Create devices templates in IoTConnect"""
    headers = {
        "Authorization": access_token
    }

    files = {'file': open(DEVICE_TEMPLATES_DIR + template_name + TEMPLATES_TAIL, 'rb')}
    response = requests.post(API_DEVICE_URL + DEVICE_TEMPLATE_CREATE, files = files, headers = headers)

    template_guid = ""
    try: 
        check_status(response)
        template_guid = get_template_guid_from_response(response)
        print(f"Template {template_name} created with guid {template_guid}")
    except BadHttpStatusException as e:
        response_json = response.json()
        error_type = response_json["error"][0]["param"]
        if DEVICE_TEMPLATE_ALREADY_EXISTS == error_type:
            template_guid = get_template_guid(template_name, access_token)
            print(f"Template {template_name} already exists with guid {template_guid}")
        else:
            raise e

    return template_guid

def create_device_with_own_certificate(certificate: str, soundclass_temp_guid: str, entity_guid: str, access_token: str):
    """Create device with own certificate in IoTConnect"""
    data = {
        "entityGuid": entity_guid,
        "uniqueId": DEVICE_SOUND_CLASS,
        "deviceTemplateGuid": soundclass_temp_guid,
        "certificateText": certificate,
        "displayName": DEVICE_SOUND_CLASS
    }
    create_device(data, access_token)

def create_device_with_aws_certificate(soundgen_temp_guid: str, entity_guid: str, access_token: str):
    """Create device with aws certificate in IoTConnect"""
    data = {
        "entityGuid": entity_guid,
        "uniqueId": DEVICE_SOUND_GEN,
        "deviceTemplateGuid": soundgen_temp_guid,
        "isAutoGeneratedSelfSignCertificate": True,
        "displayName": DEVICE_SOUND_GEN
    }
    create_device(data, access_token)

def create_device(data: dict, access_token: str):
    """Create device in IoTConnect from given data"""
    headers = {
        "Content-type": "application/json",
        "Accept": "*/*",
        "Authorization": access_token
    }
    response = requests.post(API_DEVICE_URL + DEVICE_CREATE, json = data, headers = headers)

    try: 
        check_status(response)
        device_guid = get_device_guid_from_response(response)
        print(f"Device {data["displayName"]} created with guid {device_guid}")
    except BadHttpStatusException as e:
        response_json = response.json()
        error_type = response_json["error"][0]["param"]
        if DEVICE_ALREADY_EXISTS == error_type:
            device_guid = get_device_guid(data["displayName"], access_token)
            print(f"Device {data["displayName"]} already exists with guid {device_guid}")
        else:
            raise e

if __name__ == "__main__":
    iot_connect_setup()
