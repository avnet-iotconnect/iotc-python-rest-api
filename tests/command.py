import random
import sys
import time

import avnet.iotconnect.restapi.lib.template as template
from avnet.iotconnect.restapi.lib import device, config, command
from avnet.iotconnect.restapi.lib.error import InvalidActionError

TEMPLATE_CODE = 'apidemo1'
FIRMWARE_NAME = 'APIDEMO1FW'
DUID = 'apidemodev01'

# Enable trace programmatically or set environment variable to see more output
# from avnet.iotconnect.restapi.lib import config as cfg
# cfg.api_trace_enabled = True

command_received = False  # track whether the sent command was received in the SDK example below.


def run_sdk_send_receive_command(device_guid: str, command_guid: str):
    global command_received
    try:
        from avnet.iotconnect.sdk.lite import Client
    except ModuleNotFoundError:
        print("It looks like the iotc-pyton-lite-sdk is not installed. Please install it with python3 -m pip install iotconnect-lite-sdk")
        sys.exit(5)

    from avnet.iotconnect.sdk.lite import Client, DeviceConfig, C2dCommand, Callbacks, DeviceConfigError
    from avnet.iotconnect.sdk.lite import __version__ as SDK_VERSION
    from avnet.iotconnect.sdk.sdklib.mqtt import C2dAck

    def on_command(msg: C2dCommand):
        global command_received
        print("Received command", msg.command_name, msg.command_args, msg.ack_id)
        if msg.command_name == "sample_command":
            c.send_command_ack(msg, C2dAck.CMD_SUCCESS_WITH_ACK, "Command received")
            command_received = True
        else:
            print("Command %s not implemented!" % msg.command_name)
            if msg.ack_id is not None:  # it could be a command without "Acknowledgement Required" flag in the device template
                c.send_command_ack(msg, C2dAck.CMD_FAILED, "Not Implemented")

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
        command_was_sent = False  # send the command only once
        while True:
            if not c.is_connected():
                command_was_sent = False
                print('(re)connecting...')
                c.connect()
                if not c.is_connected():
                    print('Unable to connect. Exiting.')  # Still unable to connect after 100 (default) re-tries.
                    sys.exit(2)

            c.send_telemetry({
                'version': "COMMAND TEST 1.0",
                'SDK_VERSION': SDK_VERSION,
                'confidence': random.randint(0, 100)
            })

            time.sleep(1)
            if not command_was_sent:
                # normally we would send this command with REST API from a different device,
                # but here we just use the REST API here to send the command in the main SDK loop.
                command_was_sent = True
                result = command.send(command_guid, device_guid, "argument1 argument2")
                print(result)

            time.sleep(5)
            if command_received:
                c.disconnect()
                print("Command was received. Client disconnected.")
                return

    except DeviceConfigError as dce:
        print(dce)
        sys.exit(1)

    except KeyboardInterrupt:
        print("Exiting.")
        sys.exit(0)


# clean up device if it is already there
try:
    device.delete_match_duid(DUID)
except InvalidActionError:
    print("Device originally not found and not deleted.")

# clean up template if it is already there
try:
    template.delete_match_code(TEMPLATE_CODE)
except InvalidActionError:
    print("Template originally not found and not deleted.")

template_create_result = template.create('sample-device-template.json', new_template_code=TEMPLATE_CODE, new_template_name="ApiExample")
print('create=', template_create_result)
template_guid = template_create_result.deviceTemplateGuid

# test creation of a device with generated certificate and private key
pkey_pem, cert_pem = config.generate_ec_cert_and_pkey(DUID)
with open('device-pkey.pem', 'w') as pk_file:
    pk_file.write(pkey_pem)
with open('device-cert.pem', 'w') as cert_file:
    cert_file.write(cert_pem)
with open('device-cert.pem', 'r') as file:
    certificate = file.read()
device_create_result = device.create(template_guid=template_guid, duid=DUID, device_certificate=certificate)
print('create=', device_create_result)
device_guid = device_create_result.newid

device_json = config.generate_device_json(DUID)
with open('iotcDeviceConfig.json', 'w') as f:
    f.write(device_json)

sample_command = command.get_with_name(template_guid, 'sample_command')
print(sample_command)

# run the SDK and have it send this command once and wait for it to come back to the SDK client.
run_sdk_send_receive_command(device_guid, sample_command.guid)

print('Command sending and receiving complete.')

device.delete_match_duid(DUID)

template.delete_match_code(TEMPLATE_CODE)
