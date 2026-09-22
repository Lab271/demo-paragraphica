"""The about page: what Terra Virtualis is, who makes it, and which engines it runs
on. The engine table is built from backend.BACKENDS / IMAGE_MODELS at request
time, so adding a model there is the only change needed (#42)."""

from dataclasses import dataclass
from html import escape

from paragraphica import __version__
from paragraphica import backend as backends
from paragraphica.gallery import CSS, LOCKUP, REPO

MAINTAINER = "Ilja Heitlager"

# Display names for slug prefixes; anything not listed is title-cased.
PROVIDERS = {
    "openai": "OpenAI",
    "black-forest-labs": "Black Forest Labs",
    "bytedance-seed": "ByteDance Seed",
    "google": "Google",
    "microsoft": "Microsoft",
    "qwen": "Qwen (Alibaba)",
    "x-ai": "xAI",
    "recraft": "Recraft",
}


@dataclass(frozen=True)
class Model:
    label: str
    slug: str
    provider: str
    default: bool


def provider_of(slug: str) -> str:
    prefix = slug.split("/")[0] if "/" in slug else "google"  # bare Gemini ids are Google's
    return PROVIDERS.get(prefix, prefix.replace("-", " ").title())


def about_data(backend_name: str = backends.DEFAULT_BACKEND) -> dict:
    """Everything the page and /about.json show. Pure: no network, no store."""
    engines = []
    for name in backends.BACKENDS:
        text, image = backends.DEFAULT_MODELS[name]
        engines.append({"name": name, "active": name == backend_name, "text_model": text, "image_model": image})
    default_image = backends.DEFAULT_MODELS["openrouter"][1]
    models = [
        Model(label, slug, provider_of(slug), slug == default_image) for label, slug in backends.IMAGE_MODELS.items()
    ]
    providers: dict[str, list[Model]] = {}
    for m in models:
        providers.setdefault(m.provider, []).append(m)
    return {
        "name": "Terra Virtualis",
        "version": __version__,
        "maintainer": MAINTAINER,
        "organisation": "LAB271 \\ Schuberg Philis",
        "license": "MIT",
        "repo": REPO,
        "backend": backend_name,
        "engines": engines,
        "providers": [
            {"name": p, "models": [{"label": m.label, "slug": m.slug, "default": m.default} for m in ms]}
            for p, ms in providers.items()
        ],
    }


ABOUT_CSS = """
.about { max-width: 52rem; padding: 1.5rem; }
.about h2 { margin: 2rem 0 .6rem; font-size: 21px; }
.about p { margin: .5rem 0; max-width: 40rem; }
.about a { color: var(--c-tq); text-decoration: none; }
.about a:hover { text-decoration: underline; }
.about table { border-collapse: collapse; width: 100%; font-family: var(--mono); font-size: 12.5px; letter-spacing: .04em; }
.about th, .about td { text-align: left; padding: .45rem .6rem; border-bottom: 1px solid var(--c-border); vertical-align: top; }
.about th { color: var(--c-muted); font-weight: 400; }
.about td.p { color: var(--c-tq); white-space: nowrap; }
.about td.s { color: var(--c-muted); }
.about .tag { display: inline-block; margin-left: .5rem; padding: 0 8px; border-radius: 999px 999px 999px 0; background: var(--c-panel); color: var(--c-tq); font-size: 10.5px; }
.about kbd { font-family: var(--mono); background: var(--c-panel); padding: 0 .4rem; border-radius: 6px 6px 6px 0; }
"""


def _engine_rows(d: dict) -> str:
    rows = []
    for e in d["engines"]:
        tag = "<span class=tag>active</span>" if e["active"] else ""
        rows.append(
            f"<tr><td class=p>{escape(e['name'])}{tag}</td><td>{escape(e['text_model'])}</td>"
            f"<td>{escape(e['image_model'])}</td></tr>"
        )
    return "".join(rows)


