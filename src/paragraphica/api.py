"""Thin wrappers around the external HTTP APIs. Nothing in here is unit-tested
against the network; the recorded responses in tests/*.json are the contract."""

import os

import requests

TIMEOUT = 30


def _mapbox_token() -> str:
    token = os.environ["PARA_MAPBOX_API"]
    assert token.startswith("pk.")
    return token


def call_mapbox(lat: float, lon: float) -> dict:
    """Reverse geocode; returns the first Mapbox v6 feature."""
    api_url = "https://api.mapbox.com/search/geocode/v6/reverse?latitude={}&longitude={}&access_token={}"
    response = requests.get(api_url.format(lat, lon, _mapbox_token()), timeout=TIMEOUT)
    return response.json()["features"][0]


def call_mapbox_forward(query: str) -> tuple[float, float]:
    """Forward geocode a free-text place name to (lat, lon)."""
    api_url = "https://api.mapbox.com/search/geocode/v6/forward?q={}&limit=1&access_token={}"
    response = requests.get(api_url.format(requests.utils.quote(query), _mapbox_token()), timeout=TIMEOUT)
    lon, lat = response.json()["features"][0]["geometry"]["coordinates"]
    return lat, lon


def call_openweathermap(lat: float, lon: float) -> dict:
    api_url = "https://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&units=metric&appid={}"
    token = os.environ["PARA_OPENWEATHERMAP_API"]
    response = requests.get(api_url.format(lat, lon, token), timeout=TIMEOUT)
    return response.json()


# --- Google Gemini (google-genai; key from GEMINI_API_KEY or GOOGLE_API_KEY) ---

# Gemini image models take an aspect ratio + 1K/2K/4K instead of WxH + low/medium/high.
GEMINI_ASPECT = {"1024x1024": "1:1", "1536x1024": "3:2", "1024x1536": "2:3"}
GEMINI_IMAGE_SIZE = {"low": "1K", "medium": "1K", "high": "2K"}


def call_gemini_text(model: str, messages: list[dict], max_tokens: int = 400, temperature: float = 0.1) -> str:
    from google import genai
    from google.genai import types

    system = " ".join(m["content"] for m in messages if m["role"] == "system") or None
    user = "\n".join(m["content"] for m in messages if m["role"] == "user")
    client = genai.Client()
    res = client.models.generate_content(
        model=model,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system, max_output_tokens=max_tokens, temperature=temperature
        ),
    )
    return res.text or ""


def call_gemini_image(prompt: str, model: str, quality: str, size: str) -> tuple[str | None, bytes, str]:
    """Image via generate_content (Imagen endpoints were shut down Aug 2026).
    Returns (accompanying text if any, image bytes, mime type). The Developer API
    picks the format itself (JPEG in practice); output_mime_type is Vertex-only."""
    from google import genai
    from google.genai import types

    client = genai.Client()
    res = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
            image_config=types.ImageConfig(
                aspect_ratio=GEMINI_ASPECT.get(size, "1:1"),
                image_size=GEMINI_IMAGE_SIZE.get(quality, "1K"),
            ),
        ),
    )
    text, image, mime = None, None, "image/png"
    for part in res.candidates[0].content.parts:
        if part.inline_data is not None and image is None:
            image = part.inline_data.data
            mime = part.inline_data.mime_type or mime
        elif part.text:
            text = (text or "") + part.text
    if image is None:
        raise RuntimeError(f"Gemini returned no image for model {model!r}: {text!r}")
    return text, image, mime


def list_gemini_models() -> list[tuple[str, str]]:
    """(model id, supported generate actions) for every Gemini model the key can call."""
    from google import genai

    out = []
    for m in genai.Client().models.list():
        acts = ",".join(a for a in (m.supported_actions or []) if "generate" in a.lower())
        out.append(((m.name or "").removeprefix("models/"), acts))
    return sorted(out)
