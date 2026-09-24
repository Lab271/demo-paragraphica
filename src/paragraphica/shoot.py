"""The phone page (#48): scan the QR on the wall, drop a pin where you would rather
be, pick the dials, press the shutter; the picture lands on the wall. Served at
/shoot; talks to /geocode, the vocabulary endpoints and POST /shoot."""

from paragraphica.gallery import CSS, LOCKUP

LEAFLET = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/"

SHOOT_CSS = """
html, body { height: 100%; }
body { display: flex; flex-direction: column; overflow: hidden; }
header { padding: .7rem 1rem; gap: .8rem; }
header h1 { font-size: 18px; }
header .lockup svg { height: 16px; } header .lockup svg + svg { height: 15px; }
header .slash.tq { right: 1.6rem; width: 9px; } header .slash.or { right: .7rem; width: 4px; }
#map { flex: 1; min-height: 40vh; background: var(--c-canvas-2); }
#map.leaflet-container { font-family: var(--sans); }
#where { position: absolute; top: .6rem; left: .6rem; right: .6rem; z-index: 500; display: flex; gap: .4rem; }
#where input { flex: 1; min-width: 0; box-shadow: 0 4px 18px rgba(0,0,0,.5); }
#where button { height: 40px; background: var(--c-canvas-2); }
#pin { position: absolute; left: 50%; top: 50%; z-index: 450; width: 28px; height: 40px; margin: -40px 0 0 -14px; pointer-events: none; }
#sheet { background: var(--c-canvas-2); border-top: 1px solid var(--c-border); padding: .8rem 1rem calc(.8rem + env(safe-area-inset-bottom)); display: grid; grid-template-columns: 1fr 1fr; gap: .5rem; }
#sheet .place { grid-column: 1 / -1; font-family: var(--mono); font-size: 12.5px; letter-spacing: .06em; color: var(--c-muted); min-height: 1.2em; }
#sheet > * { min-width: 0; }
#sheet select, #sheet input { width: 100%; max-width: 100%; font-size: 16px; }
.map-wrap { min-width: 0; }
#map .leaflet-control-attribution { background: rgba(2,12,23,.7); color: var(--c-muted); font-size: 9px; }
#map .leaflet-control-attribution a { color: var(--c-muted); }
#sheet select[hidden] { display: none; }
#sheet button.shutter { grid-column: 1 / -1; height: 56px; border-radius: 999px; background: var(--c-tq); color: var(--c-ink); border: 0; font-size: 15px; letter-spacing: .12em; justify-content: center; }
#sheet button.shutter[disabled] { opacity: .5; cursor: progress; }
#status { grid-column: 1 / -1; min-width: 0; }
#status.err { color: var(--c-orange); }
#done { position: fixed; inset: 0; background: var(--c-canvas); display: none; flex-direction: column; z-index: 900; }
#done.open { display: flex; }
#done img { flex: 1; min-height: 0; object-fit: contain; width: 100%; background: var(--c-ink); }
#done .info { padding: 1rem; display: grid; gap: .6rem; }
#done .info h2 { margin: 0; font-size: 18px; }
#done .info .how { color: var(--c-tq); }
#done .info button { justify-content: center; height: 48px; }
.map-wrap { position: relative; flex: 1; display: flex; }
"""

# The map pin: a turquoise teardrop with a square corner, the house shape.
PIN = """<svg id=pin viewBox="0 0 28 40" aria-hidden="true"><path d="M14 0C6.3 0 0 6.3 0 14c0 10 14 26 14 26s14-16 14-26C28 6.3 21.7 0 14 0z" fill="#1EE8ED"/><circle cx="14" cy="14" r="5" fill="#020C17"/></svg>"""