def _model_rows(d: dict) -> str:
    rows = []
    for p in d["providers"]:
        for i, m in enumerate(p["models"]):
            who = escape(p["name"]) if i == 0 else ""
            tag = "<span class=tag>default</span>" if m["default"] else ""
            rows.append(
                f"<tr><td class=p>{who}</td><td>{escape(m['label'])}{tag}</td><td class=s>{escape(m['slug'])}</td></tr>"
            )
    return "".join(rows)


def render(d: dict | None = None) -> str:
    d = d or about_data()
    return f"""<!doctype html>
<html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width, initial-scale=1">
<title>About \\ {escape(d["name"])}</title><style>{CSS}{ABOUT_CSS}</style></head>
<body>
<header>{LOCKUP}<h1>{escape(d["name"])}</h1><span class=count>v{escape(d["version"])}</span>
<a class=nav href="/">\\ gallery</a>
<span class="slash tq"></span><span class="slash or"></span></header>
<div class=about>
<h2>What it is</h2>
<p>Terra Virtualis is a lensless camera. It knows where it stands, asks a language model what
the view from there looks like, and asks an image model to paint it in a chosen look. It is
LAB271's remake of <a href="https://bjoernkarmann.dk/project/paragraphica">Paragraphica</a> by
Bjørn Karmann.</p>
<p>The camera is a thin client: a Raspberry Pi with a GPS fix and a screen talks to this
service, which does the geocoding and the model calls. The models run in the cloud today and
on a Mac Mini in the lab tomorrow.</p>

<h2>Who</h2>
<p>Main developer: <b>{escape(d["maintainer"])}</b> \\ {escape(d["organisation"])} \\
{escape(d["license"])} license \\ <a href="{escape(d["repo"])}">source on GitHub</a> \\ version {escape(d["version"])}.</p>

<h2>Engines</h2>
<p>A backend is the one thing that talks to a model. The service runs on one backend at a
time; the <span class=tag>active</span> one below. Each has a default text model for the
description and a default image model for the picture.</p>
<table><tr><th>backend</th><th>text model</th><th>image model</th></tr>{_engine_rows(d)}</table>

<h2>Image models</h2>
<p>On the OpenRouter backend the image model is a per-picture choice, the dropdown in the
gallery form. These are the models on offer, by provider.</p>
<table><tr><th>provider</th><th>model</th><th>slug</th></tr>{_model_rows(d)}</table>

<h2>How to use it</h2>
<p>Type a place in the gallery form, pick a look, a subject and a framing, and press
<b>generate</b>. The picture lands in the gallery with its description and prompt behind the
card. Click a picture to open it with a map of where it stands; <kbd>←</kbd> <kbd>→</kbd>
move, <kbd>f</kbd> fills the screen, <kbd>p</kbd> starts a slideshow. Pictures are kept in
<code>history.jsonl</code> next to the image files.</p>
</div>
<footer>terra virtualis \\ a lensless camera that imagines the view from where it stands \\ after bjørn karmann's paragraphica \\ LAB271 \\ schuberg philis</footer>
</body></html>
"""


def text(d: dict | None = None) -> str:
    """The same story for the terminal (`terra about`)."""
    d = d or about_data()
    lines = [
        f"{d['name']} v{d['version']}: a lensless camera that imagines the view from where it stands.",
        f"After Bjørn Karmann's Paragraphica. {d['maintainer']} \\ {d['organisation']} \\ {d['license']} \\ {d['repo']}",
        "",
        "backends:",
    ]
    for e in d["engines"]:
        mark = " (active)" if e["active"] else ""
        lines.append(f"  {e['name']:12}{mark:9} text {e['text_model']}  image {e['image_model']}")
    lines.append("")
    lines.append("image models (openrouter):")
    for p in d["providers"]:
        for m in p["models"]:
            mark = " (default)" if m["default"] else ""
            lines.append(f"  {p['name']:18} {m['label']:24} {m['slug']}{mark}")
    return "\n".join(lines)
