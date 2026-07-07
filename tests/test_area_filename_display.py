from src.hadocs.utils.display import area_filename


def fake_slugify(value):
    return str(value).lower().replace(" ", "_")


def test_unassigned_area_filename_is_english():
    assert area_filename("_uden_område", fake_slugify) == "no_area"
    assert area_filename("_uden_omraade", fake_slugify) == "no_area"
    assert area_filename("_uden_omr├Ñde", fake_slugify) == "no_area"


def test_normal_area_filename_uses_existing_slugify():
    assert area_filename("Living Room", fake_slugify) == "living_room"
