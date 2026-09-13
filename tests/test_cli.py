from typer.testing import CliRunner

from paragraphica import cli
from paragraphica.backend import Generated
from paragraphica.context import Context

runner = CliRunner()
CTX = Context(address="Utrecht, Netherlands")


class FakeBackend:
    image_calls = 0

    def describe(self, messages):
        return "The Dom tower."

    def image(self, prompt, quality, size):
        FakeBackend.image_calls += 1
        return Generated(image=b"JPG", mime_type="image/jpeg")


def _offline(monkeypatch):
    """No network: fake backend, and the geo lookups replaced by a fixed context."""
    FakeBackend.image_calls = 0
    monkeypatch.setattr(cli.backends, "make_backend", lambda name: FakeBackend())
    monkeypatch.setattr(cli.core, "build_context", lambda *a, **k: CTX)


def test_dry_run_prints_prompt_without_image(monkeypatch):
    _offline(monkeypatch)
    result = runner.invoke(cli.app, ["generate", "--lat", "52.09", "--lon", "5.12", "--style", "lego", "--dry-run"])
    assert result.exit_code == 0, result.output
    assert "Description: The Dom tower." in result.output
    assert "Prompt:      The view from Utrecht, Netherlands." in result.output
    assert FakeBackend.image_calls == 0
    assert "Image:" not in result.output


def test_generate_stores_image_history_and_gallery(monkeypatch, tmp_path):
    _offline(monkeypatch)
    result = runner.invoke(cli.app, ["generate", "--lat", "52.09", "--lon", "5.12", "--out-dir", str(tmp_path)])
    assert result.exit_code == 0, result.output
    images = sorted(tmp_path.glob("*-utrecht-photo.jpg"))  # suffix follows the returned format
    assert len(images) == 1 and images[0].read_bytes() == b"JPG"
    assert "Image:" in result.output and images[0].name in result.output
    assert (tmp_path / "history.jsonl").read_text().count("\n") == 1
    assert "Utrecht, Netherlands" in (tmp_path / "index.html").read_text()
    assert FakeBackend.image_calls == 1


def test_history_and_gallery_commands(monkeypatch, tmp_path):
    _offline(monkeypatch)
    assert runner.invoke(cli.app, ["history", "--out-dir", str(tmp_path)]).output.startswith("no history")
    for style in ("lego", "polaroid"):
        runner.invoke(
            cli.app, ["generate", "--lat", "52.09", "--lon", "5.12", "--style", style, "--out-dir", str(tmp_path)]
        )
    out = runner.invoke(cli.app, ["history", "--out-dir", str(tmp_path), "--last", "1"]).output
    assert "polaroid" in out and "lego" not in out
    result = runner.invoke(cli.app, ["gallery", "--out-dir", str(tmp_path)])
    assert result.exit_code == 0 and "index.html" in result.output
    assert (tmp_path / "index.html").read_text().count("<article") == 2


def test_unknown_style_is_rejected():
    result = runner.invoke(cli.app, ["generate", "--lat", "1", "--lon", "1", "--style", "cubism"])
    assert result.exit_code != 0
    assert "unknown style" in result.output


def test_options_lists_vocabulary():
    result = runner.invoke(cli.app, ["options"])
    assert result.exit_code == 0
    assert "film noir" in result.output and "three highlights" in result.output and "aerial" in result.output


def test_models_lists_and_filters(monkeypatch):
    monkeypatch.setattr(
        cli.api,
        "list_gemini_models",
        lambda: [("gemini-3.1-flash-image", "generateContent"), ("veo-3", "generateVideos")],
    )
    result = runner.invoke(cli.app, ["models"])
    assert result.exit_code == 0
    assert "gemini-3.1-flash-image" in result.output and "veo-3" not in result.output


def test_variants_write_n_images(monkeypatch, tmp_path):
    _offline(monkeypatch)
    result = runner.invoke(
        cli.app, ["generate", "--lat", "52.09", "--lon", "5.12", "--variants", "3", "--out-dir", str(tmp_path)]
    )
    assert result.exit_code == 0, result.output
    assert len(list(tmp_path.glob("*.jpg"))) == 3 and FakeBackend.image_calls == 3
    assert (tmp_path / "history.jsonl").read_text().count("\n") == 3
    assert result.output.count("Image:") == 3


def test_caption_option_asks_for_lettering(monkeypatch):
    _offline(monkeypatch)
    result = runner.invoke(cli.app, ["generate", "--lat", "52.09", "--lon", "5.12", "--caption", "--dry-run"])
    assert result.exit_code == 0, result.output
    assert 'The place name "Utrecht" lettered into the picture' in result.output


def test_gallery_play_opens_slideshow_url(monkeypatch, tmp_path):
    opened = []
    monkeypatch.setattr(cli.typer, "launch", lambda url: opened.append(url))
    assert runner.invoke(cli.app, ["gallery", "--out-dir", str(tmp_path), "--play"]).exit_code == 0
    assert opened == [(tmp_path / "index.html").resolve().as_uri() + "?play"]
