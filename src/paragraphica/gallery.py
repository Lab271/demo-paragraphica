"""A single static HTML page over the history store. No server, no framework;
opens from file:// and later from the Pi's screen."""

from html import escape

from paragraphica.backend import MODEL_LABELS
from paragraphica.store import Record

REPO = "https://github.com/Lab271/demo-paragraphica"

CSS = """
/* Lab271 house style: the dark canvas of the Schuberg Philis brand, refracted (design system v1).
   Turquoise is the intent, orange is the truth: the one orange element on this surface is the
   slash pair in the header, so buttons stay turquoise. Cobalt appears only in the lockup.
   Mono leads all small type; the backslash is the bullet; every diagonal is skewX(14deg). */
:root { color-scheme: dark;
  --c-canvas:#020C17; --c-canvas-2:#061323; --c-panel:#082646; --c-border:#12263F; --c-text:#FFFFFF; --c-muted:#8AA0B8;
  --c-tq:#1EE8ED; --c-orange:#FF8D33; --c-ink:#020C17;
  --sans:'TT Interphases','Avenir Next','Inter',system-ui,sans-serif; --mono:'TT Interphases Mono',ui-monospace,Menlo,'Courier New',monospace;
  --angle-slash:14deg; --ease:cubic-bezier(.2,0,.2,1); }
* { box-sizing: border-box; }
body { margin:0; background:var(--c-canvas); color:var(--c-text); font:16px/1.5 var(--sans); -webkit-font-smoothing:antialiased; }
.mono, .when, .how, .count, summary, .lab-eyebrow, footer, #status, #view .pos, form#gen label { font-family:var(--mono); font-size:12.5px; letter-spacing:.06em; }
header { position:relative; overflow:hidden; display:flex; flex-wrap:wrap; gap:1rem 1.6rem; align-items:center; padding:1.1rem 1.5rem; border-bottom:1px solid var(--c-border); }
header .lockup { display:flex; align-items:center; gap:.9rem; flex:none; }
header .lockup svg { display:block; height:22px; width:auto; }
header .lockup svg + svg { height:20px; }
header h1 { margin:0; font-size:clamp(20px, 2.2vw, 26px); font-weight:900; letter-spacing:-.04em; line-height:1.09; }
header .count { color:var(--c-muted); }
header select { margin-left:auto; }
header a.nav { color:var(--c-tq); font-family:var(--mono); font-size:12.5px; letter-spacing:.06em; text-decoration:none; margin-right:4.5rem; }
header a.nav:hover { text-decoration:underline; }
header .slash { position:absolute; top:-12px; height:140%; border-radius:4px; transform:skewX(var(--angle-slash)); pointer-events:none; }
header .slash.tq { right:2.4rem; width:13px; background:var(--c-tq); }
header .slash.or { right:1.1rem; width:6px; background:var(--c-orange); border-radius:3px; }
select, input { background:var(--c-canvas-2); color:var(--c-text); border:1px solid var(--c-border); padding:.45rem .8rem; border-radius:10px 10px 10px 0; font:15px var(--sans); }
select:focus-visible, input:focus-visible, button:focus-visible { outline:2px solid var(--c-tq); outline-offset:2px; border-color:var(--c-tq); }
main { display:grid; gap:1.2rem; padding:1.5rem; grid-template-columns:repeat(auto-fill, minmax(320px, 1fr)); }
article { background:var(--c-canvas-2); border:1px solid var(--c-border); border-radius:12px 12px 12px 0; overflow:hidden; display:flex; flex-direction:column; }
article[hidden] { display:none; }
article img { width:100%; aspect-ratio:1/1; object-fit:cover; display:block; background:var(--c-ink); }
.meta { padding:.8rem 1.1rem 0; display:flex; gap:.6rem; flex-wrap:wrap; align-items:center; }
.style { display:inline-flex; align-items:center; height:26px; padding:0 12px; border-radius:999px 999px 999px 0; background:var(--c-panel); color:var(--c-tq); font-family:var(--mono); font-size:11px; letter-spacing:.08em; }
.when, .how { color:var(--c-muted); }
.who { display:inline-flex; align-items:center; height:26px; padding:0 12px; border-radius:999px 999px 999px 0; border:1px solid var(--c-tq); color:var(--c-tq); font-family:var(--mono); font-size:11px; letter-spacing:.08em; }
#qr { position:fixed; right:1.2rem; bottom:1.2rem; z-index:20; display:none; align-items:center; gap:.7rem; padding:.5rem .7rem .5rem .5rem; background:rgba(255,255,255,.96); color:var(--c-ink); border-radius:12px 12px 12px 0; font-family:var(--mono); font-size:11px; letter-spacing:.06em; line-height:1.3; }
#qr img { width:96px; height:96px; display:block; }
#view.full.playing ~ #qr { display:flex; }
header a.nav + a.nav { margin-left:-3rem; }
#qrbig { position:fixed; inset:0; z-index:30; display:none; align-items:center; justify-content:center; flex-direction:column; gap:1.2rem; background:rgba(2,12,23,.96); cursor:pointer; }
#qrbig.open { display:flex; }
#qrbig .card { background:#fff; padding:1.4rem; border-radius:16px 16px 16px 0; }
#qrbig img { width:min(70vh, 70vw); height:auto; display:block; }
#qrbig .url { color:var(--c-tq); font-family:var(--mono); font-size:14px; letter-spacing:.08em; }
#qrbig .hint { color:var(--c-muted); font-family:var(--mono); font-size:12.5px; letter-spacing:.06em; }
h2 { margin:.5rem 1.1rem .2rem; font-size:16px; font-weight:900; letter-spacing:-.03em; line-height:1.2; }
details { margin:0 1.1rem 1rem; }
summary { cursor:pointer; color:var(--c-muted); }
summary:hover { color:var(--c-text); }
details p { white-space:pre-wrap; margin:.5rem 0 0; font-size:14px; }
details .prompt { color:var(--c-muted); }
footer { color:var(--c-muted); padding:2rem 1.5rem; border-top:1px solid var(--c-border); }
article img { cursor:zoom-in; }
#view { position:fixed; inset:0; background:rgba(2,12,23,.96); display:none; flex-direction:column; z-index:10; }
#view.open { display:flex; }
#view .bar { display:flex; gap:.6rem; align-items:center; padding:.6rem 1rem; }
#view .bar .pos { color:var(--c-muted); }
#view .bar button { margin-left:auto; }
#view .bar button + button { margin-left:0; }
button, #view button { display:inline-flex; align-items:center; gap:8px; height:36px; padding:0 18px; border:1px solid var(--c-tq); border-radius:999px; background:transparent; color:var(--c-tq); font-family:var(--mono); font-size:12.5px; letter-spacing:.06em; cursor:pointer; transition:opacity 160ms var(--ease), background 160ms var(--ease); }
button:hover { background:var(--c-panel); }
button:active { transform:scale(.98); }
#view .stage { flex:1; display:grid; grid-template-columns:minmax(0,3fr) minmax(0,2fr); gap:.6rem; padding:0 3.5rem; min-height:0; position:relative; }
#view .stage .pic { display:flex; align-items:center; justify-content:center; min-height:0; }
#view .stage img { max-width:100%; max-height:100%; object-fit:contain; }
#view #map { min-height:0; border-radius:12px 12px 12px 0; background:var(--c-canvas-2); border:1px solid var(--c-border); display:flex; align-items:center; justify-content:center; color:var(--c-muted); font-family:var(--mono); font-size:12.5px; text-align:center; padding:0 1rem; }
#view #map.leaflet-container { padding:0; color:#333; }
@media (max-width: 800px) { #view .stage { grid-template-columns:1fr; grid-template-rows:2fr 1fr; padding:0 .5rem; } header a.nav { margin-right:3rem; } }
#view .nav { position:absolute; top:50%; transform:translateY(-50%); height:48px; width:48px; padding:0; justify-content:center; font-size:1.6rem; font-family:var(--sans); opacity:.75; }
#view .nav:hover { opacity:1; }
#view .prev { left:1rem; } #view .next { right:1rem; }
#view .info { padding:.8rem 1.5rem 1.2rem; max-height:38vh; overflow:auto; border-top:1px solid var(--c-border); }
#view .info h2 { margin:.3rem 0 .4rem; font-size:21px; }
#view .info p { margin:.4rem 0; white-space:pre-wrap; }
#view .info .prompt { color:var(--c-muted); font-size:14px; }
#view.full .bar, #view.full .info, #view.full #map { display:none; }
#view.full .stage { grid-template-columns:1fr; padding:0; }
#view.full .stage img { max-height:100vh; }
#view.playing .bar [data-act=play] { background:var(--c-panel); }
#view.playing .nav { display:none; }
form#gen { display:flex; flex-wrap:wrap; gap:.6rem; align-items:center; padding:1rem 1.5rem; background:var(--c-canvas-2); border-bottom:1px solid var(--c-border); }
form#gen label { color:var(--c-muted); display:flex; gap:.4rem; align-items:center; }
form#gen input[name=location] { flex:1 1 14rem; min-width:10rem; }
form#gen button { background:var(--c-tq); color:var(--c-ink); border:0; height:40px; padding:0 22px; }
form#gen button:hover { background:var(--c-tq); opacity:.82; }
form#gen button[disabled] { opacity:.45; cursor:progress; }
#status { color:var(--c-muted); min-width:12rem; }
#status.err { color:var(--c-text); }
"""

