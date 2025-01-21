import avnet.iotconnect.restapi.lib.template as template
from avnet.iotconnect.restapi.lib.error import ConflictResponseError, NotFoundResponseError
from avnet.iotconnect.restapi.lib.template import TemplateCreateResult

t = template.get_by_template_code('apidemo1')

try:
    template.delete_match_code('notexists')
    raise Exception("delete_match_guid failed")
except ConflictResponseError as ex:
    print("delete_match_code: Template already exists", ex)

template.delete_match_guid('DEADB33F-72BC-430C-844E-3E177DEADB33F')


if t is not None:
    print('get_by_template_code=', t.templateCode)
    print('get_by_guid=', template.get_by_guid(t.guid))
    template.delete_match_guid(t.guid)
    print('Delete success')

create_result: TemplateCreateResult = template.create('sample-device-template.json', new_template_code="apidemo1", new_template_name="ApiExample")
print('create=', create_result)

if create_result is not None:
    print('get_by_guid=', template.get_by_guid(create_result.deviceTemplateGuid))
    template.delete_match_guid(create_result.deviceTemplateGuid)
    print('deleted')

template.delete_match_guid(create_result.deviceTemplateGuid)
try:
    template.delete_match_guid(create_result.deviceTemplateGuid)
except ConflictResponseError as ex:
    # we are expecting this to return ConflictResponseError
    print("delete test success", ex)
try:
    template.delete_match_code('apidemo1')
except ConflictResponseError as ex:
    # we are expecting this to return ConflictResponseError
    print("delete test success", ex)



