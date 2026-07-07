from __future__ import annotations

from pathlib import Path
import base64

DISPLAY = Path("src/hadocs/utils/display.py")
TEST = Path("tests/test_area_filename_display.py")
DOC = Path("docs/ISSUE_4_STEP3_AREA_FILENAME.md")

DOC_TEXT = base64.b64decode("IyBJc3N1ZSAjNCBTdGVwIDM6IEFyZWEgZmlsZW5hbWUgaGVscGVyCgpFeHRlbmRzIGBzcmMvaGFkb2NzL3V0aWxzL2Rpc3BsYXkucHlgIHdpdGggYGFyZWFfZmlsZW5hbWUoKWAuCgpVbmFzc2lnbmVkIEhvbWUgQXNzaXN0YW50IGFyZWFzIGNhbiBub3cgZ2VuZXJhdGU6CgpgYGB0ZXh0Cm5vX2FyZWEubWQKYGBgCgpOb3JtYWwgYXJlYXMgc3RpbGwgdXNlIHRoZSBleGlzdGluZyBgc2x1Z2lmeSgpYCBiZWhhdmlvci4KCk5vIGdlbmVyYXRvciBiZWhhdmlvciBpcyBjaGFuZ2VkIGluIHRoaXMgc3RlcC4K").decode("utf-8")


APPEND_TEXT = """
NO_AREA_FILENAME = "no_area"


def area_filename(value: object, slugify_func) -> str:
    if is_unassigned_area(value):
        return NO_AREA_FILENAME
    return slugify_func(display_area(value))
"""


TEST_TEXT = """from src.hadocs.utils.display import area_filename


def fake_slugify(value):
    return str(value).lower().replace(" ", "_")


def test_unassigned_area_filename_is_english():
    assert area_filename("_uden_område", fake_slugify) == "no_area"
    assert area_filename("_uden_omraade", fake_slugify) == "no_area"
    assert area_filename("_uden_omr├Ñde", fake_slugify) == "no_area"


def test_normal_area_filename_uses_existing_slugify():
    assert area_filename("Living Room", fake_slugify) == "living_room"
"""


def main() -> None:
    if not DISPLAY.exists():
        raise SystemExit("Missing src/hadocs/utils/display.py. Apply and commit step 1 first.")

    text = DISPLAY.read_text(encoding="utf-8")
    if "def area_filename(" not in text:
        text = text.rstrip() + "\n\n" + APPEND_TEXT
        DISPLAY.write_text(text + "\n", encoding="utf-8")

    TEST.write_text(TEST_TEXT, encoding="utf-8")
    DOC.write_text(DOC_TEXT, encoding="utf-8")

    print("Issue #4 step 3 applied: area_filename() helper added.")
    print("Run: py -3.14 -m pytest")
    print("Commit if green:")
    print("  git add src/hadocs/utils/display.py tests/test_area_filename_display.py docs/ISSUE_4_STEP3_AREA_FILENAME.md tools/apply_issue4_step3_area_filename.py")
    print('  git commit -m "Add area filename display helper"')


if __name__ == "__main__":
    main()
