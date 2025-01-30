# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

import argparse
import os
import sys

import avnet.iotconnect.restapi.lib.apiurl as apiurl
import avnet.iotconnect.restapi.lib.credentials as credentials
from avnet.iotconnect.restapi.lib import config, template, device, entity, util
from avnet.iotconnect.restapi.lib.error import ApiException, ConflictResponseError


def init():
    def _register_configure(ap: argparse.ArgumentParser) -> None:
        description = \
            """ 
            Configure IoTConnect credentials.
            Credentials from the environment will be used if arguments are not supplied.
            This action will store these settings configuration file
            and allow you to run this tool without authenticating for 24 hours since
            last authentication token (automatic) refresh.
            All arguments are required, but environment variables can be used instead.        
            """
        ap.description = description
        ap.add_argument(
            "-u", "--username", dest="username", default=os.environ.get("IOTC_USER"),
            help="Your account username (email). IOTC_USER environment variable can be used instead."
        )
        ap.add_argument(
            "-p", "--password", dest="password", default=os.environ.get("IOTC_PASS"),
            help="Your account password. IOTC_PASS environment variable can be used instead."
        )
        ap.add_argument(
            "-s", "--skey", dest="skey", default=os.environ.get("IOTC_SKEY"),
            help="Your solution key. IOTC_SKEY environment variable can be used instead."
        )
        ap.add_argument(
            "--pf", "--platform", dest="platform", choices=config.PF_CHOICES, default=os.environ.get("IOTC_PF") or config.PF_AWS,
            help='Account platform ("aws" for AWS, or "az" for Azure). IOTC_PF environment variable can be used instead.'
        )
        ap.add_argument(
            "-e", "--env", dest="env", choices=config.ENV_CHOICES, default=os.environ.get("IOTC_ENV") or config.ENV_POC,
            help='Account environment - From settings -> Key Vault in the Web UI. IOTC_ENV environment variable can be used instead.'
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
            "-c", "--cert", dest="cert", default="device-cert.pem",
            help='Path to a pem certificate of your device. You can generate one using the generate-cert command. Default is "device-cert.pem"'
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
            print(f'Device with duid "{a.duid}" appears to not exist or cannot be deleted. Error was:', cre)
            sys.exit(2)
        print("Device deleted successfully.")

    #######################

    def _register_generate_cert(ap: argparse.ArgumentParser) -> None:
        description = \
            """ 
            Create a self-signed private key and a certificate
            in the user's current working directory with the following names by default:
            device-pkey.pem: Private key generated with secp256r1 (prime256v1) EC curve
            device-cert.pem: A certificate based on this private key.
            DUID will be used (in combination with CPID as prefix) to generate a certificate that will match your device's MQTT Client ID 
            """
        ap.description = description
        ap.add_argument(
            dest="duid",
            help='Device Unique ID (DUID) to use for this certificate. See the command description for more info.'
        )
        ap.add_argument(
            "--cert-file", dest="cert_file", default="device-cert.pem",
            help='Optional file name and path to write the certificate key to. Default is device-cert.pem.'
        )
        ap.add_argument(
            "--pkey-file", dest="pkey_file", default="device-pkey.pem",
            help='Optional file name and path to write the private key to. Default is device-pkey.pem.'
        )

    def _process_generate_cert(a: argparse.Namespace) -> None:
        try:
            pkey_pem, cert_pem = util.generate_ec_cert_and_pkey(a.duid)
            with open(a.pkey_file, 'w') as pk_file:
                pk_file.write(pkey_pem)
            with open(a.cert_file, 'w') as cert_file:
                cert_file.write(cert_pem)
        except RuntimeError as ex:
            print("There was a problem while writing the files: ", ex)

        print(f'Certificate and private key were written to "{a.cert_file}" and "{a.pkey_file}".')

    #######################

    def _register_generate_device_json(ap: argparse.ArgumentParser) -> None:
        description = \
            """ 
            Generate iotcDeviceConfig.json that can be used along with a certificate and a private key to configure a Python SDK
            """
        ap.description = description
        ap.add_argument(
            dest="duid",
            help='Device Unique ID (DUID).'
        )
        ap.add_argument(
            "--file", dest="file", default="iotcDeviceConfig.json",
            help='Optional file name and path to write the json to. Default is "iotcDeviceConfig.json".'
        )

    def _process_generate_device_json(a: argparse.Namespace) -> None:
        try:
            device_json = util.generate_device_json(a.duid)
            with open(a.file, 'w') as f:
                f.write(device_json)
        except RuntimeError as ex:
            print("There was a problem while writing the file: ", ex)

        print(f'Device config JSON written to "{a.file}".')

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
    subparser = subparsers.add_parser('generate-cert')
    subparser.set_defaults(func=_process_generate_cert)
    _register_generate_cert(subparser)
    subparser = subparsers.add_parser('generate-device-json')
    subparser.set_defaults(func=_process_generate_device_json)
    _register_generate_device_json(subparser)
    return parser


def process(argv):
    args = _parser.parse_args(argv)
    try:
        args.func(args)
    except ApiException as ex:
        print(ex)
        sys.exit(1)


_parser = init()

def main():
    # entry hook for iotonnect-cli
    process(sys.argv[1:])

if __name__ == "__main__":
    main()