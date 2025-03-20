# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

from http import HTTPMethod
from typing import Optional, List

from . import apiurl, entity
from .apirequest import request
from .error import UsageError

# OTA push types
OTA_TARGET_ENTITY=1
OTA_TARGET_ENTITY_WITH_SIBLINGS=2 # not supported
OTA_TARGET_DEVICE=3


def push_to_entity(upgrade_guid: str, entity_guid: Optional[str] = None, force: bool = True, scheduled_on: str = None):
    """
    Pushes the upgrade to the devices under the target entity and sub-entities of that entity.
    While draft entities can be pushed to handpicked targeted devices with push_ota_to_device(),
    push_ota_to_entity() can only be used with published upgrades.

    NOTE:

    :param upgrade_guid: GUID of the firmware upgrade.
    :param entity_guid: (Optional) GUID of the entity that will contain target devices to push firmware too.
        If not supplied, the account root entity will be used.
    :param force: (Optional) If this value is set to false, and specific upgrade
        has been previously pushed and is pending, this OTA push will have no effect.
    :param scheduled_on: (Optional) Set this value to a GMT time formatted by YYYY-MM-DD HH:mm:ss
        to schedule the OTA to start on a specific date and time.
    """

    if entity_guid is None:
       entity_guid = entity.get_root_entity().guid

    data = {
      "firmwareUpgradeGuid": upgrade_guid,
      "entityGuid": entity_guid,
      "isForceUpdate": force,
      # "isTrialDraft": False,  # We gain nothing by providing this value and drafts will fail pushing to entity anyway
      "target": OTA_TARGET_ENTITY,
      # "reportingGroupGuid": "string", # not supported yet
      # "isSphere": True    # not supported
    }
    if scheduled_on is not None:
        data['scheduledOn'] = scheduled_on

    response = request(apiurl.ep_firmware, '/ota-update', method=HTTPMethod.POST, json=data)
    return response.data.get_one()

def push_to_device(upgrade_guid: str, device_guids: List[str], is_draft=False, force: bool = True, scheduled_on: str = None):
    """
    Pushes the upgrade to the devices listed in the device_guids.

    :param upgrade_guid: GUID of the firmware upgrade.
    :param device_guids: A list of device GUIDs to which to push the OTA to. The list must have at least one device.
    :param is_draft: (Optional) While this value is optional, the caller should set this value to True if their
        upgrade is a draft (Upgrade.is_draft()) when using a draft to push to devices. If this is not set appropriately
        the push will fail on the back end.
    :param force: (Optional) If this value is set to false, and specific upgrade
        has been previously pushed and is pending, this OTA push will have no effect.
    :param scheduled_on: (Optional) Set this value to a GMT time formatted by YYYY-MM-DD HH:mm:ss
        to schedule the OTA to start on a specific date and time.
    """

    if device_guids is None or (len(device_guids) == 0):
        raise UsageError('device_guids parameter must be a list with at least one entry')


    data = {
      "firmwareUpgradeGuid": upgrade_guid,
      "isForceUpdate": force,
      "deviceGuids": device_guids,
      "isTrialDraft": is_draft,
      "target": OTA_TARGET_DEVICE,
      # "reportingGroupGuid": "string", # not supported yet
      # "isSphere": True    # not supported
    }
    response = request(apiurl.ep_firmware, '/ota-update', method=HTTPMethod.POST, json=data)
    return response.data.get_one()

