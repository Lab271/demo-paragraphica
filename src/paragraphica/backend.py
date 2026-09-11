"""Model backends. A backend is the only thing in the pipeline that talks to a
model; everything upstream is strings and dataclasses."""

import os
from dataclasses import dataclass
from typing import Protocol

from paragraphica import api

DEFAULT_TEXT_MODEL = os.environ.get("PARA_TEXT_MODEL", "gpt-5-mini")
DEFAULT_IMAGE_MODEL = os.environ.get("PARA_IMAGE_MODEL", "gpt-image-2")


@dataclass(frozen=True)
class Generated:
    image: bytes
    revised_prompt: str | None = None


class Backend(Protocol):
    def describe(self, messages: list[dict]) -> str: ...

    def image(self, prompt: str, quality: str, size: str) -> Generated: ...


@dataclass
class OpenAIBackend:
    text_model: str = DEFAULT_TEXT_MODEL
    image_model: str = DEFAULT_IMAGE_MODEL

    def describe(self, messages: list[dict]) -> str:
        return api.call_gpt(self.text_model, messages)

    def image(self, prompt: str, quality: str, size: str) -> Generated:
        revised, data = api.call_image(prompt, self.image_model, quality, size)
        return Generated(image=data, revised_prompt=revised)
