from paragraphica.gallery import render
from paragraphica.store import Record


def rec(**kw):
    base = {
        "timestamp": "2026-09-11T17:52:03+02:00",
        "location": "",
        "address": "Stationsplein, Amsterdam, Netherlands",
        "lat": 52.378,
        "lon": 4.9,
        "style": "film noir",
        "context": "landmark",
        "position": "eye level",
        "quality": "medium",
        "time_of_day": "afternoon",
        "weather": "",
        "description": "Trams & <crowds>.",
        "prompt": "P",
        "revised_prompt": None,
        "backend": "gemini",
        "text_model": "t",
        "image_model": "gemini-3.1-flash-image",
        "image": "a.jpg",
        "duration_s": 20.5,
    }
    base.update(kw)
    return Record(**base)


def test_render_empty():
    html = render([])
    assert "0 images" in html and "<article" not in html


def test_render_cards_newest_first_and_escaped():
    html = render([rec(image="old.jpg", timestamp="2026-09-10T10:00:00+02:00", style="lego"), rec(image="new.jpg")])
    assert html.index("new.jpg") < html.index("old.jpg")
    assert "Trams &amp; &lt;crowds&gt;." in html
    assert '<option value="film noir">' in html and '<option value="lego">' in html
    assert 'data-style="film noir"' in html
    assert "gemini-3.1-flash-image \\ 20.5s" in html


def test_image_base_prefixes_paths():
    assert 'src="a.jpg"' in render([rec()])
    assert 'src="/images/a.jpg"' in render([rec()], image_base="/images/")


def test_viewer_present_with_navigation():
    html = render([rec()])
    assert "id=view" in html and "data-act=prev" in html and "data-act=next" in html and "data-act=full" in html
    assert "ArrowLeft" in html and "Escape" in html and "location.hash" in html


def test_controls_only_when_asked():
    assert "<form id=gen" not in render([rec()])
    html = render([rec()], controls=True)
    assert "<form id=gen" in html and 'data-src="/styles"' in html and "fetch('/generate'" in html


def test_revised_prompt_shown_when_present():
    assert "model note" not in render([rec()])
    assert "model note</b> caption" in render([rec(revised_prompt="caption")])


def test_weather_shown_and_time_controls():
    html = render([rec(weather="The temperature is 10.06 degrees Celsius with few clouds.")], controls=True)
    assert "few clouds" in html
    assert 'name=time_of_day data-src="/times"' in html and "name=include_weather" in html


def test_cards_carry_coordinates_and_viewer_loads_leaflet_lazily():
    html = render([rec(lat=52.378, lon=4.9)])
    assert 'data-lat="52.378" data-lon="4.9"' in html
    assert "cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/" in html and "id=map" in html
    assert "<script src=" not in html  # loaded on first open, not at page load


def test_lab271_lockup_and_slash_pair_present():
    html = render([rec()])
    assert 'aria-label="LAB271"' in html and 'aria-label="Schuberg Philis"' in html
    assert 'class="slash tq"' in html and 'class="slash or"' in html
    assert "#1E80ED" in html  # cobalt: the lockup and nowhere else
    assert html.count("#1E80ED") == 1


def test_slideshow_controls_and_url_start():
    html = render([rec()])
    assert "data-act=play" in html and "=== 'p'" in html
    assert "URLSearchParams(location.search).get('play')" in html and "every = 8000" in html
    assert "filter(a => !a.hidden)" in html  # the look filter drives the deck
