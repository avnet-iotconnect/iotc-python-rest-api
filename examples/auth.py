import os

from avnet.iotconnect.restapi.lib.credentials import authenticate, refresh

authenticate(os.environ['IOTC_USER'], os.environ['IOTC_PASS'], os.environ['IOTC_SKEY'])
refresh()
refresh()

