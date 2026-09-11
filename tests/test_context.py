from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from paragraphica import context
from tests.conftest import SBP


def test_address_from_mapbox(mapbox_feature):
    assert context.address_from_mapbox(mapbox_feature) == "Boeingavenue, Schiphol-Rijk, Netherlands"


def test_address_without_street(mapbox_feature):
    del mapbox_feature["properties"]["context"]["street"]
    assert context.address_from_mapbox(mapbox_feature) == "Schiphol-Rijk, Netherlands"


def test_weather_from_openweathermap(owm_response):
    assert (
        context.weather_from_openweathermap(owm_response) == "The temperature is 10.06 degrees Celsius with few clouds."
    )


@pytest.mark.parametrize(
    "hour,expected",
    [
        (3, "dark night"),
        (6, "early in the morning"),
        (9, "morning"),
        (14, "afternoon"),
        (18, "early in the evening"),
        (22, "late in the evening"),
    ],
)
def test_time_of_day(hour, expected):
    assert context.time_of_day(hour) == expected


def test_local_hour_is_offline_and_zone_aware():
    # 12:00 UTC in February is 13:00 in Amsterdam (CET, no DST).
    noon_utc = datetime(2024, 2, 19, 12, 0, tzinfo=ZoneInfo("UTC"))
    assert context.local_hour(*SBP, now=noon_utc) == 13


def test_local_hour_falls_back_to_utc_when_no_zone(monkeypatch):
    monkeypatch.setattr(context, "_tf", type("NoZone", (), {"timezone_at": lambda self, lat, lng: None})())
    noon_utc = datetime(2024, 2, 19, 12, 0, tzinfo=ZoneInfo("UTC"))
    assert context.local_hour(0.0, -30.0, now=noon_utc) == 12


def test_build_context_uses_apis_only_when_asked(monkeypatch, mapbox_feature, owm_response):
    calls = []
    monkeypatch.setattr(context.api, "call_mapbox", lambda lat, lon: calls.append("mapbox") or mapbox_feature)
    monkeypatch.setattr(context.api, "call_openweathermap", lambda lat, lon: calls.append("owm") or owm_response)

    ctx = context.build_context(*SBP, include_time=False, include_weather=False)
    assert ctx == context.Context(address="Boeingavenue, Schiphol-Rijk, Netherlands", lat=SBP[0], lon=SBP[1])
    assert calls == ["mapbox"]

    ctx = context.build_context(*SBP, include_time=True, include_weather=True)
    assert ctx.weather.startswith("The temperature is 10.06")
    assert ctx.time_of_day
    assert calls == ["mapbox", "mapbox", "owm"]


def test_wander_stays_within_radius_and_is_seeded():
    import math
    import random

    a = context.wander(52.378, 4.9, 1500, random.Random(7))
    b = context.wander(52.378, 4.9, 1500, random.Random(7))
    assert a == b
    dlat = (a[0] - 52.378) * 111_320
    dlon = (a[1] - 4.9) * 111_320 * math.cos(math.radians(52.378))
    assert 0 < math.hypot(dlat, dlon) <= 1500
    assert context.wander(52.378, 4.9, 1500, random.Random(8)) != a
