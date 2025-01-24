# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

import os

from avnet.iotconnect.restapi.lib.credentials import authenticate, refresh
import avnet.iotconnect.restapi.lib.entity as entity
import avnet.iotconnect.restapi.lib.template as template

# See documentation on how to set up your IOTC_EVN and IOTC_PF environment variables first.

# You can specify your credentials here.
# You can also use the CLI example and authenticate once. Credentials will be valid for 24 hours,
# but will be refreshed and extended automatically every hour (by default) when you use the API.
authenticate(os.environ['IOTC_USER'], os.environ['IOTC_PASS'], os.environ['IOTC_SKEY'])

print('Guid=', entity.get_root_entity())
print('All=', entity.query_all())
print('Root=', entity.get_root_entity())
print('create=', template.create('sample-device-template.json', new_template_code="apidemo1", new_template_name="Python REST API example from apy.py "))
print('create=', template.create('sample-device-template.json', new_template_code="apidemo2", new_template_name="Python REST API example from apy.py "))



