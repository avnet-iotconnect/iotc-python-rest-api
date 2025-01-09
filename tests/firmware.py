from avnet.iotconnect.restapi.lib import firmware
import avnet.iotconnect.restapi.lib.template as template
from avnet.iotconnect.restapi.lib.error import UsageError

#result = template.query("[?starts_with(code,`a`)]")
#print('query=', result)

try:
    firmware.delete_match_name("APIDEMO1FW")
except UsageError as ex:
    print("Firmware originally not found")

t = template.get_by_template_code('apidemo1')
print('get_by_template_code=', t)
if t is not None:
    result = template.get_by_guid(t.guid)
    print('get_by_guid=', result)
    template.delete_match_guid(t.guid)
    print('Delete success')


result = template.create('sample-device-template.json', new_template_code="apidemo1", new_template_name="ApiExample")
print('create=', result)

print(firmware.query())
print(firmware.get_by_name("APIDEMO1FW"))


result = firmware.create(template_guid=t.guid, name="APIDEMO1FW", hw_version="1.0")
print(result)

try:
    firmware.delete_match_name('APIDEMO1FW')
except UsageError as ex:
    print("SUCCESS. Caught", ex)


template.delete_match_guid(t.guid)

try:
    template.delete_match_code('apidemo1')
except UsageError as ex:
    print("SUCCESS. Caught", ex)




