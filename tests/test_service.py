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
    last_model = None

    def describe(self, messages):
        if messages[0]["content"] == service.ctxmod.GEOCODE_SYSTEM:
            return '{"name": null}'  # the geocoder fallback declines: unknown places stay 404
        return "The Dom tower."

    def image(self, prompt, quality, size, model=None):
        FakeBackend.last_model = model
        return Generated(image=b"JPG", revised_prompt="note", mime_type="image/jpeg", cost=0.005)


UTRECHT = [
    {
        "properties": {"feature_type": "place", "full_address": "Utrecht, Netherlands"},
        "geometry": {"coordinates": [5.12, 52.09]},
    }
]


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(backend, "make_backend", lambda name: FakeBackend())
    monkeypatch.setattr(core, "build_context", lambda *a, **k: CTX)
    monkeypatch.setattr(service.ctxmod.api, "call_mapbox_forward", lambda q: UTRECHT if q == "Utrecht" else [])
    return TestClient(service.create_app(Store(tmp_path)))


def test_vocabulary_endpoints(client):
    assert "polaroid" in client.get("/styles").json()
    assert "landmark" in client.get("/contexts").json()
    assert "aerial" in client.get("/positions").json()
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
    real = core.generate_variants

    def spy(req, backend, n, **kw):
        seen["req"] = req
        return real(req, backend, n, **kw)

    monkeypatch.setattr(service.core, "generate_variants", spy)
    r = client.post("/generate", json={"lat": 52.09, "lon": 5.12, "time_of_day": "dark night", "include_weather": True})
    assert r.status_code == 200, r.text
    assert seen["req"].time_of_day == "dark night" and seen["req"].include_weather is True
    assert client.post("/generate", json={"lat": 1, "lon": 1, "time_of_day": "teatime"}).status_code == 422


def test_variants_return_all_records(client):
    r = client.post("/generate", json={"lat": 52.09, "lon": 5.12, "variants": 2})
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["records"]) == 2 and body["image_url"] == body["records"][0]["image_url"]
    assert client.get("/healthz").json()["images"] == 2
    assert client.post("/generate", json={"lat": 1, "lon": 1, "variants": 9}).status_code == 422


def test_caption_flag_reaches_the_prompt(client):
    r = client.post("/generate", json={"lat": 52.09, "lon": 5.12, "style": "polaroid", "caption": True})
    assert r.status_code == 200, r.text
    assert "lettered into the picture" in r.json()["prompt"]
    assert r.json()["caption"] is True


@pytest.fixture
def openrouter_client(monkeypatch, tmp_path):
    monkeypatch.setattr(backend, "make_backend", lambda name: FakeBackend())
    monkeypatch.setattr(core, "build_context", lambda *a, **k: CTX)
    return TestClient(service.create_app(Store(tmp_path), backend_name="openrouter"))


def test_models_endpoint_only_for_openrouter(client, openrouter_client):
    assert client.get("/models").json() == {}
    assert openrouter_client.get("/models").json()["flux.2 pro"] == "black-forest-labs/flux.2-pro"


def test_image_model_label_resolves_to_slug_and_is_stored(openrouter_client):
    r = openrouter_client.post("/generate", json={"lat": 52.09, "lon": 5.12, "image_model": "flux.2 pro"})
    assert r.status_code == 200, r.text
    assert FakeBackend.last_model == "black-forest-labs/flux.2-pro"
    assert r.json()["image_model"] == "black-forest-labs/flux.2-pro"
    assert r.json()["cost"] == 0.005


def test_unknown_image_model_is_422(client, openrouter_client):
    assert openrouter_client.post("/generate", json={"lat": 1, "lon": 1, "image_model": "dall-e 3"}).status_code == 422
    assert client.post("/generate", json={"lat": 1, "lon": 1, "image_model": "flux.2 pro"}).status_code == 422


def test_provider_refusal_is_502_json(monkeypatch, tmp_path):
    class Refusing(FakeBackend):
        def image(self, prompt, quality, size, model=None):
            raise RuntimeError("Alibaba: blocked this request through content moderation.")

    monkeypatch.setattr(backend, "make_backend", lambda name: Refusing())
    monkeypatch.setattr(core, "build_context", lambda *a, **k: CTX)
    c = TestClient(service.create_app(Store(tmp_path)))
    r = c.post("/generate", json={"lat": 52.37, "lon": 4.9})
    assert r.status_code == 502 and "content moderation" in r.json()["detail"]


def test_about_page_and_json(client, openrouter_client):
    assert client.get("/about.json").json()["backend"] == "gemini"
    html = openrouter_client.get("/about").text
    assert (
        "Ilja Heitlager" in html
        and "black-forest-labs/flux.2-pro" in html
        and "openrouter<span class=tag>active" in html
    )
    assert 'href="/about"' in openrouter_client.get("/").text


def test_static_exploded_view_is_served_and_on_the_about_page(client):
    assert 'src="/static/paragraphica-exploded.jpg"' in client.get("/about").text
    r = client.get("/static/paragraphica-exploded.jpg")
    assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg" and len(r.content) > 50_000
    assert client.get("/static/../pyproject.toml").status_code == 404
    assert client.get("/static/nope.jpg").status_code == 404


def test_eras_endpoint_and_override(client, monkeypatch):
    assert client.get("/eras").json()[0] == "1650"
    seen = {}
    real = core.generate_variants

    def spy(req, model, n, **kw):
        seen["req"] = req
        return real(req, model, n, **kw)

    monkeypatch.setattr(core, "generate_variants", spy)
    r = client.post("/generate", json={"lat": 52.09, "lon": 5.12, "era": "ice age"})
    assert r.status_code == 200 and seen["req"].era == "ice age" and r.json()["era"] == "ice age"
    assert client.post("/generate", json={"lat": 1, "lon": 1, "era": "1066"}).status_code == 422