# Co-brand lockup (design system decision 02 and 03): Lab271 left, the cobalt slash of the
# Schuberg Philis logo divides. Inlined so the static page needs no asset files.
LOCKUP = """<div class=lockup><svg height="22" role="img" aria-label="LAB271" viewBox="0 0 249 75" fill="none" xmlns="http://www.w3.org/2000/svg">
<g clip-path="url(#clip0_15_240)">
<path d="M0 74.2V0H21.2V55.12H51.94V74.2H0ZM49.8531 74.2L75.8231 0H100.733L126.703 74.2H104.443L101.157 63.6H75.2931L72.1131 74.2H49.8531ZM82.0771 44.52H94.4791L88.2251 22.26L82.0771 44.52ZM128.831 74.2V0H166.461C182.361 0 190.311 7.95 190.311 20.67C190.311 28.09 185.541 34.132 180.771 36.57C186.071 39.22 191.371 44.52 191.371 53.53C191.371 65.19 184.481 74.2 167.521 74.2H128.831ZM150.031 56.18H163.811C168.051 56.18 170.171 54.06 170.171 50.88C170.171 47.7 168.051 45.58 163.811 45.58H150.031V56.18ZM150.031 28.62H162.751C166.991 28.62 169.111 26.5 169.111 23.32C169.111 20.14 166.991 18.02 162.751 18.02H150.031V28.62Z" fill="white"></path>
<path d="M200.24 28.6V22.52L208.88 14.84C210.48 13.368 211.76 12.28 211.76 10.68C211.76 9.40002 210.8 8.76002 209.52 8.76002C207.92 8.76002 207.28 9.72002 207.28 11H200.24C200.24 5.88002 203.12 2.68002 209.84 2.68002C215.92 2.68002 218.8 6.20002 218.8 10.36C218.8 13.56 217.2 15.992 214.448 18.424L209.52 22.52H218.48V28.6H200.24ZM220.83 28.6L229.662 9.08002H218.782V3.00002H236.702V9.08002L227.87 28.6H220.83ZM241.802 28.6V12.6H236.042V6.52002H240.202C241.162 6.52002 241.802 5.94402 241.802 4.92002V3.00002H248.522V28.6H241.802Z" fill="#4DE3E5"></path>
</g>
<defs>
<clipPath id="clip0_15_240">
<rect width="249" height="75"></rect>
</clipPath>
</defs>
</svg><svg height="20" role="img" aria-label="Schuberg Philis" id="a" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240.92 65.3"><path id="b" fill="#FFFFFF" d="M161.72,35.5c3.7,0,6,.3,6.9,.7s1.9,2.1,1.9,3.1c0,.4-.3,.6-.6,.6-1.7-.2-4.6-.6-7.8-.6-3.8,0-5.8,.5-6.7,1.2s-1.3,2.1-1.3,3.8c0,1.3,.2,2,.5,2.4,1,1.2,13,2.7,15,3.9,.9,.6,1.6,2.3,1.6,5.1,0,3.9-1,6.3-2.5,7.6-1.3,1.1-3.9,1.9-9.4,1.9-3.7,0-6.7-.4-7.6-.9-1-.6-1.8-2.2-1.8-3.3,0-.4,.4-.6,.7-.6,1.8,.3,5.6,.9,8.6,.9,3.9,0,5.5-.4,6.2-1,.8-.6,1.3-1.7,1.3-3.6,0-1.6-.3-2.4-.8-2.7-1.2-1.1-12.9-2.7-14.7-3.9-1-.7-1.5-2.7-1.5-5.1,0-3.7,1-6,2.5-7.2,1.7-1.4,4.7-2.3,9.5-2.3Zm-40.3,.4c1,0,1.4,.3,1.4,1.6v22.4c0,.9,.3,1.2,1.2,1.2h2.5c4.2,0,7.4-.2,9.5-.3,.4,0,.6,.2,.6,.6,0,.9-1.2,2.7-2,3.1-.7,.3-2.9,.4-7.6,.4h-2.1c-2.6,0-3.3,0-5.5-.1-.3,0-1-.2-1-1.2v-27.2c0-.3,.1-.6,.4-.6h2.6v.1Zm-41.8,0c1.2,0,1.5,.3,1.5,1.7v8.5c0,2,.2,2.2,1.8,2.2h11.4c1.5,0,1.8-.3,1.8-2v-8.8c0-1.3,.3-1.6,1.5-1.6h2.3c.5,0,.5,.2,.5,.6v27.7c0,.4-.2,.6-.5,.6h-2.3c-1.2,0-1.4-.3-1.4-1.5v-9.1c0-1.9-.3-2.1-1.9-2.1h-11.3c-1.7,0-1.9,.2-1.9,2.1v9c0,1.4-.3,1.6-1.5,1.6h-2.2c-.4,0-.5-.3-.5-.6v-27.7c0-.4,.2-.6,.5-.6h2.2Zm31.4,0c.4,0,.5,.3,.5,.6v27.1c0,.9-.4,1.2-1.2,1.2h-2.5c-.4,0-.5-.3-.5-.6v-27.1c0-.8,.3-1.2,1.1-1.2h2.6Zm33.1,0c.4,0,.5,.3,.5,.6v27.1c0,.9-.4,1.2-1.2,1.2h-2.5c-.4,0-.5-.3-.5-.6v-27.1c0-.8,.3-1.2,1.1-1.2h2.6Zm-74.3,1.2c1.3,.9,2.6,2.9,2.6,7.2,0,3.7-1.3,6.9-2.9,8-1.3,1-3.6,1.4-7.3,1.4h-5.9c-.6,0-.9,.2-.9,1.1v9.2c0,.7-.2,.9-.9,.9h-2.9c-.4,0-.5-.2-.5-.6v-27.6c0-.5,.3-.6,.6-.6,2.8-.1,6.1-.2,9.5-.2,5.5-.1,7.3,.3,8.6,1.2Zm-8.6,2.3h-1.1c-1.6,0-3,0-3.9,.1-.5,0-.8,.2-.8,.8v8.8c0,.7,.2,.9,.9,.9h5.4c2.5,0,3.5-.1,4.3-.5,1.1-.6,2.1-2.1,2.1-5,0-2.5-.6-3.8-1.5-4.4-.8-.4-2-.7-5.4-.7ZM108.72,.5c1.9,0,2.4,.2,2.4,2.4v15.6c0,3.3,.3,4.8,1.2,5.8,.9,.9,2.9,1.7,6.1,1.7s5.2-.6,6.2-1.5c.9-.9,1.5-2.4,1.5-5.9V2.8c0-2.1,.6-2.3,2.4-2.3h1.4c.4,0,.6,.2,.6,.6V18.7c0,4.9-.7,7.1-2.4,8.7-1.4,1.3-4.6,2.6-9.7,2.6s-8.3-1.2-9.8-2.8c-1.4-1.6-1.9-3.6-1.9-8V1.1c0-.4,.2-.6,.5-.6h1.5ZM35.12,.1c3.7,0,6,.3,6.9,.7,.9,.4,1.9,2.1,1.9,3.1,0,.4-.3,.6-.6,.6-1.8-.1-4.7-.5-7.9-.5-3.8,0-5.8,.5-6.7,1.2-.9,.7-1.3,2.1-1.3,3.8,0,1.3,.2,2,.5,2.4,1,1.2,13,2.7,15,3.9,.9,.6,1.6,2.3,1.6,5.1,0,3.9-1,6.3-2.5,7.6-1.3,1.1-3.9,1.9-9.4,1.9-3.6,0-6.6-.4-7.6-.9-1-.6-1.8-2.2-1.8-3.3,0-.4,.4-.6,.7-.6,1.8,.3,5.6,.9,8.6,.9,3.9,0,5.5-.4,6.2-1,.8-.6,1.3-1.7,1.3-3.6,0-1.6-.3-2.4-.8-2.7-.6-.5-3.9-1.2-7.3-1.9l-.7-.2c-3-.6-5.8-1.3-6.7-1.8-1-.8-1.5-2.8-1.5-5.2,0-3.7,1-6,2.5-7.2C27.22,1,30.22,.1,35.12,.1Zm28.2,.1c3.7,0,6.1,.2,7.1,.8,1.1,.6,1.8,2.1,1.8,3,0,.3-.2,.6-.6,.6-1.7-.2-4.2-.6-7.8-.6-4.3,0-6.4,.6-7.6,1.8-1.5,1.3-2.7,4.3-2.7,9.3s.9,8.1,2.5,9.3c1.3,1,3.7,1.6,7.7,1.6,3.4,0,6.6-.5,8.1-.6,.3,0,.6,.1,.5,.5-.1,1-.9,2.5-1.9,3.1-.9,.5-3.5,1-8.1,1-5,0-8.1-1-9.7-2.5-1.9-1.6-3.6-5.1-3.6-11.9s1.9-10.8,4.2-12.6c1.8-1.7,4.6-2.8,10.1-2.8Zm84.1,.3c5.8,0,7.8,.5,9,1.3,1.2,.9,2.2,2.7,2.2,5.6,0,2.6-.7,4.2-1.3,5.3-.3,.6-.6,.9-.6,1.3,0,.3,.2,.7,.7,1.2,1,1.1,2.2,3,2.2,6,0,3.9-1.5,6.1-3.1,7.1-1.3,.9-3.6,1.4-9,1.4-3.8,0-7-.1-9.5-.2-.3,0-1-.2-1-1.2V1.5c0-.7,.5-.8,.9-.8,2.6-.1,5.9-.2,9.5-.2Zm91.1,.4c1,.5,1.9,2.2,1.9,3.1,0,.4-.3,.6-.6,.6-1.8-.3-5-.7-8.2-.7-4.3,0-6.8,.7-8.1,1.8-1.4,1.3-2.8,4.3-2.8,9.2s.9,8,2.5,9.3c1.2,1,3.4,1.7,6.5,1.7,2.5,0,4.4-.3,5.6-.6,.8-.2,1.1-.5,1.1-1.5v-5.7c0-.8-.3-1-1.1-1h-5.4c-.4,0-.6-.1-.6-.6,0-.7,.9-2.4,1.6-2.8,.4-.3,.9-.3,1.8-.3h6.6c1,0,1.6,.2,1.6,1.5v11.6c0,1-.4,1.6-1.6,1.9-2,.5-5.3,1.1-9.3,1.1-5.6,0-8.3-1.1-10-2.6-1.8-1.6-3.4-5-3.4-11.7,0-7.3,2.2-10.9,4.1-12.5C222.52,1.2,225.72,0,231.32,0c3.8,0,6.2,.3,7.2,.9Zm-55.4-.2c.8,.2,1.8,2.1,1.8,3.1,0,.3-.3,.6-.6,.6-2.2-.1-5.6-.2-8.9-.2h-.8c-1.8,0-3.4,0-4.5,.1-.9,0-1.1,.3-1.1,1.2v6.6c0,.7,.3,.8,.9,.8h13.1c.4,0,.6,.2,.6,.6,0,.6-.8,2.3-1.5,2.8-.5,.3-1,.3-2,.3h-10.3c-.6,0-.9,.2-.9,1v6.9c0,.9,.3,1.2,1.2,1.2h4.8c4.5,0,7.6-.1,9.9-.3,.3,0,.6,.1,.6,.5,0,.9-1.2,2.8-2.1,3.1-.8,.3-2.9,.4-7.6,.4h-1.7c-3.5,0-6.4,0-8.6-.1-.3,0-1-.2-1-1.2V1.5c0-.7,.6-.9,.9-.9,2.7-.1,5.4-.2,9.1-.2h1.4c3.8,0,6.6,0,7.3,.3Zm-103.5-.2c1.2,0,1.5,.3,1.5,1.7V10.7c0,2.1,.3,2.2,1.9,2.2h11.2c1.5,0,1.8-.3,1.8-2V2.1c0-1.3,.3-1.6,1.5-1.6h2.3c.5,0,.5,.2,.5,.6V28.8c0,.4-.2,.6-.5,.6h-2.3c-1.2,0-1.4-.3-1.4-1.5v-9.1c0-1.9-.3-2.1-1.9-2.1h-11.2c-1.6,0-1.9,.2-1.9,2v9.2c0,1.4-.3,1.6-1.5,1.6h-2.2c-.4,0-.5-.3-.5-.6V1.1c0-.4,.2-.6,.5-.6h2.2Zm120.8-.1c5.7,0,7.7,.4,9.1,1.4,1.4,1,2.4,2.9,2.4,6.1,0,3.4-.9,5.7-2.3,7.5-.6,.7-.8,1.1-.8,1.7s.2,1.4,.8,3l3.3,8.7c.2,.4,0,.9-.5,.9h-1c-2.1,0-3-.6-3.8-2.8l-2.2-6c-.8-2.1-1.6-2.6-3.7-2.6h-5.9c-.7,0-.9,.2-.9,1v9.5c0,.7-.2,.9-.9,.9h-3c-.4,0-.5-.2-.5-.6V1.2c0-.4,.3-.6,.6-.6,2.5-.1,6.4-.2,9.3-.2Zm-50.8,16h-7.2c-.8,0-1.1,.3-1.1,1.2v7.1c0,.9,.3,1.1,1.2,1.1,1.1,0,2.9,.1,5,.1,2.9,0,5-.2,5.9-.8,.9-.7,1.6-1.9,1.6-4.1s-.9-3.7-1.9-4.2c-.6-.3-1.3-.3-3.5-.4Zm50.9-12.4c-1.9,0-3.9,0-5,.1-.5,0-.8,.2-.8,.9V13.4c0,.8,.2,1,.9,1h6.5c1.7,0,2.4-.1,3-.3,.9-.3,2.3-2.4,2.3-5.4,0-1.9-.5-3.1-1.3-3.8-.6-.6-2.4-.9-5.6-.9Zm-53.5,.1c-1.7,0-3.4,0-4.6,.2-.9,0-1.1,.3-1.1,1.2v6.4c0,.8,.3,.9,1,.9h6.8c1.7,0,2.7-.1,3.3-.4,.8-.5,1.8-1.6,1.8-4,0-2.1-.6-3-1.4-3.5-.9-.5-2.4-.8-5.8-.8Z"></path><path id="c" fill="#1E80ED" d="M.02,.7C-.08,.2,.22,0,.62,0H4.72c1.7,0,2.6,.5,3.3,2.6l21.3,62c.1,.4,0,.7-.4,.7h-4.2c-1.5,0-2.6-.5-3.3-2.6L.02,.7"></path></svg></div>"""

