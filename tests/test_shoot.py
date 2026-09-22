import pytest
from fastapi.testclient import TestClient

from paragraphica import backend, core, service
from paragraphica.backend import Generated
from paragraphica.context import Context, Located
from paragraphica.store import Store

CTX = Context(address="Lisbon, Portugal", time_of_day="evening")


class FakeBackend:
    text_model = "t"
    image_model = "i"

    def describe(self, messages):
        return "The Tagus."

    def image(self, prompt, quality, size, model=None):
        return Generated(image=b"JPG", mime_type="image/jpeg")


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(backend, "make_backend", lambda name: FakeBackend())
    monkeypatch.setattr(core, "build_context", lambda *a, **k: CTX)
    monkeypatch.setattr(
        service.ctxmod,
        "geocode",
        lambda q, describe: (
            Located(38.72, -9.14, "Lisbon, Portugal")
            if "lis" in q.lower()
            else (_ for _ in ()).throw(service.ctxmod.LocationNotFound(q))
        ),
    )
    return TestClient(service.create_app(Store(tmp_path), backend_name="openrouter"))


def test_shoot_page_has_map_dials_and_shutter(client):
    html = client.get("/shoot").text
    for needle in (
        "leaflet",
        "id=map",
        'data-src="/styles"',
        'data-src="/eras"',
        'data-src="/models"',
        "name=nickname",
        "class=shutter",
        "fetch('/shoot'",
    ):
        assert needle in html
    assert 'aria-label="LAB271"' in html


def test_geocode_endpoint(client):
    assert client.get("/geocode", params={"q": "Lisbon"}).json()["name"] == "Lisbon, Portugal"
    assert client.get("/geocode", params={"q": "Nowhereville"}).status_code == 404
    assert client.get("/geocode", params={"q": "x"}).status_code == 422


def test_shoot_stores_nickname_and_source_and_lands_on_the_wall(client):
    r = client.post("/shoot", json={"lat": 38.72, "lon": -9.14, "nickname": " Ilja ", "era": "1650"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["nickname"] == "Ilja" and d["source"] == "phone" and d["era"] == "1650"
    wall = client.get("/").text
    assert "<span class=who>Ilja</span>" in wall
    assert client.get("/healthz").json()["images"] == 1


def test_shoot_is_rate_limited_per_client(client):
    for _ in range(service.SHOTS_PER_MINUTE):
        assert client.post("/shoot", json={"lat": 1, "lon": 1}).status_code == 200
    r = client.post("/shoot", json={"lat": 1, "lon": 1})
    assert r.status_code == 429 and "a minute" in r.json()["detail"]
    assert client.post("/generate", json={"lat": 1, "lon": 1}).status_code == 200  # the wall is not limited


def test_rate_limit_window_slides():
    rl = service.RateLimit(per_minute=2)
    assert rl.allow("a", now=0) and rl.allow("a", now=1) and not rl.allow("a", now=2)
    assert rl.allow("b", now=2)
    assert rl.allow("a", now=61)


def test_qr_encodes_the_shoot_url(client):
    r = client.get("/qr.svg")
    assert r.status_code == 200 and r.headers["content-type"].startswith("image/svg+xml")
    assert "<svg" in r.text and 'xmlns="http://www.w3.org/2000/svg"' in r.text  # loadable as <img src>


def test_wall_polls_and_shows_qr_only_when_served(client, tmp_path):
    wall = client.get("/").text
    assert "fetch('/healthz'" in wall and "setInterval(refresh, 10000)" in wall and "id=qr" in wall
    from paragraphica import gallery

    assert "refresh" not in gallery.render([]) and "id=qr" not in gallery.render([])


def test_nickname_too_long_is_422(client):
    assert client.post("/shoot", json={"lat": 1, "lon": 1, "nickname": "x" * 25}).status_code == 422
    assert client.post("/generate", json={"lat": 1, "lon": 1, "source": "robot"}).status_code == 422
