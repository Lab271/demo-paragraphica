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
    assert "Prompt:      Give a typical view of the Utrecht, Netherlands." in result.output
    assert FakeBackend.image_calls == 0
    assert "Image:" not in result.output


def test_generate_writes_png(monkeypatch, tmp_path):
    _offline(monkeypatch)
    out = tmp_path / "x.png"
    result = runner.invoke(cli.app, ["generate", "--lat", "52.09", "--lon", "5.12", "--out", str(out)])
    assert result.exit_code == 0, result.output
    # suffix follows the format the model returned, not the one requested
    assert (tmp_path / "x.jpg").read_bytes() == b"JPG"
    assert "Image:" in result.output and "x.jpg" in result.output
    assert FakeBackend.image_calls == 1


def test_unknown_style_is_rejected():
    result = runner.invoke(cli.app, ["generate", "--lat", "1", "--lon", "1", "--style", "cubism"])
    assert result.exit_code != 0
    assert "unknown style" in result.output


def test_options_lists_vocabulary():
    result = runner.invoke(cli.app, ["options"])
    assert result.exit_code == 0
    assert "film noir" in result.output and "three highlights" in result.output


def test_models_lists_and_filters(monkeypatch):
    monkeypatch.setattr(
        cli.api,
        "list_gemini_models",
        lambda: [("gemini-3.1-flash-image", "generateContent"), ("veo-3", "generateVideos")],
    )
    result = runner.invoke(cli.app, ["models"])
    assert result.exit_code == 0
    assert "gemini-3.1-flash-image" in result.output and "veo-3" not in result.output
