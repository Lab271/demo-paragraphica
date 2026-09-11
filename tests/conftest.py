import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent

# Geo location of Schuberg Philis / Boeingavenue 271
SBP = (52.274972, 4.750813)


@pytest.fixture
def mapbox_feature() -> dict:
    return json.loads((FIXTURES / "mapbox_search_sbp.json").read_text())["features"][0]


@pytest.fixture
def owm_response() -> dict:
    return json.loads((FIXTURES / "openweathermap_sbp.json").read_text())
