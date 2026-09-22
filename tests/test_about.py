from paragraphica import __version__, about
from paragraphica import backend as backends


def test_about_data_covers_every_backend_and_model():
    d = about.about_data("openrouter")
    assert d["version"] == __version__ and d["maintainer"] == "Ilja Heitlager"
    assert {e["name"] for e in d["engines"]} == set(backends.BACKENDS)
    assert [e["name"] for e in d["engines"] if e["active"]] == ["openrouter"]
    slugs = {m["slug"] for p in d["providers"] for m in p["models"]}
    assert slugs == set(backends.IMAGE_MODELS.values())
    defaults = [m["slug"] for p in d["providers"] for m in p["models"] if m["default"]]
    assert defaults == [backends.DEFAULT_MODELS["openrouter"][1]]


def test_providers_come_from_the_slug_prefix():
    assert about.provider_of("black-forest-labs/flux.2-pro") == "Black Forest Labs"
    assert about.provider_of("some-new-vendor/model-1") == "Some New Vendor"
    assert about.provider_of("gemini-3.1-flash-image") == "Google"
    names = [p["name"] for p in about.about_data()["providers"]]
    assert names[0] == "OpenAI" and len(names) == len(set(names))


def test_page_lists_everything_in_house_style():
    html = about.render(about.about_data("gemini"))
    for label, slug in backends.IMAGE_MODELS.items():
        assert label in html and slug in html
    for name in backends.BACKENDS:
        assert name in html
    assert "Ilja Heitlager" in html and "MIT" in html and f"v{__version__}" in html
    assert 'aria-label="LAB271"' in html and 'href="/">' in html
    assert "gemini<span class=tag>active" in html and "openrouter<span class=tag>active" not in html


def test_text_version_for_the_terminal():
    out = about.text(about.about_data("openrouter"))
    assert "openrouter   (active)" in out and "flux.2 pro" in out and "(default)" in out
