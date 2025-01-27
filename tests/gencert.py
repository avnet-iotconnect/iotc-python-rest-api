import json
import os
import sys

from avnet.iotconnect.restapi.lib import util

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

pkey_pem, cert_pem = util.generate_ec_cert_and_pkey(DUID)

with open('device-pkey.pem', 'w') as file:
    file.write(pkey_pem)

with open('device-cert.pem', 'w') as file:
    file.write(cert_pem)

print("Key and certificate written to device-pkey.pem and device-cert.pem")
