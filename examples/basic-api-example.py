# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

import avnet.iotconnect.restapi.lib.entity as entity
import avnet.iotconnect.restapi.lib.template as template
import avnet.iotconnect.restapi.lib.user as user
from avnet.iotconnect.restapi.lib import token
from avnet.iotconnect.restapi.lib.error import InvalidActionError

"""
This example prints some basic user information, creates a device template and deletes it.

To learn more about API examples, refer to the (unit) tests directory in this repo. 
"""

print('Username:', token.decode_access_token().user.id)
print('CPID:', token.decode_access_token().user.cpId)
print('Root EntityL', entity.get_root_entity())
print("My User Details:", user.get_own_user())

try:
    template.delete_match_code("example")
except InvalidActionError:
    print("Template did not exist prior to executing the example.")

template_create_result = template.create('sample-device-template.json', new_template_code="example", new_template_name='API Demo EXample')
print("Template created successfully.")
template.delete_match_guid(template_create_result.deviceTemplateGuid)
print("Template deleted successfully.")





