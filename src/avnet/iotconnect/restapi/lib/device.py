"""This module provides IoTConnect authentication functionality."""
from typing import Optional, Any

from . import apiurl
from .apirequest import request, Parser
from .error import UsageError


def query_all(query_str: str = '*', fields: Optional[list[str]] = None, single_value=False) -> Any:
    response = request(apiurl.ep_user, "/Device/lookup")
    if single_value:
        return response.data.get_or_raise('[%s]%s' % (query_str, Parser.field_names_query_component(fields)))
    else:
        return response.data.get_all('[%s]%s' % (query_str, Parser.field_names_query_component(fields)))


def get_by_duid(duid: str) -> Any:
    """ Get device entry by device unique id (duid) """
    if duid is None:
        raise UsageError('get_by_duid: The device DUID argument is missing')
    response = request(apiurl.ep_user, "/api/v2/Device/uniqueId/" + duid)
    return response.data.get_or_raise('%s|[0]' % (Parser.field_names_query_component(fields)))
