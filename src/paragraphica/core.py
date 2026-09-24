"""Location + Style + Context -> Prompt -> Image. One function, no UI."""

import random
import time
from dataclasses import dataclass, replace

from paragraphica import prompts
from paragraphica.backend import Backend
from paragraphica.context import Context, build_context, wander


@dataclass(frozen=True)
class Request:
    lat: float
    lon: float
    style: str = prompts.DEFAULT_LOOK
    context: str = prompts.DEFAULT_SUBJECT
    position: str = prompts.DEFAULT_FRAMING
    main_prompt: str = prompts.MAIN_PROMPT
    include_time: bool = True
    include_weather: bool = False
    time_of_day: str | None = None  # override the clock, e.g. 'dark night' for a day/night pair
    era: str | None = None  # the age dial: a key of prompts.ERAS, None = today (#47)
    quality: str = "medium"
    size: str = "1024x1024"
    image_model: str | None = None  # IMAGE_MODELS slug; None = backend default (#38)
    wander_m: float = 0.0  # move to a random point within this radius before geocoding (#22)
    seed: int | None = None  # makes wandering reproducible
    caption: bool = False  # letter the place name into the picture (#25)
    nickname: str = ""  # who took it, shown on the card (#48)
    source: str = "cli"  # cli | wall | phone (#48)


@dataclass(frozen=True)
class Result:
    context: Context
    description: str
    prompt: str
    image: bytes | None = None
    revised_prompt: str | None = None
    mime_type: str = "image/png"
    duration_s: float = 0.0  # model calls only, not the geo lookups
    cost: float | None = None  # USD, when the backend reports it


def _prepare(req: Request, backend: Backend, context: Context | None) -> tuple[Context, str, str, float]:
    """Everything up to the image call: context, description, prompt. Shared by variants."""
    lat, lon = req.lat, req.lon
    if req.wander_m > 0:
        lat, lon = wander(lat, lon, req.wander_m, random.Random(req.seed))
    ctx = context or build_context(lat, lon, req.include_time and not req.time_of_day, req.include_weather)
    if req.time_of_day:
        ctx = replace(ctx, time_of_day=req.time_of_day)
    t0 = time.perf_counter()
    description = backend.describe(prompts.describe_messages(req.context, ctx, era=req.era))
    prompt = prompts.build_prompt(
        ctx.address, description, req.style, req.position, req.main_prompt, req.caption, era=req.era
    )
    return ctx, description, prompt, t0


def _image(req: Request, backend: Backend, ctx: Context, description: str, prompt: str, t0: float) -> Result:
    gen = backend.image(prompt, req.quality, req.size, req.image_model)
    return Result(
        context=ctx,
        description=description,
        prompt=prompt,
        image=gen.image,
        revised_prompt=gen.revised_prompt,
        mime_type=gen.mime_type,
        duration_s=time.perf_counter() - t0,
        cost=gen.cost,
    )


def generate(req: Request, backend: Backend, *, dry_run: bool = False, context: Context | None = None) -> Result:
    """Run the pipeline. `context` can be injected to skip the geo lookups;
    `dry_run` stops after the prompt and spends no image call."""
    ctx, description, prompt, t0 = _prepare(req, backend, context)
    if dry_run:
        return Result(context=ctx, description=description, prompt=prompt, duration_s=time.perf_counter() - t0)
    return _image(req, backend, ctx, description, prompt, t0)


def generate_variants(req: Request, backend: Backend, n: int, *, context: Context | None = None) -> list[Result]:
    """One description, n images of the same prompt (#23). Each result times its own image call."""
    ctx, description, prompt, t0 = _prepare(req, backend, context)
    out = []
    for _ in range(max(1, n)):
        out.append(_image(req, backend, ctx, description, prompt, t0))
        t0 = time.perf_counter()
    return out
