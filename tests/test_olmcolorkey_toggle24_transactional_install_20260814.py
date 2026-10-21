from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDITOR = ROOT / "tools/emulation/audit_olmcolorkey_toggle24_transactional_install_20260814.py"
REPORT = ROOT / "refs/conformance/olmcolorkey_toggle24_transactional_install_20260814.json"
DOC = REPORT.with_suffix(".md")
EXPECTED_AUDITOR = "1e50c4771dad27888b946fe4460d27906ba61590012750d42f1edb05377c5438"
EXPECTED_REPORT = "5eeec71c1f35420ca8904e145ed939f77b46a355eb4d9a86148ad465219f0851"
EXPECTED_DOC = "2e2cc50f9609d8777b2c1d7b6bfa5b9c9ff8b079bbc4dffa10ef61bfbb7e4baf"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    spec = importlib.util.spec_from_file_location("colorkey_install_audit_test", AUDITOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ColorKeyToggle24TransactionalInstall(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if sha(AUDITOR) != EXPECTED_AUDITOR:
            raise AssertionError("auditor identity drift")
        cls.auditor = load()
        cls.report = json.loads(REPORT.read_text())

    def reject(self, mutation) -> None:
        changed = copy.deepcopy(self.report)
        mutation(changed)
        with self.assertRaises(RuntimeError):
            self.auditor.validate(changed)

    def test_default_is_read_only_and_live_exact(self):
        before = (REPORT.read_bytes(), DOC.read_bytes())
        result = subprocess.run([sys.executable, str(AUDITOR)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(before, (REPORT.read_bytes(), DOC.read_bytes()))

    def test_canonical_hashes(self):
        self.assertEqual(sha(REPORT), EXPECTED_REPORT)
        self.assertEqual(sha(DOC), EXPECTED_DOC)

    def test_bundle_identity_chain(self):
        self.assertEqual(self.report["installed_predecessor"]["retained_full_bundle_copies"], 3)
        self.assertTrue(self.report["installed_predecessor"]["full_inventories_exact"])
        self.assertTrue(self.report["installed_candidate"]["candidate_installed_full_inventory_exact"])
        self.assertEqual(self.report["identity_transition"]["changed_plugins"], ["OLMColorKey"])
        self.assertTrue(self.report["identity_transition"]["other_nine_rows_exact"])

    def test_all10_two_pass_ae_free(self):
        self.assertEqual(self.report["all10_preflight"]["passes"], 2)
        self.assertTrue(self.report["all10_preflight"]["byte_identical"])
        self.assertEqual(self.report["all10_preflight"]["status"], "ae_not_running")
        self.assertEqual(self.report["after_effects_processes"], [])

    def test_recanonicalized_tamper_fails_closed(self):
        self.reject(lambda report: report.__setitem__("extra", True))
        self.reject(lambda report: report["authorities"].__setitem__("production_source", "0" * 64))
        self.reject(lambda report: report["installed_candidate"].__setitem__("binary_sha256", "0" * 64))
        self.reject(lambda report: report["identity_transition"].__setitem__("changed_plugins", ["OLMColorKey", "OLMSmoother2"]))
        self.reject(lambda report: report["all10_preflight"].__setitem__("passes", 1))
        self.reject(lambda report: report["claims_not_made"].append("AE launched"))


if __name__ == "__main__":
    unittest.main()
