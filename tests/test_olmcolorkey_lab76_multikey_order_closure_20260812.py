#!/usr/bin/env python3
"""Fail-closed report checks for the bounded Lab76 multi-key closure."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/test_olmcolorkey_lab76_multikey_order_closure_20260812.py"
REPORT = ROOT / "refs/conformance/olmcolorkey_lab76_multikey_order_closure_20260812.json"


def load_module():
    spec = importlib.util.spec_from_file_location("olmck_lab76_order_closure", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class Lab76MultiKeyOrderClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def assert_tamper_fails(self, mutate) -> None:
        report = copy.deepcopy(self.report)
        mutate(report)
        self.assertFalse(self.module.validate_report(report))

    def test_committed_report_is_valid(self) -> None:
        self.assertTrue(self.module.validate_report(copy.deepcopy(self.report)))
        self.assertTrue(self.module.validate_current_identities())

    def test_identity_tampering_fails_closed(self) -> None:
        self.assert_tamper_fails(lambda r: r["identities"].update(aexcompat_commit="0" * 40))
        self.assert_tamper_fails(lambda r: r["identities"].update(production_source_sha256="f" * 64))

    def test_owner_hash_and_record_tampering_fail_closed(self) -> None:
        self.assert_tamper_fails(lambda r: r["public_owner"][0].update(raw_pixel_sha256="0" * 64))
        self.assert_tamper_fails(lambda r: r["public_owner"][0].update(pixel_format="argb32f"))
        self.assert_tamper_fails(lambda r: r["public_owner"].__setitem__(1, copy.deepcopy(r["public_owner"][0])))
        self.assert_tamper_fails(lambda r: r["owner_record"].update(after_sha256="0" * 64))
        self.assert_tamper_fails(lambda r: r["owner_record"].update(trace_guards_intact=False))
        self.assert_tamper_fails(
            lambda r: r["owner_record"]["semantic_fields"].update(color_space_at_0x30=2))
        self.assert_tamper_fails(lambda r: r["fixture"].update(row_padding_bytes=4))

    def test_hook_and_algorithm_tampering_fail_closed(self) -> None:
        self.assert_tamper_fails(
            lambda r: r["classifier_hook"]["events"][2]["comparison"].update(
                f32_bits=["0x00000000"] * 3))
        self.assert_tamper_fails(
            lambda r: r["classifier_hook"]["per_component_witness"]["events"][1]["key"].update(
                f32_bits=["0x00000000"] * 3))
        self.assert_tamper_fails(
            lambda r: r["classifier_hook"]["events"][0]["key"].update(values=[0.0] * 3))
        self.assert_tamper_fails(
            lambda r: r["classifier_hook"].update(instruction_count=629))
        self.assert_tamper_fails(
            lambda r: r["classifier_hook"]["per_component_witness"].update(
                instruction_count=642))
        self.assert_tamper_fails(
            lambda r: r["classifier_hook"].update(interpretation="broadened"))
        self.assert_tamper_fails(
            lambda r: r["classifier_hook"]["per_component_witness"].update(
                interpretation="broadened"))
        self.assert_tamper_fails(
            lambda r: r["native_algorithm"].update(shared_mutation_ab=[0.0, 0.0]))
        self.assert_tamper_fails(
            lambda r: r["native_algorithm"].update(scalar="portable L1 mean"))

    def test_lifecycle_padding_and_input_tampering_fail_closed(self) -> None:
        self.assert_tamper_fails(
            lambda r: r["production_effectmain"]["gates"].update(parameter_checkins=32))
        self.assert_tamper_fails(
            lambda r: r["production_effectmain"]["gates"].update(output_padding_preserved=False))
        self.assert_tamper_fails(
            lambda r: r["production_effectmain"]["gates"].update(
                input_complete_buffer_unchanged=False))
        self.assert_tamper_fails(
            lambda r: r["production_effectmain"].update(chain=["typed RenderWorld"]))
        self.assert_tamper_fails(
            lambda r: r["production_admission"]["predicate_one_away"].update(rejects=113))
        self.assert_tamper_fails(
            lambda r: r["production_admission"]["classic_render_guard"].update(
                rejected_output_untouched=False))
        self.assert_tamper_fails(
            lambda r: r["production_admission"]["smart_null_world_guard"].update(
                checkin_layer_pixels=0))
        self.assert_tamper_fails(
            lambda r: r["production_admission"].update(
                outside_behavior="new rule generalized"))

    def test_counterfactual_regression_and_claim_tampering_fail_closed(self) -> None:
        self.assert_tamper_fails(
            lambda r: r["counterfactuals"].update(reverse_order_changes_all_three_raw_hashes=False))
        self.assert_tamper_fails(
            lambda r: r["counterfactuals"].update(reason="broadened"))
        self.assert_tamper_fails(lambda r: r["regressions"]["edge_blur"].update(status="mismatch"))
        self.assert_tamper_fails(
            lambda r: r["regressions"]["edge_blur"].update(stdout_sha256="0" * 64))
        self.assert_tamper_fails(
            lambda r: r["installation_status"].update(status="current"))
        self.assert_tamper_fails(lambda r: r.update(claim_boundary=r["claim_boundary"] + " broadened"))
        self.assert_tamper_fails(lambda r: r["fail_close"].clear())


if __name__ == "__main__":
    unittest.main()
