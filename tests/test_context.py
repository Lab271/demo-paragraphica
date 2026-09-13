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


# --- forward geocoding (#29) ---

ROUEN = {
    "properties": {"feature_type": "street", "full_address": "Rue D'amsterdam, 76800 Saint-Étienne-du-Rouvray, France"},
    "geometry": {"coordinates": [1.089, 49.397]},
}
JORDAAN = {
    "properties": {"feature_type": "neighborhood", "full_address": "Jordaan, Amsterdam, North Holland, Netherlands"},
    "geometry": {"coordinates": [4.88, 52.376]},
}
NEPAL = {
    "properties": {"feature_type": "place", "full_address": "Ligha, Lumbini Province, Nepal"},
    "geometry": {"coordinates": [82.9, 28.3]},
}


def test_pick_mapbox_hit_rejects_streets_and_unrelated_places():
    assert context.pick_mapbox_hit("amsterdam wallen", [ROUEN]) is None
    assert context.pick_mapbox_hit("amsterdam red light district", [NEPAL]) is None
    assert context.pick_mapbox_hit("amsterdam jordaan", [ROUEN, JORDAAN]) == context.Located(
        52.376, 4.88, JORDAAN["properties"]["full_address"]
    )
    assert context.pick_mapbox_hit("Amsterdam", []) is None


def test_parse_geocode():
    got = context.parse_geocode(
        '```json\n{"name": "De Wallen, Amsterdam, Netherlands", "lat": 52.3747, "lon": 4.8986}\n```'
    )
    assert got == context.Located(52.3747, 4.8986, "De Wallen, Amsterdam, Netherlands")
    assert context.parse_geocode('{"name": null}') is None
    assert context.parse_geocode("no idea") is None
    assert context.parse_geocode('{"name": "x", "lat": "north"}') is None


def test_geocode_falls_back_to_model_then_gives_up(monkeypatch):
    monkeypatch.setattr(context.api, "call_mapbox_forward", lambda q: [ROUEN])
    asked = []

    def describe(messages):
        asked.append(messages[1]["content"])
        return '{"name": "De Wallen, Amsterdam, Netherlands", "lat": 52.37, "lon": 4.9}'

    assert context.geocode("amsterdam wallen", describe).name == "De Wallen, Amsterdam, Netherlands"
    assert asked == ["amsterdam wallen"]

    monkeypatch.setattr(context.api, "call_mapbox_forward", lambda q: [JORDAAN])
    assert context.geocode("amsterdam jordaan", describe).lat == 52.376
    assert asked == ["amsterdam wallen"]  # Mapbox hit accepted, model not consulted

    with pytest.raises(context.LocationNotFound):
        context.geocode("xyzzyq", lambda m: '{"name": null}')
