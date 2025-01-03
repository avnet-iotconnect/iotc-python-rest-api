import avnet.iotconnect.restapi.lib.template as template
from avnet.iotconnect.restapi.lib.error import UsageError

result = template.query()
print('all=', result)
result = template.get_by_template_code('apidemo1')
print('get_by_template_code=', result)
if result is not None:
    result = template.get_by_guid(result.guid)
    print('get_by_guid=', result)
    template.delete_match_guid(result.guid)
    print('Delete success')

result = template.create('sample-device-template.json', new_template_code="apidemo1", new_template_name="ApiExample")
print('create=', result)
if result is not None:
    result = template.get_by_guid(result)
    print('get_by_guid=', result)
    template.delete_match_guid(result.guid)
    print('delete=', result)

try:
    template.delete_match_code('apidemo1')
except UsageError as ex:
    print("SUCCESS. Caught", ex)



