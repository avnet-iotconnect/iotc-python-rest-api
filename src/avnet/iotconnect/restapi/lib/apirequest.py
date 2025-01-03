from dataclasses import make_dataclass, Field
from http import HTTPStatus, HTTPMethod
from typing import Optional, TypeVar, Union, Protocol, ClassVar, Any

import jmespath
import requests
from requests.adapters import HTTPAdapter, Retry

from . import config
from .error import ResponseError, AuthError, ApiException, SingleValueExpected

_get_auth_headers = None  # avoid circular dependency


class Headers(dict[str, str]):
    N_CONTENT_TYPE = "Content-Type"
    N_ACCEPT = "Accept"
    N_AUTHORIZATION = "Authorization"
    V_APP_JSON = "application/json"

# Credit: intgr - stackoverflow example https://stackoverflow.com/questions/61736151/how-to-make-a-typevar-generic-type-in-python-with-dataclass-constraint
class DataclassInstance(Protocol):
    __dataclass_fields__: ClassVar[dict[str, Field[Any]]]

T = TypeVar('T', bound=DataclassInstance)

class Parser:
    def __init__(self, value: Optional[dict]):
        self.value = value if value is not None else []

    def get(self, expr: Optional[str] = '[*]', dc: Optional[T] = None) -> Union[list[dict], list[T]]:
        ret = jmespath.search(expr, self.value)
        if dc is None:
            return ret
        else:
            object_list = []
            for item in ret:
                object_list.append(make_dataclass(dc.__name__, ((k, type(v)) for k, v in item.items()))(**item))
            return object_list

    def get_one(self, expr='[*]', dc: Optional[T] = None) -> Optional[Union[dict, T]]:
        values = self.get(expr, dc)
        if values is None or len(values) == 0:
            return None
        if len(values) > 1:
            raise SingleValueExpected
        return values[0]

    def get_object_value(self, expr) -> Any:
        """ Return value from content that is not an array """
        return jmespath.search(expr, self.value)


class Response:
    def __init__(self, response: requests.Response):
        self.response = response
        self.status = response.status_code
        self.body = Parser(None)
        self.data = Parser(None)

        try:
            self.body = Parser(response.json())
            self.data = Parser(self.body.value.get("data"))
            if config.api_trace_enabled:
                print("Response: status=%d body=%s" % (self.status, self.body.value))
        except requests.exceptions.JSONDecodeError:
            if config.api_trace_enabled:
                print("Raw Response:", response)
            raise ApiException("API request failed. Status: %d (%s)" % (self.status, HTTPStatus(self.status).phrase))

    def ensure_success(self, codes_ok: list[int] = frozenset([HTTPStatus.OK])) -> None:
        """If status is bad - raise exception"""
        if self.status not in codes_ok:
            if len(self.body.value) == 0:
                raise ResponseError("Unable to obtain response")
            value_status = self.body.get('status')
            if value_status is not None:
                message = self.body.get('message')
                if message is None:
                    message = "The server returned HTTP code %d." % value_status
                else:
                    message = 'Server reported message: "%s."' % message  # give a cleaner report
                errors = self.body.get('error')
                # try parse out errors:
                if errors is not None and type(errors) is list:
                    message += " Errors: "
                    for e in errors:
                        message += str(e) + " "
                if value_status == 401:
                    raise AuthError(message)
                else:
                    raise ResponseError(message)
            else:
                raise ResponseError("Bad HTTP response status: " + str(self.status))


def request(endpoint: str, path: str, data: Optional[dict] = None, headers: dict[str, str] = None, method: Optional[HTTPMethod] = None, allow_failure=False, files=None):
    s = requests.Session()
    retries = Retry(total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    s.mount('https://', HTTPAdapter(max_retries=retries))
    if config.api_trace_enabled:
        traced_data = data
        if isinstance(traced_data, dict) and traced_data.get('password') is not None:  # do not print passwords
            traced_data = dict(traced_data)
            traced_data['password'] = '*******'
        print("%s%s data=%s" % (endpoint, path, traced_data))

    if headers is None:  # default headers
        # avoid circular dependency
        global _get_auth_headers
        if _get_auth_headers is None:
            from .credentials import get_auth_headers
            _get_auth_headers = get_auth_headers
        headers = _get_auth_headers()

    if method is None:  # figure out default method
        if data is not None or files is not None:
            method = HTTPMethod.POST
        else:
            method = HTTPMethod.GET

    response = Response(s.request(method, endpoint + path, json=data, headers=headers, files=files))
    if not allow_failure:
        response.ensure_success()
    return response
