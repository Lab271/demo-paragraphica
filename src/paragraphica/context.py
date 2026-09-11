"""Where and when: the facts about a location that go into the prompt.

Pure functions over recorded API responses, plus one `build_context` that
performs the network calls. Timezone is computed offline."""

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


def build_context(lat: float, lon: float, include_time: bool = True, include_weather: bool = False) -> Context:
    """The only function here that touches the network."""
    return Context(
        address=address_from_mapbox(api.call_mapbox(lat, lon)),
        time_of_day=time_of_day(local_hour(lat, lon)) if include_time else "",
        weather=weather_from_openweathermap(api.call_openweathermap(lat, lon)) if include_weather else "",
    )
