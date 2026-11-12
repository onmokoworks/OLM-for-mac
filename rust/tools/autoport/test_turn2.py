import unittest
from turn2_report import budget_valid

class Turn2Tests(unittest.TestCase):
    def test_limits_and_incomplete_attempt_are_not_qualified(self):
        call={'function':'f','total_attempt_seconds':300}
        self.assertTrue(budget_valid({'calls':[call]*4}))
        self.assertFalse(budget_valid({'calls':[call]*5}))
        self.assertFalse(budget_valid({'calls':[{'function':'f'}]}))
        self.assertFalse(budget_valid({'calls':[dict(call,total_attempt_seconds=300.001)]}))
        self.assertFalse(budget_valid({'calls':[dict(call,function=str(i)) for i in range(61)]}))

if __name__=='__main__':unittest.main()
