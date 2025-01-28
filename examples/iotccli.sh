#!/bin/bash
# Top level bash script that can be used to route and invoke the basic CLI.

set -e # in case this script ends up having more than one line

python3 -c "import sys; import avnet.iotconnect.restapi.cli.main as cli; cli.process(sys.argv[1:])" "${@}"
