from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/emulation/audit_olmdirectionalblur_testseam_install_20260814.py"
spec = importlib.util.spec_from_file_location("directional_testseam_install", GENERATOR)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DirectionalTestSeamInstallClosureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(module.REPORT.read_text())

    def test_live_and_default_read_only(self) -> None:
        self.assertTrue(module.validate(self.report))
        before = (module.REPORT.read_bytes(), module.NOTE.read_bytes())
        run = subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(before, (module.REPORT.read_bytes(), module.NOTE.read_bytes()))

    def test_recanonicalized_tampering_fails_closed(self) -> None:
        mutations = (
            lambda r: r.update(extra=True),
            lambda r: r["identities"].update(candidate_authority_sha256="0" * 64),
            lambda r: r["binary"].update(new_sha256="0" * 64),
            lambda r: r["binary"]["backup_binary_sha256"].update(installed_backup="0" * 64),
            lambda r: r["transaction"].update(same_volume_atomic_exchange=False),
            lambda r: r["transaction"].update(identity_relation_directional_only=False),
            lambda r: r["scope"].update(after_effects_launched=True),
            lambda r: r["scope"].update(native_ae_numerical_claim=True),
        )
        for mutate in mutations:
            value = copy.deepcopy(self.report)
            mutate(value)
            self.assertFalse(module.validate(value, live=False))


if __name__ == "__main__":
    unittest.main()
