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
        "context": "main attraction",
        "position": "normal",
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
    assert "gemini-3.1-flash-image · 20.5s" in html


def test_revised_prompt_shown_when_present():
    assert "Model note" not in render([rec()])
    assert "Model note</b> caption" in render([rec(revised_prompt="caption")])
