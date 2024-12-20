import argparse
import sys

from avnet.iotconnect.restapi import CliCredentials

cli = CliCredentials()
cli.reg
cli.register_refresh(argparse.ArgumentParser(sys.argv[1:]))
c.random