import os

from avnet.iotconnect.restapi.lib.credentials import authenticate, refresh
import avnet.iotconnect.restapi.lib.entity as entity
import avnet.iotconnect.restapi.lib.template as template

#authenticate(os.environ['IOTC_USER'], os.environ['IOTC_PASS'], os.environ['IOTC_SKEY'])
#refresh()
print('Guid=', entity.get_by_name("Americas"))
print('All=', entity.query_all())
print('Root=', entity.get_root_entity())
print('create=', template.create('sample-device-template.json', new_template_code="apidemo1", new_template_name="Python REST API example from apy.py "))
print('create=', template.create('sample-device-template.json', new_template_code="apidemo2", new_template_name="Python REST API example from apy.py "))



