import pytest
from fastapi.testclient import TestClient

from paragraphica import backend, core, service
from paragraphica.backend import Generated
from paragraphica.context import Context
from paragraphica.store import Store

CTX = Context(address="Utrecht, Netherlands", time_of_day="morning")


class FakeBackend:
    text_model = "t"
    image_model = "i"

    def describe(self, messages):
        return "The Dom tower."

    def image(self, prompt, quality, size):
        return Generated(image=b"JPG", revised_prompt="note", mime_type="image/jpeg")


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(backend, "make_backend", lambda name: FakeBackend())
    monkeypatch.setattr(core, "build_context", lambda *a, **k: CTX)
    monkeypatch.setattr(
        service.api,
        "call_mapbox_forward",
        lambda q: (52.09, 5.12) if q == "Utrecht" else (_ for _ in ()).throw(IndexError),
    )
    return TestClient(service.create_app(Store(tmp_path)))


def test_vocabulary_endpoints(client):
    assert "polaroid" in client.get("/styles").json()
    assert "main attraction" in client.get("/contexts").json()
    assert "low angle" in client.get("/positions").json()
    assert client.get("/healthz").json()["images"] == 0


def test_generate_stores_and_serves_image(client):
    r = client.post("/generate", json={"location": "Utrecht", "style": "lego"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["address"] == "Utrecht, Netherlands" and body["style"] == "lego"
    assert body["description"] == "The Dom tower." and body["revised_prompt"] == "note"
    assert body["image_url"].startswith("/images/") and body["image_url"].endswith("-utrecht-lego.jpg")
    img = client.get(body["image_url"])
    assert img.status_code == 200 and img.content == b"JPG"
    assert client.get("/healthz").json()["images"] == 1


def test_history_newest_first_and_gallery(client):
    client.post("/generate", json={"lat": 52.09, "lon": 5.12, "style": "lego"})
    client.post("/generate", json={"lat": 52.09, "lon": 5.12, "style": "polaroid"})
    hist = client.get("/history").json()
    assert [h["style"] for h in hist] == ["polaroid", "lego"]
    assert len(client.get("/history?last=1").json()) == 1
    page = client.get("/")
    assert page.status_code == 200 and page.text.count("<article") == 2
    assert 'src="/images/' in page.text  # served page must not link images relative to /
    assert "<form id=gen" in page.text  # #16: generate controls on the served page


def test_validation(client):
    assert client.post("/generate", json={"lat": 1, "lon": 1, "style": "cubism"}).status_code == 422
    assert client.post("/generate", json={"location": "Nowhere-xyz"}).status_code == 404
    assert client.get("/images/../op.env").status_code == 404
    assert client.get("/images/missing.jpg").status_code == 404


def test_transient_model_error_is_503(client, monkeypatch):
    def boom(*a, **k):
        raise backend.TransientError("503 high demand")

    monkeypatch.setattr(FakeBackend, "describe", boom)
    r = client.post("/generate", json={"lat": 52.09, "lon": 5.12})
    assert r.status_code == 503 and "temporarily" in r.json()["detail"]


def test_times_and_override(client, monkeypatch):
    times = client.get("/times").json()
    assert "dark night" in times
    seen = {}
    real = core.generate

    def spy(req, backend, **kw):
        seen["req"] = req
        return real(req, backend, **kw)

    monkeypatch.setattr(service.core, "generate", spy)
    r = client.post("/generate", json={"lat": 52.09, "lon": 5.12, "time_of_day": "dark night", "include_weather": True})
    assert r.status_code == 200, r.text
    assert seen["req"].time_of_day == "dark night" and seen["req"].include_weather is True
    assert client.post("/generate", json={"lat": 1, "lon": 1, "time_of_day": "teatime"}).status_code == 422
