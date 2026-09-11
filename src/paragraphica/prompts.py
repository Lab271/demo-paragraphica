"""Prompt vocabulary and the one template that assembles the image prompt.
No network, no state: everything here is testable with plain strings."""

from paragraphica.context import Context

SYSTEM_PROMPT = "You are an artist and you will give a utmost realistic description of the surroundings."

MAIN_PROMPT = "Give a typical view of"

STYLES = {
    "realistic": "Use a cinematic realism image. Realistic with cinematic photography.",
    "film noir": "Use a low key black and white film noir picture style.",
    "frank miller": 'Apply a sinister frank miller style like the movie "Sin City".',
    "impressionism": "Use a 19th century impressionistic painting style.",
    "lego": "Provide this as a fictional lego box set with typical characters to buy in the store.",
    "isometric": "Show this as a 3D isometric graphic with characteristic landmarks.",
    "coloring page": "Coloring page style, bold lines, black and white.",
    "pop-up": "pop up HAPPY BIRTHDAY greeting card for a rugby fan.",
    "polaroid": (
        "Shot on an instant Polaroid camera: square frame with the white border, slightly faded colours, "
        "soft focus, light leaks and a warm vintage tint."
    ),
}

CONTEXTS = {
    "main attraction": "Provide the single main attraction near {} in a few sentences.",
    "local people": "Describe the local people near {} in 5 sentences.",
    "local animals": "Briefly describe the typical local fauna near {}.",
    "local plants": "Provide a clear description in 5 sentences of the local flora near {}.",
    "three highlights": (
        "Mention only three interesting spots in the vicinity of {} in one sentence "
        "without mentioning the address with the template 'Near by you can see:'."
    ),
}

POSITIONS = {
    "normal": "",
    "wide angle": "Use wide angle.",
    "selfie": "Provide in a selfie style position.",
    "holga": "Minimalist, holga photo view.",
    "low angle": "Shoot from a low angle.",
}


def describe_messages(context_key: str, ctx: Context, system_prompt: str = SYSTEM_PROMPT) -> list[dict]:
    """Chat messages asking the text model to describe the scene."""
    parts = [CONTEXTS[context_key].format(ctx.address)]
    if ctx.time_of_day:
        parts.append(f"It is {ctx.time_of_day}.")
    if ctx.weather:
        parts.append(ctx.weather)
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": " ".join(parts)},
    ]


def build_prompt(
    address: str,
    description: str,
    style: str,
    position: str = "normal",
    main_prompt: str = MAIN_PROMPT,
) -> str:
    """The image prompt. Empty fragments (e.g. position 'normal') are dropped."""
    parts = [f"{main_prompt} the {address}.", description.strip(), POSITIONS[position], STYLES[style]]
    return " ".join(p for p in parts if p)
