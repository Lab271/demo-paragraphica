import pytest

from paragraphica import api, backend


def test_default_backend_is_gemini(monkeypatch):
    monkeypatch.delenv("PARA_TEXT_MODEL", raising=False)
    monkeypatch.delenv("PARA_IMAGE_MODEL", raising=False)
    b = backend.make_backend()
    assert isinstance(b, backend.GeminiBackend)
    assert (b.text_model, b.image_model) == ("gemini-3.1-flash-lite", "gemini-3.1-flash-image")


def test_unknown_backend():
    with pytest.raises(ValueError, match="unknown backend"):
        backend.make_backend("midjourney")


def test_model_override_from_env(monkeypatch):
    monkeypatch.setenv("PARA_IMAGE_MODEL", "gemini-3.1-flash-lite-image")
    assert backend.GeminiBackend().image_model == "gemini-3.1-flash-lite-image"


def test_gemini_backend_maps_calls(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        api, "call_gemini_text", lambda model, messages: seen.setdefault("text", (model, messages)) and "desc"
    )
    monkeypatch.setattr(api, "call_gemini_image", lambda prompt, model, quality, size: ("note", b"JPG", "image/jpeg"))
    b = backend.GeminiBackend(text_model="t", image_model="i")
    assert b.describe([{"role": "user", "content": "x"}]) == "desc"
    assert seen["text"][0] == "t"
    gen = b.image("p", "high", "1024x1024")
    assert gen == backend.Generated(image=b"JPG", revised_prompt="note", mime_type="image/jpeg")


@pytest.mark.parametrize("quality,expected", [("low", "1K"), ("medium", "1K"), ("high", "2K"), ("weird", "1K")])
def test_gemini_quality_mapping(quality, expected):
    assert api.GEMINI_IMAGE_SIZE.get(quality, "1K") == expected


def test_gemini_aspect_mapping():
    assert api.GEMINI_ASPECT["1536x1024"] == "3:2"
    assert api.GEMINI_ASPECT.get("777x777", "1:1") == "1:1"


class _Http(Exception):
    def __init__(self, code):
        super().__init__(f"http {code}")
        self.code = code


def test_with_retry_retries_once_on_5xx(monkeypatch):
    monkeypatch.setattr(backend.time, "sleep", lambda s: None)
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) == 1:
            raise _Http(503)
        return "ok"

    assert backend.with_retry(flaky) == "ok" and len(calls) == 2


def test_with_retry_gives_up_and_wraps(monkeypatch):
    monkeypatch.setattr(backend.time, "sleep", lambda s: None)
    with pytest.raises(backend.TransientError):
        backend.with_retry(lambda: (_ for _ in ()).throw(_Http(504)))


def test_with_retry_does_not_retry_4xx(monkeypatch):
    calls = []

    def bad():
        calls.append(1)
        raise _Http(404)

    with pytest.raises(_Http):
        backend.with_retry(bad)
    assert len(calls) == 1
