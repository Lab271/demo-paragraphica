import pytest
import sys
import os


# put the token in your (protected) env
# You can find the account in 1password under labs, account labssbp2024
def test_checktoken():
    assert os.environ['PARA_MAPBOX_API'] != None


52.27593190546326, 4.7494178783208945