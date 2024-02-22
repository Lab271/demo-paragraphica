from paragraphica import api
from datetime import datetime

LLM_MODEL = "gpt-4"
DRAW_MODEL = "dall-e-3"


class ImageModel:
    WEATHER_PROMPT = "The temperature is {} degrees Celsius with {}."

    def __init__(self, styles, contexts, positions, system_prompt):
        self.styles=styles
        self.contexts=contexts
        self.positions=positions
        self.system_prompt=system_prompt
        self.size="1024x1024"
        self.quality="standard"

    def get_address(self, lat, lon):
        res = api.call_mapbox(lat, lon)['properties']['context']
        if 'street' in res:
            street=res['street']['name'] + ", "
        else:
            street = ""
        address = street + res['place']['name'] + ", " + res['country']['name']
        return address

    def describe_location(self, address, context, time, weather):
        location = self.contexts[context].format(address)
        if time:
            location += 'It is ' + time + ". "
        location += weather + " "
        thread = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": location}
        ]
        return thread

    def get_localtime(self, lat, lon):
        res = api.call_geotimezone(lat, lon)['current_local_datetime']
        hour = datetime.fromisoformat(res).hour
        if hour > 19:
            return 'late in the evening'
        elif hour > 17:
            return 'early in the evening'
        elif hour > 11: 
            return 'afternoon'
        elif hour > 7:
            return 'morning'
        elif hour > 5:
            return 'early in the morning'
        else:
            return 'dark night'

    def describe_weather(self, lat, lon):
        res = api.call_openweathermap(lat, lon)
        return ImageModel.WEATHER_PROMPT.format(res['main']['temp'], res['weather'][0]['description'])

    def generate_prompt(self, main_prompt, address, description, position, style):
        description = api.call_gpt(LLM_MODEL, description, 400, 0.1, 0.1)
        prompt = main_prompt + " the " + address + ". "
        prompt += description + " "
        prompt += self.positions[position]
        prompt += self.styles[style]
        return prompt

    def generate(self, prompt, model=DRAW_MODEL, image_quality="standard", gen_style="natural"):
        return api.call_dalle(prompt, gen_style, size=self.size, quality=image_quality, model=model)
