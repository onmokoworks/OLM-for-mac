#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_windows_32bpc_second_generation_mac_boundary import boundary_verdict


class BoundaryVerdictTests(unittest.TestCase):
    def test_control_mismatch_refuses_ae_exact(self) -> None:
        verdict, reasons = boundary_verdict(True, True, False)
        self.assertEqual(verdict, "AE exact refused")
        self.assertIn("EXR import boundary", reasons[0])

    def test_same_host_failure_is_not_hidden(self) -> None:
        verdict, reasons = boundary_verdict(True, False, True)
        self.assertEqual(verdict, "AE exact refused")
        self.assertIn("Mac effect/control", reasons[0])

    def test_exact_controls_still_do_not_claim_ae_exact(self) -> None:
        verdict, reasons = boundary_verdict(True, True, True)
        self.assertEqual(verdict, "cross-host controls exact; AE exact still unclaimed")
        self.assertFalse(any("refused" in reason.lower() for reason in reasons))


if __name__ == "__main__":
    unittest.main()
