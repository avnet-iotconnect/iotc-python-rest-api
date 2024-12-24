from http import HTTPStatus

import requests
from jsonpath_ng.ext import parse
from requests.adapters import HTTPAdapter, Retry

from . import credentials
from .error import ResponseError


class Headers(dict[str, str]):
    N_CONTENT_TYPE = "Content-Type"
    N_ACCEPT = "Accept"
    N_AUTHORIZATION = "Authorization"
    V_APP_JSON = "application/json"


from typing import Any


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
            raise ResponseError("Unable to obtain response")
        if self.status not in codes_ok:
            raise ResponseError("Bad HTTP response status: " + str(self.status))

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
            raise ResponseError('Could not locate "%s" in the response' % expr)
        return value

    def get_values_or_raise(self, expr) -> Any:
        values = self.get_values(expr)
        if len(values) == 0:
            raise ResponseError('Could not locate "%s" in the response' % expr)
        return values


def request(endpoint: str, path: str, data=None, headers: dict[str, str] = None):
    # print("data=%s" % data)
    s = requests.Session()
    retries = Retry(total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    s.mount('https://', HTTPAdapter(max_retries=retries))
    if headers is None:  # default headers
        headers = credentials.get_auth_headers()
    if data is not None:
        response = Response(s.post(endpoint + path, json=data, headers=headers))
    else:
        response = Response(s.get(endpoint + path, json=data, headers=headers))
    response.ensure_success()
    return response
