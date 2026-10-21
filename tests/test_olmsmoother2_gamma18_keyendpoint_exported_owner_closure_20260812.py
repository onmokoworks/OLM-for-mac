from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/emulation/test_olmsmoother2_gamma18_keyendpoint_exported_owner_closure_20260812.py"
REPORT = ROOT / "refs/conformance/olmsmoother2_gamma18_keyendpoint_exported_owner_closure_20260812.json"


def load_generator():
    spec = importlib.util.spec_from_file_location("sm2_gamma18_endpoint_closure", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class Smoother2Gamma18EndpointClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_generator()
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def assert_tamper_fails(self, mutate) -> None:
        report = copy.deepcopy(self.report)
        mutate(report)
        self.assertFalse(self.module.validate_report(report))

    def test_committed_report_and_current_identities_validate(self) -> None:
        self.assertTrue(self.module.validate_report(copy.deepcopy(self.report)))
        self.assertTrue(self.module.validate_current_identities())

    def test_identity_tampering_fails_closed(self) -> None:
        self.assert_tamper_fails(
            lambda r: r["identities"].update(aexcompat_worker_sha256="0" * 64))
        self.assert_tamper_fails(
            lambda r: r["identities"].update(aexcompat_commit="f" * 40))
        self.assert_tamper_fails(
            lambda r: r["identities"].update(production_source_sha256="1" * 64))
        self.assert_tamper_fails(
            lambda r: r["identities"].update(effectmain_harness_sha256="2" * 64))

    def test_fixture_and_derivation_tampering_fail_closed(self) -> None:
        self.assert_tamper_fails(lambda r: r["fixture"].update(dimensions=[1, 25]))
        self.assert_tamper_fails(
            lambda r: r["fixture"]["rgb_u8"].__setitem__(0, [1, 1, 1]))
        self.assert_tamper_fails(
            lambda r: r["fixture"].update(source_rgba8_sha256="3" * 64))
        self.assert_tamper_fails(
            lambda r: r["fixture"].update(derivation="arbitrary fixture"))

    def test_parameter_tampering_fails_closed(self) -> None:
        self.assert_tamper_fails(lambda r: r["parameters"].update(gamma_value=2.4))
        self.assert_tamper_fails(
            lambda r: r["parameters"].update(color_key_rgb_u8=[1, 1, 1]))
        self.assert_tamper_fails(
            lambda r: r["parameters"]["gamma_palette_rgb_u8"].reverse())

    def test_exported_owner_raw_and_lifecycle_tampering_fail_closed(self) -> None:
        self.assert_tamper_fails(
            lambda r: r["actual_exported_smart_owner"][0].update(raw_sha256="4" * 64))
        self.assert_tamper_fails(
            lambda r: r["actual_exported_smart_owner"][1].update(
                smart_render_completed=False))
        self.assert_tamper_fails(
            lambda r: r["actual_exported_smart_owner"][2].update(guards_intact=False))
        self.assert_tamper_fails(
            lambda r: r["actual_exported_smart_owner"].pop())

    def test_public_effectmain_raw_tampering_fails_closed(self) -> None:
        self.assert_tamper_fails(
            lambda r: r["production_public_effectmain"]["rows"][3].update(
                raw_sha256="5" * 64))
        self.assert_tamper_fails(
            lambda r: r["production_public_effectmain"]["rows"][4].update(
                pixel_format="argb8"))
        self.assert_tamper_fails(
            lambda r: r["production_public_effectmain"].update(
                chain=["typed RenderBits output"]))

    def test_padding_input_and_callback_tampering_fail_closed(self) -> None:
        gates = lambda r: r["production_public_effectmain"]["gates"]
        self.assert_tamper_fails(
            lambda r: gates(r).update(complete_input_buffer_unchanged=False))
        self.assert_tamper_fails(
            lambda r: gates(r).update(input_row_padding_preserved=False))
        self.assert_tamper_fails(
            lambda r: gates(r).update(output_row_padding_preserved=False))
        self.assert_tamper_fails(
            lambda r: gates(r).update(parameter_checkins_per_cell=14))

    def test_cross_check_claim_and_fail_close_tampering_fail_closed(self) -> None:
        self.assert_tamper_fails(
            lambda r: r["cross_checks"].update(
                noninvert_version_outputs_distinct_all_depths=False))
        self.assert_tamper_fails(
            lambda r: r["cross_checks"]["endpoint_pixels_present"].update(key=[4, 4]))
        self.assert_tamper_fails(
            lambda r: r["intermediate_gamma_observability"].update(
                gamma_1_8_distinct_from_1_0_and_2_4_all_depths=False))
        self.assert_tamper_fails(
            lambda r: r["intermediate_gamma_observability"]
            ["raw_sha256_by_gamma_and_depth"]["1.0"].update(PF8="6" * 64))
        self.assert_tamper_fails(
            lambda r: r.update(claim_boundary=r["claim_boundary"] + " broadened"))
        self.assert_tamper_fails(lambda r: r["fail_close"].clear())
        self.assert_tamper_fails(lambda r: r.update(production_code_changed=True))
        self.assert_tamper_fails(lambda r: r.update(contradictory_claim="AE exact"))
        self.assert_tamper_fails(
            lambda r: r["exact_key_endpoint_observability"].update(
                exact_key_endpoint_action_distinct_all_depths=False))
        self.assert_tamper_fails(
            lambda r: r["exact_key_endpoint_observability"]
            ["key_disabled_raw_sha256_by_depth"].update(PF32="7" * 64))


if __name__ == "__main__":
    unittest.main()
