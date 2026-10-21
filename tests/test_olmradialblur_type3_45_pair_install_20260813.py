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
GENERATOR = ROOT / "tools/emulation/audit_olmradialblur_type3_45_pair_install_20260813.py"
REPORT = ROOT / "refs/conformance/olmradialblur_type3_45_pair_install_20260813.json"
DOC = REPORT.with_suffix(".md")
GENERATOR_SHA = "6d2ac762e80dd58b6ed3a7cc795416c617634fee7cc80b32ad24b87735a538d7"
REPORT_SHA = "3b4553aa14602e098f1a67455377073e30612c241ed56ca2c99db2d598028b04"
DOC_SHA = "ca2fc08fdcae1ab606e4ea3dbb865f10c1ae4b1d4caffe7621c9eb06644470de"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    spec = importlib.util.spec_from_file_location("radial_type3_45_install_audit", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RadialType345PairInstallTest(unittest.TestCase):
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
