import argparse
import json
import os
import sys

import avnet.iotconnect.restapi.lib.credentials as credentials
import avnet.iotconnect.restapi.lib.apiurl as apiurl
from avnet.iotconnect.restapi.lib.error import UsageError, ApiException


def init():
    def _register_configure(ap: argparse.ArgumentParser) -> None:
        description = \
            """ 
            Configure IoTConnect credentials.
            Credentials from the environment will be used if arguments are not supplied.
            This action will store the API token into the configuration file
            and allow you to run this tool without authenticating for 24 hours.            
            """
        ap.description = description
        ap.add_argument(
            "-u", "--username", dest="username", default=os.environ.get("IOTC_USER"),
            help="Your username/email - or use the IOTC_USER environment variable."
        )
        ap.add_argument(
            "-p", "--password", dest="password", default=os.environ.get("IOTC_PASS"),
            help="your password. Be mindful of leaving this password in your OS command history and pass it as IOTC_PASSWORD environment variable instead."
        )
        ap.add_argument(
            "-s", "--skey", dest="skey", default=os.environ.get("IOTC_SKEY"),
            help="your solution key."
        )
        ap.add_argument(
            "-pf", "--platform", dest="platform", choices=apiurl.PF_CHOICES, default=os.environ.get("IOTC_PF") or apiurl.PF_AWS,
            help='account platform ("aws" for AWS, or "az" for azure) - or use the IOTC_ENV environment variable.'
        )
        ap.add_argument(
            "-e", "--env", dest="env", choices=apiurl.ENV_CHOICES, default=os.environ.get("IOTC_ENV") or apiurl.ENV_UAT,
            help='account solution environment - or use IOTC_ENV environment variable. NOTE: "poc" environment is usually "uat"'
        )

    def _register_refresh(ap: argparse.ArgumentParser) -> None:
        description = \
            """ 
            Attempt to refresh an existing token. This action will store the refreshed token into configuration
            and allow you to run this tool without authenticating for 24 hours.
            """
        ap.description = description

    def _process_configure(a: argparse.Namespace) -> None:
        apiurl.configure(apiurl.default_endpoint_mapper(a.platform, a.env))
        credentials.authenticate(username=a.username, password=a.password, solution_key=a.skey)
        print("Logged in successfully.")

    def _process_refresh(a: argparse.Namespace) -> None:
        credentials.refresh()
        print("Token refreshed successfully.")



    main_description = \
        """ 
        Use IoTConnect REST API to perform account and device operations.
        Invoke \"configure\" first to log in. This will create a session token which will be stored
        on your system. This token will be used and refreshed automatically in subsequent invocations.
        """
    parser = argparse.ArgumentParser(
        prog='iotccli',
        description=main_description
    )
    subparsers = parser.add_subparsers(title="commands", description="Available subcommands", dest="command")
    subparsers.required = True
    subparser = subparsers.add_parser('configure')
    subparser.set_defaults(func=_process_configure)
    _register_configure(subparser)
    subparser = subparsers.add_parser('refresh')
    subparser.set_defaults(func=_process_refresh)
    _register_refresh(subparser)
    return parser

def process(argv):
    args = _parser.parse_args(argv)
    try:
        args.func(args)
    except ApiException as ex:
        print(ex)
        sys.exit(1)


_parser = init()


