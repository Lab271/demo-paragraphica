"""HTTP service over the core and the store, for the Pi client and the gallery.

    terra serve            # or: make serve (wraps it in `op run` for the keys)

Thin by design: validation + one call into core.generate + Store.save. API keys
live in this process's environment and never appear in a response."""

import time
from collections import defaultdict, deque
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
from pydantic import BaseModel, Field

from paragraphica import __version__, about, core, gallery, prompts, shoot
from paragraphica import backend as backends
from paragraphica import context as ctxmod
from paragraphica.context import TIMES_OF_DAY
from paragraphica.store import Store

DEFAULT_LATLON = (52.274972, 4.750813)  # Schuberg Philis, Schiphol-Rijk
STATIC = Path(__file__).parent / "static"  # ships in the wheel: hatchling packages the whole directory
SHOTS_PER_MINUTE = 3  # per client address on /shoot: a room full of phones must not run up the bill (#48)


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
    era: str | None = Field(None, description="The age dial; one of GET /eras, None = today")
    wander_m: float = Field(0.0, ge=0, le=20000, description="Move to a random spot within this radius first")
    seed: int | None = None
    variants: int = Field(1, ge=1, le=4, description="Images for the same prompt")
    caption: bool = Field(False, description="Letter the place name into the picture")
    nickname: str = Field("", max_length=24, description="Who took it; shown on the card")
    source: str = Field("wall", pattern="^(wall|phone|cli)$")


class RateLimit:
    """Sliding window per key, in memory. Good enough for one room; budgets are #49."""

    def __init__(self, per_minute: int = SHOTS_PER_MINUTE) -> None:
        self.per_minute = per_minute
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        q = self.hits[key]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= self.per_minute:
            return False
        q.append(now)
        return True


def create_app(store: Store | None = None, backend_name: str = backends.DEFAULT_BACKEND) -> FastAPI:
    store = store or Store()
    app = FastAPI(title="Terra Virtualis", version=__version__)
    shots = RateLimit()

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

    @app.get("/eras")
    def eras() -> list[str]:
        return list(prompts.ERAS)

    @app.get("/times")
    def times() -> list[str]:
        return list(TIMES_OF_DAY)

    @app.get("/history")
    def history(last: Annotated[int, Query(ge=1, le=1000)] = 50) -> list[dict]:
        recs = store.records()[-last:]
        return [_public(r) for r in reversed(recs)]

    def _generate(req: GenerateRequest) -> dict:
        _check("style", req.style, prompts.STYLES)
        _check("context", req.context, prompts.CONTEXTS)
        _check("position", req.position, prompts.POSITIONS)
        if req.time_of_day:
            _check("time_of_day", req.time_of_day, dict.fromkeys(TIMES_OF_DAY))
        if req.image_model:
            _check("image_model", req.image_model, models())
        if req.era:
            _check("era", req.era, prompts.ERAS)
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
            era=req.era or None,
            wander_m=req.wander_m,
            seed=req.seed,
            caption=req.caption,
            nickname=req.nickname.strip(),
            source=req.source,
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

    @app.post("/generate")
    def generate(req: GenerateRequest) -> dict:
        return _generate(req)

    @app.post("/shoot")
    def shoot_post(req: GenerateRequest, request: Request) -> dict:
        """The phone's shutter (#48): the same pipeline, one picture, rate limited per client."""
        client = request.client.host if request.client else "?"
        if not shots.allow(client):
            raise HTTPException(429, f"easy: {SHOTS_PER_MINUTE} pictures a minute per phone; try again shortly")
        req = req.model_copy(update={"variants": 1, "source": "phone"})
        return _generate(req)

    @app.get("/geocode")
    def geocode(q: Annotated[str, Query(min_length=2, max_length=120)]) -> dict:
        """Forward geocode for the phone's search box: Mapbox first, the text model as fallback."""
        try:
            found = ctxmod.geocode(q, backends.make_backend(backend_name).describe)
        except ctxmod.LocationNotFound:
            raise HTTPException(404, f"location not found: {q!r}") from None
        except backends.TransientError as e:
            raise HTTPException(503, f"model temporarily unavailable: {e}") from None
        return {"lat": found.lat, "lon": found.lon, "name": found.name}

    @app.get("/shoot", response_class=HTMLResponse)
    def shoot_page() -> str:
        return shoot.render(has_models=backend_name == "openrouter")

    @app.get("/qr.svg")
    def qr(request: Request) -> Response:
        """QR to /shoot on this host; the wall shows it in the slideshow corner."""
        import io

        import segno

        url = str(request.base_url).rstrip("/") + "/shoot"
        buf = io.BytesIO()  # a full SVG document (with xmlns), so <img src=/qr.svg> can load it
        segno.make(url, error="m").save(buf, kind="svg", scale=4, dark="#020C17", light="#FFFFFF", border=2)
        return Response(buf.getvalue(), media_type="image/svg+xml")

    @app.get("/images/{name}")
    def image(name: str) -> FileResponse:
        path = store.root / Path(name).name  # no traversal: basename only
        if not path.is_file() or path.suffix not in {".png", ".jpg", ".webp"}:
            raise HTTPException(404, "no such image")
        return FileResponse(path)

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return gallery.render(store.records(), image_base="/images/", controls=True)

    @app.get("/static/{name}")
    def static(name: str) -> FileResponse:
        path = STATIC / Path(name).name  # basename only, no traversal
        if not path.is_file():
            raise HTTPException(404, "no such file")
        return FileResponse(path)

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
