from copy import deepcopy

class PolicyEngine:
    def apply(self, findings, policies, now=None):
        active = sorted(
            (policy for policy in policies if policy.is_active(now)),
            key=lambda policy: policy.priority,
            reverse=True,
        )
        return [self._apply_one(finding, active) for finding in findings]

    def _apply_one(self, finding, policies):
        result = deepcopy(finding)
        for policy in policies:
            if not self._matches(result, policy):
                continue
            if policy.id not in result.applied_policy_ids:
                result.applied_policy_ids.append(policy.id)
            if policy.action.suppress:
                result.suppressed = True
            if policy.action.reclassify_as is not None:
                if result.original_severity is None:
                    result.original_severity = result.severity
                result.severity = policy.action.reclassify_as
            result.penalty *= policy.action.penalty_multiplier
            if policy.action.add_tags:
                tags = set(result.metadata.get('tags', []))
                tags.update(policy.action.add_tags)
                result.metadata['tags'] = sorted(tags)
        return result

    @staticmethod
    def _matches(finding, policy) -> bool:
        scope = policy.scope
        for expected, actual in (
            (scope.target_type, finding.target_type),
            (scope.target_id, finding.target_id),
            (scope.device_id, finding.device_id),
            (scope.entity_id, finding.entity_id),
            (scope.integration_id, finding.integration_id),
            (scope.area_id, finding.area_id),
        ):
            if expected is not None and expected != actual:
                return False
        if scope.finding_codes and finding.code not in scope.finding_codes:
            return False
        if scope.categories and finding.category not in scope.categories:
            return False
        return all(
            finding.metadata.get(key) == value
            for key, value in scope.metadata_equals.items()
        )