JS = """
const sel = document.getElementById('style');
sel.addEventListener('change', () => {
  for (const a of document.querySelectorAll('article'))
    a.hidden = sel.value !== '' && a.dataset.style !== sel.value;
});
"""

VIEWER = """
<div id=view role=dialog aria-modal=true aria-label="Image detail">
  <div class=bar><span class=pos></span><button data-act=play title="Slideshow (P)">play</button><button data-act=full title="Only the picture (F)">full</button><button data-act=close title="Close (Esc)">close</button></div>
  <div class=stage><button class="nav prev" data-act=prev title="Previous (←)">‹</button><div class=pic><img alt=""></div><div id=map></div><button class="nav next" data-act=next title="Next (→)">›</button></div>
  <div class=info><div class=meta></div><h2></h2><p class=desc></p><p class=prompt></p><p class=note></p></div>
</div>
"""

VIEWER_JS = """
const view = document.getElementById('view');
const cards = () => [...document.querySelectorAll('article')].filter(a => !a.hidden);
let cur = -1;
function show(i) {
  const list = cards(); if (!list.length) return;
  cur = (i + list.length) % list.length;
  const a = list[cur];
  view.querySelector('.stage img').src = a.querySelector('img').src;
  view.querySelector('.stage img').alt = a.querySelector('img').alt;
  view.querySelector('.meta').innerHTML = a.querySelector('.meta').innerHTML;
  view.querySelector('h2').textContent = a.querySelector('h2').textContent;
  const ps = a.querySelectorAll('details p');
  view.querySelector('.desc').textContent = ps[0] ? ps[0].textContent : '';
  view.querySelector('.prompt').textContent = ps[1] ? ps[1].textContent : '';
  view.querySelector('.note').textContent = ps[2] ? ps[2].textContent : '';
  view.querySelector('.pos').textContent = `${cur + 1} / ${list.length}`;
  view.classList.add('open'); document.body.style.overflow = 'hidden';
  showMap(parseFloat(a.dataset.lat), parseFloat(a.dataset.lon), a.querySelector('h2').textContent);
  history.replaceState(null, '', '#' + (cur + 1));
}
const LEAFLET = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/';
let leaflet = null, map = null, marker = null;
function loadLeaflet() {
  if (leaflet) return leaflet;
  leaflet = new Promise((ok, fail) => {
    const css = document.createElement('link'); css.rel = 'stylesheet'; css.href = LEAFLET + 'leaflet.min.css'; document.head.append(css);
    const js = document.createElement('script'); js.src = LEAFLET + 'leaflet.min.js'; js.onload = ok; js.onerror = fail; document.head.append(js);
  });
  return leaflet;
}
function showMap(lat, lon, label) {
  const el = document.getElementById('map');
  if (isNaN(lat) || isNaN(lon)) { el.textContent = 'no location'; return; }
  loadLeaflet().then(() => {
    if (!map) {
      el.textContent = '';
      map = L.map(el, { zoomControl: true, attributionControl: true });
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '&copy; OpenStreetMap' }).addTo(map);
      marker = L.marker([lat, lon]).addTo(map);
    }
    marker.setLatLng([lat, lon]).bindPopup(label);
    map.setView([lat, lon], 15);
    setTimeout(() => map.invalidateSize(), 50);
  }).catch(() => { el.textContent = `${lat.toFixed(5)}, ${lon.toFixed(5)} (map unavailable offline)`; });
}
// Slideshow (#36): full-screen, newest first, one picture every `every` ms; any interaction pauses.
let timer = null, every = 8000;
function play(on) {
  clearInterval(timer); timer = null;
  view.classList.toggle('playing', on);
  view.querySelector('[data-act=play]').textContent = on ? 'pause' : 'play';
  if (!on) return;
  if (!view.classList.contains('open')) show(0);
  view.classList.add('full');
  timer = setInterval(() => show(cur + 1), every);
}
function close() { play(false); view.classList.remove('open', 'full'); document.body.style.overflow = ''; history.replaceState(null, '', location.pathname); }
document.querySelectorAll('article a').forEach(a => a.addEventListener('click', ev => { ev.preventDefault(); show(cards().indexOf(a.closest('article'))); }));
view.addEventListener('click', ev => {
  const act = ev.target.dataset.act;
  if (act === 'play') { play(!timer); return; }
  if (timer) play(false);
  if (act === 'close') close();
  else if (act === 'prev') show(cur - 1);
  else if (act === 'next') show(cur + 1);
  else if (act === 'full') { view.classList.toggle('full'); if (map) setTimeout(() => map.invalidateSize(), 50); }
  else if (ev.target.tagName === 'IMG' && view.classList.contains('full')) view.classList.remove('full');
});
document.addEventListener('keydown', ev => {
  if (ev.key.toLowerCase() === 'p') { play(!timer); return; }
  if (!view.classList.contains('open')) return;
  if (timer) play(false);
  if (ev.key === 'Escape') close();
  else if (ev.key === 'ArrowLeft') show(cur - 1);
  else if (ev.key === 'ArrowRight') show(cur + 1);
  else if (ev.key.toLowerCase() === 'f') { view.classList.toggle('full'); if (map) setTimeout(() => map.invalidateSize(), 50); }
});
const hash = parseInt(location.hash.slice(1), 10);
if (hash > 0) show(hash - 1);
const q = new URLSearchParams(location.search).get('play');  // ?play or ?play=12 (seconds)
if (q !== null) { every = (parseInt(q, 10) || 8) * 1000; play(true); }
"""

