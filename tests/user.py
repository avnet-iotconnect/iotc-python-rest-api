import os
import sys

from avnet.iotconnect.restapi.lib import user

username=os.environ.get('IOTC_USER')

if username is None:
    print("Must set IOTC_USER in env")
    sys.exit(1)

print(user.get_by_email("michael.lamp@avnet.com"))

u = user.get_by_email(username)
print("get_by_email", u)

print("get_by_guid", user.get_by_guid(u.guid))

print("CPID:", u.companyGuid)

