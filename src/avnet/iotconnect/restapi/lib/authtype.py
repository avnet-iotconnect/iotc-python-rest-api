# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

"""
IoTConnect authentication type codes.

Single source of truth for the ``authType`` value on a device template and the matching
``at`` value in ``iotcDeviceConfig.json`` - they share this one enum.
See https://docs.iotconnect.io/iotconnect/sdk/message-protocol/device-message-2-1/reference-table/#authtypes
"""

AT_CA_SIGNED = 2
AT_SELF_SIGNED = 3
AT_TPM = 4
AT_SYMMETRIC_KEY = 5
AT_CA_INDIVIDUAL = 7