CONTROLS = """
<form id=gen>
  <input name=location placeholder="Location, e.g. Amsterdam" autocomplete=off required>
  <select name=style data-src="/styles" title="Look"></select>
  <select name=context data-src="/contexts" title="Subject"></select>
  <select name=position data-src="/positions" title="Framing"></select>
  <select name=quality><option>low</option><option selected>medium</option><option>high</option></select>
  <select name=image_model data-src="/models" data-first="default model" title="Image model"></select>
  <select name=time_of_day data-src="/times" data-first="now (local time)"></select>
  <select name=era data-src="/eras" data-first="today" title="Era"></select>
  <label><input type=checkbox name=include_weather> weather</label>
  <label><input type=checkbox name=caption> caption</label>
  <button type=submit>generate</button>
  <span id=status></span>
</form>
"""

QR = """
<div id=qr><img src="/qr.svg" alt="QR code to /shoot"><span>scan \\ pick a spot<br>\\ shoot \\ it lands here</span></div>
<div id=qrbig role=dialog aria-label="Scan to shoot from your phone"><div class=card><img src="/qr.svg" alt="QR code to /shoot"></div><span class=url></span><span class=hint>scan with your phone \\ pick a spot \\ shoot \\ it lands here \\ tap anywhere to close</span></div>
"""

