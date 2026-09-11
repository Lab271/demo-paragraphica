def test_recorded_reverse_geocode(mapbox_feature):
    assert mapbox_feature["properties"]["name"] == "Boeingavenue 271"
