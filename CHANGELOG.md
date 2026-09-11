# Changelog

All notable changes to Terra Virtualis (demo-paragraphica). Format: [Keep a Changelog](https://keepachangelog.com/), versions follow SemVer.

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
