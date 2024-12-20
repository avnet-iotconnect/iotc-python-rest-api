"""This module performs IoTConnect OTA FW Update."""

import argparse
import requests
import string
import random

from common.credentials import authenticate
from common.constants import (
    DEVICE_SOUND_CLASS,
    FW_OTA_FILE,
    API_FW_URL,
    FW_ADD,
    FW_PREFIX,
    API_FILE_URL,
    FILE_UPLOAD,
    FIRMWARE_UPGRADE,
    FIRMWARE_UPGRADE_PUBLISH,
    OTA_TARGET_ENTITY,
    OTA_UPDATE,
    MAX_FW_VERSION_SIZE,
    FIRMWARE_ALREADY_EXISTS,
    DEVICE_SOUND_CLASS,
    FW_UPGRADE
)
from common.check_status import check_status, BadHttpStatusException
from common.common import (
    get_template_guid,
    get_entity_guid,
    get_firmware_guid
)


def iot_connect_fw_ota():
    """Perform IoTConnect FW OTA"""
    args = parse_arguments()
    access_token = authenticate(args.username, args.password, args.solution_key)
    print("Successful login - now create OTA update for the device.")
    template_guid = get_template_guid(DEVICE_SOUND_CLASS, access_token)

    hw_version = "1.0.0"
    fw_version = ''.join(random.choices(string.ascii_uppercase + string.digits, k=MAX_FW_VERSION_SIZE))
    firmware_draft_name = FW_PREFIX + fw_version.replace('.', '')
    fw_upgrade_guid = create_firmware_update(template_guid, DEVICE_SOUND_CLASS, firmware_draft_name, fw_version, hw_version, access_token)
    upload_fw_file(fw_upgrade_guid, access_token)
    publish_fw(fw_upgrade_guid, access_token)
    entity_guid = get_entity_guid(args.entity_name, access_token)
    create_fw_ota(fw_upgrade_guid, entity_guid, access_token)

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

def create_firmware(device_template_guid: str, firmware_name: str, fw_version: str, hw_version: str, access_token: str,) -> requests.Response:
    """Create new firmware in IoTConnect"""
    data = {
        "deviceTemplateGuid": device_template_guid,
        "software": fw_version,
        "firmwareName": firmware_name,
        "hardware": hw_version
    }

    headers = {
        "Content-type": "application/json",
        "Accept": "*/*",
        "Authorization": access_token
    }
    response = requests.post(API_FW_URL + FW_ADD, json = data, headers = headers)
    return response

def create_upgdare(firmware_guid: str, fw_version: str, access_token: str,) -> requests.Response:
    """Upgrade the firmware in IoTConnect"""
    data = {
        "firmwareGuid": firmware_guid,
        "software": fw_version,
    }

    headers = {
        "Content-type": "application/json",
        "Accept": "*/*",
        "Authorization": access_token
    }
    response = requests.post(API_FW_URL + FW_UPGRADE, json = data, headers = headers)
    check_status(response)
    response_json = response.json()
    guid = response_json["data"][0]["newId"]

    print(f"Firmware upgrade created with guid {guid}")
    return guid

def create_firmware_update(device_template_guid: str, device_template_name: str, firmware_name: str, fw_version: str, hw_version: str, access_token: str,) -> str:
    """Create new firmware update in IoTConnect"""
    response = create_firmware(device_template_guid, firmware_name, fw_version, hw_version, access_token)
    guid = ""
    try: 
        check_status(response)
        response_json = response.json()
        guid = response_json["data"][0]["firmwareUpgradeGuid"]
        print(f"Firmware {firmware_name} created with guid {guid}")
    except BadHttpStatusException as e:
        response_json = response.json()
        error_type = response_json["error"][0]["param"]
        if FIRMWARE_ALREADY_EXISTS == error_type:
            print("Firmware already exist, upgrade")
            fw_guid = get_firmware_guid(device_template_name, access_token)
            print(f"Firmware guid {fw_guid}")
            guid = create_upgdare(fw_guid, fw_version, access_token)
        else:
            raise e

    return guid

def upload_fw_file(fw_upgrade_guid: str, access_token: str):
    """Upload firmware file to IoTConnect"""
    headers = {
        "Authorization": access_token
    }

    fw_file = {
        'fileData': open(FW_OTA_FILE, 'rb')
    }

    data = {
        'fileRefGuid': fw_upgrade_guid,
        'ModuleType': 'firmware',
    }
    response = requests.post(API_FILE_URL + FILE_UPLOAD, files = fw_file, data = data, headers = headers)

    check_status(response)
    response_json = response.json()
    guid = response_json["data"][0]["guid"]

    print(f"Firmware file created with guid {guid}")

def publish_fw(fw_upgrade_guid: str, access_token: str):
    """Release firmware in IoTConnect for OTA"""
    data = {
        "firmwareUpgradeGuid": fw_upgrade_guid,
    }

    headers = {
        "Content-type": "application/json",
        "Accept": "*/*",
        "Authorization": access_token
    }
    response = requests.put(API_FW_URL + FIRMWARE_UPGRADE + fw_upgrade_guid + FIRMWARE_UPGRADE_PUBLISH, json = data, headers = headers)
    check_status(response)

    print("FW Released")

def create_fw_ota(fw_upgrade_guid: str, entity_guid: str, access_token: str):
    """Create firmware OTA update for the given entity"""
    data = {
        "firmwareUpgradeGuid": fw_upgrade_guid,
        "entityGuid": entity_guid,
        "isForceUpdate": True,
        "target": OTA_TARGET_ENTITY
    }

    headers = {
        "Content-type": "application/json",
        "Accept": "*/*",
        "Authorization": access_token
    }
    response = requests.post(API_FW_URL + OTA_UPDATE, json = data, headers = headers)
    check_status(response)
    response_json = response.json()

    print("OTA Update created for:")
    for ota_info in response_json["data"]:
        print(f" - Device with guid {ota_info["deviceGuid"]}. OTA Update Guid {ota_info["otaUpdateGuid"]}")


if __name__ == "__main__":
    iot_connect_fw_ota()
