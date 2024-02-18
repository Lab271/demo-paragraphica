from openai import OpenAI
from base64 import b64decode

MODEL = "dall-e-3"

def get_picture(prompt="a white siamese cat", size="1024x1024", quality="standard"):
    client = OpenAI()
    response = client.images.generate(
        model=MODEL,
        prompt=prompt,
        size=size,
        quality=quality,
        response_format='b64_json',
        n=1,
    )

    image_data = b64decode(response.data[0].b64_json)
    prompt = response.data[0].revised_prompt
    return prompt, image_data

