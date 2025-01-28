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
    reviewStatus: str
    isCpidOptional: bool

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
    decoded_payload = base64.b64decode(payload)
    data = json.loads(decoded_payload.decode("utf-8"))
    return util.deserialize_dataclass(AccessToken, data)

