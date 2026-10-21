from __future__ import annotations
import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/test_olmradialblur_type3_layer_span_natural_closure_20260812.py"

def load():
    spec = importlib.util.spec_from_file_location("radial_type3_natural", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

class Type3NaturalClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load(); cls.report = json.loads(cls.m.REPORT.read_text())

    def test_canonical_report(self): self.m.validate(self.report)
    def test_content_basis_raw_exact(self):
        self.assertEqual(len(self.report["rows"]), 10)
        self.assertTrue(all(all(r["matches"].values()) for r in self.report["rows"]))
    def test_counterfactual_is_effective(self):
        self.assertTrue(self.report["gates"]["counterfactual_layer_changes_span_and_post_blur"])
    def test_tamper_status_rejected(self):
        bad=copy.deepcopy(self.report);bad["status"]="mismatch"
        with self.assertRaises(AssertionError): self.m.validate(bad)
    def test_tamper_hash_rejected(self):
        bad=copy.deepcopy(self.report);bad["rows"][0]["actual"]["output"]="0"*64
        with self.assertRaises(AssertionError): self.m.validate(bad)
    def test_tamper_paired_actual_and_production_hash_rejected(self):
        bad=copy.deepcopy(self.report)
        bad["rows"][9]["actual"]["post_blur"]="0"*64
        bad["rows"][9]["production"]["post_blur"]="0"*64
        with self.assertRaises(AssertionError): self.m.validate(bad)
    def test_tamper_smart_output_relation_rejected(self):
        bad=copy.deepcopy(self.report)
        bad["rows"][4]["smart_output_sha256"]="0"*64
        bad["rows"][4]["smart_matches_actual"]=False
        with self.assertRaises(AssertionError): self.m.validate(bad)
    def test_tamper_gate_rejected(self):
        bad=copy.deepcopy(self.report);bad["gates"]["host_layer_checkout_checkin_regression_pass"]=False
        with self.assertRaises(AssertionError): self.m.validate(bad)
    def test_tamper_counterfactual_production_rejected(self):
        bad=copy.deepcopy(self.report);bad["rows"][1]["production"]["post_blur"]="f"*64
        with self.assertRaises(AssertionError): self.m.validate(bad)
    def test_tamper_scope_rejected(self):
        bad=copy.deepcopy(self.report);bad["scope"]="all PF32"
        with self.assertRaises(AssertionError): self.m.validate(bad)
    def test_tamper_address_rejected(self):
        bad=copy.deepcopy(self.report);bad["aex"]["composer"]="0x180006340"
        with self.assertRaises(AssertionError): self.m.validate(bad)
    def test_default_main_validates_without_generation(self):
        with mock.patch.object(sys, "argv", [str(SCRIPT)]), \
             mock.patch.object(self.m, "generate", side_effect=AssertionError("write attempted")), \
             mock.patch.object(self.m, "validate") as validate:
            self.assertEqual(self.m.main(), 0)
        validate.assert_called_once()
    def test_write_main_explicitly_generates(self):
        generated=copy.deepcopy(self.report)
        with mock.patch.object(sys, "argv", [str(SCRIPT), "--write"]), \
             mock.patch.object(self.m, "generate", return_value=generated) as generate, \
             mock.patch.object(self.m, "validate") as validate:
            self.assertEqual(self.m.main(), 0)
        generate.assert_called_once_with()
        validate.assert_called_once_with(generated)

if __name__ == "__main__": unittest.main()
