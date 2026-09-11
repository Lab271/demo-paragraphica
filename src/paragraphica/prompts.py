"""Prompt vocabulary and the one template that assembles the image prompt.
No network, no state: everything here is testable with plain strings.

Three axes, named for the camera's dials (#13):

  Look     — medium and era of the picture      (was "style")
  Framing  — where the camera stands            (was "position")
  Subject  — what the text model describes      (was "context")

Every fragment is one sentence of concrete visual cues, written for Gemini,
which follows long grounded prompts and needs no meta text ("Provide this
as…"). Dict order is dial order (#10). The old names STYLES / POSITIONS /
CONTEXTS stay as aliases and the request/record fields keep their old names,
so history written before the rename still loads and renders."""

from paragraphica.context import Context

SYSTEM_PROMPT = (
    "You are a location scout writing for a photographer. Describe only what can be seen "
    "from the given spot, in concrete visual terms: buildings, materials, light, people, "
    "movement. No history lessons, no adjectives without a noun to hang on."
)

# {address} is filled in; the description follows, then framing and look.
MAIN_PROMPT = "The view from {address}."

LOOKS = {
    "photo": "Photorealistic, shot on a full-frame camera with natural light and true colours.",
    "polaroid": (
        "Instant Polaroid print: square frame with the white border, faded colours, soft focus, "
        "light leaks and a warm vintage tint."
    ),
    "film noir": "Low-key black and white, hard shadows, wet streets reflecting a few lights, 1940s film noir.",
    "frank miller": (
        "Graphic novel ink in the manner of Frank Miller's Sin City: stark high-contrast black and white, heavy "
        "solid blacks, figures as white silhouettes, rain as white streaks, one object in blood red."
    ),
    "impressionist": "Oil on canvas in the manner of 1880s impressionism: visible brushstrokes, broken colour, soft edges.",
    "woodblock": "Japanese ukiyo-e woodblock print: flat colour areas, bold outlines, stylised clouds and water.",
    "blueprint": "Architectural blueprint: white line drawing on cyan paper, measurements, annotations, grid.",
    "isometric": "Clean 3D isometric illustration with characteristic landmarks, tilt-shift miniature feel.",
    "lego": "Built entirely from Lego bricks, minifigures for people, presented as a photographed set.",
    "coloring page": "Black line art on white for a colouring book: bold clean outlines, no shading, no colour.",
    "pixel": "16-bit pixel art, 320x240 feel, limited palette, dithering, video game screenshot.",
}

FRAMINGS = {
    "eye level": "",
    "wide": "Ultra-wide lens at eye level, the whole scene in one frame.",
    "low": "Camera close to the ground looking up, foreground exaggerated.",
    "aerial": "Seen from a drone about 60 metres up, looking down at an angle.",
    "street": "Candid street photography at 35 mm, mid-distance, people in motion.",
}

SUBJECTS = {
    "landmark": "Name and describe the single most recognisable sight visible from {}, in three sentences.",
    "people": "Describe the people typically on the street near {} right now: dress, activity, pace. Four sentences.",
    "nature": "Describe the plants, trees, water and animals one would see around {}. Three sentences.",
    "night life": "Describe {} after dark: lit windows, bars, traffic, the crowd. Three sentences.",
    "food": "Describe the food visible on the street near {}: stalls, terraces, what people eat and drink. Three sentences.",
    "three highlights": "Name three things worth seeing within walking distance of {} in one sentence, no addresses.",
}

# Compatibility aliases (code and history written before #13).
STYLES = LOOKS
POSITIONS = FRAMINGS
CONTEXTS = SUBJECTS

DEFAULT_LOOK = "photo"
DEFAULT_FRAMING = "eye level"
DEFAULT_SUBJECT = "landmark"


def describe_messages(subject: str, ctx: Context, system_prompt: str = SYSTEM_PROMPT) -> list[dict]:
    """Chat messages asking the text model to describe the scene."""
    parts = [SUBJECTS[subject].format(ctx.address)]
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
    look: str,
    framing: str = DEFAULT_FRAMING,
    main_prompt: str = MAIN_PROMPT,
) -> str:
    """The image prompt: opener, description, framing, look. Empty fragments are dropped."""
    opener = main_prompt.format(address=address) if "{address}" in main_prompt else f"{main_prompt} {address}."
    parts = [opener, description.strip(), FRAMINGS[framing], LOOKS[look]]
    return " ".join(p for p in parts if p)
