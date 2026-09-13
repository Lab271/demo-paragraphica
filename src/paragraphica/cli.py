"""`terra` — the developer loop. `generate --dry-run` is the prompt-engineering knob."""

from pathlib import Path
from typing import Annotated

import typer

from paragraphica import api, core, gallery, prompts
from paragraphica import backend as backends
from paragraphica import context as ctxmod
from paragraphica.store import Store

app = typer.Typer(no_args_is_help=True, help="Terra Virtualis: imagine the view at a location.")

DEFAULT_LATLON = (52.274972, 4.750813)  # Schuberg Philis, Schiphol-Rijk
OUT_DIR = Path("output")


def _choice(name: str, value: str, options: dict) -> None:
    if value not in options:
        raise typer.BadParameter(f"unknown {name} {value!r}; one of: {', '.join(options)}")


@app.command()
def generate(
    location: Annotated[str | None, typer.Option("--location", "-l", help="Place name (forward geocoded)")] = None,
    lat: Annotated[float | None, typer.Option(help="Latitude; overrides --location")] = None,
    lon: Annotated[float | None, typer.Option(help="Longitude; overrides --location")] = None,
    style: Annotated[
        str, typer.Option("--style", "-s", help="Look: " + " | ".join(prompts.LOOKS))
    ] = prompts.DEFAULT_LOOK,
    context: Annotated[
        str, typer.Option("--context", "-c", help="Subject: " + " | ".join(prompts.SUBJECTS))
    ] = prompts.DEFAULT_SUBJECT,
    position: Annotated[
        str, typer.Option("--position", "-p", help="Framing: " + " | ".join(prompts.FRAMINGS))
    ] = prompts.DEFAULT_FRAMING,
    quality: Annotated[str, typer.Option(help="low | medium | high")] = "medium",
    backend: Annotated[
        str, typer.Option("--backend", "-b", help="Model backend (PARA_BACKEND)")
    ] = backends.DEFAULT_BACKEND,
    weather: Annotated[bool, typer.Option(help="Include current weather")] = False,
    time: Annotated[bool, typer.Option(help="Include local time of day")] = True,
    time_of_day: Annotated[
        str | None, typer.Option("--time-of-day", help="Override the clock: " + " | ".join(ctxmod.TIMES_OF_DAY))
    ] = None,
    wander: Annotated[
        float, typer.Option("--wander", help="Metres: move to a random spot within this radius first (#22)")
    ] = 0.0,
    seed: Annotated[int | None, typer.Option(help="Reproducible wandering")] = None,
    variants: Annotated[
        int, typer.Option("--variants", "-n", min=1, max=4, help="Images for the same prompt (#23)")
    ] = 1,
    caption: Annotated[bool, typer.Option("--caption", help="Letter the place name into the picture (#25)")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print description + prompt, make no image call")] = False,
    out_dir: Annotated[
        Path, typer.Option("--out-dir", "-o", help="History store: images + history.jsonl + index.html")
    ] = OUT_DIR,
) -> None:
    """Generate one image for a location."""
    _choice("style", style, prompts.STYLES)
    _choice("context", context, prompts.CONTEXTS)
    _choice("position", position, prompts.POSITIONS)
    _choice("backend", backend, backends.BACKENDS)
    if time_of_day is not None:
        _choice("time-of-day", time_of_day, dict.fromkeys(ctxmod.TIMES_OF_DAY))

    model = backends.make_backend(backend)
    if lat is None or lon is None:
        if location:
            try:
                found = ctxmod.geocode(location, model.describe)
            except ctxmod.LocationNotFound:
                raise typer.BadParameter(f"location not found: {location!r}", param_hint="--location") from None
            lat, lon, location = found.lat, found.lon, found.name
        else:
            lat, lon = DEFAULT_LATLON

    req = core.Request(
        lat=lat,
        lon=lon,
        style=style,
        context=context,
        position=position,
        include_time=time,
        include_weather=weather,
        quality=quality,
        time_of_day=time_of_day,
        wander_m=wander,
        seed=seed,
        caption=caption,
    )
    results = (
        [core.generate(req, model, dry_run=dry_run)]
        if dry_run or variants == 1
        else core.generate_variants(req, model, variants)
    )
    result = results[0]

    typer.echo(f"Backend:     {backend}")
    typer.echo(
        f"Location:    {result.context.address} ({result.context.lat or lat:.6f}, {result.context.lon or lon:.6f})"
    )
    if result.context.time_of_day:
        typer.echo(f"Time:        {result.context.time_of_day}")
    if result.context.weather:
        typer.echo(f"Weather:     {result.context.weather}")
    typer.echo(f"Description: {result.description}")
    typer.echo(f"Prompt:      {result.prompt}")
    if dry_run:
        return
    store = Store(out_dir)
    for res in results:
        rec = store.save(
            req,
            res,
            backend=backend,
            text_model=getattr(model, "text_model", ""),
            image_model=getattr(model, "image_model", ""),
            location=location or "",
        )
        if res.revised_prompt:
            typer.echo(f"Revised:     {res.revised_prompt}")
        typer.echo(f"Image:       {store.root / rec.image}  ({rec.duration_s:g}s)")
    _write_gallery(store)


def _write_gallery(store: Store) -> Path:
    page = store.root / "index.html"
    page.write_text(gallery.render(store.records()), encoding="utf-8")
    return page


@app.command()
def history(
    last: Annotated[int, typer.Option("--last", "-n", help="Show the most recent N runs")] = 20,
    out_dir: Annotated[Path, typer.Option("--out-dir", "-o")] = OUT_DIR,
) -> None:
    """List recent generations from the history store."""
    recs = Store(out_dir).records()
    if not recs:
        typer.echo(f"no history in {out_dir}")
        return
    for r in recs[-last:]:
        typer.echo(f"{r.timestamp[:16].replace('T', ' ')}  {r.style:14} {r.address:40.40} {r.image}")


@app.command("gallery")
def gallery_cmd(
    out_dir: Annotated[Path, typer.Option("--out-dir", "-o")] = OUT_DIR,
    open_: Annotated[bool, typer.Option("--open", help="Open the page in the default browser")] = False,
) -> None:
    """(Re)build output/index.html, the static gallery over the history store."""
    page = _write_gallery(Store(out_dir))
    typer.echo(f"Gallery:     {page}")
    if open_:
        typer.launch(str(page.resolve()))


@app.command()
def options() -> None:
    """List the vocabulary: looks, subjects, framings."""
    for title, table in (
        ("looks (--style)", prompts.LOOKS),
        ("subjects (--context)", prompts.SUBJECTS),
        ("framings (--position)", prompts.FRAMINGS),
    ):
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


@app.command()
def serve(
    host: Annotated[str, typer.Option(help="Bind address; 0.0.0.0 for the LAN")] = "0.0.0.0",
    port: Annotated[int, typer.Option()] = 8471,
) -> None:
    """Run the HTTP service (gallery at /, API at /generate, /history, /styles...)."""
    from paragraphica import service

    service.run(host=host, port=port)
