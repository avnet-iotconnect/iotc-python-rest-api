"""This module defines constants."""

STATUS_OK = 200

API_AUTH_URL = "https://awspocauth.iotconnect.io/api/v2.1/"
API_DEVICE_URL = "https://awspocdevice.iotconnect.io/api/v2.1/"
API_USER_URL = "https://awspocuser.iotconnect.io/api/v2.1/"
API_FW_URL = "https://awspocfirmware.iotconnect.io/api/v2.1/"
API_FILE_URL = "https://awspocfile.iotconnect.io/api/v2.1/"
API_EVENT_URL = "https://awspocevent.iotconnect.io/api/v2.1/"

LOGIN = "Auth/login"
DEVICE_TEMPLATE_CREATE = "device-template/quick"
DEVICE_TEMPLATE_LIST = "device-template"
DEVICE_CREATE = "Device"
ENTITY_LIST = "Entity"
FW_ADD = "Firmware"
FW_UPGRADE = "firmware-upgrade"
FILE_UPLOAD = "File"
FIRMWARE_UPGRADE = "firmware-upgrade/"
FIRMWARE_UPGRADE_PUBLISH = "/publish"
OTA_UPDATE = "ota-update"
RULE = "Rule"
USER = "User"
SEVERETY_LOOKUP = "severity-level/lookup"
COMMAND = "template-command/"
COMMAND_SEND = "template-command/send"

DEVICE_TEMPLATES_DIR = "templates/devices/"
TEMPLATES_TAIL = "_template.JSON"

DEVICE_SOUND_CLASS = "soundclass"
DEVICE_SOUND_GEN = "soundgener"

DEVICE_TEMPLATES = [DEVICE_SOUND_CLASS, DEVICE_SOUND_GEN]

DEVICE_TEMPLATE_ALREADY_EXISTS = "DeviceTemplateNameAlreadyExists"
DEVICE_ALREADY_EXISTS = "UniqueIdAlreadyExists"
FIRMWARE_ALREADY_EXISTS = "TemplateAlreadyAttachedWithFirmware"

FW_OTA_FILE = "ota/fw.iso"
FW_PREFIX = "SC"
MAX_FW_VERSION_SIZE = 8

OTA_TARGET_ENTITY = 1

CREDS_S3_COMMAND = "creds_s3"

S3_ENDPOINT_HEADER = "endpoint"
S3_APIKEY_HEADER = "apikey"
