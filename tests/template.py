import avnet.iotconnect.restapi.lib.template as template
from avnet.iotconnect.restapi.lib.error import UsageError
from avnet.iotconnect.restapi.lib.template import TemplateCreateResult

#result = template.query("[?starts_with(code,`a`)]")
#print('query=', result)
print(template.get_by_template_code('mchipkey'))
t = template.get_by_template_code('apidemo1')
if t is not None:
    print('get_by_template_code=', t.code)
    result = template.get_by_guid(t.guid)
    print('get_by_guid=', result)
    template.delete_match_guid(t.guid)
    print('Delete success')

create_result: TemplateCreateResult = template.create('sample-device-template.json', new_template_code="apidemo1", new_template_name="ApiExample")
print('create=', create_result)
if create_result is not None:
    t = template.get_by_guid(create_result.deviceTemplateGuid)
    print('get_by_guid=', create_result)
    template.delete_match_guid(t.guid)
    print('deleted')

try:
    template.delete_match_code('apidemo1')
except UsageError as ex:
    print("SUCCESS. Caught", ex)



