# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

"""
Shared building blocks for endpoint query options (filtering, sorting, pagination)
and mutation inputs.

The IoTConnect REST list endpoints expose strongly-typed query parameters plus a
common pagination scheme (``pageNumber`` / ``pageSize`` / ``sortBy``), and their
responses carry a sibling ``count`` next to ``data``. These helpers model that
uniformly:

* :class:`Params` - a base dataclass whose :func:`api_param` fields serialize to
  the API's query/body parameter names, with optional *resolvers* that convert a
  friendly value (a DUID, a template code, an entity name) into the GUID the API
  expects.
* :class:`Query` - :class:`Params` plus pagination and sorting.
* :class:`Page` - the result wrapper returned by list operations: the current
  page of items plus the total ``count``, with transparent auto-paging via
  :meth:`Page.all`.

A field declares both its API name and (optionally) how a friendly value maps to
the API value, so a single :meth:`Params.to_params` handles every endpoint the
same way::

    @dataclass
    class DeviceQuery(Query):
        duid:     Optional[str] = api_param("UniqueId")
        status:   Optional[DeviceStatus] = api_param("Status")          # enum -> "active"
        template: Optional[str] = api_param("TemplateGuid", resolver=_resolve_template)
"""

import re
from dataclasses import dataclass, field, fields, replace
from enum import Enum
from http import HTTPStatus
from typing import Any, Callable, Generic, Iterator, Optional, TypeVar, Union

from .apirequest import request

T = TypeVar('T')


def api_param(
        name: str,
        *,
        resolver: Optional[Callable[[Any], Any]] = None,
        description: Optional[str] = None,
        examples: Optional[list] = None,
        default: Any = None,
):
    """
    Declare a query/body field that maps to the API parameter ``name``.

    :param name: The API parameter name this field serializes to (e.g. "UniqueId").
    :param resolver: Optional callable that converts a friendly value into the
        API's expected value (typically a friendly id -> GUID lookup). It is only
        invoked when the field has a non-None value.
    :param description: Human/agent-facing description. Carried in the field
        metadata so an MCP layer can surface it into a tool schema.
    :param examples: Optional example values, surfaced the same way as description.
    :param default: Field default. Defaults to None, meaning "not set" - the field
        is omitted from the request.
    """
    return field(default=default, metadata={
        'api': name,
        'resolver': resolver,
        'description': description,
        'examples': examples,
    })


_GUID_RE = re.compile(
    r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
)


def is_guid(value: Any) -> bool:
    """True if ``value`` looks like a GUID. Used by resolvers to skip lookups."""
    return isinstance(value, str) and bool(_GUID_RE.match(value.strip()))


def _serialize(value: Any) -> Any:
    """Convert a Python value into its API query-parameter representation."""
    if isinstance(value, bool):
        # IoTConnect expects lowercase string booleans in query params.
        return 'true' if value else 'false'
    if isinstance(value, Enum):
        return value.value
    return value


@dataclass
class Params:
    """
    Base for query/mutation inputs.

    Serializes the fields declared with :func:`api_param` into a dict of API
    parameters, applying per-field resolvers and value normalization. Fields
    declared without :func:`api_param` (e.g. pagination on :class:`Query`) are
    ignored here and handled by the subclass.
    """

    def to_params(self) -> dict[str, Any]:
        params: dict[str, Any] = {}
        for f in fields(self):
            meta = f.metadata
            if 'api' not in meta:
                continue  # not an API-mapped filter/body field
            value = getattr(self, f.name)
            if value is None:
                continue
            resolver = meta.get('resolver')
            params[meta['api']] = resolver(value) if resolver else _serialize(value)
        return params


class Order(Enum):
    ASC = 'asc'
    DESC = 'desc'


@dataclass
class Sort:
    """Typed sort spec; serializes to the API's "field asc" / "field desc" form."""
    field: str
    order: Order = Order.ASC

    def __str__(self) -> str:
        return f'{self.field} {self.order.value}'


@dataclass
class Query(Params):
    """:class:`Params` plus the pagination/sort options common to every list endpoint."""
    page: int = 1
    page_size: int = 100
    sort_by: Optional[Union[str, Sort]] = None

    def to_params(self) -> dict[str, Any]:
        params = super().to_params()
        params['pageNumber'] = self.page
        params['pageSize'] = self.page_size
        if self.sort_by is not None:
            params['sortBy'] = str(self.sort_by)
        return params


@dataclass
class Page(Generic[T]):
    """
    A single page of list results plus the total count, with transparent auto-paging.

    Iterate the wrapper directly to walk the current page, or :meth:`all` to walk
    every page without doing ``pageNumber`` arithmetic::

        page = device.query(DeviceQuery(status=DeviceStatus.ACTIVE))
        print(f"{page.total_count} active devices")
        for d in page.all():
            ...
    """
    items: list[T]
    page_number: int
    page_size: int
    total_count: Optional[int]  # None when the endpoint does not report a count (e.g. /Device)
    # Closure that fetches another page by number; set by the list operation.
    _fetch: Optional[Callable[[int], 'Page[T]']] = field(default=None, repr=False)

    def __iter__(self) -> Iterator[T]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    @property
    def total_pages(self) -> Optional[int]:
        if self.total_count is None:
            return None  # unknown without a count
        if self.page_size <= 0:
            return 1
        return max(1, (self.total_count + self.page_size - 1) // self.page_size)

    @property
    def has_next(self) -> bool:
        if self.total_count is None:
            # no count to page by, so assume more only while pages come back full
            return self.page_size > 0 and len(self.items) >= self.page_size
        return self.page_number < self.total_pages

    def all(self) -> Iterator[T]:
        """Yield every item across all pages, fetching subsequent pages on demand."""
        page = self
        while True:
            yield from page.items
            if not page.has_next or page._fetch is None:
                return
            page = page._fetch(page.page_number + 1)


def run_query(
        endpoint: str,
        path: str,
        query: Query,
        dc: type,
        *,
        codes_ok=(HTTPStatus.NO_CONTENT,),
) -> Page:
    """
    Execute a paginated list query and return a :class:`Page` of ``dc`` instances.

    Serializes ``query`` to API parameters, GETs ``endpoint + path``, maps the
    response ``data`` to ``dc``, and reads the envelope ``count`` for pagination.
    The returned page auto-pages via :meth:`Page.all`. ``HTTP 204`` is accepted by
    default so an empty list comes back cleanly.

    This is the single place list endpoints are wired up, so every ``*.query()``
    behaves identically.
    """
    def fetch(page_number: int) -> Page:
        q = replace(query, page=page_number)
        response = request(endpoint, path, params=q.to_params(), codes_ok=list(codes_ok))
        # count is absent on some endpoints (e.g. /Device returns -1); treat anything
        # not a real non-negative total as unknown so paging falls back to fullness.
        count = response.body.get_object_value('count')
        total_count = count if isinstance(count, int) and count >= 0 else None
        return Page(
            items=response.data.get(dc=dc),
            page_number=page_number,
            page_size=q.page_size,
            total_count=total_count,
            _fetch=fetch,
        )

    return fetch(query.page)
