"""`terra` — the developer loop. `generate --dry-run` is the prompt-engineering knob."""

from pathlib import Path
from typing import Annotated

import typer

from paragraphica import api, core, prompts
from paragraphica import backend as backends

app = typer.Typer(no_args_is_help=True, help="Terra Virtualis: imagine the view at a location.")

DEFAULT_LATLON = (52.274972, 4.750813)  # Schuberg Philis, Schiphol-Rijk
EXTENSIONS = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}


def _choice(name: str, value: str, options: dict) -> None:
    if value not in options:
        raise typer.BadParameter(f"unknown {name} {value!r}; one of: {', '.join(options)}")


@app.command()
def generate(
    location: Annotated[str | None, typer.Option("--location", "-l", help="Place name (forward geocoded)")] = None,
    lat: Annotated[float | None, typer.Option(help="Latitude; overrides --location")] = None,
    lon: Annotated[float | None, typer.Option(help="Longitude; overrides --location")] = None,
    style: Annotated[str, typer.Option("--style", "-s")] = "realistic",
    context: Annotated[str, typer.Option("--context", "-c")] = "main attraction",
    position: Annotated[str, typer.Option("--position", "-p")] = "normal",
    quality: Annotated[str, typer.Option(help="low | medium | high")] = "medium",
    backend: Annotated[
        str, typer.Option("--backend", "-b", help="Model backend (PARA_BACKEND)")
    ] = backends.DEFAULT_BACKEND,
    weather: Annotated[bool, typer.Option(help="Include current weather")] = False,
    time: Annotated[bool, typer.Option(help="Include local time of day")] = True,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print description + prompt, make no image call")] = False,
    out: Annotated[Path, typer.Option("--out", "-o", help="Output image; suffix follows the returned format")] = Path(
        "output/output"
    ),
) -> None:
    """Generate one image for a location."""
    _choice("style", style, prompts.STYLES)
    _choice("context", context, prompts.CONTEXTS)
    _choice("position", position, prompts.POSITIONS)
    _choice("backend", backend, backends.BACKENDS)

    if lat is None or lon is None:
        lat, lon = api.call_mapbox_forward(location) if location else DEFAULT_LATLON

    req = core.Request(
        lat=lat,
        lon=lon,
        style=style,
        context=context,
        position=position,
        include_time=time,
        include_weather=weather,
        quality=quality,
    )
    result = core.generate(req, backends.make_backend(backend), dry_run=dry_run)

    typer.echo(f"Backend:     {backend}")
    typer.echo(f"Location:    {result.context.address} ({lat:.6f}, {lon:.6f})")
    if result.context.time_of_day:
        typer.echo(f"Time:        {result.context.time_of_day}")
    if result.context.weather:
        typer.echo(f"Weather:     {result.context.weather}")
    typer.echo(f"Description: {result.description}")
    typer.echo(f"Prompt:      {result.prompt}")
    if dry_run:
        return
    out = out.with_suffix(EXTENSIONS.get(result.mime_type, ".bin"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(result.image or b"")
    if result.revised_prompt:
        typer.echo(f"Revised:     {result.revised_prompt}")
    typer.echo(f"Image:       {out}")


@app.command()
def options() -> None:
    """List the available styles, contexts and positions."""
    for title, table in (("styles", prompts.STYLES), ("contexts", prompts.CONTEXTS), ("positions", prompts.POSITIONS)):
        typer.echo(f"{title}:")
        for key in table:
            typer.echo(f"  {key}")


@app.command()
def models(
    filter: Annotated[str, typer.Option("--filter", "-f", help="Substring to match")] = "gemini",
) -> None:
    """List the Gemini models available to the configured key (needs GEMINI_API_KEY)."""
    for name, acts in api.list_gemini_models():
        if filter in name:
            typer.echo(f"{name:45} {acts}")
