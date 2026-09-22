"""Thin wrappers around the external HTTP APIs. Nothing in here is unit-tested
against the network; the recorded responses in tests/*.json are the contract."""

import base64
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


def call_mapbox_forward(query: str, limit: int = 3) -> list[dict]:
    """Forward geocode a free-text place name; returns Mapbox v6 features, best first.
    Callers judge them (context.pick_mapbox_hit): with an unknown name Mapbox happily
    returns a street called 'Amsterdam' on another continent (#29)."""
    api_url = "https://api.mapbox.com/search/geocode/v6/forward?q={}&limit={}&access_token={}"
    response = requests.get(api_url.format(requests.utils.quote(query), limit, _mapbox_token()), timeout=TIMEOUT)
    return response.json().get("features", [])


def call_openweathermap(lat: float, lon: float) -> dict:
    api_url = "https://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&units=metric&appid={}"
    token = os.environ["PARA_OPENWEATHERMAP_API"]
    response = requests.get(api_url.format(lat, lon, token), timeout=TIMEOUT)
    return response.json()


# --- Google Gemini (google-genai; key from GEMINI_API_KEY or GOOGLE_API_KEY) ---

GEMINI_TIMEOUT_MS = 60_000


def _gemini_client():
    """Our timeout, and the SDK's own retry loop disabled: backend.with_retry is the
    only retry, so a hung call cannot block a dial press for minutes (#28)."""
    from google import genai
    from google.genai import types

    return genai.Client(
        http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS, retry_options=types.HttpRetryOptions(attempts=1))
    )


# Gemini image models take an aspect ratio + 1K/2K/4K instead of WxH + low/medium/high.
GEMINI_ASPECT = {"1024x1024": "1:1", "1536x1024": "3:2", "1024x1536": "2:3"}
GEMINI_IMAGE_SIZE = {"low": "1K", "medium": "1K", "high": "2K"}


def _afc_disabled():
    # We pass no tools, but the SDK still logs an "automatic function calling is not
    # recommended" warning on every direct generate_content call unless AFC is off.
    from google.genai import types

    return types.AutomaticFunctionCallingConfig(disable=True)


def call_gemini_text(model: str, messages: list[dict], max_tokens: int = 400, temperature: float = 0.1) -> str:
    from google.genai import types

    system = " ".join(m["content"] for m in messages if m["role"] == "system") or None
    user = "\n".join(m["content"] for m in messages if m["role"] == "user")
    client = _gemini_client()
    res = client.models.generate_content(
        model=model,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
            temperature=temperature,
            automatic_function_calling=_afc_disabled(),
        ),
    )
    return res.text or ""


def call_gemini_image(prompt: str, model: str, quality: str, size: str) -> tuple[str | None, bytes, str]:
    """Image via generate_content (Imagen endpoints were shut down Aug 2026).
    Returns (accompanying text if any, image bytes, mime type). The Developer API
    picks the format itself (JPEG in practice); output_mime_type is Vertex-only."""
    from google.genai import types

    client = _gemini_client()
    res = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
            automatic_function_calling=_afc_disabled(),
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


# --- OpenRouter: one key, one request shape, 30+ image models (#38) ---

OPENROUTER_URL = "https://openrouter.ai/api/v1"
OPENROUTER_TIMEOUT = 150  # FLUX.2 pro takes ~20 s, Qwen image ~85 s (live test 2026-09-22)


class OpenRouterError(RuntimeError):
    """Non-2xx from OpenRouter; `status_code` lets backend.with_retry handle 5xx/429."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


def _openrouter_post(path: str, body: dict) -> dict:
    headers = {
        "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
        "HTTP-Referer": "https://github.com/Lab271/demo-paragraphica",
        "X-Title": "Terra Virtualis",
    }
    r = requests.post(f"{OPENROUTER_URL}{path}", json=body, headers=headers, timeout=OPENROUTER_TIMEOUT)
    if not r.ok:
        raise OpenRouterError(f"OpenRouter {r.status_code}: {r.text[:200]}", r.status_code)
    return r.json()


def _openrouter_quality(model: str, quality: str) -> dict:
    """Vendors name the quality dial differently; FLUX and Recraft take none."""
    vendor = model.split("/")[0]
    if vendor == "openai":
        return {"quality": quality}
    if vendor in ("google", "qwen"):
        return {"resolution": GEMINI_IMAGE_SIZE.get(quality, "1K")}
    if vendor == "bytedance-seed":
        return {"resolution": "2K" if quality != "high" else "4K"}  # Seedream rejects 1K
    return {}


def call_openrouter_image(prompt: str, model: str, quality: str, size: str) -> tuple[bytes, str, float | None]:
    """POST /images. Returns (image bytes, mime type, cost in USD when reported)."""
    aspect = GEMINI_ASPECT.get(size, "1:1")
    if model.startswith("recraft/"):  # Recraft has no 3:2; 4:3 is the nearest it takes
        aspect = {"3:2": "4:3", "2:3": "3:4"}.get(aspect, aspect)
    body = {"model": model, "prompt": prompt, "aspect_ratio": aspect}
    body.update(_openrouter_quality(model, quality))
    res = _openrouter_post("/images", body)
    data = (res.get("data") or [{}])[0]
    if not data.get("b64_json"):
        raise RuntimeError(f"OpenRouter returned no image for model {model!r}: {str(res)[:200]}")
    cost = (res.get("usage") or {}).get("cost")
    return base64.b64decode(data["b64_json"]), data.get("media_type") or "image/png", cost


def call_openrouter_text(model: str, messages: list[dict], max_tokens: int = 400, temperature: float = 0.1) -> str:
    res = _openrouter_post(
        "/chat/completions",
        {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature},
    )
    return res["choices"][0]["message"]["content"] or ""


def list_openrouter_models(filter: str = "") -> list[tuple[str, str]]:
    """(slug, name) for OpenRouter models whose slug contains `filter`, image models first."""
    res = requests.get(f"{OPENROUTER_URL}/models", timeout=TIMEOUT).json()
    out = []
    for m in res.get("data", []):
        if filter in m["id"]:
            out.append((m["id"], m.get("name", "")))
    return sorted(out)
