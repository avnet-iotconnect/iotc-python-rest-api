# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.
import json
from http import HTTPMethod

import requests

from avnet.iotconnect.restapi.lib.error import ConfigError

# This file provides API endpoints by using discovery https://discovery.iotconnect.io/api/uisdk/solutionkey/your-solution-key/env/your-device-env?version=v2
# for example and provides mapping similar to https://docs.iotconnect.io/iotconnect/rest-api/?env=uat&pf=az
# Note that Azure is not at 2.1 yet. Azure docs also available at: https://developer.iotconnect.io/.



ep_master = None
ep_auth = None
ep_user = None
ep_device = None
ep_firmware = None
ep_event = None
ep_telemetry = None
ep_file = None

def configure_using_discovery():
    from . import apirequest, config
    global ep_master, ep_auth, ep_user, ep_device, ep_firmware, ep_event, ep_telemetry, ep_file
    if config.skey is None:
        # nothing we can do until the user gives us the information
        # must return silently, and then we can fail when using API URL if this is wrong
        return
    version = '2.1' if config.pf == 'aws' else '2'
    from . import config
    # do a low level request here without using request local module in order to avoid circular dependencies
    response = requests.request(method=HTTPMethod.GET, url=f'https://discovery.iotconnect.io/api/uisdk/solutionkey/{config.skey}/env/{config.env}', params={'version': version, 'pf':config.pf}, headers={})
    if response.status_code != 200:
        raise ConfigError(f'Unable to resolve API URLS for platform={config.pf} env={config.env} SKEY={config.skey}. Response code {response.status_code}, body: {response.text}')

    d = response.json().get('data')

    ep_master = d.get("masterBaseUrl")
    ep_auth = d.get("authBaseUrl")
    ep_user = d.get("userBaseUrl")
    ep_device = d.get("deviceBaseUrl")
    ep_firmware = d.get("firmwareBaseUrl")
    ep_event = d.get("eventBaseUrl")
    ep_telemetry = d.get("telemetryBaseUrl")
    ep_file = d.get("fileBaseUrl")
