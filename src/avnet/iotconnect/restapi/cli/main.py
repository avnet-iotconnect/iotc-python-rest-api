import argparse
import json
import os
import sys

import avnet.iotconnect.restapi.lib.credentials as credentials
import avnet.iotconnect.restapi.lib.apiurl as apiurl
import avnet.iotconnect.restapi.lib.entity as entity
from avnet.iotconnect.restapi.lib.entity import query
from avnet.iotconnect.restapi.lib.error import ResponseError, UsageError, ApiException


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

    def _register_entity(ap: argparse.ArgumentParser) -> None:
        description = \
            """ 
            Query account entities.
            """
        ap.description = description

    def _process_configure(a: argparse.Namespace) -> None:
        apiurl.configure(apiurl.default_endpoint_mapper(a.platform, a.env))
        credentials.authenticate(username=a.username, password=a.password, solution_key=a.skey)

    def _process_refresh(a: argparse.Namespace) -> None:
        credentials.refresh()

    def _process_entity(a: argparse.Namespace) -> None:
        def _register_get(ap: argparse.ArgumentParser) -> None:
            description = \
                """ 
                Get one or more entities. If a single value is returned, it will be returned as a string. Otherwise JSON will be returned.        
                """
            ap.description = description
            ap.add_argument("-f", "--fields", dest="fields", nargs='+', default=None, help="Fields to return. By default all fields are returned")
            q = ap.add_mutually_exclusive_group()
            q.add_argument("-n", "--name", dest="name", default=None, help="Filter by name.")
            q.add_argument("-g", "--guid", dest="guid", default=None, help="Filter by GUID.")
            q.add_argument("-q", "--query", dest="query", default="*", help='Custom jmespath query (default="*").')

        def _register_get_root(ap: argparse.ArgumentParser) -> None:
            ap.description = "Get root entity of the account."
            ap.add_argument("-f", "--fields", dest="fields", nargs='+', default=None, help="Fields to return. By default all fields are returned")
            q = ap.add_mutually_exclusive_group()
            q.add_argument("-n", "--name", dest="name", default=None, help="Filter by name.")
            q.add_argument("-g", "--guid", dest="guid", default=None, help="Filter by GUID.")
            q.add_argument("-q", "--query", dest="query", default="*", help='Custom jmespath query (default="*").')

        def _process_get(a: argparse.Namespace) -> None:
            query_str = "*"
            if a.name is not None:
                query_str="?name=`%s`" % a.name
            if a.guid is not None:
                query_str="?guid=`%s`" % a.guid
            if a.query is not None:
                query_str = a.query
            result = entity.query(query_str=query_str, fields=a.fields)
            if type(result) is str:
                print(result)
            else:
                print(json.dumps(result))

        def _process_get_root(a: argparse.Namespace) -> None:
           print(entity.get_root_entity(fields=a.fields))

        sp = parser.add_subparsers(title="commands", description="Available subcommands", dest="command")
        sp.required = True
        sp = subparsers.add_parser('get')
        sp.set_defaults(func=_process_get)
        _register_get(sp)
        sp = subparsers.add_parser('get-root')
        subparser.set_defaults(func=_process_get_root)
        _register_get_root(sp)

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
    except UsageError as ex:
        print(ex)
        sys.exit(2)


_parser = init()


