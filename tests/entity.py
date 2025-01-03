import avnet.iotconnect.restapi.lib.entity as entity

result = entity.query()
print('all=', result)
result = entity.get_root_entity()
print('root=', result)
result = entity.get_by_name(result.name)
print('get_by_name=', result)
