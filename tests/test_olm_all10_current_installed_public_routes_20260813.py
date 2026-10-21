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
GENERATOR = ROOT / "tools/emulation/test_olm_all10_current_installed_public_routes_20260813.py"
REPORT = ROOT / "refs/conformance/olm_all10_current_installed_public_routes_20260813.json"
MARKDOWN = ROOT / "refs/conformance/olm_all10_current_installed_public_routes_20260813.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator():
    spec = importlib.util.spec_from_file_location("all10_public_routes", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class All10CurrentInstalledPublicRoutesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()
        cls.report = json.loads(REPORT.read_text())

    def test_default_is_read_only_and_live_exact(self) -> None:
        before = (REPORT.read_bytes(), MARKDOWN.read_bytes())
        run = subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("PASS_ALL10_CURRENT_INSTALLED_PUBLIC_ROUTES_AE_FREE_BOUNDED", run.stdout)
        self.assertEqual((REPORT.read_bytes(), MARKDOWN.read_bytes()), before)

    def test_exact_ten_bounded_rows(self) -> None:
        self.assertEqual(len(self.report["rows"]), 10)
        self.assertEqual([row["plugin"] for row in self.report["rows"]], sorted(self.generator.EXPECTED))
        self.assertEqual(self.report["after_effects_processes"], [])
        self.assertTrue(self.report["scope"]["heterogeneous_bounded_coverage_only"])
        self.assertTrue(self.report["scope"]["all_ten_arm64_and_x86_64_slices_replayed"])
        self.assertTrue(all(row["installed_universal_slices_replayed"] for row in self.report["rows"]))
        self.assertFalse(self.report["scope"]["all_tuples_depths_geometries_claimed"])
        self.assertFalse(self.report["scope"]["native_after_effects_claimed"])

    def test_live_report_hashes_and_identities(self) -> None:
        authority = json.loads(self.generator.AUTHORITY.read_text())
        by_name = {row["plugin"]: row for row in authority["plugins"]}
        for row in self.report["rows"]:
            self.assertEqual(sha256(ROOT / row["public_report"]), row["public_report_sha256"])
            self.assertEqual(row["source_sha256"], by_name[row["plugin"]]["source_sha256"])
            self.assertEqual(row["installed_binary_sha256"], by_name[row["plugin"]]["binary_sha256"])

    def test_unknown_keys_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["extra"] = True
        with self.assertRaises(RuntimeError):
            self.generator.validate_schema(changed)
        changed = copy.deepcopy(self.report)
        changed["rows"][0]["extra"] = True
        with self.assertRaises(RuntimeError):
            self.generator.validate_schema(changed)

    def test_report_or_status_swap_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["rows"][0]["public_report_sha256"] = changed["rows"][1]["public_report_sha256"]
        with self.assertRaises(RuntimeError):
            self.generator.validate_schema(changed)
        changed = copy.deepcopy(self.report)
        changed["rows"][0]["public_status"] = changed["rows"][1]["public_status"]
        with self.assertRaises(RuntimeError):
            self.generator.validate_schema(changed)

    def test_claim_broadening_rejected(self) -> None:
        for key in (
            "all_tuples_depths_geometries_claimed", "native_after_effects_claimed",
            "after_effects_launched", "windows_native_host_claim_generalized",
            "developer_id_or_notarization_claimed",
        ):
            changed = copy.deepcopy(self.report)
            changed["scope"][key] = True
            with self.assertRaises(RuntimeError, msg=key):
                self.generator.validate_schema(changed)

    def test_row_native_ae_and_authority_flags_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["rows"][0]["native_after_effects"] = True
        with self.assertRaises(RuntimeError):
            self.generator.validate_schema(changed)
        changed = copy.deepcopy(self.report)
        changed["rows"][0]["installed_authority_checks_all_true"] = False
        with self.assertRaises(RuntimeError):
            self.generator.validate_schema(changed)
        changed = copy.deepcopy(self.report)
        changed["rows"][0]["installed_universal_slices_replayed"] = False
        with self.assertRaises(RuntimeError):
            self.generator.validate_schema(changed)

    def test_markdown_retains_honest_boundary(self) -> None:
        text = MARKDOWN.read_text()
        self.assertIn("all ten current installed plug-ins", text)
        self.assertIn("not a claim over every tuple", text)
        self.assertIn("After Effects was not launched", text)


if __name__ == "__main__":
    unittest.main()
