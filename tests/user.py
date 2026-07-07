from avnet.iotconnect.restapi.lib import user, accesstoken
from avnet.iotconnect.restapi.lib.user import UserQuery

u = user.get_own_user()
print("get_own_user", u)

if u.companyCpid != accesstoken.decode_access_token().user.cpId:
    raise Exception("cpid not equal!")

print("get_by_guid", user.get_by_guid(u.userGuid))

print("CPID:", u.companyCpid)

# list / query: there is at least one user (us), and filtering by our own email finds us.
page = user.query(UserQuery(page_size=10))
print("user.list total=", page.total_count, "first page=", len(page))
assert page.total_count >= 1, "Expected at least one user"

mine = user.query(UserQuery(email=u.userId))
print("user.list by email=", [x.userId for x in mine])
assert any(x.id == u.id for x in mine.all()), "Own user not found via list()"

u = user.get_by_email("does@not.exist.com")
print("get_by_email", u)
if u is not None:
    raise Exception("get_by_email: Test failed!")

u = user.get_by_guid('DEADB33F-1111-1111-1111-00000DEADB33F')
print("get_by_guid", u)
if u is not None:
    raise Exception("get_by_guid: Test failed!")
