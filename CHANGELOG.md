# Changelog

All notable changes to Terra Virtualis (demo-paragraphica). Format: [Keep a Changelog](https://keepachangelog.com/), versions follow SemVer.

## [0.5.0] - 2026-09-13

Web UI controls, vocabulary redesign, geocoding variety and robustness (#13, #16, #17, #18, #22, #23, #24, #28, #29).

### Added
- `Request.time_of_day` overrides the clock; CLI `--time-of-day`, `GET /times`. Form gets a "now (local time)" select and a weather checkbox; cards and detail show the weather string (#18).
- Map beside the picture in the detail overlay: Leaflet 1.9.4 from cdnjs + OpenStreetMap, loaded on first open so the static page stays offline-capable; hidden in Full mode (#17).
- `context.wander()`: random point within N metres, then reverse geocode, so the camera lands on a real street elsewhere in town. `Request.wander_m` / `seed`, CLI `--wander` / `--seed`; records store the resolved lat/lon (#22).
- `core.generate_variants()`: one description, N images. CLI `--variants 1..4`; service `variants` returns the first record plus `records: [...]` (#23).
- Looks: dutch masters, cyanotype, stained glass, tin toy, risograph, thermal, elevation, frank miller with Sin City cues (18 looks total) (#24, #13).

### Changed
- Vocabulary redesigned as three dials: Look (photo, polaroid, film noir, impressionist, woodblock, blueprint, isometric, lego, coloring page, pixel, ...), Framing (eye level, wide, low, aerial, street) and Subject (landmark, people, nature, night life, food, three highlights). Every fragment is one concrete visual sentence; system prompt rewritten as a location-scout brief. `STYLES`/`POSITIONS`/`CONTEXTS` kept as aliases, request/record fields and API paths unchanged. Defaults: photo / eye level / landmark (#13).
- Gallery form and controls complete the generate-from-gallery flow; the page reloads on success (#16).

### Fixed
- Hybrid geocoder: a Mapbox hit is accepted only if it is a named place mentioning every query word; otherwise a small Gemini text call returns `{name, lat, lon}` or null, and only then is the location a 404. The resolved name is stored instead of the raw input. "amsterdam wallen" no longer renders near Rouen (#29).
- Gemini calls: 60 s timeout, SDK retries off, 5xx backoff 2 s / 6 s, short 429 `retryDelay` honoured (#28).
- Test warnings quieted: httpx 2 for starlette's TestClient, anyio alias warning ignored.

## [0.4.0] - 2026-09-11

HTTP service and interactive gallery (#9, part of #16).

### Added
- FastAPI service: `POST /generate`, `GET /history`, `/styles`, `/contexts`, `/positions`, `/images/{name}`, gallery at `/`, `/healthz`. `terra serve`, `make serve`, `service` extra.
- launchd agent for the Mac Mini: `deploy/launchd/io.lab271.terra.plist`, `make service-install` / `service-uninstall`.
- One automatic retry on a provider 5xx (`backend.with_retry`); the service answers 503 if the retry fails too.
- Gallery: generate form on the served page; detail overlay with large image, ←/→ navigation, Full mode, record below, `#n` deep links.

### Fixed
- Served gallery linked images relative to `/`; now under `/images/`.

## [0.3.0] - 2026-09-11

History store and static gallery (#7).

### Added
- `Store`: every generation writes a timestamped image and appends one JSON line to `output/history.jsonl` (append-only, forward-compatible `extra`).
- Static gallery `output/index.html`: newest-first card grid, style filter, fold-out with description, prompt, model and duration.
- `terra history [--last N]`, `terra gallery [--open]`; `make history`, `make gallery`.
- `Result.duration_s` times the model calls.

### Changed
- `terra generate --out-dir` replaces `--out`; images are named `<timestamp>-<place>-<style>.<ext>`.

## [0.2.0] - 2026-09-11

First release of the rebuild ([docs/plan-2026-09.md](docs/plan-2026-09.md), #5).

### Added
- Core pipeline `Location + Style + Context -> Prompt -> Image` behind a `Backend` protocol (`context`, `prompts`, `backend`, `core`).
- `terra` CLI: `generate` (with `--dry-run`), `options`, `models`.
- Google Gemini backend: `gemini-3.1-flash-lite` for the description, `gemini-3.1-flash-image` for the image.
- `polaroid` style.
- API keys from the 1Password Labs vault at run time (`op.env`, `tools/op-env.sh`, `make env-check`); no `.env`.
- Packaging: `pyproject.toml` + `uv.lock`, `.mise.toml` (Python 3.12.13, uv 0.12.2), Makefile with `help` as default.
- 78 offline tests on recorded fixtures and a fake backend.

### Changed
- Timezone computed offline with `timezonefinder`; geotimezone.com dropped.
- Output file suffix follows the mime type the model returns.
- Ansible role: Gemini key lookup replaces OpenAI.
- `terra_virtualis.py` is a thin Streamlit shell over the core (removed in #10).

### Removed
- OpenAI / DALL-E 3, the `mapbox` SDK, `ImageModel`, and the dead scripts under `tests/`.
