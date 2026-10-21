from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/emulation/audit_olmradialblur_type3_35_pair_install_20260813.py"
REPORT = ROOT / "refs/conformance/olmradialblur_type3_35_pair_install_20260813.json"
DOC = REPORT.with_suffix(".md")
GENERATOR_SHA = "b5760a39b41d29c511cd8f4860691543825b6feaf329e24b56e5cf50b5068fd4"
REPORT_SHA = "1b633acaf882bea9cfd5797ee7306d06df2ae0bd434ced3319ba05a8442fbdf0"
DOC_SHA = "8c84f73ecad040faf5f903406d4adcc44b2ed32f8c6619f035e55f68ff7a498c"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    spec = importlib.util.spec_from_file_location("radial_type3_35_install_audit", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RadialType335PairInstallTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load()
        cls.report = json.loads(REPORT.read_text())

    def test_artifact_hashes(self):
        self.assertEqual(sha(GENERATOR), GENERATOR_SHA)
        self.assertEqual(sha(REPORT), REPORT_SHA)
        self.assertEqual(sha(DOC), DOC_SHA)

    def test_default_live_read_only(self):
        before = (REPORT.read_bytes(), DOC.read_bytes())
        run = subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(before, (REPORT.read_bytes(), DOC.read_bytes()))

    def test_installed_relation_and_scope(self):
        self.assertTrue(self.report["installed"]["candidate_installed_full_inventory_exact"])
        self.assertEqual(self.report["installed"]["old_full_inventory_exact_copies"], ["backup", "pre_swap", "moved_old"])
        self.assertEqual(self.report["all10_preflight"]["exact_bundles"], 10)
        self.assertFalse(self.report["scope"]["after_effects_launched"])
        self.assertFalse(self.report["scope"]["batched_ae_checkpoint_complete"])

    def test_tamper_rejected(self):
        for mutation in (
            lambda value: value.update(extra=True),
            lambda value: value["installed"].update(new_sha256="0" * 64),
            lambda value: value["identity_change"].update(other_nine_rows_exact=False),
            lambda value: value["all10_preflight"].update(exact_bundles=9),
            lambda value: value["scope"].update(after_effects_launched=True),
        ):
            changed = copy.deepcopy(self.report)
            mutation(changed)
            with self.assertRaises(ValueError):
                self.module.validate(changed)


if __name__ == "__main__":
    unittest.main()
