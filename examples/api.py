import os

from avnet.iotconnect.restapi.lib.credentials import authenticate, refresh
import avnet.iotconnect.restapi.lib.entity as entity

#authenticate(os.environ['IOTC_USER'], os.environ['IOTC_PASS'], os.environ['IOTC_SKEY'])
#refresh()
print('Guid=', entity.get_by_name("Witekio"))
print('All=', entity.get_all())
print('Root=', entity.get_root_entity())
#entity.get_guid("\\*.guid")


