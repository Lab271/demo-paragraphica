"""Model backends. A backend is the only thing in the pipeline that talks to a
model; everything upstream is strings and dataclasses.

Select with PARA_BACKEND (only "gemini" today; "local" arrives in #8). Model ids can be
overridden with PARA_TEXT_MODEL / PARA_IMAGE_MODEL."""

import os
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

from paragraphica import api

DEFAULT_BACKEND = os.environ.get("PARA_BACKEND", "gemini")

# Gemini answers 503/504 about one call in twenty under load (#28); the first retry
# almost always succeeds, the second is cheap insurance for a live demo.
RETRY_DELAYS_S = (2.0, 6.0)
MAX_429_WAIT_S = 30.0  # honour Google's retryDelay on a per-minute quota; a daily quota is not worth waiting for


class TransientError(RuntimeError):
    """The model was unavailable after retrying; the caller may try again later."""


def _status(e: Exception) -> int | None:
    code = getattr(e, "code", None) or getattr(e, "status_code", None)
    return code if isinstance(code, int) else None


def _retry_after(e: Exception) -> float | None:
    """Seconds Google asks us to wait on a 429 ('retryDelay': '48s'), if present."""
    m = re.search(r"retryDelay['\"]?\s*:\s*['\"]?(\d+(?:\.\d+)?)s", str(e))
    return float(m.group(1)) if m else None


def _wait_before_retry(e: Exception, attempt: int, delays: tuple[float, ...]) -> float | None:
    """How long to sleep before retrying `e`, or None when it must not be retried."""
    code = _status(e)
    if code is not None and code >= 500:
        return delays[attempt] if attempt < len(delays) else None
    if code == 429:
        wait = _retry_after(e)
        return wait if attempt == 0 and wait is not None and wait <= MAX_429_WAIT_S else None
    return None


def with_retry[T](fn: Callable[[], T], delays: tuple[float, ...] = RETRY_DELAYS_S) -> T:
    """Call fn; retry on 5xx (backoff per `delays`) and once on a short 429; then TransientError.
    Anything else propagates untouched."""
    attempt = 0
    while True:
        try:
            return fn()
        except Exception as e:  # provider SDKs raise their own hierarchies; filter on status code
            code = _status(e)
            if code is None or (code < 500 and code != 429):
                raise
            wait = _wait_before_retry(e, attempt, delays)
            if wait is None:
                raise TransientError(str(e)[:200]) from e
            time.sleep(wait)
            attempt += 1


DEFAULT_MODELS = {
    # Text: the non-thinking lite model returns a description in ~6 s. The
    # "gemini-flash-latest" alias timed out under load and 3.5/3.8 flash spend a small
    # token budget on thinking and return no text (probed 2026-09-11; `terra models`).
    "gemini": ("gemini-3.1-flash-lite", "gemini-3.1-flash-image"),
}


@dataclass(frozen=True)
class Generated:
    image: bytes
    revised_prompt: str | None = None
    mime_type: str = "image/png"


class Backend(Protocol):
    def describe(self, messages: list[dict]) -> str: ...

    def image(self, prompt: str, quality: str, size: str) -> Generated: ...


def _model(env: str, default: str) -> str:
    return os.environ.get(env) or default


@dataclass
class GeminiBackend:
    text_model: str = field(default_factory=lambda: _model("PARA_TEXT_MODEL", DEFAULT_MODELS["gemini"][0]))
    image_model: str = field(default_factory=lambda: _model("PARA_IMAGE_MODEL", DEFAULT_MODELS["gemini"][1]))

    def describe(self, messages: list[dict]) -> str:
        return with_retry(lambda: api.call_gemini_text(self.text_model, messages))

    def image(self, prompt: str, quality: str, size: str) -> Generated:
        text, data, mime = with_retry(lambda: api.call_gemini_image(prompt, self.image_model, quality, size))
        return Generated(image=data, revised_prompt=text, mime_type=mime)


BACKENDS: dict[str, type] = {"gemini": GeminiBackend}


def make_backend(name: str = DEFAULT_BACKEND) -> Backend:
    try:
        return BACKENDS[name]()
    except KeyError:
        raise ValueError(f"unknown backend {name!r}; one of: {', '.join(BACKENDS)}") from None
