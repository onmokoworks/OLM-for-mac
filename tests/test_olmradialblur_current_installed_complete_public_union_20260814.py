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
GENERATOR = ROOT / "tools/emulation/test_olmradialblur_current_installed_complete_public_union_20260814.py"
REPORT = ROOT / "refs/conformance/olmradialblur_current_installed_complete_public_union_20260814.json"
NOTE = REPORT.with_suffix(".md")
SHAS = {
    GENERATOR: "348c0b80f6770019380e25487ae8501d28214d798d5c6889e9ca8d4947f63f27",
    REPORT: "083bdaf45321bba8753627cb479bc5499d80077ba570262dd744d203fd3dee18",
    NOTE: "c422a8454117d12d43909af5ff620802550904ae19e0b3343231d4186b3bdcf3",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module():
    spec = importlib.util.spec_from_file_location("radial_complete_union", GENERATOR)
    if not spec or not spec.loader:
        raise RuntimeError("generator import")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RadialInstalledCompletePublicUnionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()
        cls.report = json.loads(REPORT.read_text())

    def test_hashes_and_live_validation(self) -> None:
        for path, expected in SHAS.items():
            self.assertEqual(sha256(path), expected)
        self.assertTrue(self.module.validate(self.report))

    def test_default_is_read_only(self) -> None:
        before = (REPORT.read_bytes(), NOTE.read_bytes())
        run = subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual((REPORT.read_bytes(), NOTE.read_bytes()), before)

    def test_partition_and_boundary(self) -> None:
        summary = self.report["summary"]
        self.assertEqual(summary["type1_cells_per_slice"] + summary["type3_cells_per_slice"], 151)
        self.assertEqual(summary["exact_public_cells_total"], 302)
        self.assertEqual(summary["installed_architectures"], ["arm64", "x86_64"])
        self.assertFalse(self.report["scope"]["native_after_effects"])
        self.assertFalse(self.report["scope"]["arbitrary_type1_or_type3"])

    def test_recanonicalized_claim_identity_and_count_tamper_rejected(self) -> None:
        attacks = []
        for section, key, value in (
            ("summary", "exact_public_cells_per_slice", 150),
            ("summary", "classic_smart_padded_output_exact", False),
            ("scope", "native_after_effects", True),
            ("identities", "installed_binary_sha256", "0" * 64),
            ("closures", "type1", "wrong.json"),
        ):
            changed = copy.deepcopy(self.report)
            changed[section][key] = value
            attacks.append(changed)
        claim = copy.deepcopy(self.report)
        claim["claim_boundary"] = "all Radial inputs are exact"
        attacks.append(claim)
        extra = copy.deepcopy(self.report)
        extra["unexpected"] = True
        attacks.append(extra)
        for attack in attacks:
            self.assertFalse(self.module.validate(attack))


if __name__ == "__main__":
    unittest.main()
