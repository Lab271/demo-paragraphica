from paragraphica.mapbox import call_mapbox
from paragraphica.openweathermap import call_openweathermap
from base64 import b64decode

LLM_MODEL = "gpt-4"
DRAW_MODEL = "dall-e-3"

class ImageModel:
    WEATHER_PROMPT = "The temperature is {} degrees Celsius with {}."


    def __init__(self, styles, contexts, system_prompt):
        from openai import OpenAI
        self.client = OpenAI()
        self.history = []
        self.styles=styles
        self.contexts=contexts
        self.system_prompt=system_prompt
        self.size="1024x1024"
        self.quality="standard"

    def get_address(self, lat, lon):
        res = call_mapbox(lat, lon)['properties']['context']
        street=res['street']['name'] + ", "
        address = street + res['place']['name'] + ", " + res['country']['name']
        return address

    def describe_location(self, address, context):
        thread = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.contexts[context].format(address)}
        ]
        res = self.client.chat.completions.create(
                    model = LLM_MODEL,
                    messages = thread,
                    max_tokens=256,
                    temperature=0.1, 
                    top_p = 0.1,
                ).choices[0].message.content
        return res

    def describe_weather(self, lat, lon):
        res = call_openweathermap(lat, lon)
        return ImageModel.WEATHER_PROMPT.format(res['main']['temp'], res['weather'][0]['description'])

    def generate_prompt(self, main_prompt, address, description, weather, style):
        prompt = main_prompt
        prompt += " " + address + ". "
        prompt += description + " "
        prompt += weather + " "
        prompt += self.styles[style]
        return prompt

    def generate(self, prompt, model=DRAW_MODEL, image_quality="standard", gen_style="natural"):
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
