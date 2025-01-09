import os
from typing import Callable

from .error import ConfigError

PF_AZ = "az"
PF_AWS = "aws"
PF_CHOICES = [PF_AWS, PF_AZ]
ENV_UAT = "uat"
ENV_PROD = "prod"
ENV_PROD_EU = "eu"
ENV_CHOICES = [ENV_UAT, ENV_PROD, ENV_PROD_EU]

ep_master = None
ep_auth = None
ep_user = None
ep_device = None
ep_firmware = None
ep_event = None
ep_telemetry = None
ep_file = None


def default_endpoint_mapper(platform: str, env: str) -> Callable[[str], str]:
    if platform not in PF_CHOICES:
        raise ConfigError('Invalid platform. Valid platforms are "%s"'% ', '.join(PF_CHOICES))
    elif env not in ENV_CHOICES:
        raise ConfigError('Invalid environment. Valid environments are "%s"' % ', '.join(ENV_CHOICES))

    # mapping example: https://docs.iotconnect.io/iotconnect/rest-api/auth/?env=uat&pf=aws, but Azure doesn't seem to be at 2.1 yet
    # Azure docs: https://developer.iotconnect.io/
    patterns = {
        PF_AZ: {
            ENV_UAT: "https://avnet%s.iotconnect.io/api/v2.0",
            ENV_PROD: "https://%s.iotconnect.io/api/v2.0",
            ENV_PROD_EU: "https://eu%s.iotconnect.io/api/v2.0",
        },
        PF_AWS: {
            ENV_UAT: "https://awspoc%s.iotconnect.io/api/v2.1",
            ENV_PROD: "https://%sconsole.iotconnect.io/api/v2.1",
            ENV_PROD_EU: "https://%sconsole.iotconnect.io/api/v2.1",  # there is no AWS prod EU at the moment, so we will return prod for simplicity
        }
    }
    pattern = patterns.get(platform).get(env)

    def format_url(endpoint_type: str) -> str:
        return pattern % endpoint_type

    return format_url


"""
This performs endpoint URL mapping for different environments (UAT, PROD..)
and endpoint types (auth, device ...) to a base url to which to apply API calls
"""
def configure(endpoint_mapper: Callable[[str], str] = None) -> None:
    if endpoint_mapper is None:
        raise ConfigError("Endpoint: endpoint_mapper is required!")
    global ep_master, ep_auth, ep_user, ep_device, ep_firmware, ep_event, ep_telemetry, ep_file
    ep_master = endpoint_mapper("master")
    ep_auth = endpoint_mapper("auth")
    ep_user = endpoint_mapper("user")
    ep_device = endpoint_mapper("device")
    ep_firmware = endpoint_mapper("firmware")
    ep_event = endpoint_mapper("event")
    ep_telemetry = endpoint_mapper("telemetry")
    ep_file = endpoint_mapper("file")

# Have some AWS UAT endpoints configured by default
configure(default_endpoint_mapper(os.environ.get("IOTC_PF") or PF_AWS, os.environ.get("IOTC_ENV") or ENV_UAT))
