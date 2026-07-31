import tempfile
import unittest
from pathlib import Path
from hadocs.domain.policies import Policy, PolicyAction, PolicyScope
from hadocs.persistence.database import Database
from hadocs.persistence.policy_repository import PolicyRepository

class PolicyRepositoryTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Database(Path(directory) / 'hadocs.db')
            database.migrate()
            repository = PolicyRepository(database)
            policy = Policy(
                'Garden', PolicyScope(device_id='garden-device'),
                PolicyAction(suppress=True), 'Seasonal',
            )
            repository.save(policy)
            loaded = repository.get(policy.id)
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.scope.device_id, 'garden-device')

if __name__ == '__main__':
    unittest.main()
