import os

from avnet.iotconnect.restapi.lib.credentials import authenticate, refresh
import avnet.iotconnect.restapi.lib.entity as entity

#authenticate(os.environ['IOTC_USER'], os.environ['IOTC_PASS'], os.environ['IOTC_SKEY'])
#refresh()
entity.get_guid("Witekio")
entity.get_guid("\\*.guid")


