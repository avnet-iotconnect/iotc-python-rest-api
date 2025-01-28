# SPDX-License-Identifier: MIT
# Copyright (C) 2024 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

import random
import sys
import time

try:
    from avnet.iotconnect.sdk.lite import Client
except ModuleNotFoundError:
    print("It looks like the iotc-pyton-lite-sdk is not installed. Please see comments in this file for more information.")
    sys.exit(5)

from avnet.iotconnect.sdk.lite import Client, DeviceConfig, C2dCommand, Callbacks, DeviceConfigError
from avnet.iotconnect.sdk.lite import __version__ as SDK_VERSION
from avnet.iotconnect.sdk.sdklib.mqtt import C2dAck, C2dOta

"""
This simple example can be used to test a device connection with iotc-python-lite-sdk. The SDK can be downloaded with:
wget -qN 'https://downloads.iotconnect.io/sdk/python/iotconnect_sdk_lite-1.0.0-py3-none-any.whl'
... or similar.

See more info at https://github.com/avnet-iotconnect/iotc-python-lite-sdk
"""

APP_VERSION = "1.0"

def on_command(msg: C2dCommand):
    print("Received command", msg.command_name, msg.command_args, msg.ack_id)
    if msg.command_name == "sample-command":
        c.send_command_ack(msg, C2dAck.CMD_FAILED, "Command handler not implemented")
        print("Command handler not implemented", len(msg.command_args))
    else:
        print("Command %s not implemented!" % msg.command_name)
        if msg.ack_id is not None: # it could be a command without "Acknowledgement Required" flag in the device template
            c.send_command_ack(msg, C2dAck.CMD_FAILED, "Not Implemented")


def on_ota(msg: C2dOta):
    # We just print the URL. The actual handling of the OTA request would be project specific.
    # See the ota-handling.py for more details.
    print("Received OTA request. File: %s Version: %s URL: %s" % (msg.urls[0].file_name, msg.version, msg.urls[0].url))
    # OTA messages always have ack_id, so it is safe to not check for it before sending the ack
    c.send_ota_ack(msg, C2dAck.OTA_DOWNLOAD_FAILED, "Not implemented")


def on_disconnect(reason: str, disconnected_from_server: bool):
    print("Disconnected%s. Reason: %s" % (" from server" if disconnected_from_server else "", reason))

try:
    device_config = DeviceConfig.from_iotc_device_config_json_file(
        device_config_json_path="iotcDeviceConfig.json",
        device_cert_path="device-cert.pem",
        device_pkey_path="device-pkey.pem"
    )

    c = Client(
        config=device_config,
        callbacks=Callbacks(
            command_cb=on_command,
            disconnected_cb=on_disconnect
        )
    )
    while True:
        if not c.is_connected():
            print('(re)connecting...')
            c.connect()
            if not c.is_connected():
                print('Unable to connect. Exiting.')  # Still unable to connect after 100 (default) re-tries.
                sys.exit(2)

        c.send_telemetry({
            'version': APP_VERSION,
            'sdk_version': SDK_VERSION,
            'random': random.randint(0, 100)
        })
        time.sleep(10)

except DeviceConfigError as dce:
    print(dce)
    sys.exit(1)

except KeyboardInterrupt:
    print("Exiting.")
    sys.exit(0)