# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

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
        return
    version = '2.1' if config.pf == 'aws' else '2'
    response = apirequest.request(f'https://discovery.iotconnect.io', f'/api/uisdk/solutionkey/{config.skey}/env/{config.env}', params={'version': version, 'pf':config.pf}, headers={})
    d = response.data
    ep_master = d.get_object_value("masterBaseUrl")
    ep_auth = d.get_object_value("authBaseUrl")
    ep_user = d.get_object_value("userBaseUrl")
    ep_device = d.get_object_value("deviceBaseUrl")
    ep_firmware = d.get_object_value("firmwareBaseUrl")
    ep_event = d.get_object_value("eventBaseUrl")
    ep_telemetry = d.get_object_value("telemetryBaseUrl")
    ep_file = d.get_object_value("fileBaseUrl")
