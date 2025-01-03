import json
import os
import sys

import avnet.iotconnect.restapi.lib.device as device
from avnet.iotconnect.restapi.lib import template

DUID = os.environ.get('IOTC_DUID')

# try load duid from iotcDeviceConfig.json
if DUID is None:
    try:
        with open('iotcDeviceConfig.json', 'r') as file:
            device_data = json.load(file)
            DUID = device_data.get('uid')
    except RuntimeError:
        pass

if DUID is None:
    print("Unable to determine DUID. Please provide iotcDeviceConfig.json")
    sys.exit(-1)

do_delete_template = True

t = template.get_by_template_code('apidemo1')
print('get_by_template_code=', t)
if t is not None:
    do_delete_template = False
    print("Template already exists. Not deleting after the test.")
else:
    result = template.create('sample-device-template.json', new_template_code="apidemo1", new_template_name="ApiExample")
    t = template.get_by_guid(result)

d = device.get_by_duid(DUID)
if d is not None:
    print('delete=', device.delete_match_guid(d.guid))

with open('device-cert.pem', 'r') as file:
    certificate = file.read()
    result = device.create(template_guid=t.guid, duid=DUID, device_certificate=certificate)
    print('create=', result)

print('delete device=', device.delete_match_guid(result))

if do_delete_template:
    print('delete template=', template.delete_match_guid(t.guid))
