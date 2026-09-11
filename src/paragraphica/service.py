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

from paragraphica import __version__, api, core, gallery, prompts
from paragraphica import backend as backends
from paragraphica.context import TIMES_OF_DAY
from paragraphica.store import Store

DEFAULT_LATLON = (52.274972, 4.750813)  # Schuberg Philis, Schiphol-Rijk


class GenerateRequest(BaseModel):
    location: str | None = Field(None, description="Place name, forward geocoded; ignored when lat/lon given")
    lat: float | None = None
    lon: float | None = None
    style: str = "realistic"
    context: str = "main attraction"
    position: str = "normal"
    quality: str = "medium"
    include_time: bool = True
    include_weather: bool = False
    time_of_day: str | None = Field(None, description="Override the clock; one of GET /times")


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
        if req.lat is None or req.lon is None:
            try:
                lat, lon = api.call_mapbox_forward(req.location) if req.location else DEFAULT_LATLON
            except (KeyError, IndexError):
                raise HTTPException(404, f"location not found: {req.location!r}") from None
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
            time_of_day=req.time_of_day or None,
        )
        model = backends.make_backend(backend_name)
        try:
            result = core.generate(core_req, model)
        except backends.TransientError as e:
            raise HTTPException(503, f"model temporarily unavailable: {e}") from None
        rec = store.save(
            core_req,
            result,
            backend=backend_name,
            text_model=getattr(model, "text_model", ""),
            image_model=getattr(model, "image_model", ""),
            location=req.location or "",
        )
        (store.root / "index.html").write_text(gallery.render(store.records()), encoding="utf-8")
        return _public(rec)

    @app.get("/images/{name}")
    def image(name: str) -> FileResponse:
        path = store.root / Path(name).name  # no traversal: basename only
        if not path.is_file() or path.suffix not in {".png", ".jpg", ".webp"}:
            raise HTTPException(404, "no such image")
        return FileResponse(path)

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return gallery.render(store.records(), image_base="/images/", controls=True)

    return app


def _public(rec) -> dict:
    """Record as JSON, plus the URL the client fetches the image from."""
    d = asdict(rec)
    d["image_url"] = f"/images/{rec.image}"
    return d


def run(host: str = "0.0.0.0", port: int = 8471) -> None:
    import uvicorn

    uvicorn.run(create_app(), host=host, port=port, log_level="info")
