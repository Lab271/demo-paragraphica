from paragraphica import ImageModel
import streamlit as st
import os

from mapbox import Geocoder

mapbox_token = os.environ["PARA_MAPBOX_API"]

DEFAULT_LOCATION = "Schiphol-Rijk"

MAIN_PROMPT = "Give a typical view of "

SYSTEM_PROMPT = "You are an artist and you will give a utmost realistic description of the surroundings."

STYLE_PROMPTS = {
    'realistic': 'Use a realistic imaging style like a photograph.',
    'film noir': 'Use a darkish black and white film noir picture style.',
    'impressionism': 'Use a 19th century impressionistic painting style.',
    'cubistic': 'Apply cubistic painting style.',
    'lego': 'Provide this as a fictional lego box set with typical characters to buy in the store.',
    'isometric': 'Show this as a 3D isometric graphic with characteristic landmarks.',
    'coloring page': 'Coloring page style, bold lines, black and white.',
    'pop-up': 'pop up HAPPY BIRTHDAY greeting card for a rugby fan.',
    'Dali': "Use a surrealistic Dali dream style like the 'The Persistence of Memory' painting with clocks and a rhinosoros."
}

CONTEXT_PROMPTS = {
    'Main attraction': "Provide the single main attraction near {} in a few sentences. ",
    "Three Highlights": "Mention only three interesting spots in the vicinity of {} in one sentence without mentioning the address with the template 'Near by you can see:'. ",
    "Local Fauna": "Briefly describe the local fauna near {}. ", 
    "Local Flora": "Provide a clear description in 5 sentences of the local flora near {}. "
}

BASIC_LOCATION = (52.274972, 4.750813) # Schuberg Philis

if __name__ == "__main__":
    model = ImageModel(styles=STYLE_PROMPTS, contexts=CONTEXT_PROMPTS, system_prompt=SYSTEM_PROMPT)
    geocoder = Geocoder(access_token=mapbox_token)
    lat_display_value = BASIC_LOCATION[0]
    lon_display_value = BASIC_LOCATION[1]

    with st.sidebar:
        btn = st.button("Generate")
        location = st.text_input("Enter location (will become lat/lon)", value=DEFAULT_LOCATION)
        if location:
            response = geocoder.forward(location)
            if response.status_code == 200:
                coords = response.json()['features'][0]['center']
                lon_display_value = coords[0]
                lat_display_value = coords[1]
        lat = st.number_input("Lat", value=lat_display_value, step=None, format="%0.6f")
        lon = st.number_input("Lon", value=lon_display_value, step=None, format="%0.6f")

        image_quality = st.selectbox("Select quality", ("hd", "standard"))
        gen_style = st.selectbox("Select generation style", ("vivid", "natural"))
        image_style = st.selectbox("What style would you like to use?", STYLE_PROMPTS.keys())
        image_context = st.selectbox("What context would you like to use?", CONTEXT_PROMPTS.keys())
        include_weather = st.checkbox("Include Weather", value=False)
        main_prompt = st.text_area("main prompt", value=MAIN_PROMPT, height=100)

    if btn:
        st.map({"latitude": [lat], "longitude": [lon]})
        address = model.get_address(lat, lon)
        weather = model.describe_weather(lat, lon) if include_weather else ""
        description = model.describe_location(address, image_context)
        prompt = model.generate_prompt(main_prompt, address, description, weather, style=image_style)
        st.caption(prompt)
        prompt, image = model.generate(prompt=prompt, image_quality=image_quality, gen_style=gen_style)
        st.image(image, caption=prompt)
