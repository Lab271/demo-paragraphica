import os
import requests

def call_mapbox(lat, lon):
    api_url = "https://api.mapbox.com/search/geocode/v6/reverse?latitude={}&longitude={}&access_token={}"
    token = os.environ['PARA_MAPBOX_API']
    assert token.startswith('pk.')
    response = requests.get(api_url.format(lat, lon, token))
    res = response.json()
    return res['features'][0]  #['properties']['name'] == "Boeingavenue 271"