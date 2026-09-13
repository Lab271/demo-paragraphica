# paragraphica
Our remake of the paragraphica project by [Bjoern Karmann](https://bjoernkarmann.dk/project/paragraphica), now called Terra Virtualis. This codebase is setup such that it can be tested from any developer laptop without the need of a Raspberry or GPS devices. Working title is now gpt_viewmaster, our GPT pane on the world.

Be sure to set the environ variables first

To get started (needs [mise](https://mise.jdx.dev/), which pins Python and uv):
```
    cd  [this_folder]
    mise install
    make install
```

Then, for the developer loop:
```
    make dry-run LOCATION="Amsterdam" STYLE="film noir"   # description + prompt only, no image call
    make run LOCATION="Amsterdam" STYLE="film noir"       # image + history line in output/, rebuilds output/index.html
    make history                                          # recent runs
    make gallery                                          # open the static gallery page
    uv run terra options                                  # the vocabulary: looks, subjects, framings
    make env-check && op run --env-file=op.env -- uv run terra models   # Gemini models your key can call
```
`make help` lists everything. See `docs/plan-2026-09.md` for the rebuild plan.

## Service

`make serve` runs the HTTP service on port 8471 with the keys injected by 1Password.
The gallery is at `/`, the API is what the Pi client (#10) talks to:

```
    curl -s localhost:8471/healthz
    curl -s localhost:8471/styles                     # also /contexts /positions
    curl -s -X POST localhost:8471/generate -H 'content-type: application/json' \
         -d '{"location":"Amsterdam","style":"film noir"}'      # 10-25 s; returns the record + image_url
    curl -s 'localhost:8471/history?last=5'
    curl -sO localhost:8471/images/<name from image_url>
```

Transient 503/504 from Gemini are retried once inside the backend; if the retry
fails too the service answers 503 and the client may try again.

On the Mac Mini, `make service-install` installs a launchd agent
(`deploy/launchd/io.lab271.terra.plist`) that starts at login and restarts on
failure; `make service-uninstall` removes it. It runs `op run`, so the 1Password
app must be unlocked for that user; for a headless box put an
`OP_SERVICE_ACCOUNT_TOKEN` in the plist's `EnvironmentVariables` instead.

## API keys

Keys live in the 1Password **Labs** vault and never in a file. `op.env` holds the
secret *references*; `make run` / `make dry-run` wrap the command in
`op run --env-file=op.env` so the keys exist only inside that process. For a
shell session: `eval "$(tools/op-env.sh)"`. `make env-check` shows which items
resolve without printing values.

| Variable | 1Password item (field `paragraphica`) | Used by |
|---|---|---|
| `GEMINI_API_KEY` | `Gemini` | text + image generation |
| `PARA_MAPBOX_API` | `Mapbox` | geocoding |
| `PARA_OPENWEATHERMAP_API` | `Openweathermap` | `--weather` |

**Getting a Gemini key:** sign in with the Labs Google account at
https://aistudio.google.com/apikey and create a key. Attach it to a Google Cloud
project with billing enabled; the free tier is rate-limited and image models
are billed per image. Store it as item `Gemini`, field `paragraphica`, in the
Labs vault so both `op.env` and the Ansible role find it. Model docs:
https://ai.google.dev/gemini-api/docs/image-generation

Override models with `PARA_TEXT_MODEL` / `PARA_IMAGE_MODEL`. A local backend
(Mac Mini, Ollama + Draw Things) is planned in #8.

## Todo
1. [DONE] raspberry pi python setup
2. api based prompt to midjourney or others
3. [DONE] location api
4. [DONE] weather api
5. rotary switches on RPI GPIO
6. [DONE] Parameter setting
7. Display controller
8. include camera?
9. wifi
10. image processing
11. [DONE] Raspberry pi headless setup


Libraries
1. Original: https://github.com/bjoernkarmann/Paragraphica/blob/main/main.py
2. Rotary encoder: https://github.com/miketeachman/micropython-rotary
3. open weathermap
4. geotimezone.com
5. mapbox api service
6. Google Gemini for text and image generation (OpenAI/DALL-E until Sep 2026)