def render(has_models: bool = False, title: str = "Terra Virtualis") -> str:
    models = (
        '<select name=image_model data-src="/models" data-first="default model" title="Image model"></select>'
        if has_models
        else ""
    )
    return f"""<!doctype html>
<html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Shoot \\ {title}</title>
<link rel=stylesheet href="{LEAFLET}leaflet.min.css">
<style>{CSS}{SHOOT_CSS}</style></head>
<body>
<header>{LOCKUP}<h1>{title}</h1><span class="slash tq"></span><span class="slash or"></span></header>
<div class=map-wrap>
  <form id=where autocomplete=off><input name=q placeholder="Where would you rather be?" enterkeyhint=search><button type=submit>find</button></form>
  <div id=map></div>
  {PIN}
</div>
<form id=sheet>
  <div class=place>drag the map to put the pin where you want to stand</div>
  <select name=style data-src="/styles" title="Look"></select>
  <select name=context data-src="/contexts" title="Subject"></select>
  <select name=position data-src="/positions" title="Framing"></select>
  <select name=era data-src="/eras" data-first="today" title="Era"></select>
  {models}
  <input name=nickname placeholder="your name for the wall" maxlength=24>
  <button type=submit class=shutter>shoot</button>
  <span id=status></span>
</form>
<div id=done>
  <img alt="">
  <div class=info><h2></h2><span class="mono how">now on the wall</span><button type=button id=again>shoot another</button></div>
</div>
<script src="{LEAFLET}leaflet.min.js"></script>
<script>
const START = [52.3728, 4.8936];  // Amsterdam, a good place to start dragging from
const map = L.map('map', {{ zoomControl: false }}).setView(START, 12);
L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ maxZoom: 19, attribution: '&copy; OpenStreetMap' }}).addTo(map);
const place = document.querySelector('#sheet .place');
let named = '';  // the geocoded name, valid until the map moves
map.on('movestart', () => {{ named = ''; }});
map.on('moveend', () => {{ const c = map.getCenter(); place.textContent = named || `${{c.lat.toFixed(4)}}, ${{c.lng.toFixed(4)}}`; }});

const where = document.getElementById('where');
where.addEventListener('submit', async ev => {{
  ev.preventDefault();
  const q = where.q.value.trim(); if (!q) return;
  place.textContent = `looking for ${{q}}…`;
  const r = await fetch('/geocode?q=' + encodeURIComponent(q));
  if (!r.ok) {{ place.textContent = `no idea where ${{q}} is`; return; }}
  const d = await r.json();
  map.setView([d.lat, d.lon], 14);
  named = d.name; place.textContent = d.name;
  where.q.blur();
}});

const sheet = document.getElementById('sheet');
const status = document.getElementById('status');
const btn = sheet.querySelector('.shutter');
for (const sel of sheet.querySelectorAll('select[data-src]')) {{
  fetch(sel.dataset.src).then(r => r.json()).then(opts => {{
    if (sel.dataset.first) {{ const o = document.createElement('option'); o.value = ''; o.textContent = sel.dataset.first; sel.append(o); }}
    const keys = Array.isArray(opts) ? opts : Object.keys(opts);
    for (const k of keys) {{ const o = document.createElement('option'); o.textContent = k; sel.append(o); }}
    if (!keys.length) sel.hidden = true;
  }});
}}
try {{ sheet.nickname.value = localStorage.getItem('nickname') || ''; }} catch (e) {{}}

const done = document.getElementById('done');
document.getElementById('again').addEventListener('click', () => done.classList.remove('open'));
let ticker;
sheet.addEventListener('submit', async ev => {{
  ev.preventDefault();
  const c = map.getCenter();
  const body = Object.fromEntries(new FormData(sheet));
  body.lat = c.lat; body.lon = c.lng; body.location = named;
  for (const k of ['era', 'image_model']) if (!body[k]) delete body[k];
  try {{ localStorage.setItem('nickname', body.nickname || ''); }} catch (e) {{}}
  btn.disabled = true; status.className = ''; const t0 = Date.now();
  ticker = setInterval(() => {{ status.textContent = `imagining… ${{Math.round((Date.now()-t0)/1000)}}s`; }}, 250);
  try {{
    const r = await fetch('/shoot', {{method:'POST', headers:{{'content-type':'application/json'}}, body: JSON.stringify(body)}});
    const data = await r.json().catch(() => ({{}}));
    if (!r.ok) throw new Error(data.detail || `${{r.status}} ${{r.statusText}}`);
    done.querySelector('img').src = data.image_url;
    done.querySelector('h2').textContent = data.address;
    done.classList.add('open');
    status.textContent = '';
  }} catch (e) {{
    status.className = 'err'; status.textContent = e.message;
  }} finally {{ clearInterval(ticker); btn.disabled = false; }}
}});
</script>
</body></html>
"""
