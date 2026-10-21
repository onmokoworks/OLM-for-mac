from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/test_olmkirakira_mode4_diagonal2_owner_angle_closure_20260812.py"
REPORT = ROOT / "refs/conformance/olmkirakira_mode4_diagonal2_owner_angle_closure_20260812.json"


def load_module():
    spec = importlib.util.spec_from_file_location("kira_d2_owner_angle_closure", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class KiraMode4Diagonal2OwnerAngleClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(["python3", str(SCRIPT)], cwd=ROOT, check=True)
        cls.module = load_module()
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_natural_angle_chain_and_all_depths_are_raw_exact(self) -> None:
        self.assertTrue(self.module.validate_report(self.report))

    def test_validator_fails_closed_on_causal_fields(self) -> None:
        mutations = (
            ("identities", "aexcompat_worker_sha256", "0" * 64),
            ("identities", "disassembly_sha256", "0" * 64),
            ("identities", "production_source_sha256", "0" * 64),
            ("fixture", "rotation_raw_fixed", 181),
            ("natural_trace", "raw_pixel_sha256", "0" * 64),
            ("static_owner_angle_table", "base_angle_degrees", -45),
            ("angle_representative_proof", "natural_angle_degrees", -44),
            ("angle_representative_proof", "old_ray_difference_count", 0),
            ("downstream_proof", "glow_exact", False),
            ("public_all_depths", "status", "fail_closed_mismatch"),
        )
        for first, second, value in mutations:
            changed = copy.deepcopy(self.report)
            changed[first][second] = value
            self.assertFalse(self.module.validate_report(changed), (first, second))
        changed = copy.deepcopy(self.report)
        changed["natural_trace"]["helper"]["angle_degrees"] = -44
        self.assertFalse(self.module.validate_report(changed))
        changed = copy.deepcopy(self.report)
        changed["natural_trace"]["stages"]["ray"]["sha256"] = "0" * 64
        self.assertFalse(self.module.validate_report(changed))
        changed = copy.deepcopy(self.report)
        changed["public_all_depths"]["rows"][2]["mac_effectmain_raw_sha256"] = "0" * 64
        self.assertFalse(self.module.validate_report(changed))
        changed = copy.deepcopy(self.report)
        changed["public_all_depths"]["rows"][2]["pixel_format"] = "argb16"
        self.assertFalse(self.module.validate_report(changed))
        changed = copy.deepcopy(self.report)
        changed["public_all_depths"]["rows"][0]["smart_render"]["completed"] = False
        self.assertFalse(self.module.validate_report(changed))
        changed = copy.deepcopy(self.report)
        changed["natural_trace"]["stages"]["forward"]["bytes"] = 60
        self.assertFalse(self.module.validate_report(changed))
        changed = copy.deepcopy(self.report)
        changed["angle_representative_proof"]["old_ray_differences"][0]["ulp"] = 1
        self.assertFalse(self.module.validate_report(changed))


if __name__ == "__main__":
    unittest.main()
