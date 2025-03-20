import avnet.iotconnect.restapi.lib.template as template
from avnet.iotconnect.restapi.lib import firmware, upgrade, device, config, ota
from avnet.iotconnect.restapi.lib.error import InvalidActionError, ConflictResponseError

TEMPLATE_CODE = 'apidemo1'
FIRMWARE_NAME = 'APIDEMO1FW'
DUID = 'apidemodev01'

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

firmware_create_result = firmware.create(template_guid=template_guid, name=FIRMWARE_NAME, hw_version="1.0", initial_sw_version="v1.0", description="Initial version")
print(firmware_create_result)

firmware_guid = firmware_create_result.newId
upgrade_1_guid = firmware_create_result.firmwareUpgradeGuid

# check what we get from the initial creation with the initial draft
print('#0 firmware.get_by_guid', firmware.get_by_guid(firmware_guid))

upgrade.upload(upgrade_1_guid, 'test.zip', file_name="filename-changed.zip")
upgrade.publish(upgrade_1_guid)

# check what we get with the newly uploaded files in the draft. Now we should have URLs.
print('#2 firmware.get_by_guid', firmware.get_by_guid(firmware_guid))

# create an empty new draft and upload two files.
# NOTE: Test having no sw_version and generating a build number, so omit sw_version.
new_upgrade_create_result = upgrade.create(firmware_guid=firmware_guid)
upgrade_2_guid = new_upgrade_create_result.newId

upgrade.upload(upgrade_2_guid, 'test.zip')
upgrade.upload(upgrade_2_guid, 'firmware.py', file_name='new-unit-test.py')

# check what we get with the newly uploaded files in the new draft. Now we should have one original release and one draft.
final_fw = firmware.get_by_guid(firmware_guid)

print('#3 firmware.get_by_guid', final_fw)

print('----')
print('Upgrades#: ', len(final_fw.Upgrades))
print(f"Releases#: {len(final_fw.releases())} ({final_fw.release_count()})")
print(f"Drafts#: {len(final_fw.drafts())} ({final_fw.draft_count()})")
print('Upgrade versions:', final_fw.Upgrades[0].software, final_fw.Upgrades[1].software)

print('--')
print(upgrade.get_by_guid(upgrade_1_guid).software, upgrade.get_by_guid(upgrade_1_guid).urls[0])
print(upgrade.get_by_guid(upgrade_2_guid).software, upgrade.get_by_guid(upgrade_2_guid).urls[0])
print(upgrade.get_by_guid(upgrade_2_guid).software, upgrade.get_by_guid(upgrade_2_guid).urls[1].name)
print('----')

# check what we get with published second draft as a "release".
print('#4 firmware.get_by_guid', firmware.get_by_guid(firmware_guid))

# test creation of a device with generated certificate and private key
pkey_pem, cert_pem = config.generate_ec_cert_and_pkey(DUID)
with open('device-pkey.pem', 'w') as pk_file:
    pk_file.write(pkey_pem)
with open('device-cert.pem', 'w') as cert_file:
    cert_file.write(cert_pem)
with open('device-cert.pem', 'r') as f:
    certificate = f.read()
device_create_result = device.create(template_guid=template_guid, duid=DUID, device_certificate=certificate)
print('create=', device_create_result)

try:
    ota.push_to_entity(upgrade_1_guid)  # use the root entity
    print("Success push_ota_to_entity upgrade_1_guid")
except ConflictResponseError:
    print("Failed push_ota_to_entity upgrade_1_guid!")

try:
    ota.push_to_device(upgrade_1_guid, [device_create_result.newid])
    print("Success push_ota_to_device upgrade_1_guid")
except ConflictResponseError:
    print("Failed push_ota_to_device upgrade_1_guid!")

# NOTE: We cannot use a draft to ota.push_to_entity(). We would expect it to fail.

try:
    ota.push_to_device(upgrade_2_guid, [device_create_result.newid], is_draft=True)
    print("Success push_ota_to_device upgrade_2_guid")
except ConflictResponseError:
    print("Failed push_ota_to_device upgrade_2_guid!")

upgrade.publish(upgrade_2_guid)

try:
    upgrade.publish(upgrade_2_guid)
    print("FAILED Twice-Upgrade publish test!")
except ConflictResponseError:
    print("Twice-Upgrade publish test success")

# now we should have two published firmwares with this guid
print('#5 firmware.get_by_guid', firmware.get_by_guid(firmware_guid))

upgrade.delete_match_guid(upgrade_2_guid)

# there always has to be at least one fw upgrade available so we cannot delete both
try:
    upgrade.delete_match_guid(upgrade_1_guid)
    print("FAILED Delete the only upgrade left test!")
except ConflictResponseError:
    print("Delete the only upgrade left - test success.")

firmware.deprecate_match_name(FIRMWARE_NAME)

device.delete_match_duid(DUID)

template.delete_match_code(TEMPLATE_CODE)
