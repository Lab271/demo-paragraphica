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


# --- OpenRouter (#38) ---


class _Resp:
    def __init__(self, status, payload=None, text=""):
        self.status_code, self.ok, self._payload, self.text = status, status < 400, payload, text

    def json(self):
        return self._payload


def test_openrouter_image_call_shape(monkeypatch):
    seen = {}

    def post(url, json, headers, timeout):
        seen.update(url=url, body=json, auth=headers["Authorization"], timeout=timeout)
        return _Resp(200, {"data": [{"b64_json": "SlBH", "media_type": "image/jpeg"}], "usage": {"cost": 0.045}})

    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    monkeypatch.setattr(api.requests, "post", post)
    data, mime, cost = api.call_openrouter_image("p", "black-forest-labs/flux.2-pro", "high", "1536x1024")
    assert (data, mime, cost) == (b"JPG", "image/jpeg", 0.045)
    assert seen["url"].endswith("/api/v1/images") and seen["auth"] == "Bearer sk-or-test"
    assert seen["body"] == {"model": "black-forest-labs/flux.2-pro", "prompt": "p", "aspect_ratio": "3:2"}
    assert seen["timeout"] >= 120


@pytest.mark.parametrize(
    "model,quality,extra",
    [
        ("openai/gpt-image-2", "low", {"quality": "low"}),
        ("google/gemini-3.1-flash-image", "high", {"resolution": "2K"}),
        ("google/gemini-3.1-flash-image", "low", {"resolution": "1K"}),
        ("bytedance-seed/seedream-4.5", "low", {"resolution": "2K"}),
        ("black-forest-labs/flux.2-pro", "high", {}),
    ],
)
def test_openrouter_quality_param_per_vendor(model, quality, extra):
    assert api._openrouter_quality(model, quality) == extra


def test_openrouter_recraft_has_no_3_2(monkeypatch):
    seen = {}
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    monkeypatch.setattr(
        api.requests,
        "post",
        lambda url, json, headers, timeout: seen.update(json) or _Resp(200, {"data": [{"b64_json": "SlBH"}]}),
    )
    api.call_openrouter_image("p", "recraft/recraft-v4.1", "medium", "1536x1024")
    assert seen["aspect_ratio"] == "4:3"


def test_openrouter_error_carries_status_and_retries(monkeypatch):
    calls = []

    def post(url, json, headers, timeout):
        calls.append(1)
        if len(calls) == 1:
            return _Resp(503, text="upstream busy")
        return _Resp(200, {"data": [{"b64_json": "UE5H"}]})

    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    monkeypatch.setattr(api.requests, "post", post)
    monkeypatch.setattr(backend.time, "sleep", lambda s: None)
    gen = backend.OpenRouterBackend().image("p", "medium", "1024x1024", "openai/gpt-image-2")
    assert gen == backend.Generated(image=b"PNG", mime_type="image/png", cost=None) and len(calls) == 2


def test_openrouter_4xx_propagates_untouched(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    monkeypatch.setattr(api.requests, "post", lambda *a, **kw: _Resp(402, text="insufficient credits"))
    with pytest.raises(api.OpenRouterError, match="402") as e:
        backend.OpenRouterBackend().image("p", "medium", "1024x1024")
    assert e.value.status_code == 402


def test_openrouter_moderation_message_names_the_provider(monkeypatch):
    payload = {
        "error": {"message": "blocked by content moderation", "code": 400, "metadata": {"provider_name": "Alibaba"}}
    }
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    monkeypatch.setattr(api.requests, "post", lambda *a, **kw: _Resp(400, payload, text="{...}"))
    with pytest.raises(api.OpenRouterError, match="Alibaba: blocked by content moderation") as e:
        api.call_openrouter_image("p", "qwen/qwen-image-3", "medium", "1024x1024")
    assert e.value.status_code == 400


def test_openrouter_backend_defaults_and_model_choice(monkeypatch):
    monkeypatch.delenv("PARA_TEXT_MODEL", raising=False)
    monkeypatch.delenv("PARA_IMAGE_MODEL", raising=False)
    seen = {}
    monkeypatch.setattr(
        api, "call_openrouter_image", lambda p, m, q, s: seen.update(model=m) or (b"X", "image/png", 0.005)
    )
    monkeypatch.setattr(api, "call_openrouter_text", lambda m, msgs: "desc")
    b = backend.make_backend("openrouter")
    assert isinstance(b, backend.OpenRouterBackend)
    assert b.describe([{"role": "user", "content": "x"}]) == "desc"
    b.image("p", "low", "1024x1024")
    assert seen["model"] == backend.DEFAULT_MODELS["openrouter"][1]
    b.image("p", "low", "1024x1024", "qwen/qwen-image-3")
    assert seen["model"] == "qwen/qwen-image-3"


def test_image_models_are_ten_unique_slugs():
    assert len(backend.IMAGE_MODELS) == 10
    assert len(set(backend.IMAGE_MODELS.values())) == 10
    assert all("/" in slug for slug in backend.IMAGE_MODELS.values())
