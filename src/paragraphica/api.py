import os
import requests
from openai import OpenAI
from base64 import b64decode

MODEL = "dall-e-3"


def call_mapbox(lat, lon):
    api_url = "https://api.mapbox.com/search/geocode/v6/reverse?latitude={}&longitude={}&access_token={}"
    token = os.environ['PARA_MAPBOX_API']
    assert token.startswith('pk.')
    response = requests.get(api_url.format(lat, lon, token))
    res = response.json()
    return res['features'][0]  #['properties']['name'] == "Boeingavenue 271"


def call_openweathermap(lat, lon):
    api_url = "https://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&units=metric&appid={}"
    token = os.environ['PARA_OPENWEATHERMAP_API']
    assert int(os.environ['PARA_OPENWEATHERMAP_API'], 16) > 0
    response = requests.get(api_url.format(lat, lon, token))
    res = response.json()
    return res


def call_dalle(prompt, gen_style="natural", size="1024x1024", quality="standard", model=MODEL):
    client = OpenAI()

    response = client.images.generate(
        model=model,
        prompt=prompt,
        size=size,
        quality=quality,
        style=gen_style,
        response_format='b64_json',
        n=1,
    )

    image_data = b64decode(response.data[0].b64_json)
    prompt = response.data[0].revised_prompt
    return prompt, image_data


def call_gpt(model, messages, max_tokens=256, temperature=0.1, top_p=0.1):
    client = OpenAI()

    res = client.chat.completions.create(
                model = model,
                messages = messages,
                max_tokens=max_tokens,
                temperature=temperature, 
                top_p = top_p,
            ).choices[0].message.content
    return res


def call_geotimezone(lat, lon):
    api_url = "https://api.geotimezone.com/public/timezone?latitude={}&longitude={}"
    response = requests.get(api_url.format(lat, lon))
    return response.json()
