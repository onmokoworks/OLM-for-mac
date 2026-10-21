import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "tools/emulation/test_olmtoondilate_public_admission_negative_closure_20260813.py"
REPORT = ROOT / "refs/conformance/olmtoondilate_public_admission_negative_closure_20260813.json"
spec = importlib.util.spec_from_file_location("toon_negative", MODULE)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)


def raw_from_saved():
    saved = json.loads(REPORT.read_text())
    return {"schema":"olmtoondilate.public-admission-negative/1", "all_exact":True,
            "admission":saved["admission"], "callbacks":saved["callbacks"]}


class NegativeClosureTests(unittest.TestCase):
    def test_saved_matrix_and_digest_are_exact(self):
        raw = raw_from_saved(); gates = mod.validate_raw(raw)
        self.assertEqual(gates["total_rows_exact"], 702)
        self.assertEqual(mod.row_digest(raw), json.loads(REPORT.read_text())["row_digest_sha256"])

    def test_tampered_error_is_rejected(self):
        raw = copy.deepcopy(raw_from_saved()); raw["admission"][0]["actual_err"] = 0
        with self.assertRaises(RuntimeError): mod.validate_raw(raw)

    def test_tampered_counts_and_duplicate_identity_are_rejected(self):
        raw = copy.deepcopy(raw_from_saved()); raw["callbacks"][0]["callbacks"]["pre_checkout"] = 99
        with self.assertRaises(RuntimeError): mod.validate_raw(raw)

    def test_closed_raw_and_row_schema(self):
        for mutate in (
            lambda x: x.update(extra=True),
            lambda x: x.pop("all_exact"),
            lambda x: x.update(schema="wrong"),
            lambda x: x["admission"][0].update(extra=True),
            lambda x: x["admission"][0].pop("stage"),
            lambda x: x["admission"][0].update(exact=False),
            lambda x: x["admission"][0].update(pre_render_flags_exact=False),
            lambda x: x["callbacks"][0]["callbacks"].update(extra=1),
            lambda x: x["admission"].reverse(),
        ):
            raw = copy.deepcopy(raw_from_saved()); mutate(raw)
            with self.assertRaises(RuntimeError): mod.validate_raw(raw)

    def test_closed_report_identity_matrix_digest_and_claim(self):
        saved = json.loads(REPORT.read_text())
        mod.validate_report(saved)
        mutations = {
            "status":"wrong", "schema":"wrong", "production_source_sha256":"0"*64,
            "probe_source_sha256":"0"*64, "owner":"wrong", "architecture":"wrong",
            "build_commands":[], "matrix":{}, "row_digest_sha256":"0"*64, "claim_boundary":"wrong",
        }
        for key, value in mutations.items():
            bad = copy.deepcopy(saved); bad[key] = value
            with self.assertRaises(RuntimeError): mod.validate_report(bad)
        for mutate in (lambda x:x.update(extra=True), lambda x:x.pop("owner")):
            bad=copy.deepcopy(saved); mutate(bad)
            with self.assertRaises(RuntimeError): mod.validate_report(bad)
        raw = copy.deepcopy(raw_from_saved()); raw["admission"][1]["id"] = raw["admission"][0]["id"]
        with self.assertRaises(RuntimeError): mod.validate_raw(raw)


if __name__ == "__main__":
    unittest.main()
