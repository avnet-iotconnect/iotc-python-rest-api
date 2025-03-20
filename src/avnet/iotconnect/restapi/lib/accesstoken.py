import base64
import json
from dataclasses import dataclass, field
from typing import Optional

from . import config, util


@dataclass
class AccessTokenUser:
    id: str
    companyId: str
    roleId: str
    roleName: str
    cpId: str
    entityGuid: str
    solutionGuid: str
    solutionKey: str
    reviewStatus: str = field(default=None) # NOTE: Not available on the access token obtained from refresh!
    isCpidOptional: bool = field(default=None) # true if is dedicated instance. NOTE: Not available on the access token obtained from refresh!

@dataclass
class AccessToken:
    exp: int
    iss: str
    aud: str
    user: AccessTokenUser = field(default_factory=AccessTokenUser)


def decode_access_token() -> Optional[AccessToken]:
    if config.access_token is None:
        return None
    # without needing to add jwt package...
    parts = config.access_token.split('.')
    if len(parts) != 3:
        return None
    payload = parts[1]
    # Payload will need to be padded for proper base46 decoding.
    if len(payload) % 4 != 0:
        payload += "=" * (4 - len(payload) % 4)
    decoded_payload = base64.b64decode(payload)
    data = json.loads(decoded_payload.decode("utf-8"))
    return util.deserialize_dataclass(AccessToken, data)

