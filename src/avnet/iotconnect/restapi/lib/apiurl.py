# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

from . import apirequest, config

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

def configure_using_discovery():
    global ep_master, ep_auth, ep_user, ep_device, ep_firmware, ep_event, ep_telemetry, ep_file
    if config.skey is None:
        # nothing we can do until the user gives us the information
        return
    version = '2.1' if config.pf == 'aws' else '2'
    response = apirequest.request(f'https://discovery.iotconnect.io', f'/api/uisdk/solutionkey/{config.skey}/env/{config.env}', params={'version': version}, headers={})
    d = response.data
    ep_master = d.get_object_value("masterBaseUrl")
    ep_auth = d.get_object_value("authBaseUrl")
    ep_user = d.get_object_value("userBaseUrl")
    ep_device = d.get_object_value("deviceBaseUrl")
    ep_firmware = d.get_object_value("firmwareBaseUrl")
    ep_event = d.get_object_value("eventBaseUrl")
    ep_telemetry = d.get_object_value("telemetryBaseUrl")
    ep_file = d.get_object_value("fileBaseUrl")


configure_using_discovery()