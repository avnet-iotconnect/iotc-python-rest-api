# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

from dataclasses import make_dataclass, Field
from http import HTTPStatus, HTTPMethod
from typing import Optional, TypeVar, Union, Protocol, ClassVar, Any

import jmespath
import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RetryError
from urllib3 import Retry

from . import config
from .error import ResponseError, AuthError, ApiException, SingleValueExpected, ValueExpected, ConflictResponseError, NotFoundResponseError, ConfigError

_get_auth_headers = None  # avoid circular dependency


class Headers(dict[str, str]):
    N_CONTENT_TYPE = "Content-Type"
    N_ACCEPT = "Accept"
    N_AUTHORIZATION = "Authorization"
    V_APP_JSON = "application/json"


# Credit: "intgr" at stackoverflow example https://stackoverflow.com/questions/61736151/how-to-make-a-typevar-generic-type-in-python-with-dataclass-constraint
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
                # some json keys can have dashes it seems
                for key in item.copy().keys(): # copy so we don't affect keys while looping
                    if '-' in key:
                        new_key = key.replace('-', '_')
                        item[new_key] = item.pop(key)
                object_list.append(make_dataclass(dc.__name__, ((k, type(v)) for k, v in item.items()))(**item))
            return object_list

    def get_one(self, expr='[*]', dc: Optional[T] = None) -> Optional[Union[dict, T]]:
        values = self.get(expr, dc)
        if values is None or len(values) == 0:
            return None
        if len(values) > 1:
            raise SingleValueExpected
        return values[0]

    def get_or_raise(self, expr='[*]', dc: Optional[T] = None) -> Optional[Union[dict, T]]:
        ret = self.get_one(self, expr, dc)
        if ret is None:
            raise ValueExpected
        return ret

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
            if self.status not in (HTTPStatus.NO_CONTENT.value, HTTPStatus.NOT_FOUND.value):
                raise ApiException("API request failed. Status: %d (%s)" % (self.status, HTTPStatus(self.status).phrase), self.status)
            else:
                self.body.value = []

    def ensure_success(self, codes_ok: Optional[list[int]] = None) -> None:
        """If status is bad - raise exception"""
        acceptable_codes = [HTTPStatus.OK]
        if codes_ok is not None:
            acceptable_codes.extend(codes_ok)
        if self.status not in acceptable_codes:
#            if len(self.body.value) == 0:
#                raise ResponseError("Unable to obtain response", self.status)
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

                # differentiate between these cases for better error handling
                if self.status == HTTPStatus.FORBIDDEN.value:
                    raise AuthError(message)
                elif self.status == HTTPStatus.CONFLICT.value:
                    raise ConflictResponseError(message)
                elif self.status == HTTPStatus.NOT_FOUND.value:
                    raise NotFoundResponseError(message)
                else:
                    raise ResponseError(message, self.status)
            else:
                # the response body is missing so we give a generic problem
                if self.status == HTTPStatus.FORBIDDEN.value:
                    raise AuthError("")
                elif self.status == HTTPStatus.CONFLICT.value:
                    raise ConflictResponseError("")
                elif self.status == HTTPStatus.NOT_FOUND.value:
                    raise NotFoundResponseError("")
                else:
                    raise ResponseError("Bad HTTP response status: " + str(self.status), self.status)


def request(
        endpoint: str,
        path: str,
        json: Optional[dict] = None, # same as post data, but forces content type application/json
        data: Optional[dict] = None,
        params: Optional[dict] = None,
        headers: dict[str, str] = None,
        method: Optional[HTTPMethod] = None,
        allow_failure=False,
        files=None,
        codes_ok = frozenset([HTTPStatus.OK])
) -> Optional[Response]:

    # Catch all for unconfigured API
    if endpoint is None:
        raise ConfigError("API has not been configured!")

    s = requests.Session()
    retries = Retry(total=3, backoff_factor=0.1)
    s.mount('https://', HTTPAdapter(max_retries=retries))


    if headers is None:  # default headers
        # avoid circular dependency
        global _get_auth_headers
        if _get_auth_headers is None:
            from .credentials import get_auth_headers
            _get_auth_headers = get_auth_headers
        headers = _get_auth_headers()

    if method is None:  # figure out default method
        if json is not None or data is not None or files is not None:
            method = HTTPMethod.POST
        else:
            method = HTTPMethod.GET

    if config.api_trace_enabled:
        def remove_password(traced_data):
            if isinstance(traced_data, dict) and traced_data.get('password') is not None:  # do not print passwords
                traced_data = dict(traced_data)
                traced_data['password'] = '*******'

        print("%s %s%s json=%s data=%s params=%s" % (method, endpoint, path, remove_password(json), remove_password(data), params))

    try:
        response = Response(s.request(method, endpoint + path, data=data, json=json, params=params, headers=headers, files=files))
        if not allow_failure:
            response.ensure_success(codes_ok=codes_ok)
        return response
    except RetryError as ex:
        raise
