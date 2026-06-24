# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from typing import Optional, List, Union

from . import apiurl, device, util
from .apirequest import request
from .error import UsageError, NotFoundResponseError

# The history endpoints reject ranges wider than 7 days (HTTP 412). We validate up front
# to turn that into a clean error instead of a server-side rejection.
_MAX_RANGE = timedelta(days=7)

# Default window used by get_latest() when the caller does not specify a range. The history
# feed is returned newest-first, so a single page over this window yields the most recent data.
_DEFAULT_LOOKBACK = timedelta(days=7)

# POST /Telemetry/device/{uniqueId}/recent/{dataPoints} constrains dataPoints to this range.
_RECENT_MIN = 10
_RECENT_MAX = 50


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


def get_history(
        duids: Union[str, List[str]],
        from_time: datetime,
        to_time: Optional[datetime] = None,
        time_sorted: bool = True
) -> List[TelemetryRecord]:
    """
    Get historical telemetry for one or more devices over a time range.

    Accepts either a single DUID string or a list of DUIDs (at least one is required). Each
    returned record is annotated with both its DUID (``uniqueId``) and its ``deviceGuid``.

    Note: this fetches the most recent page per device. The IoTConnect multi-device history
    endpoint is currently unreliable, so this iterates the per-device history endpoint instead.

    :param duids: A single DUID, or a list of DUIDs.
    :param from_time: Oldest point in time to include. Naive datetimes are treated as UTC.
    :param to_time: Newest point in time to include. Defaults to the current time (UTC).
    :param time_sorted: When True (default), the combined result is sorted newest-first across
        all devices. When False, records are grouped in the order the devices were supplied.
    :return: A list of TelemetryRecord.
    """
    duids = _normalize_duids(duids)
    if to_time is None:
        to_time = datetime.now(timezone.utc)
    if to_time - from_time > _MAX_RANGE:
        raise UsageError('The telemetry history range must not exceed 7 days')

    from_str = util.to_api_datetime(from_time)
    to_str = util.to_api_datetime(to_time)

    records: List[TelemetryRecord] = []
    for duid in duids:
        dev = device.get_by_duid(duid)
        if dev is None:
            raise NotFoundResponseError(f'get_history: Device with DUID "{duid}" not found')
        records.extend(_fetch_device_page(duid, dev.guid, from_str, to_str))

    if time_sorted:
        records.sort(key=lambda r: util.parse_iso_datetime(r.dTime), reverse=True)
    return records


def get_latest(duids: Union[str, List[str]], time_sorted: bool = True) -> List[TelemetryRecord]:
    """
    Get the most recent page of telemetry for one or more devices.

    Convenience wrapper around :func:`get_history` using a default lookback window. Intended for
    "just show me the latest data" use cases where an explicit range is not needed.

    :param duids: A single DUID, or a list of DUIDs.
    """
    now = datetime.now(timezone.utc)
    return get_history(duids, from_time=now - _DEFAULT_LOOKBACK, to_time=now, time_sorted=time_sorted)


def get_since(
        duids: Union[str, List[str]],
        oldest: datetime,
        time_sorted: bool = True
) -> List[TelemetryRecord]:
    """
    Get telemetry for one or more devices from the ``oldest`` time up to now.

    :param duids: A single DUID, or a list of DUIDs.
    :param oldest: Oldest point in time to include. Naive datetimes are treated as UTC.
    """
    return get_history(duids, from_time=oldest, time_sorted=time_sorted)


def get_last(
        duids: Union[str, List[str]],
        period: timedelta,
        time_sorted: bool = True
) -> List[TelemetryRecord]:
    """
    Get telemetry for one or more devices over the most recent ``period`` of time.

    For example, the last five minutes of data::

        telemetry.get_last("my-device", timedelta(minutes=5))

    :param duids: A single DUID, or a list of DUIDs.
    :param period: How far back from now to look.
    """
    if not isinstance(period, timedelta):
        raise UsageError('get_last: "period" must be a timedelta')
    now = datetime.now(timezone.utc)
    return get_history(duids, from_time=now - period, to_time=now, time_sorted=time_sorted)


def get_recent(
        duid: str,
        data_points: int = _RECENT_MIN,
        child_duid: Optional[str] = None,
        filter_attrs: Optional[List[str]] = None
) -> List[dict]:
    """
    Get the most recent data points for a single device's attributes.

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
    value = response.data.value
    return value if isinstance(value, list) else []


def get_current_values(duid: str) -> List[DeviceSensorValue]:
    """
    Get the latest value of each of a device's attributes (its current sensor snapshot).

    The underlying endpoint is keyed by device GUID, so the DUID is resolved to a GUID first.

    :param duid: Device Unique ID.
    :return: A list of the device's attributes with their most recent values.
    """
    if duid is None:
        raise UsageError('get_current_values: The device Unique ID (DUID) argument is missing')
    dev = device.get_by_duid(duid)
    if dev is None:
        raise NotFoundResponseError(f'get_current_values: Device with DUID "{duid}" not found')

    response = request(apiurl.ep_telemetry, f'/Telemetry/device/{dev.guid}', codes_ok=[HTTPStatus.NO_CONTENT])
    items = response.data.value or []
    return [
        DeviceSensorValue(**util.normalize_keys(util.filter_dict_to_dataclass_fields(item, DeviceSensorValue)))
        for item in items
    ]
