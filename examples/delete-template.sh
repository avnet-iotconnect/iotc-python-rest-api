#!/bin/bash
# Example of a useful shortcut script that can route the delete-template command to the CLI

set -e # in case this script ends up having more than one line

python3 -c "import sys; import avnet.iotconnect.restapi.cli.main as cli; cli.process(sys.argv[1:])" "${@:1}"