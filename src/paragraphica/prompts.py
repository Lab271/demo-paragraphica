"""Prompt vocabulary and the one template that assembles the image prompt.
No network, no state: everything here is testable with plain strings.

Four axes, named for the camera's dials (#13, #47):

  Look     — medium and rendering of the picture (was "style")
  Framing  — where the camera stands            (was "position")
  Subject  — what the text model describes      (was "context")
  Era      — when: the same spot in another age; unset means today

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
    "elevation": (
        "Architectural elevation drawing: flat two-dimensional orthographic view straight from the side, no "
        "perspective, no depth, thin black outlines, flat pastel fills, white background, small figures for scale."
    ),
    "isometric": "Clean 3D isometric illustration with characteristic landmarks, tilt-shift miniature feel.",
    "lego": "Built entirely from Lego bricks, minifigures for people, presented as a photographed set.",
    "coloring page": "Black line art on white for a colouring book: bold clean outlines, no shading, no colour.",
    "pixel": "16-bit pixel art, 320x240 feel, limited palette, dithering, video game screenshot.",
    "dutch masters": (
        "Oil painting in the manner of the 17th-century Dutch masters: a single window light from the left, "
        "deep warm shadow, glazed surfaces, ochre and umber palette."
    ),
    "cyanotype": "Cyanotype photographic print: Prussian blue tones, white highlights, soft edges, paper texture.",
    "stained glass": "Stained glass window: leaded black outlines, saturated glass colours, light coming from behind.",
    "tin toy": "Lithographed tin toy diorama: glossy enamel, visible tabs and rivets, simplified shapes, 1950s.",
    "risograph": "Risograph poster print in two inks, fluorescent pink and teal, slight misregistration, paper grain.",
    "thermal": "False-colour thermal camera image: heat gradients from deep blue to white-hot, soft edges, no fine text.",
}

FRAMINGS = {
    "eye level": "",
    "wide": "Ultra-wide lens at eye level, the whole scene in one frame.",
    "low": "Camera close to the ground looking up, foreground exaggerated.",
    "aerial": "Seen from a drone about 60 metres up, looking down at an angle.",
    "street": "Candid street photography at 35 mm, mid-distance, people in motion.",
    "through a window": (
        "Seen from inside through a window: the frame and sill in the foreground, faint reflections on the glass, "
        "the scene outside beyond."
    ),
    "from a canal boat": (
        "Seen from a low boat on the water: the waterline in the foreground, a bridge arching overhead, "
        "quay walls and house fronts rising on both sides."
    ),
}

SUBJECTS = {
    "landmark": "Name and describe the single most recognisable sight visible from {}, in three sentences.",
    "people": "Describe the people typically on the street near {} right now: dress, activity, pace. Four sentences.",
    "nature": "Describe the plants, trees, water and animals one would see around {}. Three sentences.",
    "night life": "Describe {} after dark: lit windows, bars, traffic, the crowd. Three sentences.",
    "food": "Describe the food visible on the street near {}: stalls, terraces, what people eat and drink. Three sentences.",
    "three highlights": "Name three things worth seeing within walking distance of {} in one sentence, no addresses.",
}

# The age dial (#47). Each era has a line for the scout (what to describe) and a line
# for the painter (period cues the image model needs). Past eras ask "as it looked",
# future ones "as it will plausibly look", so the text model speculates instead of
# refusing. Dict order is dial order: past to future, then the odd one out.
ERAS = {
    "1650": (
        "as it looked in 1650, at the height of the Dutch Golden Age",
        (
            "Set in 1650: timber and brick gables, cobbles and mud, horse carts, sailing barges, "
            "people in dark wool, white collars and wide hats, candle and daylight only."
        ),
    ),
    "1780": (
        "as it looked in 1780",
        "Set in 1780: powdered wigs and tricorn hats, carriages, oil lamps, plaster facades, hand-painted signs.",
    ),
    "1900": (
        "as it looked in 1900, the belle époque",
        (
            "Set in 1900: horse trams and the first electric ones, gas lamps, top hats and long skirts, "
            "iron and glass, sepia-warm daylight."
        ),
    ),
    "1944": (
        "as it looked in the winter of 1944",
        (
            "Set in the winter of 1944: bare trees, few people in worn coats, bicycles without tyres, "
            "shuttered shops, grey light, no cars."
        ),
    ),
    "1969": (
        "as it looked in 1969",
        "Set in 1969: round-headlight cars, flared trousers and long hair, neon signs, Kodachrome colours.",
    ),
    "1985": (
        "as it looked in 1985",
        "Set in 1985: boxy hatchbacks, big glasses and shoulder pads, payphones, slightly faded print-film colours.",
    ),
    "2050": (
        "as it will plausibly look in 2050",
        (
            "Set in 2050: mature green facades, quiet electric vehicles, solar glass, "
            "the old buildings kept and the new ones wooden."
        ),
    ),
    "2200": (
        "as it will plausibly look in 2200",
        (
            "Set in 2200: the historic core preserved under a taller, greener city, water everywhere, "
            "airships or drones in the sky, unfamiliar but calm technology."
        ),
    ),
    "ice age": (
        "as the same spot looked during the last ice age, twenty thousand years ago",
        (
            "Set in the last ice age: tundra and ice under a huge sky, no buildings, mammoths or reindeer "
            "in the distance, low cold sun."
        ),
    ),
}

# Compatibility aliases (code and history written before #13).
STYLES = LOOKS
POSITIONS = FRAMINGS
CONTEXTS = SUBJECTS

# Text control (#25). Gemini letters dates and captions into graphic looks on its
# own; off by default, on when the camera should print a titled postcard.
NO_TEXT = "No text, lettering or captions in the picture."
CAPTION = 'The place name "{address}" lettered into the picture as a title, like a postcard.'

DEFAULT_LOOK = "photo"
DEFAULT_FRAMING = "eye level"
DEFAULT_SUBJECT = "landmark"


def describe_messages(
    subject: str, ctx: Context, system_prompt: str = SYSTEM_PROMPT, era: str | None = None
) -> list[dict]:
    """Chat messages asking the text model to describe the scene; with an era, the scene
    as it was or will be then (#47)."""
    place = f"{ctx.address}, {ERAS[era][0]}" if era else ctx.address
    parts = [SUBJECTS[subject].format(place)]
    if era:
        parts.append("Describe that time, not today: buildings, people, vehicles, materials, light.")
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
    caption: bool = False,
    era: str | None = None,
) -> str:
    """The image prompt: opener, description, era, framing, look, text control. Empty fragments are dropped."""
    opener = main_prompt.format(address=address) if "{address}" in main_prompt else f"{main_prompt} {address}."
    text = CAPTION.format(address=address.split(",")[0]) if caption else NO_TEXT
    parts = [opener, description.strip(), ERAS[era][1] if era else "", FRAMINGS[framing], LOOKS[look], text]
    return " ".join(p for p in parts if p)
