import pytest
import sys
import os
import requests
import json

# Geo location of Schuberg Philis/Boeingavenue 271 is 52.274972, 4.750813
SBP = (52.274972, 4.750813)

# put the token in your (protected) env
# You can find the account in 1password under labs, account labssbp2024
def test_checktoken():
    assert os.environ['PARA_MAPBOX_API'].startswith('pk.')


# Expecting this to work curl "https://api.mapbox.com/search/geocode/v6/reverse?longitude=52.27593190546326&latitude=4.7494178783208945&access_token=$PARA_MAPBOX_API"
@pytest.mark.skip(reason="this is a live action call, use file instead")
def test_checkmapbox_reverse_live():
    api_url = "https://api.mapbox.com/search/geocode/v6/reverse?latitude={}&longitude={}&access_token={}"
    token = os.environ['PARA_MAPBOX_API']
    assert token.starts_with('pk.')
    response = requests.get(api_url.format(SBP[0], SBP[1], token))
    res = response.json()
    assert res['features'][0]['properties']['name'] == "Boeingavenue 271"


def test_checkmapbox_reverse():
    f = open('./tests/mapbox_search_sbp.json')
    res = json.loads(f.read())
    f.close()
    assert res['features'][0]['properties']['name'] == "Boeingavenue 271"

