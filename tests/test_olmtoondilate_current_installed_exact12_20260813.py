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
GENERATOR = ROOT / "tools/emulation/test_olmtoondilate_current_installed_exact12_20260813.py"
REPORT = ROOT / "refs/conformance/olmtoondilate_current_installed_exact12_20260813.json"
MARKDOWN = ROOT / "refs/conformance/olmtoondilate_current_installed_exact12_20260813.md"
GENERATOR_SHA256 = "b991ad9ab4f452289db172e573ea7aa2f8bce277fdbe3f4ad94dbb03360ea1ae"
REPORT_SHA256 = "33eb4fe76e7f852c0a698e18eb63871343efd35e258da58359d1786146a796ed"
MARKDOWN_SHA256 = "d0fa8716275efeaf3f2c91304414ea157af8d07f68aa7520e449b9447ddf8d0c"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator():
    spec = importlib.util.spec_from_file_location("toon_installed_exact12", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class ToonCurrentInstalledExact12Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()
        cls.report = json.loads(REPORT.read_text())

    def test_default_live_read_only(self) -> None:
        before = REPORT.read_bytes()
        run = subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("PASS_TOONDILATE_CURRENT_INSTALLED_EXACT12_AE_FREE", run.stdout)
        self.assertEqual(REPORT.read_bytes(), before)

    def test_exact12_installed(self) -> None:
        self.assertEqual(len(self.report["cases"]), 12)
        self.assertEqual(self.report["architectures"], ["arm64", "x86_64"])
        self.assertEqual(set(self.report["architecture_relations"]), {"arm64", "x86_64"})
        self.assertEqual(self.report["after_effects_processes"], [])
        self.assertTrue(all(row["raw_exact"] and row["input_storage_immutable"] and row["output_padding_exact"] and row["world_headers_immutable"] for row in self.report["cases"]))

    def test_canonical_artifact_identities(self) -> None:
        self.assertEqual(sha256(GENERATOR), GENERATOR_SHA256)
        self.assertEqual(sha256(REPORT), REPORT_SHA256)
        self.assertEqual(sha256(MARKDOWN), MARKDOWN_SHA256)

    def test_unknown_and_claim_tamper_rejected(self) -> None:
        changed = copy.deepcopy(self.report); changed["extra"] = True
        with self.assertRaises(RuntimeError): self.generator.validate(changed)
        changed = copy.deepcopy(self.report); changed["scope"]["native_after_effects_host_claim"] = True
        with self.assertRaises(RuntimeError): self.generator.validate(changed)
        changed = copy.deepcopy(self.report); changed["cases"][0]["raw_exact"] = False
        with self.assertRaises(RuntimeError): self.generator.validate(changed)
        changed = copy.deepcopy(self.report); changed["cases"][0]["output_active_sha256"] = "0" * 64
        changed["cases_sha256"] = self.generator.canonical(changed["cases"])
        with self.assertRaises(RuntimeError): self.generator.validate(changed)


if __name__ == "__main__":
    unittest.main()
