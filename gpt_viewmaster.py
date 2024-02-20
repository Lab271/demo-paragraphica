from paragraphica.mapbox import call_mapbox
from paragraphica.openweathermap import call_openweathermap
import streamlit as st
from PIL import Image
from base64 import b64decode
import pprint


class ImageModel:
    SYSTEM_PROMPT = "You are an artist and you will give a utmost realistic description of the surroundings."
    LOCATION_PROMPT = "Mention only three interesting spots in the vicinity of {} in one sentence without mentioning the address with the template 'Near by you can see:'"
    MAIN_PROMPT = "Give a typical view of "
    IMAGE_PROMPT = "Use {} as image style."
    WEATHER_PROMPT = "The temperature is {} degrees Celsius with {}."
    MODEL = "gpt-4"

    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI()
        self.history = []
        self.size="1024x1024"
        self.quality="standard"

    def get_address(self, lat, lon):
        res = call_mapbox(lat, lon)['properties']['context']
        # pprint.pprint(res)
        street = ""
        if 'address' in res:
            street=res['address']['name'] + ", "
        elif 'street' in res:
            street=res['street']['name'] + ", "
        address = street + res['place']['name'] + ", " + res['country']['name']
        return address

    def describe_location(self, address):
        thread = [
            {"role": "system", "content": ImageModel.SYSTEM_PROMPT},
            {"role": "user", "content": ImageModel.LOCATION_PROMPT.format(address)}
        ]
        res = self.client.chat.completions.create(
                    model = ImageModel.MODEL,
                    messages = thread,
                    max_tokens=256,
                    temperature=0.1, 
                    top_p = 0.1,
                ).choices[0].message.content
        return res

    def describe_weather(self, lat, lon):
        res = call_openweathermap(lat, lon)
        return ImageModel.WEATHER_PROMPT.format(res['main']['temp'], res['weather'][0]['main'])

    def generate_prompt(self, main_prompt, address, description, weather, style):
        prompt = main_prompt
        prompt += " " + address + ". "
        prompt += description + " "
        prompt += weather + " "
        if style == 'lego':
            prompt += 'Provide this as a fictional lego box with typical characters.'
        elif style == 'isometric':
            prompt += 'Show this as a 3D isometric graphic with characteristic landmarks.'
        elif style == 'coloring page':
            prompt += 'Coloring page style, bold lines, black and white'
        elif style == 'pop-up':
            prompt += 'pop up HAPPY BIRTHDAY greeting card for a rugby fan'
        elif style == 'Dali':
            prompt += "Use a surrealistic Dali dream style like the 'The Persistence of Memory' painting with clocks and rhinosoros."
        else:
            prompt += ImageModel.IMAGE_PROMPT.format(style)
        return prompt

    def generate(self, prompt, model="dall-e-3", image_quality="standard", gen_style="natural"):
        response = self.client.images.generate(
            model=model,
            prompt=prompt,
            size=self.size,
            style=gen_style,
            quality=image_quality,
            response_format='b64_json',
            n=1,
        )

        image_data = b64decode(response.data[0].b64_json)
        prompt = response.data[0].revised_prompt
        return prompt, image_data

if __name__ == '__main__':
        # st.title("GPT Viewmaster")

        model = ImageModel()

        with st.sidebar:
            # image_model = st.selectbox("What chat model would you like to use?", ("dall-e-3", "dall-e-2"))
            # image_size = st.selectbox("Select size", ("256x256", "1012x1012"))
            image_quality = st.selectbox("Select quality", ("standard", "hd"))
            gen_style = st.selectbox("Select generation style", ("natural", "vivid"))
            image_style = st.selectbox("What style would you like to use?", ("realistic", "film noir", "cartoon", "impressionistic", "cubistic", "isometric", "lego", "coloring page" , "pop-up", "Dali"))
            include_weather = st.checkbox("Include Weather", value=False)
            lat = st.number_input("Lat", value=52.274972, step=None, format="%0.6f")
            lon = st.number_input("Lon", value=4.750813, step=None, format="%0.6f")
            main_prompt = st.text_area(
                "main prompt", value=model.MAIN_PROMPT, height=100
            )
            btn = st.button("Generate")

        if btn:
            address = model.get_address(lat, lon)
            weather = model.describe_weather(lat, lon) if include_weather else ""
            description = model.describe_location(address)
            prompt = model.generate_prompt(main_prompt, address, description, weather, style=image_style)
            st.caption(prompt)
            prompt, image = model.generate(prompt=prompt, image_quality=image_quality, gen_style=gen_style)
            st.image(image, caption=prompt)
