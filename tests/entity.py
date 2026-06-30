# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

import avnet.iotconnect.restapi.lib.entity as entity

result = entity.query()
print('all=', result)
result = entity.get_root_entity()
print('root=', result)
print('name=', result.name)
print('guid=', result.guid)

print('details=', entity.get_detail_by_guid(guid=result.guid))

result = entity.get_by_name(result.name)
print('get_by_name=', result)