# The wall notices new pictures (#48): poll the image count, and when it grows fetch the
# page and prepend the new cards, so the card template stays in one place (server side).
WALL_JS = """
let known = parseInt(document.querySelector('header .count').textContent, 10) || 0;
function bindCards(scope) {
  scope.querySelectorAll('article a').forEach(a => a.addEventListener('click', ev => { ev.preventDefault(); show(cards().indexOf(a.closest('article'))); }));
}
async function refresh() {
  try {
    const h = await (await fetch('/healthz', {cache: 'no-store'})).json();
    if (h.images <= known) return;
    const html = await (await fetch('/', {cache: 'no-store'})).text();
    const doc = new DOMParser().parseFromString(html, 'text/html');
    const fresh = [...doc.querySelectorAll('main article')].slice(0, h.images - known).reverse();
    const main = document.querySelector('main');
    for (const a of fresh) { const node = document.importNode(a, true); main.prepend(node); bindCards(node); }
    known = h.images;
    document.querySelector('header .count').textContent = `${known} images`;
    if (timer) show(0);
  } catch (e) { /* offline or restarting: try again next tick */ }
}
setInterval(refresh, 10000);
// The shoot button (top right) shows the QR big enough to scan from across the room.
const qrbig = document.getElementById('qrbig');
qrbig.querySelector('.url').textContent = location.origin + '/shoot';
document.getElementById('qrbtn').addEventListener('click', ev => { ev.preventDefault(); qrbig.classList.add('open'); });
qrbig.addEventListener('click', () => qrbig.classList.remove('open'));
document.addEventListener('keydown', ev => { if (ev.key === 'Escape') qrbig.classList.remove('open'); });
"""

