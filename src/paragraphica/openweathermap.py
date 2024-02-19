import os
import requests
import json

def call_openweathermap(lat, lon):
    api_url = "https://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&units=metric&appid={}"
    token = os.environ['PARA_OPENWEATHERMAP_API']
    assert int(os.environ['PARA_OPENWEATHERMAP_API'], 16) > 0
    response = requests.get(api_url.format(lat, lon, token))
    res = response.json()
    return res
