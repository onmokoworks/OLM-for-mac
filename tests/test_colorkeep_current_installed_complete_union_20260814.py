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
GENERATOR = ROOT / "tools/emulation/test_colorkeep_current_installed_complete_union_20260814.py"
REPORT = ROOT / "refs/conformance/colorkeep_current_installed_complete_union_20260814.json"
NOTE = REPORT.with_suffix(".md")
SHAS = {
    GENERATOR: "582a7a0a0a6d59110be7e588113d14c0da6797a11507bd76c2119dc72b764d40",
    REPORT: "50aafd53a7cbc4309417cf0d9f3a89632e1ffcf36f2e3fdf38b92ae162a0c94a",
    NOTE: "9039ae6b59b5acbb5358c9012270e3af1419cf585fd563a261977aed6cdc9ad5",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module():
    spec = importlib.util.spec_from_file_location("colorkeep_current_union", GENERATOR)
    if not spec or not spec.loader:
        raise RuntimeError("generator import")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ColorKeepCurrentInstalledCompleteUnionTest(unittest.TestCase):
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

    def test_current_partition_and_historical_boundary(self) -> None:
        summary = self.report["summary"]
        self.assertEqual(summary["legacy_paths_per_slice"] + summary["count9_paths_per_slice"], 15)
        self.assertEqual(summary["exact_public_paths_total"], 30)
        self.assertFalse(self.report["scope"]["historical_transaction_rewritten"])
        self.assertFalse(self.report["scope"]["native_after_effects"])

    def test_recanonicalized_tamper_rejected(self) -> None:
        attacks = []
        for section, key, value in (
            ("summary", "exact_public_paths_per_slice", 14),
            ("scope", "native_after_effects", True),
            ("scope", "historical_transaction_rewritten", True),
            ("identities", "installed_binary_sha256", "0" * 64),
        ):
            changed = copy.deepcopy(self.report)
            changed[section][key] = value
            attacks.append(changed)
        runtime = copy.deepcopy(self.report)
        runtime["runtime"]["count9"]["architectures"]["arm64"]["rejects"] = 135
        attacks.append(runtime)
        claim = copy.deepcopy(self.report)
        claim["claim_boundary"] = "all ColorKeep inputs exact"
        attacks.append(claim)
        extra = copy.deepcopy(self.report)
        extra["unexpected"] = True
        attacks.append(extra)
        for attack in attacks:
            self.assertFalse(self.module.validate(attack, live=False))


if __name__ == "__main__":
    unittest.main()
