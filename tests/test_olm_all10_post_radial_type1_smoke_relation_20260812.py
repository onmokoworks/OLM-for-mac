from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/audit_olm_all10_post_radial_type1_smoke_relation_20260812.py"
REPORT = ROOT / "refs/conformance/olm_all10_post_radial_type1_smoke_relation_20260812.json"


def load():
    spec = importlib.util.spec_from_file_location("post_radial_type1_smoke_relation", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PostRadialType1SmokeRelation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load()
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def reject(self, mutation):
        report = copy.deepcopy(self.report)
        mutation(report)
        with self.assertRaises(AssertionError):
            self.module.validate(report)

    def test_validate(self):
        self.module.validate(copy.deepcopy(self.report))

    def test_post_radial_summary_tamper(self):
        self.reject(lambda report: report["bindings"]["post_radial_summary"].__setitem__("sha256", "0" * 64))

    def test_post_radial_raw_tamper(self):
        self.reject(lambda report: report["bindings"]["post_radial_raw"].__setitem__("sha256", "0" * 64))

    def test_identity_tamper(self):
        self.reject(lambda report: report["bindings"]["identity_manifest"].__setitem__("sha256", "0" * 64))

    def test_incremental_install_tamper(self):
        self.reject(lambda report: report["bindings"]["radial_incremental_install"].__setitem__("sha256", "0" * 64))

    def test_runner_tamper(self):
        self.reject(lambda report: report["bindings"]["producer_runner"].__setitem__("sha256", "0" * 64))

    def test_payload_tamper(self):
        self.reject(lambda report: report["bindings"]["producer_payload"].__setitem__("sha256", "0" * 64))

    def test_durable_artifact_set_tamper(self):
        self.reject(lambda report: report["durable_artifacts"].__setitem__("canonical_sha256", "0" * 64))

    def test_preserved_distance_summary_tamper(self):
        self.reject(lambda report: report["bindings"]["preserved_distance_summary"].__setitem__("sha256", "0" * 64))

    def test_preserved_distance_raw_tamper(self):
        self.reject(lambda report: report["bindings"]["preserved_distance_raw"].__setitem__("sha256", "0" * 64))

    def test_distance_substitution_claim_tamper(self):
        self.reject(lambda report: report["relations"].__setitem__("distance_snapshot_substitution_rejected", False))

    def test_radial_identity_tamper(self):
        self.reject(lambda report: report["relations"].__setitem__("radial_executable_sha256", "0" * 64))


if __name__ == "__main__":
    unittest.main()
