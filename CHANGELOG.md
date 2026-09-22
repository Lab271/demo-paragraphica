# Changelog

All notable changes to Terra Virtualis (demo-paragraphica). Format: [Keep a Changelog](https://keepachangelog.com/), versions follow SemVer.

## [0.12.0] - 2026-09-22

The age dial (#47).

### Added
- `--era` / `era` / `GET /eras` / a dropdown in the gallery form: the same spot in another age. Nine eras from 1650 to 2200 plus the ice age; each carries a line for the scout ("as it looked in", or "as it will plausibly look in" for the future) and period cues for the painter. Stored on the record, shown in the card path line, listed by `terra options`; `make run ERA=1650` (#47).
- Note: some providers refuse wartime prompts; `1944` stays in the dial and a refusal shows as the provider's message (0.9.1).

## [0.11.0] - 2026-09-22

### Added
- Exploded-view illustration of the Paragraphica camera on `/about`, made by the camera's own engine (GPT Image 2.5 Flare via OpenRouter) from the design as documented by Bjørn Karmann: star-nosed sensor, the radius / seed / guidance dials, Raspberry Pi 4, GPS, battery, touchscreen. Shipped in the package under `static/`, served at `/static/{name}`.

## [0.10.0] - 2026-09-22

About page (#42).

### Added
- `/about` in the house style: what Terra Virtualis is, who makes it (Ilja Heitlager, LAB271 \ Schuberg Philis, MIT), the backends with their defaults and the active one marked, and the image models grouped by provider, all built from `BACKENDS` / `IMAGE_MODELS` at request time. `/about.json` for machines, `terra about` for the terminal, an "about" link in the gallery header; the static page links to the repository (#42).

## [0.9.1] - 2026-09-22

### Fixed
- A provider refusal (e.g. Alibaba's content moderation on `qwen image 3`, or any 4xx from OpenRouter) surfaced as a bare "Internal Server Error" page that the gallery could not parse. `POST /generate` now answers 502 with the provider's message, the OpenRouter error names the provider, and the gallery shows the status instead of a JSON parse error (#38).

## [0.9.0] - 2026-09-22

OpenRouter backend with a per-picture image model (#38).

### Added
- `--backend openrouter` / `PARA_BACKEND=openrouter`: one key in front of 30+ image models via OpenRouter's Image API; 5xx/429 go through the existing retry path (#38).
- Image model as a request field: `--model` on the CLI, `image_model` on `POST /generate`, `GET /models`, and a dropdown in the gallery form. Ten curated models from the 2026-09-22 live test, GPT Image 2.5 Flare the default; the model label shows in the card path and `terra history` (#38).
- `cost` per image on the history record when the provider reports it; shown in the card summary and after `terra generate` (#38).
- `terra models -b openrouter` lists the curated models and `--filter` searches the live catalogue; `make run MODEL="flux.2 pro"` (#38).

### Changed
- `op.env`: model keys move to the project item `paragraphica` in the Labs vault, one field per vendor (`Gemini`, `OpenRouter`) (#38).

## [0.8.0] - 2026-09-13

Slideshow (#36); legacy Pi role and Streamlit UI removed.

### Added
- Slideshow: `play` button and `p` key cycle the visible pictures newest first in Full mode, default 8 s; `?play` / `?play=N` starts it on load; `terra gallery --play` (#36).

### Removed
- `ansible/` (2024 Pi role), `terra_virtualis.py` with the `streamlit` extra and `make streamlit`, `output/output.png`, `setup.py` (#6, #10).

## [0.7.0] - 2026-09-13

Gallery in the Lab271 house style.

### Changed
- Gallery and served page restyled to the Lab271 design system: midnight canvas, turquoise leads, mono for all small type in path style (`film noir \ landmark \ afternoon`), one square corner on cards and fields, pill buttons.
- Header carries the Lab271 \ Schuberg Philis co-brand lockup (inlined SVG, cobalt only there) and the refracted slash pair as the surface's one brand device.
- Fonts fall back to Avenir Next / Inter; TT Interphases is not shipped.

## [0.6.0] - 2026-09-13

Text control and two Amsterdam framings (#25, #26).

### Added
- `--caption` / `Request.caption` / gallery checkbox: letters the place name into the picture as a postcard title. Stored on the record, default off (#25).
- Framings `through a window` and `from a canal boat`; live 7-framing matrix recorded on #26, aerial kept (#26).

### Changed
- Every image prompt now ends with "No text, lettering or captions in the picture" unless `caption` is set; Gemini wrote dates on polaroids and comic captions unasked (#25).

### Removed
- `requirements.txt`: stale 2023 pins; `pyproject.toml` + `uv.lock` are the source of truth (#6).

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
