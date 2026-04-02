from pokefinder.matching.engine import (
    _category_matches,
    _grade_matches,
    _keywords_match,
    _price_matches,
    _product_matches,
)


def test_price_matches():
    assert _price_matches(150.0, 0.0, 200.0) is True
    assert _price_matches(250.0, 0.0, 200.0) is False
    assert _price_matches(50.0, 100.0, 200.0) is False
    assert _price_matches(None, 100.0, 200.0) is True  # unknown price passes


def test_category_matches():
    assert _category_matches("sealed", ["sealed", "singles"]) is True
    assert _category_matches("graded", ["sealed"]) is False
    assert _category_matches("anything", []) is True  # no filter = all pass


def test_keywords_match():
    assert _keywords_match("Pokemon 151 ETB", None, ["151", "etb"]) is True
    assert _keywords_match("Random item for sale", None, ["charizard"]) is False
    assert _keywords_match("Any listing", None, []) is True  # no keywords = all pass
    assert _keywords_match("Charizard ex SV", None, ["חרמלאון"]) is False  # different lang


def test_grade_matches():
    assert _grade_matches(10.0, "PSA", ["PSA"], 9.0) is True
    assert _grade_matches(8.0, "PSA", ["PSA"], 9.0) is False  # grade too low
    assert _grade_matches(10.0, "BGS", ["PSA"], None) is False  # wrong company
    assert _grade_matches(None, None, [], None) is True  # no filters


def test_product_matches():
    assert _product_matches("sv-151-etb", "sv-151-etb") is True
    assert _product_matches("sv-base-etb", "sv-151-etb") is False
    assert _product_matches(None, "sv-151-etb") is False  # pref wants product, listing has none
    assert _product_matches(None, None) is True  # no product restriction
