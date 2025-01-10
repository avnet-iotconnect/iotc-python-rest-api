from avnet.iotconnect.restapi.lib import firmware, upgrade
import avnet.iotconnect.restapi.lib.template as template
from avnet.iotconnect.restapi.lib.error import UsageError

# result = template.query("[?starts_with(code,`a`)]")
# print('query=', result)

TEMPLATE_CODE = 'apidemo1'
FIRMWARE_NAME = 'APIDEMO1FW'

try:
    firmware.deprecate_match_name(FIRMWARE_NAME)
except UsageError as ex:
    print("Firmware originally not found")

t = template.get_by_template_code(TEMPLATE_CODE)
print(t)
if t is not None:
    print('get_by_template_code=', t.templateCode)
    print('get_by_guid=', template.get_by_guid(t.guid))
    template.delete_match_guid(t.guid)
    print('Delete success')

template_create_result = template.create('sample-device-template.json', new_template_code=TEMPLATE_CODE, new_template_name="ApiExample")
print('create=', template_create_result)
template_guid = template_create_result.deviceTemplateGuid

firmware_create_result = firmware.create(template_guid=template_guid, name=FIRMWARE_NAME, hw_version="1.0", initial_sw_version="0.0", description="Initial version")
print(firmware_create_result)
fw_00_guid=firmware_create_result.firmwareUpgradeGuid
print('firmware.get_by_name', firmware.get_by_name(FIRMWARE_NAME))
print('firmware.get_by_guid', firmware.get_by_guid(firmware_create_result.newId))

upgrade.upload(firmware_create_result.firmwareUpgradeGuid, 'test.zip', file_name="x.foo")
upgrade.publish(firmware_create_result.firmwareUpgradeGuid)

new_upgrade_create_result = upgrade.create(firmware_guid=firmware_create_result.newId, sw_version= "1.0")
fw_10_guid=firmware_create_result.firmwareUpgradeGuid

upgrade.upload(new_upgrade_create_result.newId, 'test.zip')

upgrade.delete_match_guid(fw_10_guid)

# there always has to be at least one fw upgrade available so we cannot delete both
# upgrade.delete_match_guid(fw_00_guid)


try:
    firmware.deprecate_match_name(FIRMWARE_NAME)
except UsageError as ex:
    print("SUCCESS. Caught", ex)

try:
    template.delete_match_code(TEMPLATE_CODE)
except UsageError as ex:
    print("SUCCESS. Caught", ex)
