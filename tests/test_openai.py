from openai import OpenAI
from base64 import b64decode
import pprint
client = OpenAI()

def test_text():
    response = client.chat.completions.create(
    model="gpt-3.5-turbo-0125",
    response_format={ "type": "json_object" },
    messages=[
        {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
        {"role": "user", "content": "Who won the world series in 2020?"}
    ]
    )
    print(response.choices[0].message.content)

def test_genimage(prompt="a white siamese cat"):
    response = client.images.generate(
    model="dall-e-3",
    prompt=prompt,
    size="1024x1024",
    quality="standard",
    response_format='b64_json',
    n=1,
    )
    # print(response.data[0].url)
    # pprint.pprint(response)

    image_data = b64decode(response.data[0].b64_json)
    print("Prompt: " + response.data[0].revised_prompt)
    image_file = "output.png"
    with open(image_file, mode="wb") as png:
        png.write(image_data)

if __name__ == '__main__':
    prompt = 'an evening photo taken at the cliffordstraat, amsterdam, from a low angle. The style is manga. The weather is partly cloudy and 18 degrees. The date is Sunday, February 18th, 2024. Near by is a canal and a park. You also see Ajax fans chearing.'
    test_genimage(prompt)