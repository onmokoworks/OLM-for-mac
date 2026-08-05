#!/usr/bin/env python3
"""Regression test for the bounded Mac-only ToonDilate 32bpc readiness gate."""

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "tools/emulation/audit_olmtoondilate_16_32bpc_readiness_20260718.py"
SPEC = importlib.util.spec_from_file_location("toon_readiness", AUDIT_PATH)
AUDIT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(AUDIT)


class ToonDilate32BpcCaptureGateTests(unittest.TestCase):
    def test_current_mac_state_leaves_only_host_capture(self):
        source = AUDIT.source_facts()
        windows = {"manifest": AUDIT.manifest_facts(), "exr_headers": AUDIT.exr_header_facts()}
        package = AUDIT.current_package_facts()
        candidate_count = len(list((ROOT / "refs/reports").rglob("*toondilate*.exr")))

        gate = AUDIT.capture_gate_facts(source, windows, package, candidate_count)

        self.assertTrue(gate["source_32bpc_dispatch_ready"])
        self.assertTrue(gate["windows_float_effect_control_ready"])
        self.assertTrue(gate["mac_package_identity_ready"])
        self.assertFalse(gate["mac_candidate_effect_control_exr_present"])
        self.assertEqual(gate["verdict"], "only-host-capture-remains")


if __name__ == "__main__":
    unittest.main()
