from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/test_olmkirakira_mode2_rotation22_closure_20260812.py"
REPORT = ROOT / "refs/conformance/olmkirakira_mode2_rotation22_closure_20260812.json"


def load_module():
    spec = importlib.util.spec_from_file_location("kira_rotation22_closure", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class KiraMode2Rotation22ClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(["python3", str(SCRIPT)], cwd=ROOT, check=True)
        cls.module = load_module()
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_natural_owner_and_all_depths_are_raw_exact(self) -> None:
        self.assertTrue(self.module.validate_report(self.report))

    def test_validator_fails_closed_on_causal_fields(self) -> None:
        mutations = (
            ("identities", "aexcompat_worker_sha256", "0" * 64),
            ("identities", "aex_sha256", "0" * 64),
            ("natural_trace", "trace_truncated", True),
            ("direct_replay", "target", "0x18114ffd0"),
            ("direct_replay", "pre_scaled_by_harness", True),
            ("direct_replay", "brightness_f32_bits", "0x3f800000"),
            ("direct_replay", "actual_sha256", "0" * 64),
            ("direct_replay", "flags_hex", "ff" * 5),
            ("direct_replay", "mismatch_count", 1),
            ("history", "historical_seam_sha256", "0" * 64),
        )
        for first, second, value in mutations:
            changed = copy.deepcopy(self.report)
            changed[first][second] = value
            self.assertFalse(self.module.validate_report(changed), (first, second))
        changed = copy.deepcopy(self.report)
        changed["natural_trace"]["owner_builder"]["aggregation_selector_at_0x48"] = 2
        self.assertFalse(self.module.validate_report(changed))
        changed = copy.deepcopy(self.report)
        changed["natural_trace"]["ramp_helper"]["callsite_rva"] = "0x11500ab"
        self.assertFalse(self.module.validate_report(changed))
        changed = copy.deepcopy(self.report)
        changed["fixture"]["ordered_parameters"] = ["fake"]
        self.assertFalse(self.module.validate_report(changed))
        changed = copy.deepcopy(self.report)
        changed["natural_trace"]["owner_builder"]["brightness_f32_bits"] = "0x3f800000"
        self.assertFalse(self.module.validate_report(changed))
        changed = copy.deepcopy(self.report)
        changed["natural_trace"]["raw_pixel_sha256"] = "0" * 64
        self.assertFalse(self.module.validate_report(changed))
        changed = copy.deepcopy(self.report)
        changed["public_all_depths"]["status"] = "fail_closed_mismatch"
        self.assertFalse(self.module.validate_report(changed))
        changed = copy.deepcopy(self.report)
        changed["public_all_depths"]["rows"][0]["smart_render"]["selector"] = "FAKE"
        self.assertFalse(self.module.validate_report(changed))
        changed = copy.deepcopy(self.report)
        changed["public_all_depths"]["rows"][0]["suite_requests"] = []
        self.assertFalse(self.module.validate_report(changed))
        changed = copy.deepcopy(self.report)
        changed["public_all_depths"]["rows"][2]["mac_effectmain_raw_sha256"] = "0" * 64
        self.assertFalse(self.module.validate_report(changed))


if __name__ == "__main__":
    unittest.main()
