from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .service import HUDDService


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query and test the HUDD device matcher")
    parser.add_argument("--database", help="Optional HUDD SQLite path")
    sub = parser.add_subparsers(dest="command", required=True)

    match = sub.add_parser("match", help="Match a Home Assistant device identity")
    match.add_argument("--manufacturer")
    match.add_argument("--brand")
    match.add_argument("--model")
    match.add_argument("--name", dest="product_name")
    match.add_argument("--hardware-revision")
    match.add_argument("--region")
    match.add_argument(
        "--identifier",
        action="append",
        default=[],
        metavar="TYPE=VALUE",
        help="Repeatable identity such as zigbee_model=RTCGQ11LM",
    )

    search = sub.add_parser("search-org", help="Search organizations")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=25)
    return parser


def _identifiers(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit(f"Invalid --identifier value: {value!r}; expected TYPE=VALUE")
        kind, identifier = value.split("=", 1)
        result[kind.strip()] = identifier.strip()
    return result


def main() -> None:
    args = _parser().parse_args()
    service = HUDDService(args.database)
    if args.command == "search-org":
        print(json.dumps([asdict(item) for item in service.search_organizations(args.query, args.limit)], indent=2))
        return

    result = service.find_device(
        manufacturer=args.manufacturer,
        brand=args.brand,
        model=args.model,
        product_name=args.product_name,
        hardware_revision=args.hardware_revision,
        region=args.region,
        identifiers=_identifiers(args.identifier),
    )
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
