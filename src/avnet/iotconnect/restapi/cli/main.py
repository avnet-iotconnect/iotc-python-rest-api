# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

import argparse
import os
import sys

import avnet.iotconnect.restapi.lib.apiurl as apiurl
import avnet.iotconnect.restapi.lib.credentials as credentials
from avnet.iotconnect.restapi.lib import config, template, device, entity
from avnet.iotconnect.restapi.lib.error import ApiException, ConflictResponseError


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
            help='account platform ("aws" for AWS, or "az" for Azure) - or use the IOTC_ENV environment variable.'
        )
        ap.add_argument(
            "-e", "--env", dest="env", choices=apiurl.ENV_CHOICES, default=os.environ.get("IOTC_ENV") or apiurl.ENV_UAT,
            help='account environment - From settings -> Key Vault in the Web UI'
        )

    def _process_configure(a: argparse.Namespace) -> None:
        config.env = a.env
        config.pf = a.platform
        config.skey = a.skey
        apiurl.configure_using_discovery()
        credentials.authenticate(username=a.username, password=a.password)
        print("Logged in successfully.")

    #######################

    def _register_refresh(ap: argparse.ArgumentParser) -> None:
        description = \
            """ 
            Attempt to refresh an existing token. This action will store the refreshed token into configuration
            and allow you to run this tool without authenticating for 24 hours.
            """
        ap.description = description


    def _process_refresh(a: argparse.Namespace) -> None:
        credentials.refresh()
        print("Token refreshed successfully.")

    #######################

    def _register_create_template(ap: argparse.ArgumentParser) -> None:
        description = \
            """ 
            Create a new self-signed (Individual certificate) device given a template code and device DUID.
            Before invoking this command, Ensure that the API has been configured with with the \"configure\" command. 
            WARNING: At the time of creating this API, you will not be able to delete this device with the Web UI. Use the delete-device command. 
            """
        ap.description = description
        ap.add_argument(
            dest="template_path",
            help="Path to the Template JSON file, which contains the template definition (usually exported from a manually created template)."
        )
        ap.add_argument(
            "-n", "--code", dest="code", default=None,
            help='Optional template code to override and use instead of the code defined in the template JSON file'
        )
        ap.add_argument(
            "-e", "--name", dest="name", default=None,
            help='Optional template name to override and use instead of the name defined in the template JSON file'
        )

    def _process_create_template(a: argparse.Namespace) -> None:
        try:
            template.create(template_json_path=a.template_path, new_template_code=a.code, new_template_name=a.name)
        except ConflictResponseError as cre:
            print(f'Template either already exists or there was an error while creating the template. Error was:', cre)
            sys.exit(2)
        print("Template created successfully.")

    #######################

    def _register_create_device(ap: argparse.ArgumentParser) -> None:
        description = \
            """ 
            Create a new self-signed (Individual certificate) device given a template code and device DUID.
            Before invoking this command, Ensure that the API has been configured with with the \"configure\" command. 
            WARNING: At the time of creating this API, you will not be able to delete this device with the Web UI. Use the delete-device command. 
            """
        ap.description = description
        ap.add_argument(
            dest="template_code",
            help="Template code of your device Template."
        )
        ap.add_argument(
            dest="duid",
            help="Device Unique ID."
        )
        ap.add_argument(
            dest="cert", default=None,
            help="Path to a pem certificate of your device. You can generate one using the generate-cert command"
        )
        ap.add_argument(
            "-n", "--name", dest="name", default=None,
            help='Optional custom device Name. DUID value will be used by default'
        )
        ap.add_argument(
            "-e", "--entity", dest="entity", default=None,
            help='Optional name of the entity under which to create the dev ice. My default the top level entity will be used'
        )

    #######################

    def _register_delete_template(ap: argparse.ArgumentParser) -> None:
        description = \
            """ 
            Delete a template with given template code.
            """
        ap.description = description
        ap.add_argument(
            dest="code",
            help="Template code."
        )


    def _process_delete_template(a: argparse.Namespace) -> None:
        try:
            template.delete_match_code(a.code)
        except ConflictResponseError as cre:
            print(f'Template with code "{a.code}" appears to not exist or there was an error while deleting the template. Error was:', cre)
            sys.exit(2)
        print("Template deleted successfully.")

    #####################################################

    def _process_create_device(a: argparse.Namespace) -> None:
        if a.entity is not None:
            e = entity.get_by_name(a.entity)
            if e is None:
                print(f'Entity with name "{a.entity}" was not found')
                sys.exit(1)
        else:
            e = entity.get_root_entity()

        t = template.get_by_template_code(a.template_code)
        if t is None:
            print(f'Template with code "{a.template_code}" was not found')
            sys.exit(1)

        try:
            device.create(template_guid=t.guid, device_certificate=a.cert, duid=a.duid, name=a.name, entity_guid=e.guid)
        except ConflictResponseError as cre:
            print(f'Device with duid "{a.entity}" appears to already exist or there was an error while creating the device. Error was:', cre)
            sys.exit(2)
        print("Device created successfully.")

    #######################


    def _register_delete_device(ap: argparse.ArgumentParser) -> None:
        description = \
            """ 
            Delete a device that was previously created with REST API.
            """
        ap.description = description
        ap.add_argument(
            dest="duid",
            help="Device Unique ID."
        )


    def _process_delete_device(a: argparse.Namespace) -> None:
        try:
            device.delete_match_duid(a.duid)
        except ConflictResponseError as cre:
            print(f'device with duid "{a.duid}" appears to not exist. Error was:', cre)
            sys.exit(2)
        print("Device deleted successfully.")

    #####################################################


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
    subparser = subparsers.add_parser('create-template')
    subparser.set_defaults(func=_process_create_template)
    _register_create_template(subparser)
    subparser = subparsers.add_parser('delete-template')
    subparser.set_defaults(func=_process_delete_template)
    _register_delete_template(subparser)
    subparser = subparsers.add_parser('create-device')
    subparser.set_defaults(func=_process_create_device)
    _register_create_device(subparser)
    subparser = subparsers.add_parser('delete-device')
    subparser.set_defaults(func=_process_delete_device)
    _register_delete_device(subparser)
    return parser

def process(argv):
    args = _parser.parse_args(argv)
    try:
        args.func(args)
    except ApiException as ex:
        print(ex)
        sys.exit(1)


_parser = init()


