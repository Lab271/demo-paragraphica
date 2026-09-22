"""HTTP service over the core and the store, for the Pi client and the gallery.

    terra serve            # or: make serve (wraps it in `op run` for the keys)

Thin by design: validation + one call into core.generate + Store.save. API keys
live in this process's environment and never appear in a response."""

from dataclasses import asdict
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from paragraphica import __version__, about, core, gallery, prompts
from paragraphica import backend as backends
from paragraphica import context as ctxmod
from paragraphica.context import TIMES_OF_DAY
from paragraphica.store import Store

DEFAULT_LATLON = (52.274972, 4.750813)  # Schuberg Philis, Schiphol-Rijk


class GenerateRequest(BaseModel):
    location: str | None = Field(None, description="Place name, forward geocoded; ignored when lat/lon given")
    lat: float | None = None
    lon: float | None = None
    style: str = prompts.DEFAULT_LOOK
    context: str = prompts.DEFAULT_SUBJECT
    position: str = prompts.DEFAULT_FRAMING
    quality: str = "medium"
    image_model: str | None = Field(None, description="Image model label; one of GET /models (OpenRouter only)")
    include_time: bool = True
    include_weather: bool = False
    time_of_day: str | None = Field(None, description="Override the clock; one of GET /times")
    wander_m: float = Field(0.0, ge=0, le=20000, description="Move to a random spot within this radius first")
    seed: int | None = None
    variants: int = Field(1, ge=1, le=4, description="Images for the same prompt")
    caption: bool = Field(False, description="Letter the place name into the picture")


def create_app(store: Store | None = None, backend_name: str = backends.DEFAULT_BACKEND) -> FastAPI:
    store = store or Store()
    app = FastAPI(title="Terra Virtualis", version=__version__)

    def _check(name: str, value: str, options: dict) -> None:
        if value not in options:
            raise HTTPException(422, f"unknown {name} {value!r}; one of: {', '.join(options)}")

    @app.get("/healthz")
    def healthz() -> dict:
        return {"ok": True, "version": __version__, "backend": backend_name, "images": len(store.records())}

    @app.get("/styles")
    def styles() -> dict[str, str]:
        return prompts.STYLES

    @app.get("/contexts")
    def contexts() -> dict[str, str]:
        return prompts.CONTEXTS

    @app.get("/positions")
    def positions() -> dict[str, str]:
        return prompts.POSITIONS

    @app.get("/models")
    def models() -> dict[str, str]:
        """Image models selectable per request (label -> slug); empty unless the backend is openrouter."""
        return backends.IMAGE_MODELS if backend_name == "openrouter" else {}

    @app.get("/times")
    def times() -> list[str]:
        return list(TIMES_OF_DAY)

    @app.get("/history")
    def history(last: Annotated[int, Query(ge=1, le=1000)] = 50) -> list[dict]:
        recs = store.records()[-last:]
        return [_public(r) for r in reversed(recs)]

    @app.post("/generate")
    def generate(req: GenerateRequest) -> dict:
        _check("style", req.style, prompts.STYLES)
        _check("context", req.context, prompts.CONTEXTS)
        _check("position", req.position, prompts.POSITIONS)
        if req.time_of_day:
            _check("time_of_day", req.time_of_day, dict.fromkeys(TIMES_OF_DAY))
        if req.image_model:
            _check("image_model", req.image_model, models())
        model = backends.make_backend(backend_name)
        location = req.location or ""
        if req.lat is None or req.lon is None:
            if req.location:
                try:
                    found = ctxmod.geocode(req.location, model.describe)
                except ctxmod.LocationNotFound:
                    raise HTTPException(404, f"location not found: {req.location!r}") from None
                except backends.TransientError as e:
                    raise HTTPException(503, f"model temporarily unavailable: {e}") from None
                lat, lon, location = found.lat, found.lon, found.name
            else:
                lat, lon = DEFAULT_LATLON
        else:
            lat, lon = req.lat, req.lon
        core_req = core.Request(
            lat=lat,
            lon=lon,
            style=req.style,
            context=req.context,
            position=req.position,
            include_time=req.include_time,
            include_weather=req.include_weather,
            quality=req.quality,
            image_model=backends.IMAGE_MODELS[req.image_model] if req.image_model else None,
            time_of_day=req.time_of_day or None,
            wander_m=req.wander_m,
            seed=req.seed,
            caption=req.caption,
        )
        try:
            results = core.generate_variants(core_req, model, req.variants)
        except backends.TransientError as e:
            raise HTTPException(503, f"model temporarily unavailable: {e}") from None
        except RuntimeError as e:  # provider refused: content moderation, bad parameter, no image
            raise HTTPException(502, str(e)[:300]) from None
        recs = [
            store.save(
                core_req,
                res,
                backend=backend_name,
                text_model=getattr(model, "text_model", ""),
                image_model=core_req.image_model or getattr(model, "image_model", ""),
                location=location,
            )
            for res in results
        ]
        (store.root / "index.html").write_text(gallery.render(store.records()), encoding="utf-8")
        return {**_public(recs[0]), "records": [_public(r) for r in recs]}

    @app.get("/images/{name}")
    def image(name: str) -> FileResponse:
        path = store.root / Path(name).name  # no traversal: basename only
        if not path.is_file() or path.suffix not in {".png", ".jpg", ".webp"}:
            raise HTTPException(404, "no such image")
        return FileResponse(path)

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return gallery.render(store.records(), image_base="/images/", controls=True)

    @app.get("/about.json")
    def about_json() -> dict:
        return about.about_data(backend_name)

    @app.get("/about", response_class=HTMLResponse)
    def about_page() -> str:
        return about.render(about.about_data(backend_name))

    return app


def _public(rec) -> dict:
    """Record as JSON, plus the URL the client fetches the image from."""
    d = asdict(rec)
    d["image_url"] = f"/images/{rec.image}"
    return d


def run(host: str = "0.0.0.0", port: int = 8471) -> None:
    import uvicorn

    uvicorn.run(create_app(), host=host, port=port, log_level="info")
