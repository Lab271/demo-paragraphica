"""A single static HTML page over the history store. No server, no framework;
opens from file:// and later from the Pi's screen."""

from html import escape

from paragraphica.store import Record

CSS = """
:root { color-scheme: dark; --bg:#111; --card:#1b1b1b; --fg:#eee; --muted:#9a9a9a; --accent:#e6b450; }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font:15px/1.45 system-ui, -apple-system, Segoe UI, sans-serif; }
header { display:flex; flex-wrap:wrap; gap:1rem; align-items:baseline; padding:1.2rem 1.5rem; border-bottom:1px solid #2a2a2a; }
header h1 { margin:0; font-size:1.3rem; font-weight:600; letter-spacing:.02em; }
header .count { color:var(--muted); }
header select { margin-left:auto; background:var(--card); color:var(--fg); border:1px solid #333; padding:.35rem .5rem; border-radius:6px; }
main { display:grid; gap:1.2rem; padding:1.5rem; grid-template-columns:repeat(auto-fill, minmax(320px, 1fr)); }
article { background:var(--card); border-radius:10px; overflow:hidden; display:flex; flex-direction:column; }
article[hidden] { display:none; }
article img { width:100%; aspect-ratio:1/1; object-fit:cover; display:block; background:#000; }
.meta { padding:.8rem 1rem 0; display:flex; gap:.5rem; flex-wrap:wrap; align-items:center; }
.style { background:var(--accent); color:#111; font-weight:600; padding:.1rem .5rem; border-radius:999px; font-size:.8rem; }
.when, .how { color:var(--muted); font-size:.85rem; }
h2 { margin:.4rem 1rem .2rem; font-size:1rem; font-weight:600; }
details { margin:0 1rem .9rem; }
summary { cursor:pointer; color:var(--muted); font-size:.85rem; }
details p { white-space:pre-wrap; margin:.5rem 0 0; font-size:.9rem; }
details .prompt { color:var(--muted); }
footer { color:var(--muted); text-align:center; padding:2rem; font-size:.85rem; }
"""

JS = """
const sel = document.getElementById('style');
sel.addEventListener('change', () => {
  for (const a of document.querySelectorAll('article'))
    a.hidden = sel.value !== '' && a.dataset.style !== sel.value;
});
"""


def _card(r: Record) -> str:
    when = r.timestamp.replace("T", " ")[:16]
    how = " · ".join(x for x in (r.position if r.position != "normal" else "", r.context, r.time_of_day) if x)
    revised = f"<p class=prompt><b>Model note</b> {escape(r.revised_prompt)}</p>" if r.revised_prompt else ""
    return f"""
<article data-style="{escape(r.style)}">
  <a href="{escape(r.image)}"><img src="{escape(r.image)}" alt="{escape(r.address)} in {escape(r.style)} style" loading="lazy"></a>
  <div class=meta><span class=style>{escape(r.style)}</span><span class=when>{escape(when)}</span><span class=how>{escape(how)}</span></div>
  <h2>{escape(r.address)}</h2>
  <details>
    <summary>description · prompt · {escape(r.image_model)} · {r.duration_s:g}s</summary>
    <p>{escape(r.description)}</p>
    <p class=prompt><b>Prompt</b> {escape(r.prompt)}</p>
    {revised}
  </details>
</article>"""


def render(records: list[Record], title: str = "Terra Virtualis") -> str:
    """Newest first. Pure function: records in, one HTML document out."""
    recs = sorted(records, key=lambda r: r.timestamp, reverse=True)
    styles = sorted({r.style for r in recs})
    options = "".join(f'<option value="{escape(s)}">{escape(s)}</option>' for s in styles)
    cards = "".join(_card(r) for r in recs)
    return f"""<!doctype html>
<html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width, initial-scale=1">
<title>{escape(title)}</title><style>{CSS}</style></head>
<body>
<header><h1>{escape(title)}</h1><span class=count>{len(recs)} images</span>
<select id=style aria-label="Filter by style"><option value="">all styles</option>{options}</select></header>
<main>{cards}</main>
<footer>A lensless camera that imagines the view from where it stands. After Bjørn Karmann's Paragraphica.</footer>
<script>{JS}</script>
</body></html>
"""