CONTROLS_JS = """
const form = document.getElementById('gen');
const status = document.getElementById('status');
const btn = form.querySelector('button');
for (const sel of form.querySelectorAll('select[data-src]')) {
  fetch(sel.dataset.src).then(r => r.json()).then(opts => {
    if (sel.dataset.first) { const o = document.createElement('option'); o.value = ''; o.textContent = sel.dataset.first; sel.append(o); }
    const keys = Array.isArray(opts) ? opts : Object.keys(opts);
    for (const k of keys) { const o = document.createElement('option'); o.textContent = k; sel.append(o); }
    if (!keys.length) sel.hidden = true;  // e.g. /models when the backend has no model dial
  });
}
let ticker;
form.addEventListener('submit', async ev => {
  ev.preventDefault();
  const body = Object.fromEntries(new FormData(form));
  body.include_weather = form.include_weather.checked;
  body.caption = form.caption.checked;
  if (!body.time_of_day) delete body.time_of_day;
  if (!body.image_model) delete body.image_model;
  if (!body.era) delete body.era;
  btn.disabled = true; status.className = ''; const t0 = Date.now();
  ticker = setInterval(() => { status.textContent = `imagining ${body.location}… ${Math.round((Date.now()-t0)/1000)}s`; }, 250);
  try {
    const r = await fetch('/generate', {method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify(body)});
    const data = await r.json().catch(() => ({}));  // a crash page is HTML, not JSON
    if (!r.ok) throw new Error(data.detail || `${r.status} ${r.statusText}`);
    location.reload();
  } catch (e) {
    clearInterval(ticker); btn.disabled = false;
    status.className = 'err'; status.textContent = e.message + ' — try again';
  }
});
"""


