from pokefinder.matching.parser import detect_category, normalize_title, parse_grade


def test_detect_sealed():
    assert detect_category("Pokemon 151 ETB Elite Trainer Box") == "sealed"
    assert detect_category("Booster Box Scarlet Violet") == "sealed"
    assert detect_category("בוסטר בוקס פוקמון 151") == "sealed"


def test_detect_graded():
    assert detect_category("Charizard PSA 10") == "graded"
    assert detect_category("Pikachu BGS 9.5 graded card") == "graded"
    assert detect_category("מדורג PSA 10 charizard") == "graded"


def test_detect_bulk():
    assert detect_category("lot of 100 pokemon cards") == "bulk"
    assert detect_category("באלק קלפים x50") == "bulk"


def test_detect_singles():
    assert detect_category("Charizard ex 151 NM") == "singles"
    assert detect_category("קלף חרמלאון") == "singles"


def test_parse_grade():
    company, grade_str, grade_val = parse_grade("Charizard PSA 10 Base Set")
    assert company == "PSA"
    assert grade_val == 10.0
    assert grade_str == "PSA 10"

    company, grade_str, grade_val = parse_grade("BGS 9.5 Pikachu")
    assert company == "BGS"
    assert grade_val == 9.5

    company, grade_str, grade_val = parse_grade("no grade here")
    assert company is None


def test_normalize_title():
    result = normalize_title("Pokémon 151 ETB — מוצר חדש!")
    assert "pokemon" in result
    assert "151" in result
    assert "etb" in result
    # Punctuation stripped
    assert "—" not in result
    assert "!" not in result
