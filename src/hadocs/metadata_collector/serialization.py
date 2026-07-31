"""Canonical UTF-8 JSON serialization for immutable snapshots."""

from __future__ import annotations

import json

from .contract import Snapshot, public_mapping
from .normalization import Normalizer, canonical_value


class SnapshotSerializer:
    def __init__(self, normalizer: Normalizer | None = None) -> None:
        self.normalizer = normalizer or Normalizer()

    def serialize(self, snapshot: Snapshot) -> bytes:
        normalized = self.normalizer.normalize(snapshot)
        payload = canonical_value(public_mapping(normalized))
        return (json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n").encode(
            "utf-8"
        )

