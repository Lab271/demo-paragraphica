import pytest

from paragraphica import prompts
from paragraphica.context import Context

CTX = Context(address="Boeingavenue, Schiphol-Rijk, Netherlands", time_of_day="afternoon", weather="It rains.")


def test_describe_messages_includes_time_and_weather():
    msgs = prompts.describe_messages("main attraction", CTX)
    assert msgs[0] == {"role": "system", "content": prompts.SYSTEM_PROMPT}
    assert msgs[1]["content"] == (
        "Provide the single main attraction near Boeingavenue, Schiphol-Rijk, Netherlands in a few sentences. "
        "It is afternoon. It rains."
    )


def test_describe_messages_omits_empty_parts():
    msgs = prompts.describe_messages("local animals", Context(address="Utrecht, Netherlands"))
    assert msgs[1]["content"] == "Briefly describe the typical local fauna near Utrecht, Netherlands."


@pytest.mark.parametrize("style", prompts.STYLES)
@pytest.mark.parametrize("position", prompts.POSITIONS)
def test_build_prompt_every_style_and_position(style, position):
    prompt = prompts.build_prompt("Utrecht, Netherlands", "A canal.", style, position)
    assert prompt.startswith("Give a typical view of the Utrecht, Netherlands. A canal.")
    assert prompt.endswith(prompts.STYLES[style])
    assert "  " not in prompt


def test_build_prompt_custom_main_prompt():
    prompt = prompts.build_prompt("Utrecht", "x", "lego", main_prompt="Show me")
    assert prompt.startswith("Show me the Utrecht. x")
