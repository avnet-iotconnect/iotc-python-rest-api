import json

import avnet.iotconnect.restapi.lib.template as template
from avnet.iotconnect.restapi.lib.error import InvalidActionError
from avnet.iotconnect.restapi.lib.template import TemplateCreateResult, TemplateQuery


# test for bad delete_match_code
try:
    template.delete_match_code('notexists')
    raise Exception("delete_match_code failed")
except InvalidActionError as ex:
    print("delete_match_code: Template already exists", ex)

# test for bad delete_match_guid
try:
    template.delete_match_guid('DEADB33F-1111-1111-1111-00000DEADB33F')
    raise Exception("delete_match_guid failed")
except InvalidActionError as ex:
    print("delete_match_code: Template already exists", ex)

t = template.get_by_template_code('apidemo1')
if t is not None:
    print('get_by_template_code=', t.templateCode)
    print('get_by_guid=', template.get_by_guid(t.guid))
    template.delete_match_guid(t.guid)
    print('Delete success')

create_result: TemplateCreateResult = template.create('sample-device-template.json', new_template_code="apidemo1", new_template_name="ApiExample")
print('create=', create_result)

if create_result is None:
    raise Exception("Expected successful template creation")

print('get_by_template_code=', template.get_by_template_code('apidemo1'))
print('get_by_guid=', template.get_by_guid(create_result.deviceTemplateGuid))

# raw records vs. the normalized (junk-stripped) telemetry schema
attrs = template.get_attributes(create_result.deviceTemplateGuid)
print('get_attributes raw=', attrs)
attr_names = {a.localName for a in attrs}
assert {'version', 'sdk_version', 'random'} <= attr_names, f"Expected sample attributes, got {attr_names}"

normalized = template.get_attributes_normalized(create_result.deviceTemplateGuid)
print('get_attributes_normalized=', json.dumps(normalized, indent=2))
assert all(set(a).issubset({'name', 'type', 'unit', 'description', 'displayName', 'validation', 'tag', 'attributes'}) for a in normalized), \
    "normalized view leaked a non-meaningful field"
assert {a['name'] for a in normalized} == attr_names, "normalized view dropped/added attributes"

# list / query: the created template should be findable via a server-side filter.
# Page carries the total count; .all() walks every page transparently.
page = template.query(TemplateQuery(name="ApiExample"))
print('template.list total=', page.total_count, 'codes(first page)=', [t.templateCode for t in page])
assert any(t.guid == create_result.deviceTemplateGuid for t in page.all()), "Created template not found via list()"

template.delete_match_guid(create_result.deviceTemplateGuid)
print('template deleted')

# test for bad delete_match_guid
try:
    template.delete_match_guid(create_result.deviceTemplateGuid)
    raise Exception("delete_match_guid failed")
except InvalidActionError as ex:
    # we are expecting this to return InvalidActionError
    print("delete test success", ex)
try:
    template.delete_match_code('apidemo1')
except InvalidActionError as ex:
    # we are expecting this to return InvalidActionError
    print("delete test success", ex)



