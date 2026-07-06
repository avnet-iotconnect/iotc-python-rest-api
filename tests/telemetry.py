# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.


import json
import os
import sys
from datetime import datetime, timedelta, timezone

import avnet.iotconnect.restapi.lib.telemetry as telemetry
from avnet.iotconnect.restapi.lib import device
from avnet.iotconnect.restapi.lib.error import UsageError
from avnet.iotconnect.restapi.lib.telemetry import TelemetryRecord, DeviceSensorValue, TelemetryQuery

"""
Sanity checks for the telemetry read functions. These hit a live account, so a
device must exist. The device to use is resolved in this order: 
- IOTC_TELEMETRY_DUID env var if present
- Otherwise, so the test can run unattended - the most recently
active device on the account (sorted by last communication). The device need not be
actively sending data: the calls still succeed and simply return empty lists when
there is no telemetry.
"""

DUID = os.environ.get('IOTC_TELEMETRY_DUID')


if DUID is None:
    page = device.query(device.DeviceQuery(
        sort_by=f'{device.SORT_LAST_COMMUNICATION} desc', page_size=1)
    )
    top = next(iter(page), None)
    if top is not None:
        DUID = top.uniqueId
        print(f"Auto-selected most recently active device: {DUID} (lastCommunication={top.lastCommunication})")
        if top.lastCommunication:
            try:
                age = datetime.now(timezone.utc) - datetime.fromisoformat(top.lastCommunication.replace('Z', '+00:00'))
                if age > timedelta(days=7):
                    print(f"  NOTE: newest activity is ~{age.days}d old; history may return empty.")
            except ValueError:
                pass

if DUID is None:
    print("Unable to find a feasible DUID for test. Set IOTC_TELEMETRY_DUID, or ensure the account has a device.")
    sys.exit(-1)


# --- latest value per template attribute (sensor snapshot) ----------------

values = telemetry.get_latest_value(DUID)
print('get_latest_value count=', len(values))
assert isinstance(values, list)
assert all(isinstance(v, DeviceSensorValue) for v in values)
for v in values[:5]:
    print('  ', v.attributeName, '=', v.attributeValue)


# --- recent data points ---------------------------------------------------

recent = telemetry.get_recent(DUID)  # defaults to the minimum (10) data points
print('get_recent count=', len(recent))
assert isinstance(recent, list)


# --- history (single entry point: get_history(TelemetryQuery)) -------------

# Latest (default lookback) - the common case, no range needed.
latest = telemetry.get_history(TelemetryQuery(duids=DUID))
print('latest count=', len(latest))
assert isinstance(latest, list)
assert all(isinstance(r, TelemetryRecord) for r in latest)

# "last N" and "since T" are expressed through the from_time union, which accepts a
# native datetime, an ISO-8601 string, or a timedelta (duration back from to_time).
q_dt = TelemetryQuery(duids=DUID, from_time=datetime.now(timezone.utc) - timedelta(hours=2))  # since a datetime
q_td = TelemetryQuery(duids=DUID, from_time=timedelta(hours=1))                                # the last hour
q_str = TelemetryQuery(duids=DUID, from_time=(datetime.now(timezone.utc) - timedelta(hours=2)).isoformat())  # ISO string
print('history via datetime/timedelta/str=',
      len(telemetry.get_history(q_dt)), len(telemetry.get_history(q_td)), len(telemetry.get_history(q_str)))

# results are annotated with both identifiers and sorted newest-first
if len(latest) > 0:
    r = latest[0]
    print('newest record: dTime=', r.dTime, 'uniqueId=', r.uniqueId, 'attr keys=', list(r.attr.keys()))
    assert r.uniqueId == DUID


# --- input validation (no network needed) ---------------------------------

try:
    telemetry.get_history(TelemetryQuery(duids=DUID, from_time=timedelta(days=30)))
    raise AssertionError("Expected a UsageError for a range wider than 7 days")
except UsageError:
    print("Correctly rejected a history range wider than 7 days.")

try:
    telemetry.get_history(TelemetryQuery(duids=DUID, from_time="not-a-date"))
    raise AssertionError("Expected a UsageError for an unparseable time string")
except UsageError:
    print("Correctly rejected an unparseable time string.")

try:
    telemetry.get_recent(DUID, data_points=5)
    raise AssertionError("Expected a UsageError for data_points below the minimum")
except UsageError:
    print("Correctly rejected data_points outside the allowed range.")

print("Telemetry sanity checks passed.")
