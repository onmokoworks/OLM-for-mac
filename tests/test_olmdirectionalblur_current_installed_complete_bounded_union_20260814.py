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
GENERATOR = ROOT / "tools/emulation/test_olmdirectionalblur_current_installed_complete_bounded_union_20260814.py"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_current_installed_complete_bounded_union_20260814.json"
NOTE = REPORT.with_suffix(".md")
SHAS = {
    GENERATOR: "05cae46d7ef1425f03372d6e34f4bcbb7ee0e4a445a387b2286d98a93546ad0f",
    REPORT: "f1fd17c51ccd42d0c1491c926e763462a6dfba300690880c92cfb4fa25c002b9",
    NOTE: "8b80f54654a1a708163df561e1c96d3a7d0294b6542cfd382578b33c1aff95b5",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module():
    spec = importlib.util.spec_from_file_location("directional_complete_union", GENERATOR)
    if not spec or not spec.loader:
        raise RuntimeError("generator import")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DirectionalInstalledCompleteBoundedUnionTest(unittest.TestCase):
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

    def test_exact_failclosed_partition(self) -> None:
        summary = self.report["summary"]
        self.assertEqual((summary["arm64_exact_cells"], summary["arm64_fail_closed_cells"]), (33, 0))
        self.assertEqual((summary["x86_64_exact_cells"], summary["x86_64_fail_closed_cells"]), (27, 6))
        self.assertEqual(summary["missing_native_ucrt_counts"], [8, 50, 100])
        self.assertEqual(self.report["runtime_sha256"], self.module.digest(self.report["runtime"]))
        self.assertFalse(self.report["scope"]["native_after_effects"])

    def test_recanonicalized_runtime_claim_identity_tamper_rejected(self) -> None:
        attacks = []
        runtime = copy.deepcopy(self.report)
        runtime["runtime"]["dual_side_exported_boundary"]["x86_64_fail_closed"] = 5
        runtime["runtime_sha256"] = self.module.digest(runtime["runtime"])
        attacks.append(runtime)
        for section, key, value in (
            ("summary", "x86_64_fail_closed_cells", 0),
            ("scope", "native_after_effects", True),
            ("scope", "arbitrary_source_tuple_geometry", True),
            ("identities", "installed_binary_sha256", "0" * 64),
        ):
            changed = copy.deepcopy(self.report)
            changed[section][key] = value
            attacks.append(changed)
        claim = copy.deepcopy(self.report)
        claim["claim_boundary"] = "all cells exact on both slices"
        attacks.append(claim)
        extra = copy.deepcopy(self.report)
        extra["unexpected"] = True
        attacks.append(extra)
        for attack in attacks:
            self.assertFalse(self.module.validate(attack, live=False))


if __name__ == "__main__":
    unittest.main()
