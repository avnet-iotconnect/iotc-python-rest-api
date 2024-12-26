from http import HTTPStatus

import requests
import jmespath
from requests.adapters import HTTPAdapter, Retry

from . import config
from . import credentials
from .error import ResponseError, AuthError, MissingValueError, ApiException


class Headers(dict[str, str]):
    N_CONTENT_TYPE = "Content-Type"
    N_ACCEPT = "Accept"
    N_AUTHORIZATION = "Authorization"
    V_APP_JSON = "application/json"


from typing import Any, Optional


class Parser:
    def __init__(self, value: Optional[dict]):
        self.value = value if value is not None else {}

    def get(self, expr: str = '*'):
        result = jmespath.search(expr, self.value)
        return result[0] if len(result) == 1 else None

    def get_all(self, expr: str = '[*].*'):
        return jmespath.search(expr, self.value)


    def get_or_raise(self, expr) -> Any:
        value = self.get(expr)
        if value is None:
            raise MissingValueError('Could not locate "%s" in the response' % expr)
        return value

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
                print("Response: status=%d value=%s" % (self.status, self.body.value))
        except requests.exceptions.JSONDecodeError:
            raise ApiException("Unable to parse the response")

    def ensure_success(self, codes_ok: list[int] = frozenset([HTTPStatus.OK])) -> None:
        """If status is bad - raise exception"""
        if self.status not in codes_ok:
            if len(self.body.value) == 0:
                raise ResponseError("Unable to obtain response")
            value_status = self.body.get('status')
            if value_status is not None:
                message = self.body.get('message')
                if message is None:
                    message = "The server returned HTTP code %d" % value_status
                else:
                    message = 'Server reported message: "%s"' % message # give a cleaner report
                if value_status == 401:
                    raise AuthError(message)
                else:
                    raise ResponseError(message)
            else:
                raise ResponseError("Bad HTTP response status: " + str(self.status))

def request(endpoint: str, path: str, data: Optional[dict]=None, headers: dict[str, str] = None, allow_failure=False):
    # print("data=%s" % data)
    s = requests.Session()
    retries = Retry(total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    s.mount('https://', HTTPAdapter(max_retries=retries))
    if config.api_trace_enabled:
        traced_data = data
        if isinstance(traced_data, dict) and traced_data.get('password') is not None: # do not print passwords
            traced_data = dict(traced_data)
            traced_data['password'] = '*******'
        print("%s%s data=%s" % (endpoint, path, traced_data))
    if headers is None:  # default headers
        headers = credentials.get_auth_headers()
    if data is not None:
        response = Response(s.post(endpoint + path, json=data, headers=headers))
    else:
        response = Response(s.get(endpoint + path, json=data, headers=headers))
    if not allow_failure:
        response.ensure_success()
    return response
