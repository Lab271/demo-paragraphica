import pytest
import sys
import os
import requests
import json

# Geo location of Schuberg Philis/Boeingavenue 271 is lat=52.274972, lon=4.750813
SBP = (52.274972, 4.750813)

# put the token in your (protected) env
# You can find the account in 1password under labs, account labssbp2024
def test_checktoken():
    assert int(os.environ['PARA_OPENWEATHERMAP_API'], 16) > 0


@pytest.mark.skip(reason="this is a live action call, use file instead")
def test_openweathermap_live():
    api_url = "https://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&units=metric&appid={}"
    token = os.environ['PARA_OPENWEATHERMAP_API']
    assert int(os.environ['PARA_OPENWEATHERMAP_API'], 16) > 0
    response = requests.get(api_url.format(SBP[0], SBP[1], token))
    res = response.json()
    print(res)
    assert res['weather'] is not None


def test_checkmapbox_reverse():
    f = open('./tests/openweathermap_sbp.json')
    res = json.loads(f.read())
    f.close()
    assert res['weather'][0]['main'] == "Clouds"

