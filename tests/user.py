import os
import sys

from avnet.iotconnect.restapi.lib import user

u = user.get_own_user()
print("get_own_user", u)


print("get_by_guid", user.get_by_guid(u.userGuid))

print("CPID:", u.companyCpid)

u = user.get_by_email("does@not.exist.com")
print("get_by_email", u)
if u is not None:
    raise Exception("get_by_email: Test failed!")

u = user.get_by_guid('DEADB33F-1111-1111-1111-00000DEADB33F')
print("get_by_guid", u)
if u is not None:
    raise Exception("get_by_guid: Test failed!")
