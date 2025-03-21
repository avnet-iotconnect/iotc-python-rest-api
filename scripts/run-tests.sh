#!/bin/bash

set -e

cd "$(dirname "$0")/../"

python3 -m pip install iotconnect-sdk-lite

pushd tests 2>/dev/null
python3 command.py    # run this first - the command test will generate some files that we need
python3 template.py
python3 user.py
python3 entity.py
python3 device.py
python3 gencert.py
python3 storage.py
python3 firmware.py   # run this flast - it should clean up all residue in case there's some leftover
popd 2>/dev/null

echo "Tests Executed Successfully"

