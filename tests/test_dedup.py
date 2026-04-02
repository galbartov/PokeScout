from pokefinder.matching.dedup import is_title_price_duplicate


def test_exact_duplicate():
    existing = [{"title_normalized": "pokemon 151 etb", "price": 180.0}]
    assert is_title_price_duplicate("pokemon 151 etb", 180.0, existing) is True


def test_similar_title_close_price():
    existing = [{"title_normalized": "pokemon 151 elite trainer box", "price": 180.0}]
    # Slightly different wording, same price
    assert is_title_price_duplicate("151 elite trainer box pokemon", 182.0, existing) is True


def test_similar_title_different_price():
    existing = [{"title_normalized": "pokemon charizard psa 10", "price": 500.0}]
    # Same title but very different price → not a duplicate
    assert is_title_price_duplicate("pokemon charizard psa 10", 200.0, existing) is False


def test_different_title():
    existing = [{"title_normalized": "pikachu card", "price": 50.0}]
    assert is_title_price_duplicate("charizard etb 151", 180.0, existing) is False


def test_empty_existing():
    assert is_title_price_duplicate("any title", 100.0, []) is False
