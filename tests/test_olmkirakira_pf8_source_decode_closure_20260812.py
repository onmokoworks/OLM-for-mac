from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/emulation/test_olmkirakira_pf8_source_decode_closure_20260812.py"
REPORT = ROOT / "refs/conformance/olmkirakira_pf8_source_decode_closure_20260812.json"


def load_generator():
    spec = importlib.util.spec_from_file_location("kira_pf8_source_decode_closure", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


class KiraPF8SourceDecodeClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(["python3", str(GENERATOR)], cwd=ROOT, check=True)
        cls.module = load_generator()
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_generated_report_validates(self) -> None:
        self.assertTrue(self.module.validate_report(self.report))

    def assert_tamper_fails(self, mutate) -> None:
        report = copy.deepcopy(self.report); mutate(report)
        self.assertFalse(self.module.validate_report(report))

    def test_tampered_worker_identity_fails_closed(self) -> None:
        self.assert_tamper_fails(lambda r: r["identities"].update(worker_sha256="0" * 64))

    def test_tampered_source_plane_fails_closed(self) -> None:
        self.assert_tamper_fails(lambda r: r["natural_pf8"]["alpha_i_over_17"]
                                 ["source_plane"].update(sha256="1" * 64))

    def test_tampered_fixture_fails_closed(self) -> None:
        self.assert_tamper_fails(lambda r: r["fixture"].update(dimensions=[15, 1]))

    def test_tampered_source_watch_fails_closed(self) -> None:
        self.assert_tamper_fails(lambda r: r["natural_pf8"]["semi_transparent_color"]
                                 ["source_watch"].update(object_deref=400))

    def test_tampered_aex_reciprocal_word_fails_closed(self) -> None:
        self.assert_tamper_fails(lambda r: r["source_decode_contract"]
                                 ["aex_binary_reciprocal"].update(u32_word="0x3b808080"))

    def test_tampered_exhaustive_count_fails_closed(self) -> None:
        self.assert_tamper_fails(lambda r: r["exhaustive_byte_domain"]
                                 .update(differing_codes=125))

    def test_tampered_exhaustive_ulp_fails_closed(self) -> None:
        self.assert_tamper_fails(lambda r: r["exhaustive_byte_domain"]
                                 ["differences"][0].update(ulp=2))

    def test_tampered_seed_fails_closed(self) -> None:
        self.assert_tamper_fails(lambda r: r["alpha_highlight_chain"].update(seed_sha256="2" * 64))

    def test_tampered_ray_fails_closed(self) -> None:
        self.assert_tamper_fails(lambda r: r["alpha_highlight_chain"].update(natural_ray_sha256="3" * 64))

    def test_tampered_glow_fails_closed(self) -> None:
        self.assert_tamper_fails(lambda r: r["alpha_highlight_chain"].update(glow_exact=False))

    def test_tampered_final_fails_closed(self) -> None:
        self.assert_tamper_fails(lambda r: r["alpha_highlight_chain"].update(final_exact=False))

    def test_tampered_counterfactual_word_fails_closed(self) -> None:
        self.assert_tamper_fails(lambda r: r["divide_counterfactual"]
                                 ["alpha_word_differences"][0].update(word=3))

    def test_tampered_counterfactual_ulp_fails_closed(self) -> None:
        self.assert_tamper_fails(lambda r: r["divide_counterfactual"]
                                 ["alpha_word_differences"][1].update(ulp=2))

    def test_tampered_public_pf8_hash_fails_closed(self) -> None:
        self.assert_tamper_fails(lambda r: r["public_alpha_i_over_17"]
                                 ["rows"][0].update(mac_active_bytes_sha256="4" * 64))

    def test_tampered_public_lifecycle_fails_closed(self) -> None:
        self.assert_tamper_fails(lambda r: r["public_alpha_i_over_17"]["rows"][1]
                                 ["lifecycle"]["smart_render"].update(completed=False))

    def test_tampered_regression_hash_fails_closed(self) -> None:
        self.assert_tamper_fails(lambda r: r["existing_semi_transparent_regression"]
                                 ["rows"][0].update(actual_exported_raw_sha256="5" * 64))

    def test_tampered_claim_boundary_fails_closed(self) -> None:
        self.assert_tamper_fails(lambda r: r.update(claim_boundary=r["claim_boundary"] + " broadened"))

    def test_tampered_claims_not_made_fails_closed(self) -> None:
        self.assert_tamper_fails(lambda r: r["claims_not_made"].pop())


if __name__ == "__main__":
    unittest.main()
