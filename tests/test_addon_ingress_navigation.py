from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = REPOSITORY_ROOT / "src" / "hadocs" / "web" / "static" / "index.html"


class ElementAttributes(HTMLParser):
    def __init__(self, element_id: str):
        super().__init__()
        self.element_id = element_id
        self.attributes: dict[str, str | None] | None = None

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = dict(attrs)
        if attributes.get("id") == self.element_id:
            self.attributes = attributes


def test_html_export_stays_inside_authenticated_ingress_context():
    parser = ElementAttributes("export-html-link")
    parser.feed(INDEX_HTML.read_text(encoding="utf-8"))

    assert parser.attributes is not None
    assert parser.attributes["href"] == "./report/index.html"
    assert "target" not in parser.attributes
