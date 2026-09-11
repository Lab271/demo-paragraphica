"""Legacy Streamlit UI on top of the core pipeline. Scheduled for removal in #10;
run with `make streamlit`."""

import pprint

import streamlit as st

from paragraphica import api, prompts
from paragraphica.backend import make_backend
from paragraphica.core import Request, generate

DEFAULT_LOCATION = "Schiphol-Rijk"
DEFAULT_LATLON = (52.274972, 4.750813)  # Schuberg Philis

if __name__ == "__main__":
    lat_display_value, lon_display_value = DEFAULT_LATLON

    with st.sidebar:
        btn = st.button("Generate")
        location = st.text_input("Enter location (will become lat/lon)", value=DEFAULT_LOCATION)
        if location:
            try:
                lat_display_value, lon_display_value = api.call_mapbox_forward(location)
            except (KeyError, IndexError):
                st.warning("Location not found")

        image_style = st.selectbox("What style would you like to use?", prompts.STYLES.keys())
        position = st.selectbox("What position would you like to use?", prompts.POSITIONS.keys())
        image_context = st.selectbox("What context would you like to use?", prompts.CONTEXTS.keys())
        include_weather = st.checkbox("Include Weather", value=False)
        include_time = st.checkbox("Include local time", value=True)

        lat = st.number_input("Lat", value=lat_display_value, step=None, format="%0.6f")
        lon = st.number_input("Lon", value=lon_display_value, step=None, format="%0.6f")
        image_quality = st.selectbox("Select quality", ("medium", "low", "high"))
        main_prompt = st.text_area("main prompt", value=prompts.MAIN_PROMPT, height=100)

    if btn:
        req = Request(
            lat=lat,
            lon=lon,
            style=image_style,
            context=image_context,
            position=position,
            main_prompt=main_prompt,
            include_time=include_time,
            include_weather=include_weather,
            quality=image_quality,
        )
        result = generate(req, make_backend())
        st.caption(result.context.address)
        st.map({"latitude": [lat], "longitude": [lon]}, zoom=15)
        st.caption(pprint.pformat(result.description))
        st.divider()
        st.caption(result.prompt)
        st.image(result.image, caption=result.revised_prompt or result.prompt)
