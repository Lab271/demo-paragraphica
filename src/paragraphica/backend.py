"""Model backends. A backend is the only thing in the pipeline that talks to a
model; everything upstream is strings and dataclasses.

Select with PARA_BACKEND=gemini|openai (default gemini). Model ids can be
overridden with PARA_TEXT_MODEL / PARA_IMAGE_MODEL."""

import os
from dataclasses import dataclass, field
from typing import Protocol

from paragraphica import api

DEFAULT_BACKEND = os.environ.get("PARA_BACKEND", "gemini")

DEFAULT_MODELS = {
    "gemini": ("gemini-3.1-flash", "gemini-3.1-flash-image"),
    "openai": ("gpt-5-mini", "gpt-image-2"),
}


@dataclass(frozen=True)
class Generated:
    image: bytes
    revised_prompt: str | None = None


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
        return api.call_gemini_text(self.text_model, messages)

    def image(self, prompt: str, quality: str, size: str) -> Generated:
        text, data = api.call_gemini_image(prompt, self.image_model, quality, size)
        return Generated(image=data, revised_prompt=text)


@dataclass
class OpenAIBackend:
    text_model: str = field(default_factory=lambda: _model("PARA_TEXT_MODEL", DEFAULT_MODELS["openai"][0]))
    image_model: str = field(default_factory=lambda: _model("PARA_IMAGE_MODEL", DEFAULT_MODELS["openai"][1]))

    def describe(self, messages: list[dict]) -> str:
        return api.call_gpt(self.text_model, messages)

    def image(self, prompt: str, quality: str, size: str) -> Generated:
        revised, data = api.call_image(prompt, self.image_model, quality, size)
        return Generated(image=data, revised_prompt=revised)


BACKENDS: dict[str, type] = {"gemini": GeminiBackend, "openai": OpenAIBackend}


def make_backend(name: str = DEFAULT_BACKEND) -> Backend:
    try:
        return BACKENDS[name]()
    except KeyError:
        raise ValueError(f"unknown backend {name!r}; one of: {', '.join(BACKENDS)}") from None
