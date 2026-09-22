from paragraphica import prompts
from paragraphica.backend import Generated
from paragraphica.context import Context
from paragraphica.core import Request, generate

CTX = Context(address="Utrecht, Netherlands", time_of_day="morning")


class FakeBackend:
    def __init__(self):
        self.image_calls = 0

    def describe(self, messages):
        return "The Dom tower."

    def image(self, prompt, quality, size, model=None):
        self.image_calls += 1
        return Generated(image=b"PNG", revised_prompt=f"revised: {prompt}")


def test_dry_run_spends_no_image_call():
    backend = FakeBackend()
    result = generate(Request(lat=52.09, lon=5.12, style="lego"), backend, dry_run=True, context=CTX)
    assert backend.image_calls == 0
    assert result.image is None
    assert result.description == "The Dom tower."
    assert result.prompt.startswith("The view from Utrecht, Netherlands. The Dom tower.")
    assert result.prompt.endswith(prompts.LOOKS["lego"] + " " + prompts.NO_TEXT)


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


def test_variants_describe_once_image_n_times():
    from paragraphica.core import generate_variants

    class Counting(FakeBackend):
        describes = 0

        def describe(self, messages):
            Counting.describes += 1
            return "The Dom tower."

    backend = Counting()
    results = generate_variants(Request(lat=1, lon=1), backend, 3, context=CTX)
    assert len(results) == 3 and backend.image_calls == 3 and Counting.describes == 1
    assert len({r.prompt for r in results}) == 1


def test_wander_moves_the_geocoded_point(monkeypatch):
    from paragraphica import core

    seen = []
    monkeypatch.setattr(
        core, "build_context", lambda lat, lon, t, w: seen.append((lat, lon)) or Context(address="x", lat=lat, lon=lon)
    )
    r = generate(Request(lat=52.378, lon=4.9, wander_m=1000, seed=1), FakeBackend(), dry_run=True)
    assert seen[0] != (52.378, 4.9) and (r.context.lat, r.context.lon) == seen[0]
    r2 = generate(Request(lat=52.378, lon=4.9, wander_m=1000, seed=1), FakeBackend(), dry_run=True)
    assert (r2.context.lat, r2.context.lon) == seen[0]  # seeded: same spot
