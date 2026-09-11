from paragraphica.backend import Generated
from paragraphica.context import Context
from paragraphica.core import Request, generate

CTX = Context(address="Utrecht, Netherlands", time_of_day="morning")


class FakeBackend:
    def __init__(self):
        self.image_calls = 0

    def describe(self, messages):
        return "The Dom tower."

    def image(self, prompt, quality, size):
        self.image_calls += 1
        return Generated(image=b"PNG", revised_prompt=f"revised: {prompt}")


def test_dry_run_spends_no_image_call():
    backend = FakeBackend()
    result = generate(Request(lat=52.09, lon=5.12, style="lego"), backend, dry_run=True, context=CTX)
    assert backend.image_calls == 0
    assert result.image is None
    assert result.description == "The Dom tower."
    assert result.prompt.startswith("Give a typical view of the Utrecht, Netherlands. The Dom tower.")
    assert result.prompt.endswith("lego box set with typical characters to buy in the store.")


def test_full_run_returns_image_and_revised_prompt():
    backend = FakeBackend()
    result = generate(Request(lat=52.09, lon=5.12), backend, context=CTX)
    assert backend.image_calls == 1
    assert result.image == b"PNG"
    assert result.revised_prompt == f"revised: {result.prompt}"


def test_time_of_day_override_skips_clock(monkeypatch):
    from paragraphica import core

    calls = []
    monkeypatch.setattr(core, "build_context", lambda lat, lon, t, w: calls.append(t) or Context(address="Utrecht"))
    result = generate(Request(lat=1, lon=1, time_of_day="dark night"), FakeBackend(), dry_run=True)
    assert calls == [False]  # clock not consulted
    assert result.context.time_of_day == "dark night"
