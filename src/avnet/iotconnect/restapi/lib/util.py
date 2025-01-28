# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

# The JSON to object mapping was originally created with assistance from OpenAI's ChatGPT.
# For more information about ChatGPT, visit https://openai.com/

import datetime
import json
import os
from dataclasses import is_dataclass
from typing import Tuple, Type, Union, get_type_hints, TypeVar

from cryptography import x509
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from avnet.iotconnect.restapi.lib import config, user, token

T = TypeVar("T") # for deserializing below


def is_dedicated_instance() -> bool:
    """ Utility function for determining whether the MQTT ClientID needs to be prefixed with CPID, for example"""

    is_dedicated = token.decode_access_token().user.isCpidOptional
    if is_dedicated is not None:
        return is_dedicated
    else:
        # temporary workaround for issue https://avnet.iotconnect.io/support-info/2025012718120357
        return config.pf == config.PF_AWS and config.env == config.ENV_PROD


def get_mqtt_client_id(duid: str) -> str:
    """ If the instance is shared, the DUID needs to be prefixed with CPID to obtain the MQTT Client ID"""
    if is_dedicated_instance():
        return duid
    else:
        return f"{token.decode_access_token().user.cpId}-{duid}"

def generate_device_json(duid: str, auth_type: int = 2) -> str:
    """
    Generates a config json string that should be written to iotcDeviceConfig.json when running a python SDK
    :param duid: Device Uniqiue ID
    :param auth_type: 2 for Self-signed. 1 for CA-Signed authentication.
    :return:
    """
    device_json = {
        "ver": "2.1",
        "pf": config.pf,
        "cpid": token.decode_access_token().user.cpId,
        "env": config.env,
        "uid": duid,
        "did": get_mqtt_client_id(duid),
        "at": auth_type,
    }
    return json.dumps(device_json, indent=4) + os.linesep


def generate_ec_cert_and_pkey(duid: str, validity_days: int = 3650, curve=ec.SECP256R1()) -> Tuple[str, str]:
    """ Generates an Elliptic Curve private key and a self-signed certificate signed with the private key.
    :param duid: DUID to use for the certificate. For example "my-device-1234". This will be used to compose the Common Name.
    :param validity_days: How many days for the certificate to be valid. Default 10 years.
    :param curve: EC curve to use for the private key. Default is SECP256R1 (prime256v1) curve, as the most widely used.

    :return: Returns a tuple with the private key (first item) and certificate with PEM encoding as bytes.

    """
    private_key = ec.generate_private_key(curve)

    # Create a self-signed certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, get_mqtt_client_id(duid))
    ])
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=validity_days)
    ).sign(private_key, hashes.SHA256())

    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )

    return key_pem.decode('ascii'), cert_pem.decode('ascii')




def _is_optional_or_dataclass(field_type, value):
    """
    Check if a field type is either an Optional or a dataclass.
    """
    if hasattr(field_type, '__origin__') and field_type.__origin__ is Union:
        # Check for Optional[Type]
        inner_types = field_type.__args__
        if len(inner_types) == 2 and type(None) in inner_types:
            inner_type = [t for t in inner_types if t is not type(None)][0]
            return is_dataclass(inner_type)
    return is_dataclass(field_type)

def deserialize_dataclass(cls: Type[T], data: Union[dict, list]) -> T:
    """
    Recursively deserialize data into a dataclass or a list of dataclasses.
    """
    if isinstance(data, list):
        # Handle lists of dataclasses
        inner_type = cls.__args__[0] if hasattr(cls, '__args__') else None
        if inner_type and is_dataclass(inner_type):
            return [deserialize_dataclass(inner_type, item) for item in data]
        return data

    if isinstance(data, dict) and is_dataclass(cls):
        field_types = get_type_hints(cls)
        return cls(
            **{
                key: deserialize_dataclass(field_types[key], value)
                if key in field_types and _is_optional_or_dataclass(field_types[key], value)
                else (
                    deserialize_dataclass(field_types[key], value)
                    if key in field_types
                       and hasattr(field_types[key], '__origin__')
                       and field_types[key].__origin__ == list
                    else value
                )
                for key, value in data.items()
                if key in field_types  # Ignore unexpected fields
            }
        )
    return data