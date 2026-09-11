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
form#gen { display:flex; flex-wrap:wrap; gap:.6rem; align-items:center; padding:1rem 1.5rem; background:var(--card); border-bottom:1px solid #2a2a2a; }
form#gen input, form#gen select { background:var(--bg); color:var(--fg); border:1px solid #333; padding:.45rem .6rem; border-radius:6px; font:inherit; }
form#gen input[name=location] { flex:1 1 14rem; min-width:10rem; }
form#gen button { background:var(--accent); color:#111; font-weight:600; border:0; padding:.5rem 1rem; border-radius:6px; cursor:pointer; font:inherit; }
form#gen button[disabled] { opacity:.5; cursor:progress; }
#status { color:var(--muted); font-size:.9rem; min-width:12rem; }
#status.err { color:#f28b82; }
"""

JS = """
const sel = document.getElementById('style');
sel.addEventListener('change', () => {
  for (const a of document.querySelectorAll('article'))
    a.hidden = sel.value !== '' && a.dataset.style !== sel.value;
});
"""

CONTROLS = """
<form id=gen>
  <input name=location placeholder="Location, e.g. Amsterdam" autocomplete=off required>
  <select name=style data-src="/styles"></select>
  <select name=context data-src="/contexts"></select>
  <select name=position data-src="/positions"></select>
  <select name=quality><option>low</option><option selected>medium</option><option>high</option></select>
  <button type=submit>Generate</button>
  <span id=status></span>
</form>
"""

CONTROLS_JS = """
const form = document.getElementById('gen');
const status = document.getElementById('status');
const btn = form.querySelector('button');
for (const sel of form.querySelectorAll('select[data-src]')) {
  fetch(sel.dataset.src).then(r => r.json()).then(opts => {
    for (const k of Object.keys(opts)) { const o = document.createElement('option'); o.textContent = k; sel.append(o); }
  });
}
let ticker;
form.addEventListener('submit', async ev => {
  ev.preventDefault();
  const body = Object.fromEntries(new FormData(form));
  btn.disabled = true; status.className = ''; const t0 = Date.now();
  ticker = setInterval(() => { status.textContent = `imagining ${body.location}… ${Math.round((Date.now()-t0)/1000)}s`; }, 250);
  try {
    const r = await fetch('/generate', {method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify(body)});
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || r.statusText);
    location.reload();
  } catch (e) {
    clearInterval(ticker); btn.disabled = false;
    status.className = 'err'; status.textContent = e.message + ' — try again';
  }
});
"""


def _card(r: Record, image_base: str) -> str:
    when = r.timestamp.replace("T", " ")[:16]
    how = " · ".join(x for x in (r.position if r.position != "normal" else "", r.context, r.time_of_day) if x)
    revised = f"<p class=prompt><b>Model note</b> {escape(r.revised_prompt)}</p>" if r.revised_prompt else ""
    src = escape(image_base + r.image)
    return f"""
<article data-style="{escape(r.style)}">
  <a href="{src}"><img src="{src}" alt="{escape(r.address)} in {escape(r.style)} style" loading="lazy"></a>
  <div class=meta><span class=style>{escape(r.style)}</span><span class=when>{escape(when)}</span><span class=how>{escape(how)}</span></div>
  <h2>{escape(r.address)}</h2>
  <details>
    <summary>description · prompt · {escape(r.image_model)} · {r.duration_s:g}s</summary>
    <p>{escape(r.description)}</p>
    <p class=prompt><b>Prompt</b> {escape(r.prompt)}</p>
    {revised}
  </details>
</article>"""


def render(records: list[Record], title: str = "Terra Virtualis", image_base: str = "", controls: bool = False) -> str:
    """Newest first. Pure function: records in, one HTML document out.

    `image_base` prefixes every image path: "" for output/index.html next to the
    files, "/images/" when the service serves the page at /. `controls` adds the
    generate form; only the served page has an API to talk to."""
    recs = sorted(records, key=lambda r: r.timestamp, reverse=True)
    styles = sorted({r.style for r in recs})
    options = "".join(f'<option value="{escape(s)}">{escape(s)}</option>' for s in styles)
    cards = "".join(_card(r, image_base) for r in recs)
    return f"""<!doctype html>
<html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width, initial-scale=1">
<title>{escape(title)}</title><style>{CSS}</style></head>
<body>
<header><h1>{escape(title)}</h1><span class=count>{len(recs)} images</span>
<select id=style aria-label="Filter by style"><option value="">all styles</option>{options}</select></header>
{CONTROLS if controls else ""}
<main>{cards}</main>
<footer>A lensless camera that imagines the view from where it stands. After Bjørn Karmann's Paragraphica.</footer>
<script>{JS}{CONTROLS_JS if controls else ""}</script>
</body></html>
"""
