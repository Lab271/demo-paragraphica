import pytest
import os
import requests
import json

# Geo location of Schuberg Philis/Boeingavenue 271 is lat=52.274972, lon=4.750813
SBP = (52.274972, 4.750813)


@pytest.mark.skip(reason="this is a live action call, use file instead")
def test_geotimezone_live():
    api_url = "https://api.geotimezone.com/public/timezone?latitude={}&longitude={}"
    response = requests.get(api_url.format(SBP[0], SBP[1]))
    res = response.json()
    print(res)
    assert res['longitutde'] is not None


def test_geotimezone():
    f = open('./tests/geotimezone_sbp.json')
    res = json.loads(f.read())
    f.close()
    assert res['current_local_datetime'] == "2024-02-19T21:44:05.008"