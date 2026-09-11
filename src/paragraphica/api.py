"""Thin wrappers around the external HTTP APIs. Nothing in here is unit-tested
against the network; the recorded responses in tests/*.json are the contract."""

import os
from base64 import b64decode

import requests
from openai import OpenAI

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


def call_image(prompt: str, model: str, quality: str, size: str) -> tuple[str | None, bytes]:
    """Generate one image. The gpt-image models always return base64 and take
    no `style`/`response_format`; `revised_prompt` may be absent."""
    client = OpenAI()
    response = client.images.generate(model=model, prompt=prompt, size=size, quality=quality, n=1)
    data = response.data[0]
    return data.revised_prompt, b64decode(data.b64_json)


def call_gpt(model: str, messages: list[dict], max_tokens: int = 400, temperature: float = 0.1) -> str:
    client = OpenAI()
    res = client.chat.completions.create(
        model=model,
        messages=messages,
        max_completion_tokens=max_tokens,
        temperature=temperature,
    )
    return res.choices[0].message.content or ""


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


def call_gemini_image(prompt: str, model: str, quality: str, size: str) -> tuple[str | None, bytes]:
    """Image via generate_content (Imagen endpoints were shut down Aug 2026).
    Returns (accompanying text if any, PNG/JPEG bytes)."""
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
    text, image = None, None
    for part in res.candidates[0].content.parts:
        if part.inline_data is not None and image is None:
            image = part.inline_data.data
        elif part.text:
            text = (text or "") + part.text
    if image is None:
        raise RuntimeError(f"Gemini returned no image for model {model!r}: {text!r}")
    return text, image
