import pytest

from paragraphica import prompts
from paragraphica.context import Context

CTX = Context(address="Boeingavenue, Schiphol-Rijk, Netherlands", time_of_day="afternoon", weather="It rains.")


def test_describe_messages_includes_time_and_weather():
    msgs = prompts.describe_messages("landmark", CTX)
    assert msgs[0] == {"role": "system", "content": prompts.SYSTEM_PROMPT}
    assert msgs[1]["content"] == (
        "Name and describe the single most recognisable sight visible from Boeingavenue, Schiphol-Rijk, Netherlands, "
        "in three sentences. It is afternoon. It rains."
    )


def test_describe_messages_omits_empty_parts():
    msgs = prompts.describe_messages("nature", Context(address="Utrecht, Netherlands"))
    assert msgs[1]["content"].startswith("Describe the plants, trees, water and animals one would see around Utrecht")
    assert "It is" not in msgs[1]["content"]


@pytest.mark.parametrize("look", prompts.LOOKS)
@pytest.mark.parametrize("framing", prompts.FRAMINGS)
def test_build_prompt_every_look_and_framing(look, framing):
    prompt = prompts.build_prompt("Utrecht, Netherlands", "A canal.", look, framing)
    assert prompt.startswith("The view from Utrecht, Netherlands. A canal.")
    assert prompt.endswith(prompts.LOOKS[look] + " " + prompts.NO_TEXT)
    assert "  " not in prompt


def test_caption_letters_the_place_name_instead_of_forbidding_text():
    off = prompts.build_prompt("De Wallen, Amsterdam, Netherlands", "Canal.", "polaroid")
    on = prompts.build_prompt("De Wallen, Amsterdam, Netherlands", "Canal.", "polaroid", caption=True)
    assert off.endswith(prompts.NO_TEXT) and "De Wallen" not in off.split("Canal.")[1]
    assert on.endswith('The place name "De Wallen" lettered into the picture as a title, like a postcard.')
    assert prompts.NO_TEXT not in on


def test_fragments_are_one_concrete_sentence():
    for table in (prompts.LOOKS, prompts.FRAMINGS):
        for key, frag in table.items():
            assert not frag.lower().startswith(("use ", "provide", "show this", "apply")), key
            assert frag == "" or frag.endswith("."), key


def test_build_prompt_custom_main_prompt_with_and_without_placeholder():
    assert prompts.build_prompt("Utrecht", "x", "lego", main_prompt="Postcard of {address}.").startswith(
        "Postcard of Utrecht. x"
    )
    assert prompts.build_prompt("Utrecht", "x", "lego", main_prompt="Show me").startswith("Show me Utrecht. x")


def test_aliases_and_defaults():
    assert (
        prompts.STYLES is prompts.LOOKS
        and prompts.CONTEXTS is prompts.SUBJECTS
        and prompts.POSITIONS is prompts.FRAMINGS
    )
    assert prompts.DEFAULT_LOOK in prompts.LOOKS and prompts.DEFAULT_FRAMING in prompts.FRAMINGS
    assert prompts.FRAMINGS[prompts.DEFAULT_FRAMING] == ""


def test_era_reaches_scout_and_painter():
    msgs = prompts.describe_messages("landmark", CTX, era="1650")
    assert "as it looked in 1650" in msgs[1]["content"] and "Describe that time, not today" in msgs[1]["content"]
    assert "It is afternoon." in msgs[1]["content"]
    prompt = prompts.build_prompt(CTX.address, "Gables.", "photo", era="1650")
    assert prompt.index("Gables.") < prompt.index("Set in 1650") < prompt.index(prompts.LOOKS["photo"])
    assert "Set in" not in prompts.build_prompt(CTX.address, "Gables.", "photo")


def test_future_eras_ask_for_plausibility_and_every_era_has_two_lines():
    assert "will plausibly look" in prompts.ERAS["2200"][0]
    assert all(len(v) == 2 and v[0] and v[1] for v in prompts.ERAS.values())
    assert next(iter(prompts.ERAS)) == "1650" and "ice age" in prompts.ERAS
