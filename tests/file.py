from avnet.iotconnect.restapi.lib import file
from avnet.iotconnect.restapi.lib.file import FILE_MODULE_CUSTOM


# Enable trace programmatically or set environment variable to see more output
# from avnet.iotconnect.restapi.lib import config as cfg
# cfg.api_trace_enabled = True


MY_APP_GUID='8BBEEDCD-EB33-436A-B69C-3FDC58EC6D37'


result = file.get_by_module_type_and_guid(FILE_MODULE_CUSTOM, MY_APP_GUID)
print('Initial list of files:', result)

result = file.create(FILE_MODULE_CUSTOM, MY_APP_GUID, file_path='file.py')
print(result)

result = file.get_by_module_type_and_guid(FILE_MODULE_CUSTOM, MY_APP_GUID)
print('Files after create:', result)

for f in result:
    file.delete_match_guid(FILE_MODULE_CUSTOM, f.guid)

result = file.get_by_module_type_and_guid(FILE_MODULE_CUSTOM, MY_APP_GUID)
print('Files after delete:', result)