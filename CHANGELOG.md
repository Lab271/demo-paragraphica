# Changelog

All notable changes to Terra Virtualis (demo-paragraphica). Format: [Keep a Changelog](https://keepachangelog.com/), versions follow SemVer.

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
