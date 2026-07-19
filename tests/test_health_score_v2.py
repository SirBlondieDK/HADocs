import unittest
from src.hadocs.intelligence.health_score_v2 import HealthScoreV2

class HealthScoreV2Tests(unittest.TestCase):
    def test_empty_findings_gives_100(self):
        self.assertEqual(HealthScoreV2().calculate([]).score, 100.0)

if __name__ == '__main__':
    unittest.main()
