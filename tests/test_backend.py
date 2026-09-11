import pytest

from paragraphica import api, backend


def test_default_backend_is_gemini(monkeypatch):
    monkeypatch.delenv("PARA_TEXT_MODEL", raising=False)
    monkeypatch.delenv("PARA_IMAGE_MODEL", raising=False)
    b = backend.make_backend()
    assert isinstance(b, backend.GeminiBackend)
    assert (b.text_model, b.image_model) == ("gemini-3.1-flash", "gemini-3.1-flash-image")


def test_openai_backend_selectable():
    assert isinstance(backend.make_backend("openai"), backend.OpenAIBackend)


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
    monkeypatch.setattr(api, "call_gemini_image", lambda prompt, model, quality, size: ("note", b"PNG"))
    b = backend.GeminiBackend(text_model="t", image_model="i")
    assert b.describe([{"role": "user", "content": "x"}]) == "desc"
    assert seen["text"][0] == "t"
    gen = b.image("p", "high", "1024x1024")
    assert gen == backend.Generated(image=b"PNG", revised_prompt="note")


@pytest.mark.parametrize("quality,expected", [("low", "1K"), ("medium", "1K"), ("high", "2K"), ("weird", "1K")])
def test_gemini_quality_mapping(quality, expected):
    assert api.GEMINI_IMAGE_SIZE.get(quality, "1K") == expected


def test_gemini_aspect_mapping():
    assert api.GEMINI_ASPECT["1536x1024"] == "3:2"
    assert api.GEMINI_ASPECT.get("777x777", "1:1") == "1:1"
