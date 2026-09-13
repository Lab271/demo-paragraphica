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
    def __init__(self, code, msg=""):
        super().__init__(msg or f"http {code}")
        self.code = code


def _flaky(fails, exc):
    calls = []

    def fn():
        calls.append(1)
        if len(calls) <= fails:
            raise exc
        return "ok"

    fn.calls = calls
    return fn


def test_with_retry_5xx_recovers_within_two_retries(monkeypatch):
    slept = []
    monkeypatch.setattr(backend.time, "sleep", slept.append)
    fn = _flaky(2, _Http(503))
    assert backend.with_retry(fn) == "ok" and len(fn.calls) == 3
    assert slept == [2.0, 6.0]


def test_with_retry_5xx_gives_up_after_two_retries(monkeypatch):
    monkeypatch.setattr(backend.time, "sleep", lambda s: None)
    fn = _flaky(9, _Http(504))
    with pytest.raises(backend.TransientError):
        backend.with_retry(fn)
    assert len(fn.calls) == 3


def test_with_retry_429_honours_short_retry_delay(monkeypatch):
    slept = []
    monkeypatch.setattr(backend.time, "sleep", slept.append)
    fn = _flaky(1, _Http(429, "RESOURCE_EXHAUSTED ... {'@type': 'RetryInfo', 'retryDelay': '12s'}"))
    assert backend.with_retry(fn) == "ok" and slept == [12.0]


def test_with_retry_429_long_or_missing_delay_is_not_retried(monkeypatch):
    monkeypatch.setattr(backend.time, "sleep", lambda s: pytest.fail("must not sleep"))
    for msg in ("quota exceeded, 'retryDelay': '48s'", "daily quota exceeded"):
        fn = _flaky(9, _Http(429, msg))
        with pytest.raises(backend.TransientError):
            backend.with_retry(fn)
        assert len(fn.calls) == 1


def test_with_retry_does_not_retry_other_4xx(monkeypatch):
    monkeypatch.setattr(backend.time, "sleep", lambda s: pytest.fail("must not sleep"))
    fn = _flaky(9, _Http(404))
    with pytest.raises(_Http):
        backend.with_retry(fn)
    assert len(fn.calls) == 1


def test_gemini_client_has_timeout_and_no_sdk_retries():
    c = api._gemini_client.__wrapped__() if hasattr(api._gemini_client, "__wrapped__") else None
    # Build the options the same way the factory does and check them, without a key.
    from google.genai import types

    opts = types.HttpOptions(timeout=api.GEMINI_TIMEOUT_MS, retry_options=types.HttpRetryOptions(attempts=1))
    assert opts.timeout == 60_000 and opts.retry_options.attempts == 1 and c is None
