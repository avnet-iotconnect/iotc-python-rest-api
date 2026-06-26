# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Avnet
# Authors: Nikola Markovic <nikola.markovic@avnet.com> et al.


import json
import os
import sys
from datetime import datetime, timedelta, timezone

import avnet.iotconnect.restapi.lib.telemetry as telemetry
from avnet.iotconnect.restapi.lib.error import UsageError
from avnet.iotconnect.restapi.lib.telemetry import TelemetryRecord, DeviceSensorValue, TelemetryQuery

"""
Sanity checks for the telemetry read functions. These hit a live account, so a
device (identified by IOTC_DUID or iotcDeviceConfig.json) must exist. The device
need not be actively sending data - the calls should still succeed and simply
return empty lists when there is no telemetry.
"""

DUID = os.environ.get('IOTC_DUID')

# try load duid from iotcDeviceConfig.json
if DUID is None:
    try:
        with open('iotcDeviceConfig.json', 'r') as file:
            device_data = json.load(file)
            DUID = device_data.get('uid')
    except RuntimeError:
        pass

if DUID is None:
    print("Unable to determine DUID. Please provide iotcDeviceConfig.json")
    sys.exit(-1)


# --- current values (sensor snapshot) -------------------------------------

values = telemetry.get_current_values(DUID)
print('get_current_values count=', len(values))
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
