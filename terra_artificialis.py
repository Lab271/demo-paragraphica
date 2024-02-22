from paragraphica import ImageModel
import streamlit as st
import os
import pprint

from mapbox import Geocoder

mapbox_token = os.environ["PARA_MAPBOX_API"]

DEFAULT_LOCATION = "Schiphol-Rijk"
DEFAULT_LATLON = (52.274972, 4.750813) # Schuberg Philis

MAIN_PROMPT = "Give a typical view of "

SYSTEM_PROMPT = "You are an artist and you will give a utmost realistic description of the surroundings."

STYLE_PROMPTS = {
    'realistic': 'Use a realistic imaging style like in a photograph.',
    'film noir': 'Use a low key black and white film noir picture style.',
    'frank miller': 'Apply a sinister frank miller style like the movie "Sin City".',
    'impressionism': 'Use a 19th century impressionistic painting style.',
    'lego': 'Provide this as a fictional lego box set with typical characters to buy in the store.',
    'isometric': 'Show this as a 3D isometric graphic with characteristic landmarks.',
    'coloring page': 'Coloring page style, bold lines, black and white.',
    'pop-up': 'pop up HAPPY BIRTHDAY greeting card for a rugby fan.',
    # 'Dali': "Use a surrealistic Dali dream style like the 'The Persistence of Memory' painting with clocks and a rhinosoros."
}

CONTEXT_PROMPTS = {
    'Main attraction': "Provide the single main attraction near {} in a few sentences. ",
    "Local People": "Describe the local people without political correctness in 5 sentences. ",
    "Local Animals": "Briefly describe the typical local fauna near {}. ", 
    "Local Plants": "Provide a clear description in 5 sentences of the local flora near {}. ",
    "Three Highlights": "Mention only three interesting spots in the vicinity of {} in one sentence without mentioning the address with the template 'Near by you can see:'. ",
}

POSITION_PROMPTS = {
    'normal': '',
    'wide angle': 'Use wide angle. ',
    'selfie': 'Provide in a selfie style position. ',
    'holga': 'Minimalist, holga photo view. ',
    'low angle': 'Shoot from a low angle. ',
}

if __name__ == "__main__":
    model = ImageModel(styles=STYLE_PROMPTS, contexts=CONTEXT_PROMPTS, positions=POSITION_PROMPTS, system_prompt=SYSTEM_PROMPT)
    geocoder = Geocoder(access_token=mapbox_token)
    lat_display_value = DEFAULT_LATLON[0]
    lon_display_value = DEFAULT_LATLON[1]

    with st.sidebar:
        btn = st.button("Generate")
        location = st.text_input("Enter location (will become lat/lon)", value=DEFAULT_LOCATION)
        if location:
            response = geocoder.forward(location)
            if response.status_code == 200:
                coords = response.json()['features'][0]['center']
                lon_display_value = coords[0]
                lat_display_value = coords[1]

        image_style = st.selectbox("What style would you like to use?", STYLE_PROMPTS.keys())
        position = st.selectbox("What position would you like to use?", POSITION_PROMPTS.keys())
        image_context = st.selectbox("What context would you like to use?", CONTEXT_PROMPTS.keys())
        include_weather = st.checkbox("Include Weather", value=False)
        include_time = st.checkbox("Include local time", value=True)

        lat = st.number_input("Lat", value=lat_display_value, step=None, format="%0.6f")
        lon = st.number_input("Lon", value=lon_display_value, step=None, format="%0.6f")
        image_quality = st.selectbox("Select quality", ("hd", "standard"))
        gen_style = st.selectbox("Select generation style", ("vivid", "natural"))
        main_prompt = st.text_area("main prompt", value=MAIN_PROMPT, height=100)

    if btn:
        address = model.get_address(lat, lon)
        st.caption(address)
        # https://wiki.openstreetmap.org/wiki/Zoom_levels
        st.map({"latitude": [lat], "longitude": [lon]}, zoom=15)
        weather = model.describe_weather(lat, lon) if include_weather else ""
        time = model.get_localtime(lat, lon) if include_time else ""
        description = model.describe_location(address, image_context, time, weather)
        st.caption(pprint.pformat(description))
        st.divider()
        prompt = model.generate_prompt(main_prompt, address, description, position, style=image_style)
        st.caption(prompt)
        prompt, image = model.generate(prompt=prompt, image_quality=image_quality, gen_style=gen_style)
        st.image(image, caption=prompt)
