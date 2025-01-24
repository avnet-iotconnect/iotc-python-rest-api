# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

import datetime
from typing import Tuple

from cryptography import x509
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID


def generate(common_name: str, validity_days: int =3650, curve=ec.SECP256R1()) -> Tuple[str, str]:
    """ Generates an Elliptic Curve private key and a self-signed certificate signed with the private key.
    :param common_name: Common name to use for the certificate. For example "my-device-1234"
    :param validity_days: How many days for the certificate to be valid. Default 10 years.
    :param curve: EC curve to use for the private key. Default is SECP256R1 (prime256v1) curve, as the most widely used.

    :return: Returns a tuple with the private key (first item) and certificate with PEM encoding as byrts.

    """
    private_key = ec.generate_private_key(curve)

    # Create a self-signed certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, common_name)
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
