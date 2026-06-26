# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.


import json
import os
import sys

import avnet.iotconnect.restapi.lib.device as device
from avnet.iotconnect.restapi.lib import template
from avnet.iotconnect.restapi.lib.device import DeviceQuery, DeviceStatus
from avnet.iotconnect.restapi.lib.query import Sort, Order

TEMPLATE_CODE = 'apidemo1'

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

t = template.get_by_template_code(TEMPLATE_CODE)
print('get_by_template_code=', t)
if t is not None:
    do_delete_template = False
    print("Template already exists. Not deleting after the test.")
else:
    result = template.create('sample-device-template.json', new_template_code=TEMPLATE_CODE, new_template_name="ApiExample")
    t = template.get_by_guid(result.deviceTemplateGuid)

d = device.get_by_duid(DUID)
if d is not None:
    print('delete=', device.delete_match_guid(d.guid))

t = template.get_by_template_code(TEMPLATE_CODE)
if not t.isAttachedWithDevice:
    print("Template is correctly not associated with a device.")
else:
    raise ValueError("Template seems to have a device associated with it")


with open('device-cert.pem', 'r') as file:
    certificate = file.read()
    # template accepts a code or a GUID here - we pass the code
    result = device.create(template_guid=TEMPLATE_CODE, duid=DUID, device_certificate=certificate)
    print('create=', result)

t = template.get_by_template_code(TEMPLATE_CODE)

if t.isAttachedWithDevice:
    print("Template is now associated with this device.")
else:
    raise ValueError("Template does not seem to have a device associated with it")


# --- list / query options -------------------------------------------------

# Page wrapper carries the server-side total count alongside the current page.
page = device.query()
print('total devices=', page.total_count)
print('first page size=', len(page))

# Filter by our DUID; the result should contain exactly the device we created.
page = device.query(DeviceQuery(duid=DUID))
print('filter by duid=', [dev.uniqueId for dev in page])
assert any(dev.uniqueId == DUID for dev in page), "Created device not found by DUID filter"

# Filter by template code (resolved to a GUID for us) + sort, small page size.
q = DeviceQuery(template=TEMPLATE_CODE, sort_by=Sort('uniqueId', Order.ASC), page_size=10)
page = device.query(q)
print('filter by template=', [dev.uniqueId for dev in page])
assert any(dev.uniqueId == DUID for dev in page), "Created device not found by template filter"

# Enum-typed status filter; .all() walks every page transparently.
active_duids = [dev.uniqueId for dev in device.query(DeviceQuery(status=DeviceStatus.ACTIVE)).all()]
print('active device count (all pages)=', len(active_duids))


# --- named update: activate / deactivate ----------------------------------

device.set_active_match_duid(DUID, False)
d = device.get_by_duid(DUID)
print('after deactivate isActive=', d.isActive)
assert d.isActive is False, "Device should be inactive"

device.set_active_match_duid(DUID, True)
d = device.get_by_duid(DUID)
print('after activate isActive=', d.isActive)
assert d.isActive is True, "Device should be active"


# --- cleanup --------------------------------------------------------------

print('delete device=', device.delete_match_duid(DUID))

if do_delete_template:
    print('delete template=', template.delete_match_guid(t.guid))
