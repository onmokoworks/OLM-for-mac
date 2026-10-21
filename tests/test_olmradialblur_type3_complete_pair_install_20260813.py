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
GENERATOR = ROOT / "tools/emulation/audit_olmradialblur_type3_complete_pair_install_20260813.py"
REPORT = ROOT / "refs/conformance/olmradialblur_type3_complete_pair_install_20260813.json"
DOC = REPORT.with_suffix(".md")
GENERATOR_SHA = "5cbf20d9ea2ca0ce0223e5fa036a32006ccfa5446240b8a6b4587ac076e91875"
REPORT_SHA = "6098ae99c4c378eca6eff4e2b46bd1bc89192295357d12bfe4afd6f8b3d528d4"
DOC_SHA = "875e3b6d50b5dedb074c3462fa6a13a7df8aef978a2d997a16eafab41e9875b1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    spec = importlib.util.spec_from_file_location("radial_type3_install_audit", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RadialType3CompletePairInstallTest(unittest.TestCase):
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
