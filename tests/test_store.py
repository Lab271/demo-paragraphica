from datetime import datetime

import pytest

from paragraphica.context import Context
from paragraphica.core import Request, Result
from paragraphica.store import Store, slugify

CTX = Context(address="Boeingavenue, Schiphol-Rijk, Netherlands", time_of_day="afternoon")
REQ = Request(lat=52.27, lon=4.75, style="film noir")
RESULT = Result(context=CTX, description="Planes.", prompt="P", image=b"JPG", mime_type="image/jpeg", duration_s=12.34)
NOW = datetime(2026, 9, 11, 17, 52, 3).astimezone()


def _save(store, result=RESULT, **kw):
    return store.save(REQ, result, backend="gemini", text_model="t", image_model="i", now=NOW, **kw)


def test_slugify():
    assert slugify("Boeingavenue, Schiphol-Rijk") == "boeingavenue-schiphol-rijk"
    assert slugify("!!!") == "image"
    assert len(slugify("x" * 100)) == 40


def test_save_writes_image_and_record(tmp_path):
    store = Store(tmp_path)
    rec = _save(store, location="Schiphol-Rijk")
    assert rec.image == "20260911-175203-boeingavenue-film-noir.jpg"
    assert (tmp_path / rec.image).read_bytes() == b"JPG"
    assert rec.duration_s == 12.3 and rec.location == "Schiphol-Rijk" and rec.time_of_day == "afternoon"
    assert store.history_path.read_text().count("\n") == 1


def test_records_round_trip_and_order(tmp_path):
    store = Store(tmp_path)
    a = _save(store)
    b = _save(store)  # same second -> collision suffix
    assert b.image == "20260911-175203-boeingavenue-film-noir-2.jpg"
    assert store.records() == [a, b]


def test_unknown_keys_land_in_extra(tmp_path):
    store = Store(tmp_path)
    _save(store)
    line = store.history_path.read_text().rstrip("\n")
    store.history_path.write_text(line[:-1] + ', "future_field": 1}\n')
    assert store.records()[0].extra == {"future_field": 1}


def test_dry_run_result_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="no image"):
        _save(Store(tmp_path), result=Result(context=CTX, description="d", prompt="p"))


def test_empty_store(tmp_path):
    assert Store(tmp_path / "missing").records() == []
