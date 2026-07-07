# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

import avnet.iotconnect.restapi.lib.device as device
import avnet.iotconnect.restapi.lib.entity as entity
import avnet.iotconnect.restapi.lib.template as template
import avnet.iotconnect.restapi.lib.user as user
from avnet.iotconnect.restapi.lib import accesstoken, config
from avnet.iotconnect.restapi.lib.device import DeviceQuery, DeviceStatus
from avnet.iotconnect.restapi.lib.error import InvalidActionError

"""
This example prints some basic user information, lists devices, then creates a
device template and deletes it.

To learn more about API examples, refer to the (unit) tests directory in this repo.
"""

print('Username:', config.username)
print('User GUID:', accesstoken.decode_access_token().user.id)
print('CPID:', accesstoken.decode_access_token().user.cpId)
print('Root Entity:', entity.get_root_entity())
print("My User Details:", user.get_own_user())

# Query devices with server-side filtering and pagination. device.query() returns a
# Page: iterate it for the current page, read .total_count for the full total, or
# call .all() to walk every page transparently.
page = device.query(DeviceQuery(page_size=5))
print('Total devices:', page.total_count)
for d in page:
    print('  device:', d.uniqueId, '(active=%s)' % d.isActive)

# Filters are strongly typed (enums where the API expects fixed values).
active_count = sum(1 for _ in device.query(DeviceQuery(status=DeviceStatus.ACTIVE)).all())
print('Active devices:', active_count)

try:
    template.delete_match_code("example")
except InvalidActionError:
    print("Template did not exist prior to executing the example.")

template_create_result = template.create('sample-device-template.json', new_template_code="example", new_template_name='API Demo EXample')
print("Template created successfully.")
template.delete_match_guid(template_create_result.deviceTemplateGuid)
print("Template deleted successfully.")





