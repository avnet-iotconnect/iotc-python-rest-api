"""This module provides IoTConnect authentication functionality."""
from typing import Optional, Any

from . import apiurl
from .apirequest import request, Parser
from .error import UsageError

def query(query_str: str = '*', fields: Optional[list[str]] = None, single_value=False) -> Any:
    response = request(apiurl.ep_user, "/Entity/lookup")
    if single_value:
        return response.data.get_or_raise('[%s]%s' % (query_str, Parser.field_names_query_component(fields)))
    else:
        return response.data.get_all('[%s]%s' % (query_str, Parser.field_names_query_component(fields)))

def get_by_name(name: Optional[str] = None, fields: list[str] = ("guid",)) -> str:
    """Lookup an entity by name"""
    if name is None:
        raise UsageError('get_guid: The entity name argument is missing')
    return query('?name == `%s`' % name, fields, single_value=True)


def get_root_entity(fields: Optional[list[str]] = ("guid",)) -> str:
    """Find root entity for the account"""
    return query('?parentEntityGuid == null' , fields, single_value=True)

def get_all(fields: list[str] = None) -> list:
    return query(fields=fields)