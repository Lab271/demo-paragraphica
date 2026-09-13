"""Where and when: the facts about a location that go into the prompt.

Pure functions over recorded API responses, plus one `build_context` that
performs the network calls. Timezone is computed offline."""

import json
import math
import random
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from timezonefinder import TimezoneFinder

from paragraphica import api

_tf = TimezoneFinder()

WEATHER_TEMPLATE = "The temperature is {} degrees Celsius with {}."

# Every value time_of_day() can produce; also the allowed values for a manual override.
TIMES_OF_DAY = (
    "early in the morning",
    "morning",
    "afternoon",
    "early in the evening",
    "late in the evening",
    "dark night",
)


@dataclass(frozen=True)
class Context:
    address: str
    time_of_day: str = ""
    weather: str = ""
    lat: float = 0.0  # where the description is about (after wandering, #22)
    lon: float = 0.0


def address_from_mapbox(feature: dict) -> str:
    """'Boeingavenue, Schiphol-Rijk, Netherlands' from a Mapbox v6 feature."""
    ctx = feature["properties"]["context"]
    parts = []
    if "street" in ctx:
        parts.append(ctx["street"]["name"])
    parts.append(ctx["place"]["name"])
    parts.append(ctx["country"]["name"])
    return ", ".join(parts)


def weather_from_openweathermap(res: dict) -> str:
    return WEATHER_TEMPLATE.format(res["main"]["temp"], res["weather"][0]["description"])


def time_of_day(hour: int) -> str:
    if hour > 19:
        return "late in the evening"
    if hour > 17:
        return "early in the evening"
    if hour > 11:
        return "afternoon"
    if hour > 7:
        return "morning"
    if hour > 5:
        return "early in the morning"
    return "dark night"


def local_hour(lat: float, lon: float, now: datetime | None = None) -> int:
    """Hour of day at (lat, lon), computed offline. Falls back to UTC over sea."""
    zone = _tf.timezone_at(lat=lat, lng=lon) or "UTC"
    now = now or datetime.now(tz=ZoneInfo("UTC"))
    return now.astimezone(ZoneInfo(zone)).hour


def wander(lat: float, lon: float, metres: float, rng: random.Random | None = None) -> tuple[float, float]:
    """A uniformly random point within `metres` of (lat, lon). Reverse geocoding it
    afterwards gives a real street elsewhere in town instead of the city-centre pin
    Mapbox returns for a bare city name (#22)."""
    rng = rng or random.Random()
    r = metres * math.sqrt(rng.random())  # sqrt: uniform over the disc, not clustered at the centre
    theta = rng.random() * 2 * math.pi
    dlat = (r * math.cos(theta)) / 111_320
    dlon = (r * math.sin(theta)) / (111_320 * math.cos(math.radians(lat)) or 1e-9)
    return round(lat + dlat, 6), round(lon + dlon, 6)


def build_context(lat: float, lon: float, include_time: bool = True, include_weather: bool = False) -> Context:
    """The only function here that touches the network."""
    return Context(
        address=address_from_mapbox(api.call_mapbox(lat, lon)),
        time_of_day=time_of_day(local_hour(lat, lon)) if include_time else "",
        weather=weather_from_openweathermap(api.call_openweathermap(lat, lon)) if include_weather else "",
        lat=lat,
        lon=lon,
    )


# --- Forward geocoding (#29) -------------------------------------------------
#
# Mapbox is precise for names it knows (Jordaan, Montmartre, Kreuzberg) but never
# says "unknown": for "amsterdam wallen" it returns a Rue d'Amsterdam near Rouen.
# So a Mapbox hit is accepted only when it looks like an answer to the question,
# and otherwise a small text-model call resolves colloquial names to coordinates.

GEOCODE_SYSTEM = (
    "You are a geocoder. Given a free-text place description, possibly colloquial or "
    "misspelled, return the WGS84 coordinates of its centre as JSON only: "
    '{"name": "<canonical name, city, country>", "lat": <float>, "lon": <float>}. '
    'If you cannot identify a real place, return {"name": null}.'
)

# Feature types that stand for "a named place" rather than a street or house
# number; a query of one or two words is not asking for an address.
_PLACE_TYPES = {"country", "region", "postcode", "district", "place", "locality", "neighborhood", "poi"}


@dataclass(frozen=True)
class Located:
    lat: float
    lon: float
    name: str  # what the coordinates stand for, e.g. "De Wallen, Amsterdam, Netherlands"


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"\w+", text.lower()) if len(w) >= 3}


def pick_mapbox_hit(query: str, features: list[dict]) -> Located | None:
    """The first feature that names a place and mentions every word of the query."""
    want = _words(query)
    for f in features:
        props = f.get("properties", {})
        if props.get("feature_type") not in _PLACE_TYPES:
            continue
        label = props.get("full_address") or props.get("name") or ""
        if want <= _words(label):
            lon, lat = f["geometry"]["coordinates"]
            return Located(lat, lon, label)
    return None


def parse_geocode(text: str) -> Located | None:
    """The model's JSON answer, or None when it declined or returned garbage."""
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        d = json.loads(m.group())
        if not d.get("name"):
            return None
        return Located(float(d["lat"]), float(d["lon"]), str(d["name"]))
    except (ValueError, TypeError, KeyError):
        return None


class LocationNotFound(LookupError):
    pass


def geocode(query: str, describe: Callable[[list[dict]], str]) -> Located:
    """Mapbox first, the text model as fallback; `describe` is Backend.describe."""
    hit = pick_mapbox_hit(query, api.call_mapbox_forward(query))
    if hit is None:
        hit = parse_geocode(
            describe([{"role": "system", "content": GEOCODE_SYSTEM}, {"role": "user", "content": query}])
        )
    if hit is None:
        raise LocationNotFound(query)
    return hit
