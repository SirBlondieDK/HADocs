from src.hadocs.utils.text import slugify


def test_slugify_danish():
    assert slugify("Soveværelse") == "sovevaerelse"
    assert slugify("Køkken") == "koekken"
