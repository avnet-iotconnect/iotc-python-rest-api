# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from typing import List, Optional, Union

from . import apiurl, device, util
from .apirequest import request
from .error import UsageError, NotFoundResponseError

# The history endpoints reject ranges wider than 7 days (HTTP 412). We validate up front
# to turn that into a clean error instead of a server-side rejection.
_MAX_RANGE = timedelta(days=7)

# Default window used when a query does not specify a range. The history feed is returned
# newest-first, so a single page over this window yields the most recent data.
_DEFAULT_LOOKBACK = timedelta(days=7)

# POST /Telemetry/device/{uniqueId}/recent/{dataPoints} constrains dataPoints to this range.
_RECENT_MIN = 10
_RECENT_MAX = 50

# A point in time accepted by telemetry query options: a native ``datetime`` or an ISO-8601
# string (e.g. "2026-06-24T17:23:59Z"). Naive datetimes are treated as UTC.
TimeInput = Union[datetime, str]


@dataclass
class TelemetryRecord:
    """
    A single telemetry feed record, annotated with the device it belongs to.

    ``uniqueId`` (DUID) comes from the server; ``deviceGuid`` is filled in by this library so
    that every record carries both identifiers. ``attr`` is the raw attribute name/value map,
    left as a dict because its shape depends on the device template.
    """
    uniqueId: str
    deviceGuid: str
    dTime: Optional[str] = field(default=None)  # ISO-8601 UTC (GMT) string, e.g. 2026-06-24T17:23:59.590Z
    attr: dict = field(default_factory=dict)


@dataclass
class DeviceSensorValue:
    """A single attribute's most recent value, as shown on the device's sensor list."""
    attributeName: str
    attributeValue: Optional[str] = field(default=None)
    displayName: Optional[str] = field(default=None)
    deviceUpdatedDate: Optional[str] = field(default=None)  # ISO date-time string
    templateAttributeGuid: Optional[str] = field(default=None)
    DataType: Optional[str] = field(default=None)


@dataclass
class TelemetryQuery:
    """
    Options for reading historical telemetry (see :func:`get_history`).

    The time range can be given absolutely or relatively, using native Python types:

    * ``from_time`` accepts a ``datetime``, an ISO-8601 string, or a ``timedelta``. A
      ``timedelta`` is taken as a duration back from ``to_time`` - e.g.
      ``timedelta(minutes=5)`` means "the last 5 minutes".
    * ``to_time`` accepts a ``datetime`` or an ISO-8601 string, and defaults to now.

    If ``from_time`` is omitted, a default 7-day lookback is used. The resulting window
    must not exceed 7 days. Naive datetimes are treated as UTC.

    :param duids: A single DUID, or a list of DUIDs (at least one is required).
    :param from_time: Start of the range (datetime / ISO string / timedelta-before-``to_time``).
    :param to_time: End of the range (datetime / ISO string). Defaults to now.
    :param time_sorted: When True (default), records are sorted newest-first across all
        devices. When False, they are grouped in the order the devices were supplied.
    """
    duids: Union[str, List[str]]
    from_time: Optional[Union[datetime, str, timedelta]] = None
    to_time: Optional[TimeInput] = None
    time_sorted: bool = True


def get_history(query: TelemetryQuery) -> List[TelemetryRecord]:
    """
    Get historical telemetry for one or more devices over a time range.

    Each returned record is annotated with both its DUID (``uniqueId``) and its
    ``deviceGuid``. See :class:`TelemetryQuery` for the range options - the ``from_time``
    union covers the common cases without dedicated helpers::

        get_history(TelemetryQuery("dev"))                              # latest (default lookback)
        get_history(TelemetryQuery("dev", from_time=timedelta(minutes=5)))  # last 5 minutes
        get_history(TelemetryQuery("dev", from_time=some_datetime))     # since a point in time

    Note: this fetches the most recent page per device. The multi-device endpoint
    (POST /Telemetry/history) returns HTTP 500 on valid, correctly-formatted input
    (verified 2026-06-25), so this iterates the per-device history endpoint instead.
    """
    duids = _normalize_duids(query.duids)
    from_time, to_time = _resolve_range(query)
    from_str = util.to_api_datetime(from_time)
    to_str = util.to_api_datetime(to_time)

    records: List[TelemetryRecord] = []
    for duid in duids:
        dev = device.get_by_duid(duid)
        if dev is None:
            raise NotFoundResponseError(f'get_history: Device with DUID "{duid}" not found')
        records.extend(_fetch_device_page(duid, dev.guid, from_str, to_str))

    # The history endpoint has no sortBy (path params only), and we fetch each device's
    # feed separately, so the concatenation across devices is not globally ordered. Sort
    # client-side to merge the per-device feeds into one newest-first stream.
    if query.time_sorted:
        records.sort(key=lambda r: util.parse_iso_datetime(r.dTime), reverse=True)
    return records


