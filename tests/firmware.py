import avnet.iotconnect.restapi.lib.template as template
from avnet.iotconnect.restapi.lib import firmware, upgrade, util, device
from avnet.iotconnect.restapi.lib.error import ConflictResponseError, InvalidActionError

TEMPLATE_CODE = 'apidemo1'
FIRMWARE_NAME = 'APIDEMO1FW'
DUID='apidemodev01'

# Enable trace programmatically or set environment variable to see more output
# from avnet.iotconnect.restapi.lib import config as cfg
# cfg.api_trace_enabled = True


# clean up firmware if it is already there
try:
    firmware.deprecate_match_name(FIRMWARE_NAME)
except InvalidActionError as ex:
    print("Firmware originally not found and not deleted.")

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
firmware_create_result = firmware.create(template_guid=template_guid, name=FIRMWARE_NAME, hw_version="1.0", initial_sw_version="0.0", description="Initial version")
print(firmware_create_result)
fw_00_guid=firmware_create_result.firmwareUpgradeGuid
print('firmware.get_by_name', firmware.get_by_name(FIRMWARE_NAME))
print('#0 firmware.get_by_guid', firmware.get_by_guid(firmware_create_result.newId))

upgrade.upload(fw_00_guid, 'test.zip', file_name="filename-changed.zip")

pkey_pem, cert_pem = util.generate_ec_cert_and_pkey(DUID)
with open('device-pkey.pem', 'w') as pk_file:
    pk_file.write(pkey_pem)
with open('device-cert.pem', 'w') as cert_file:
    cert_file.write(cert_pem)
with open('device-cert.pem', 'r') as file:
    certificate = file.read()
result = device.create(template_guid=template_guid, duid=DUID, device_certificate=certificate)
print('create=', result)
print('#1 firmware.get_by_guid', firmware.get_by_guid(firmware_create_result.newId))
upgrade.publish(fw_00_guid)

print('#2 firmware.get_by_guid', firmware.get_by_guid(fw_00_guid))


new_upgrade_create_result = upgrade.create(firmware_guid=firmware_create_result.newId, sw_version= "1.0")
fw_10_guid=new_upgrade_create_result.newId
print('#3 firmware.get_by_guid', firmware.get_by_guid(firmware_create_result.newId))
upgrade.upload(new_upgrade_create_result.newId, 'test.zip')
upgrade.publish(fw_10_guid)

print('#4 firmware.get_by_guid', firmware.get_by_guid(firmware_create_result.newId))

upgrade.delete_match_guid(fw_10_guid)

# there always has to be at least one fw upgrade available so we cannot delete both
# upgrade.delete_match_guid(fw_00_guid)
firmware.deprecate_match_name(FIRMWARE_NAME)

device.delete_match_duid(DUID)


template.delete_match_code(TEMPLATE_CODE)
