#!/bin/bash

set -e

cd "$(dirname "$0")/../"

python3 -m pip install iotconnect-sdk-lite

pushd tests 2>/dev/null
set -x
python3 firmware.py   # run this first. It will clean up any residue
python3 command.py    # the command test will generate some files that we need in the next steps
python3 template.py
python3 user.py
python3 entity.py
python3 device.py
python3 telemetry.py
python3 gencert.py
python3 storage.py
set +x
popd 2>/dev/null

echo "Tests Executed Successfully"

