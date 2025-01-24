# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

from dataclasses import dataclass

from . import apiurl
from .apirequest import request
from .error import UsageError


@dataclass
class Entity:
    guid: str
    name: str
    parentEntityGuid: str


def query(query_str: str = '[*]') -> list[Entity]:
    response = request(apiurl.ep_user, "/Entity/lookup")
    return response.data.get(query_str, dc=Entity)


def query_expect_one(query_str: str = '[*]') -> Entity:
    response = request(apiurl.ep_user, '/Entity/lookup')
    return response.data.get_one(query_str, dc=Entity)


def get_by_name(name) -> Entity:
    """Lookup an entity by name"""
    if name is None:
        raise UsageError('get_by_name: The entity name argument is missing')
    return query_expect_one(f"[?name==`{name}`]")


def get_root_entity() -> Entity:
    """Find root entity for the account"""
    return query_expect_one('[?parentEntityGuid == null]')
