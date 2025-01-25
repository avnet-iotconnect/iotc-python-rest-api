# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

# An example of how basic CLI can be invoked

import sys

import avnet.iotconnect.restapi.cli.main as cli

cli.process(sys.argv[1:])