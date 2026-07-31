import unittest
from hadocs.domain.findings import Finding, FindingCategory, FindingSeverity, TargetType
from hadocs.domain.policies import Policy, PolicyAction, PolicyScope
from hadocs.intelligence.policy_engine import PolicyEngine

class PolicyEngineTests(unittest.TestCase):
    def test_suppresses_matching_device(self):
        finding = Finding(
            'entity_unavailable', FindingCategory.AVAILABILITY,
            FindingSeverity.WARNING, TargetType.ENTITY,
            'sensor.garden', 'Unavailable', 4.0,
            device_id='garden-device',
        )
        policy = Policy(
            'Seasonal garden device',
            PolicyScope(device_id='garden-device'),
            PolicyAction(suppress=True),
            'Disconnected during winter',
        )
        result = PolicyEngine().apply([finding], [policy])[0]
        self.assertTrue(result.suppressed)
        self.assertFalse(finding.suppressed)

if __name__ == '__main__':
    unittest.main()
