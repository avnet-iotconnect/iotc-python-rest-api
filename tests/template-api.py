import avnet.iotconnect.restapi.lib.template as template

result = template.query_all()
print('all=', result)
result = template.get_by_template_code('test1234')
print('code=', result)
result = template.get_by_template_code('test1234', fields=['guid', 'name'])
print('code=', result)
# result = template.delete('a87cfb71-7b23-44e9-b4ea-fdf53f89393d')
print('delete=', result)
print('create=', template.create('sample-device-template.json', new_template_code="apidemo1", new_template_name="Python REST API example 1 from api.py "))
#print('create=', template.create('sample-device-template.json', new_template_code="apidemo2", new_template_name="Python REST API example 2 from api.py "))



