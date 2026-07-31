from __future__ import annotations

from pathlib import Path

from .database import connection
from .models import Device, DeviceIdentity, Organization


def _split_codes(value: str | None) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


class HUDDRepository:
    def __init__(self, database: str | Path | None = None) -> None:
        self.database = database

    def get_organization(self, name_or_id: str) -> Organization | None:
        sql = """
        SELECT * FROM v_organization_overview
        WHERE hudd_id = ? OR canonical_name = ? COLLATE NOCASE
        LIMIT 1
        """
        with connection(self.database) as con:
            row = con.execute(sql, (name_or_id, name_or_id)).fetchone()
        return self._organization(row) if row else None

    def search_organizations(self, query: str, limit: int = 25) -> list[Organization]:
        pattern = f"%{query.strip()}%"
        sql = """
        SELECT DISTINCT v.*
        FROM v_organization_overview v
        LEFT JOIN organizations o ON o.hudd_id = v.hudd_id
        LEFT JOIN organization_aliases a ON a.organization_id = o.id
        WHERE v.canonical_name LIKE ? COLLATE NOCASE
           OR a.alias LIKE ? COLLATE NOCASE
        ORDER BY CASE WHEN v.canonical_name = ? COLLATE NOCASE THEN 0 ELSE 1 END,
                 v.canonical_name
        LIMIT ?
        """
        with connection(self.database) as con:
            rows = con.execute(
                sql, (pattern, pattern, query.strip(), max(1, min(limit, 100)))
            ).fetchall()
        return [self._organization(row) for row in rows]

    def candidate_devices(self, identity: DeviceIdentity, limit: int = 100) -> list[Device]:
        """Return a broad candidate set. Final acceptance happens in DeviceMatcher."""
        terms = [
            identity.model,
            identity.product_name,
            identity.manufacturer,
            identity.brand,
            *identity.identifiers.values(),
        ]
        terms = [term.strip() for term in terms if term and term.strip()]
        if not terms:
            return []

        clauses: list[str] = []
        params: list[object] = []
        for term in terms:
            pattern = f"%{term}%"
            clauses.append(
                """(
                    d.model LIKE ? COLLATE NOCASE OR
                    d.product_name LIKE ? COLLATE NOCASE OR
                    m.canonical_name LIKE ? COLLATE NOCASE OR
                    b.canonical_name LIKE ? COLLATE NOCASE OR
                    da.alias LIKE ? COLLATE NOCASE OR
                    di.identifier_value LIKE ? COLLATE NOCASE
                )"""
            )
            params.extend([pattern] * 6)

        sql = f"""
        SELECT DISTINCT d.*, m.canonical_name AS manufacturer_name,
               b.canonical_name AS brand_name
        FROM devices d
        LEFT JOIN organizations m ON m.id = d.manufacturer_id
        LEFT JOIN organizations b ON b.id = d.brand_id
        LEFT JOIN device_aliases da ON da.device_id = d.id
        LEFT JOIN device_identifiers di ON di.device_id = d.id
        WHERE {' OR '.join(clauses)}
        ORDER BY d.product_name, d.model
        LIMIT ?
        """
        params.append(max(1, min(limit, 250)))
        with connection(self.database) as con:
            rows = con.execute(sql, params).fetchall()
            return [self._device_with_identity(con, row) for row in rows]

    def find_devices(
        self,
        *,
        manufacturer: str | None = None,
        brand: str | None = None,
        model: str | None = None,
        product_name: str | None = None,
        limit: int = 25,
    ) -> list[Device]:
        identity = DeviceIdentity(
            manufacturer=manufacturer,
            brand=brand,
            model=model,
            product_name=product_name,
        )
        return self.candidate_devices(identity, limit=limit)

    @staticmethod
    def _organization(row) -> Organization:
        return Organization(
            hudd_id=row["hudd_id"],
            canonical_name=row["canonical_name"],
            entity_type=row["entity_type"],
            category=row["category"],
            connection_class=row["connection_class"],
            review_status=row["review_status"],
            support_codes=_split_codes(row["support_codes"]),
            notes=row["notes"],
        )

    @classmethod
    def _device_with_identity(cls, con, row) -> Device:
        aliases = [
            item["alias"]
            for item in con.execute(
                "SELECT alias FROM device_aliases WHERE device_id = ? ORDER BY alias", (row["id"],)
            ).fetchall()
        ]
        identifiers: dict[str, list[str]] = {}
        for item in con.execute(
            """SELECT identifier_type, identifier_value FROM device_identifiers
               WHERE device_id = ? ORDER BY identifier_type, identifier_value""",
            (row["id"],),
        ).fetchall():
            identifiers.setdefault(item["identifier_type"], []).append(item["identifier_value"])
        return cls._device(row, aliases=aliases, identifiers=identifiers)

    @staticmethod
    def _device(row, *, aliases=None, identifiers=None) -> Device:
        return Device(
            hudd_id=row["hudd_id"],
            product_name=row["product_name"],
            model=row["model"],
            manufacturer=row["manufacturer_name"],
            brand=row["brand_name"],
            hardware_revision=row["hardware_revision"],
            region=row["region"],
            product_family=row["product_family"],
            lifecycle_status=row["lifecycle_status"],
            review_status=row["review_status"],
            aliases=aliases or [],
            identifiers=identifiers or {},
        )
