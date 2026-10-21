from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/test_olmcolorkey_public_source_bound_closure_20260813.py"
REPORT = ROOT / "refs/conformance/olmcolorkey_public_source_bound_closure_20260813.json"
TOOL_SHA256 = "8d30702c279a87633084572d0e9e729b2c0c629bfb6118da1c2ff682713dbbd8"


def load_tool():
    spec = importlib.util.spec_from_file_location("olmck_closure", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ColorKeyPublicSourceBoundClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool = load_tool()
        cls.report = json.loads(REPORT.read_text())

    def test_generator_identity_is_external(self) -> None:
        self.assertEqual(hashlib.sha256(TOOL.read_bytes()).hexdigest(), TOOL_SHA256)

    def test_canonical_report_and_live_inputs(self) -> None:
        self.assertTrue(self.tool.validate_report(self.report, live=False))
        self.assertEqual(self.tool.live_identities(), self.tool.EXPECTED_IDENTITIES)

    def test_rejects_unknown_keys(self) -> None:
        mutations = (
            lambda d: d.update(extra=True),
            lambda d: d["scope"].update(extra=True),
            lambda d: d["lifecycle"].update(extra=True),
            lambda d: d["world_contract"].update(extra=True),
            lambda d: d["negative_closure"].update(extra=True),
            lambda d: d["canonical_rows"][0].update(extra=True),
        )
        for mutation in mutations:
            changed = copy.deepcopy(self.report)
            mutation(changed)
            self.assertFalse(self.tool.validate_report(changed, live=False))

    def test_rejects_identity_probe_count_and_scope_tamper(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["identities"]["production_source"] = "0" * 64
        self.assertFalse(self.tool.validate_report(changed, live=False))
        changed = copy.deepcopy(self.report)
        changed["probe_runs"]["public_entries"]["stdout_bytes"] += 1
        self.assertFalse(self.tool.validate_report(changed, live=False))
        changed = copy.deepcopy(self.report)
        changed["negative_closure"]["source_tuple_world_atomic_cases"] += 1
        self.assertFalse(self.tool.validate_report(changed, live=False))
        changed = copy.deepcopy(self.report)
        changed["scope"]["native_after_effects"] = True
        self.assertFalse(self.tool.validate_report(changed, live=False))

    def test_rejects_paired_recanonicalized_row_tamper(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["canonical_rows"][0]["raw_sha256"] = "0" * 64
        changed["canonical_rows_sha256"] = self.tool.digest(changed["canonical_rows"])
        self.assertFalse(self.tool.validate_report(changed, live=False))


if __name__ == "__main__":
    unittest.main()
