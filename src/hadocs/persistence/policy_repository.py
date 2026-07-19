from __future__ import annotations
import json
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from src.hadocs.domain.findings import FindingCategory, FindingSeverity, TargetType
from src.hadocs.domain.policies import Policy, PolicyAction, PolicyScope

class PolicyRepository:
    def __init__(self, database) -> None:
        self.database = database

    def list(self, include_disabled: bool = True) -> list[Policy]:
        sql = 'SELECT * FROM policies'
        if not include_disabled:
            sql += ' WHERE enabled = 1'
        sql += ' ORDER BY priority DESC, created_at ASC'
        with self.database.connect() as connection:
            rows = connection.execute(sql).fetchall()
        return [self._from_row(row) for row in rows]

    def get(self, policy_id: str) -> Policy | None:
        with self.database.connect() as connection:
            row = connection.execute(
                'SELECT * FROM policies WHERE id = ?', (policy_id,)
            ).fetchone()
        return self._from_row(row) if row else None

    def save(self, policy: Policy) -> Policy:
        scope_json = json.dumps(self._normalise(asdict(policy.scope)), sort_keys=True)
        action_json = json.dumps(self._normalise(asdict(policy.action)), sort_keys=True)
        with self.database.connect() as connection:
            connection.execute(
                '''INSERT INTO policies (
                    id, name, enabled, priority, scope_json, action_json,
                    reason, starts_at, expires_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name, enabled=excluded.enabled,
                    priority=excluded.priority, scope_json=excluded.scope_json,
                    action_json=excluded.action_json, reason=excluded.reason,
                    starts_at=excluded.starts_at, expires_at=excluded.expires_at,
                    updated_at=excluded.updated_at''',
                (
                    policy.id, policy.name, int(policy.enabled), policy.priority,
                    scope_json, action_json, policy.reason,
                    policy.starts_at.isoformat() if policy.starts_at else None,
                    policy.expires_at.isoformat() if policy.expires_at else None,
                    policy.created_at.isoformat(), policy.updated_at.isoformat(),
                ),
            )
        return policy

    def delete(self, policy_id: str) -> bool:
        with self.database.connect() as connection:
            return connection.execute(
                'DELETE FROM policies WHERE id = ?', (policy_id,)
            ).rowcount > 0

    @classmethod
    def _normalise(cls, value):
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, set):
            return sorted(cls._normalise(item) for item in value)
        if isinstance(value, dict):
            return {key: cls._normalise(item) for key, item in value.items()}
        return value

    @staticmethod
    def _from_row(row) -> Policy:
        scope = json.loads(row['scope_json'])
        action = json.loads(row['action_json'])
        return Policy(
            id=row['id'],
            name=row['name'],
            enabled=bool(row['enabled']),
            priority=int(row['priority']),
            scope=PolicyScope(
                target_type=TargetType(scope['target_type']) if scope.get('target_type') else None,
                target_id=scope.get('target_id'),
                device_id=scope.get('device_id'),
                entity_id=scope.get('entity_id'),
                integration_id=scope.get('integration_id'),
                area_id=scope.get('area_id'),
                finding_codes=set(scope.get('finding_codes', [])),
                categories={FindingCategory(value) for value in scope.get('categories', [])},
                metadata_equals=dict(scope.get('metadata_equals', {})),
            ),
            action=PolicyAction(
                suppress=bool(action.get('suppress', False)),
                reclassify_as=FindingSeverity(action['reclassify_as']) if action.get('reclassify_as') else None,
                penalty_multiplier=float(action.get('penalty_multiplier', 1.0)),
                add_tags=set(action.get('add_tags', [])),
            ),
            reason=row['reason'],
            starts_at=datetime.fromisoformat(row['starts_at']) if row['starts_at'] else None,
            expires_at=datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None,
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
        )
