"""Model backends. A backend is the only thing in the pipeline that talks to a
model; everything upstream is strings and dataclasses.

Select with PARA_BACKEND (only "gemini" today; "local" arrives in #8). Model ids can be
overridden with PARA_TEXT_MODEL / PARA_IMAGE_MODEL."""

import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

from paragraphica import api

DEFAULT_BACKEND = os.environ.get("PARA_BACKEND", "gemini")

RETRIES = 1  # Gemini answers 503/504 roughly one call in three under load; one retry is enough
RETRY_DELAY_S = 2.0


class TransientError(RuntimeError):
    """The model was unavailable after retrying; the caller may try again later."""


def _is_transient(e: Exception) -> bool:
    code = getattr(e, "code", None) or getattr(e, "status_code", None)
    return isinstance(code, int) and code >= 500


def with_retry[T](fn: Callable[[], T], retries: int = RETRIES, delay: float = RETRY_DELAY_S) -> T:
    """Call fn; on a 5xx from the provider wait and retry `retries` times, then raise TransientError."""
    for attempt in range(retries + 1):
        try:
            return fn()
        except Exception as e:  # provider SDKs raise their own hierarchies; filter on status code
            if not _is_transient(e):
                raise
            if attempt == retries:
                raise TransientError(str(e)[:200]) from e
            time.sleep(delay)
    raise AssertionError("unreachable")


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
