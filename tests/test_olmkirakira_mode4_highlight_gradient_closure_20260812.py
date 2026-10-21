from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/emulation/test_olmkirakira_mode4_highlight_gradient_closure_20260812.py"
REPORT = ROOT / "refs/conformance/olmkirakira_mode4_highlight_gradient_closure_20260812.json"


def load_generator():
    spec = importlib.util.spec_from_file_location("highlight_gradient_closure", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class KiraMode4HighlightGradientClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(["python3", str(GENERATOR)], cwd=ROOT, check=True)
        cls.module = load_generator()
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_generated_report_validates(self) -> None:
        self.assertTrue(self.module.validate_report(self.report))

    def test_tampered_actual_ray_identity_fails_closed(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["hostless_same_run_actual_aex"]["actual_ray_sha256"] = "0" * 64
        self.assertFalse(self.module.validate_report(tampered))

    def test_tampered_counterfactual_words_fail_closed(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["counterfactual_old_separable"]["old_ray_differences"][0]["word"] = 4
        self.assertFalse(self.module.validate_report(tampered))

    def test_tampered_counterfactual_probe_identity_fails_closed(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["identities"]["counterfactual_probe_sha256"] = "1" * 64
        self.assertFalse(self.module.validate_report(tampered))

    def test_tampered_counterfactual_old_ray_identity_fails_closed(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["counterfactual_old_separable"]["old_ray_sha256"] = "2" * 64
        self.assertFalse(self.module.validate_report(tampered))

    def test_tampered_counterfactual_actual_word_fails_closed(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["counterfactual_old_separable"]["old_ray_differences"][0]["actual"] = "0x3ed359b3"
        self.assertFalse(self.module.validate_report(tampered))

    def test_tampered_counterfactual_ulp_fails_closed(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["counterfactual_old_separable"]["old_ray_differences"][1]["ulp"] = 2
        self.assertFalse(self.module.validate_report(tampered))

    def test_tampered_static_anchor_fails_closed(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["static_binary_and_core_anchors"]["highlight_three_pass_boxfilter_calls"]["0x18114fa95"] = 0
        self.assertFalse(self.module.validate_report(tampered))

    def test_tampered_core_contract_fails_closed(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["static_binary_and_core_anchors"]["production_core_contract"]["row_accumulator"] = "float"
        self.assertFalse(self.module.validate_report(tampered))

    def test_tampered_mode4_active_hash_fails_closed(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["public_exported_mode4"]["rows"][2]["mac_active_bytes_sha256"] = "f" * 64
        self.assertFalse(self.module.validate_report(tampered))

    def test_tampered_public_pixel_format_fails_closed(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["public_exported_mode2_control"]["rows"][1]["pixel_format"] = "argb32f"
        self.assertFalse(self.module.validate_report(tampered))

    def test_tampered_public_byte_count_fails_closed(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["public_exported_mode1_cross_mode_regression"]["rows"][0]["bytes"] = 61
        self.assertFalse(self.module.validate_report(tampered))

    def test_tampered_lifecycle_fails_closed(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["public_exported_mode4"]["rows"][0]["lifecycle"]["smart_render"]["completed"] = False
        self.assertFalse(self.module.validate_report(tampered))

    def test_tampered_mode1_pf8_promotion_fails_closed(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["public_exported_mode1_cross_mode_regression"]["rows"][0]["exact"] = False
        self.assertFalse(self.module.validate_report(tampered))

    def test_tampered_supersedes_fails_closed(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["supersedes"] = "wrong.json"
        self.assertFalse(self.module.validate_report(tampered))

    def test_tampered_history_identity_fails_closed(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["history"]["sha256"] = "3" * 64
        self.assertFalse(self.module.validate_report(tampered))

    def test_tampered_claim_boundary_fails_closed(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["claim_boundary"] += " broadened"
        self.assertFalse(self.module.validate_report(tampered))

    def test_tampered_claims_not_made_fails_closed(self) -> None:
        tampered = copy.deepcopy(self.report)
        tampered["claims_not_made"].pop()
        self.assertFalse(self.module.validate_report(tampered))


if __name__ == "__main__":
    unittest.main()