def _card(r: Record, image_base: str) -> str:
    when = r.timestamp.replace("T", " ")[:16]
    how = " \\ ".join(
        x
        for x in (
            r.position if r.position not in ("normal", "eye level") else "",
            r.context,
            r.era,
            r.time_of_day,
            r.weather,
            "captioned" if r.caption else "",
            MODEL_LABELS.get(r.image_model, ""),
        )
        if x
    )
    cost = f" \\ ${r.cost:.3f}" if r.cost is not None else ""
    who = f"<span class=who>{escape(r.nickname)}</span>" if r.nickname else ""
    revised = f"<p class=prompt><b>model note</b> {escape(r.revised_prompt)}</p>" if r.revised_prompt else ""
    src = escape(image_base + r.image)
    return f"""
<article data-style="{escape(r.style)}" data-lat="{r.lat}" data-lon="{r.lon}">
  <a href="{src}"><img src="{src}" alt="{escape(r.address)} in {escape(r.style)} style" loading="lazy"></a>
  <div class=meta><span class=style>{escape(r.style)}</span><span class=when>{escape(when)}</span>{who}<span class=how>{escape(how)}</span></div>
  <h2>{escape(r.address)}</h2>
  <details>
    <summary>description \\ prompt \\ {escape(r.image_model)} \\ {r.duration_s:g}s{cost}</summary>
    <p>{escape(r.description)}</p>
    <p class=prompt><b>prompt</b> {escape(r.prompt)}</p>
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
    # The served page has /about; the static file points at the README instead (#42).
    about = (
        '<a class=nav href="/shoot" id=qrbtn title="Scan to shoot from your phone">\\ shoot</a><a class=nav href="/about">\\ about</a>'
        if controls
        else f'<a class=nav href="{REPO}">\\ about</a>'
    )
    return f"""<!doctype html>
<html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width, initial-scale=1">
<title>{escape(title)}</title><style>{CSS}</style></head>
<body>
<header>{LOCKUP}<h1>{escape(title)}</h1><span class=count>{len(recs)} images</span>
<select id=style aria-label="Filter by look"><option value="">all looks</option>{options}</select>
{about}
<span class="slash tq"></span><span class="slash or"></span></header>
{CONTROLS if controls else ""}
<main>{cards}</main>
{VIEWER}
{QR if controls else ""}
<footer>terra virtualis \\ a lensless camera that imagines the view from where it stands \\ after bjørn karmann's paragraphica \\ LAB271 \\ schuberg philis</footer>
<script>{JS}{VIEWER_JS}{CONTROLS_JS + WALL_JS if controls else ""}</script>
</body></html>
"""