def get_recent(
        duid: str,
        data_points: int = _RECENT_MIN,
        child_duid: Optional[str] = None,
        filter_attrs: Optional[List[str]] = None
) -> List[dict]:
    """
    Get the most recent data points for a single device's attributes.
    The putput will contain all values - even the ones that don't exist in the template.

    :param duid: Device Unique ID.
    :param data_points: Number of recent data points to return. Must be between 10 and 50.
    :param child_duid: Unique ID of a gateway child device, when reading from a child.
    :param filter_attrs: Optional list of attribute names to restrict the result to.
    :return: The raw list of recent telemetry records.
    """
    if duid is None:
        raise UsageError('get_recent: The device Unique ID (DUID) argument is missing')
    if not _RECENT_MIN <= data_points <= _RECENT_MAX:
        raise UsageError(f'get_recent: "data_points" must be between {_RECENT_MIN} and {_RECENT_MAX}')

    data = {}
    if child_duid is not None:
        data["childUniqueId"] = child_duid
    if filter_attrs is not None:
        data["filterAttrs"] = filter_attrs

    response = request(apiurl.ep_telemetry, f'/Telemetry/device/{duid}/recent/{data_points}', json=data, codes_ok=[HTTPStatus.NO_CONTENT])
    # Response ``data`` is an object ({count, feed, version}); the records are under ``feed``.
    raw = response.data.value
    feed = raw.get('feed') if isinstance(raw, dict) else None
    return feed or []


def get_latest_value(duid: str) -> List[DeviceSensorValue]:
    """
    Get the latest value of each of a device's attributes (its current sensor snapshot).

    Template-mapped, latest single value received from the device one per template attribute.
    Unmapped values are ignored.
    The underlying endpoint is keyed by device GUID, so the DUID is resolved to a GUID first.

    :param duid: Device Unique ID.
    :return: One :class:`DeviceSensorValue` per template attribute, with its most recent value.
    """
    if duid is None:
        raise UsageError('get_latest_value: The device Unique ID (DUID) argument is missing')
    dev = device.get_by_duid(duid)
    if dev is None:
        raise NotFoundResponseError(f'get_latest_value: Device with DUID "{duid}" not found')

    response = request(apiurl.ep_telemetry, f'/Telemetry/device/{dev.guid}', codes_ok=[HTTPStatus.NO_CONTENT])
    items = response.data.value or []
    return [
        DeviceSensorValue(**util.normalize_keys(util.filter_dict_to_dataclass_fields(item, DeviceSensorValue)))
        for item in items
    ]


# --- internals -------------------------------------------------------------

def _resolve_range(query: TelemetryQuery) -> tuple[datetime, datetime]:
    """Turn a query's flexible time inputs into a validated (from, to) datetime pair."""
    now = datetime.now(timezone.utc)
    to_time = util.coerce_datetime(query.to_time) if query.to_time is not None else now

    if query.from_time is None:
        from_time = to_time - _DEFAULT_LOOKBACK
    elif isinstance(query.from_time, timedelta):
        from_time = to_time - query.from_time
    else:
        from_time = util.coerce_datetime(query.from_time)

    if from_time > to_time:
        raise UsageError('The telemetry range "from_time" must be before "to_time"')
    if to_time - from_time > _MAX_RANGE:
        raise UsageError('The telemetry history range must not exceed 7 days')
    return from_time, to_time


def _normalize_duids(duids: Union[str, List[str]]) -> List[str]:
    """Accept a single DUID string or a list of them; return a clean, non-empty list."""
    if isinstance(duids, str):
        duids = [duids]
    elif isinstance(duids, (list, tuple)):
        duids = list(duids)
    else:
        raise UsageError('DUIDs must be a string or a list of strings')
    duids = [d.strip() for d in duids if d is not None and d.strip()]
    if len(duids) == 0:
        raise UsageError('At least one DUID must be provided')
    return duids


def _fetch_device_page(duid: str, device_guid: str, from_str: str, to_str: str) -> List[TelemetryRecord]:
    """Fetch one page of history for a single device and annotate each record with its DUID + GUID."""
    response = request(
        apiurl.ep_telemetry,
        f'/Telemetry/attribute-history/device/{duid}/from/{from_str}/to/{to_str}',
        codes_ok=[HTTPStatus.NO_CONTENT]
    )
    raw = response.data.value
    feed = raw.get('feed') if isinstance(raw, dict) else None
    records = []
    for item in (feed or []):
        records.append(TelemetryRecord(
            uniqueId=item.get('uniqueId', duid),
            deviceGuid=device_guid,
            dTime=item.get('dTime'),
            attr=item.get('attr') or {},
        ))
    return records
