import requests
from http import HTTPStatus

from . import credentials
from .error import ResponseException
from jsonpath_ng.ext import parse


class Headers(dict[str, str]):
    N_CONTENT_TYPE = "Content-Type"
    N_ACCEPT = "Accept"
    N_AUTHORIZATION = "Authorization"
    V_APP_JSON = "application/json"


from typing import NoReturn, List, Any


class Response:
    def __init__(self, response: requests.Response):
        self.response = response
        self.status = response.status_code
        self.value = None
        try:
            self.value = response.json()
            print(self.value)
        except requests.exceptions.JSONDecodeError:
            pass

    def ensure_success(self, codes_ok: list[int] = frozenset([HTTPStatus.OK])) -> None:
        """If status is bad - raise exception"""
        if self.value is None:
            raise ResponseException("Unable to obtain response")
        if self.status not in codes_ok:
            raise ResponseException("Bad HTTP response status: " + str(self.status))

    def has_value(self, expr) -> bool:
        jsonpath_expr = parse(expr)
        return len(jsonpath_expr.find(self.value)) > 0

    def get_value(self, expr) -> Any:
        jsonpath_expr = parse(expr)
        lookup = jsonpath_expr.find(self.value)
        return lookup[0].value if len(lookup) == 1 else None

    def get_values(self, expr) -> Any:
        jsonpath_expr = parse(expr)
        lookup = jsonpath_expr.find(self.value)
        return list(r.value for r in lookup)

    def get_value_or_raise(self, expr) -> Any:
        value = self.get_value(expr)
        if value is None:
            raise ResponseException('Could not locate "%s" in the response' % expr)
        return value

    def get_values_or_raise(self, expr) -> Any:
        values = self.get_values(expr)
        if len(values) == 0:
            raise ResponseException('Could not locate "%s" in the response' % expr)
        return values


def request(endpoint: str, path: str, data=None, headers: dict[str, str] = None):
    if headers is None: # default headers
        headers = credentials.get_auth_headers()
    response = Response(requests.post(endpoint + path, json=data, headers=headers))
    response.ensure_success()
    return response
