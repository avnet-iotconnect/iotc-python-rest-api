#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (C) 2024 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

set -e

this_dir=$(dirname "$0")

pushd "${this_dir}/.." >/dev/null
python3 -m pip install -e .

popd >/dev/null
