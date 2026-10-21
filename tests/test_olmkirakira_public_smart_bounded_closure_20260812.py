import copy
import importlib.util
import json
import subprocess
import unittest
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/test_olmkirakira_public_smart_bounded_closure_20260812.py"
REPORT = ROOT / "refs/conformance/olmkirakira_public_smart_bounded_closure_20260812.json"
SPEC = importlib.util.spec_from_file_location("kira_smart_closure", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
EXPECTED_GENERATOR_SHA = "5b3e93d45632c3452e81b0b39f63786c6c146e28e0fb7ed5611a0217ec3ea9f1"
assert SPEC.loader
SPEC.loader.exec_module(MOD)

class KiraPublicSmartBoundedClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["python3", str(SCRIPT)], cwd=ROOT, check=True)
        cls.report = json.loads(REPORT.read_text())

    def test_42_cells_are_oracle_classic_smart_exact(self):
        self.assertEqual(hashlib.sha256(SCRIPT.read_bytes()).hexdigest(), EXPECTED_GENERATOR_SHA)
        MOD.validate(self.report)
        self.assertEqual(len(self.report["positive_cells"]), 42)
        self.assertEqual({c["depth"] for c in self.report["positive_cells"]}, {8,16,32})

    def test_conditional_parameter_lifecycle_and_optional_pixel_checkin(self):
        counts = [c["checkout_checkin"][0] for c in self.report["positive_cells"]]
        self.assertEqual({n: counts.count(n) for n in set(counts)}, {25:24, 26:15, 27:3})
        self.assertTrue(all(c["pixel_callbacks"] == [1,1,1,0] for c in self.report["positive_cells"]))

    def test_full_request_controls_are_exact_all_depths(self):
        controls=self.report["request_controls"]
        self.assertEqual({r["depth"] for r in controls},{8,16,32})
        self.assertTrue(all(r["request_rect"]==[0,0,5,3] and r["oracle_sha256"]==r["smart_sha256"]==r["classic_sha256"] for r in controls))

    def test_recanonicalized_request_control_tamper_rejected(self):
        bad=copy.deepcopy(self.report); bad["request_controls"][0]["callbacks"]=[1,1,0,0]
        bad["canonical_request_controls_sha256"]=MOD.canonical_controls(bad["request_controls"])
        with self.assertRaises(AssertionError): MOD.validate(bad)

    def test_negative_rows_are_executed_and_immutable(self):
        rows = self.report["negative_rows"]
        self.assertEqual(len(rows), 765)
        self.assertTrue(all(r["output_untouched"] and r["input_headers_immutable"] for r in rows))

    def test_paired_expected_actual_tamper_is_rejected(self):
        bad = copy.deepcopy(self.report)
        bad["positive_cells"][0]["oracle_sha256"] = "0" * 64
        bad["positive_cells"][0]["smart_sha256"] = "0" * 64
        bad["positive_cells"][0]["classic_sha256"] = "0" * 64
        bad["canonical_cells_sha256"] = MOD.canonical(bad["positive_cells"])
        with self.assertRaises(AssertionError): MOD.validate(bad)

    def test_negative_error_counter_tamper_is_rejected(self):
        bad = copy.deepcopy(self.report)
        bad["negative_rows"][0]["error"] += 1
        with self.assertRaises(AssertionError): MOD.validate(bad)

    def test_contract_scope_identity_and_cell_schema_tamper_rejected(self):
        mutations=[]
        for path,value in [("scope",{}),("contract",{}),("negative_matrix",{} )]:
            bad=copy.deepcopy(self.report); bad[path]=value; mutations.append(bad)
        bad=copy.deepcopy(self.report); bad["identities"]["harness_sha256"]="0"*64; mutations.append(bad)
        bad=copy.deepcopy(self.report); bad["positive_cells"][0]["pixel_format"]="PF16/ARGB64"; mutations.append(bad)
        bad=copy.deepcopy(self.report); bad["positive_cells"][0]["pixel_callbacks"]=[1,1,1,1]; mutations.append(bad)
        for bad in mutations:
            with self.assertRaises(AssertionError): MOD.validate(bad)

    def test_recanonicalized_named_stage_tamper_rejected(self):
        bad=copy.deepcopy(self.report)
        row=next(r for r in bad["negative_rows"] if r["identity"]=="output_error")
        row["callbacks"]="1/1/0/0"
        bad["canonical_negative_rows_sha256"]=MOD.canonical_negatives(bad["negative_rows"])
        with self.assertRaises(AssertionError): MOD.validate(bad)

    def test_param_identity_collision_tamper_rejected(self):
        bad=copy.deepcopy(self.report)
        params=[r for r in bad["negative_rows"] if r["identity"].startswith("param_")]
        params[1]["identity"]=params[0]["identity"]
        bad["canonical_negative_rows_sha256"]=MOD.canonical_negatives(bad["negative_rows"])
        with self.assertRaises(AssertionError): MOD.validate(bad)

    def test_recanonicalized_per_tuple_lifecycle_swap_rejected(self):
        bad=copy.deepcopy(self.report)
        a=next(c for c in bad["positive_cells"] if c["tuple"]=="m1_h7_r0")
        b=next(c for c in bad["positive_cells"] if c["tuple"]=="m2_h7_ramp_r0")
        a["checkout_checkin"],b["checkout_checkin"]=b["checkout_checkin"],a["checkout_checkin"]
        bad["canonical_cells_sha256"]=MOD.canonical(bad["positive_cells"])
        with self.assertRaises(AssertionError): MOD.validate(bad)

    def test_default_validator_is_read_only(self):
        before = (REPORT.read_bytes(), REPORT.with_suffix(".md").read_bytes())
        subprocess.run(["python3", str(SCRIPT)], cwd=ROOT, check=True)
        after = (REPORT.read_bytes(), REPORT.with_suffix(".md").read_bytes())
        self.assertEqual(before, after)

if __name__ == "__main__":
    unittest.main()
