def test_recorded_weather(owm_response):
    assert owm_response["weather"][0]["main"] == "Clouds"
