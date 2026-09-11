"""Location + Style + Context -> Prompt -> Image. One function, no UI."""

import time
from dataclasses import dataclass

from paragraphica import prompts
from paragraphica.backend import Backend
from paragraphica.context import Context, build_context


@dataclass(frozen=True)
class Request:
    lat: float
    lon: float
    style: str = "realistic"
    context: str = "main attraction"
    position: str = "normal"
    main_prompt: str = prompts.MAIN_PROMPT
    include_time: bool = True
    include_weather: bool = False
    quality: str = "medium"
    size: str = "1024x1024"


@dataclass(frozen=True)
class Result:
    context: Context
    description: str
    prompt: str
    image: bytes | None = None
    revised_prompt: str | None = None
    mime_type: str = "image/png"
    duration_s: float = 0.0  # model calls only, not the geo lookups


def generate(req: Request, backend: Backend, *, dry_run: bool = False, context: Context | None = None) -> Result:
    """Run the pipeline. `context` can be injected to skip the geo lookups;
    `dry_run` stops after the prompt and spends no image call."""
    ctx = context or build_context(req.lat, req.lon, req.include_time, req.include_weather)
    t0 = time.perf_counter()
    description = backend.describe(prompts.describe_messages(req.context, ctx))
    prompt = prompts.build_prompt(ctx.address, description, req.style, req.position, req.main_prompt)
    if dry_run:
        return Result(context=ctx, description=description, prompt=prompt, duration_s=time.perf_counter() - t0)
    gen = backend.image(prompt, req.quality, req.size)
    return Result(
        context=ctx,
        description=description,
        prompt=prompt,
        image=gen.image,
        revised_prompt=gen.revised_prompt,
        mime_type=gen.mime_type,
        duration_s=time.perf_counter() - t0,
    )
