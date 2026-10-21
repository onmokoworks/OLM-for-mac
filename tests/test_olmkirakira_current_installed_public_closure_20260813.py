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
GENERATOR = ROOT / "tools/emulation/test_olmkirakira_current_installed_public_closure_20260813.py"
REPORT = ROOT / "refs/conformance/olmkirakira_current_installed_public_closure_20260813.json"
MARKDOWN = REPORT.with_suffix(".md")
GENERATOR_SHA256 = "bb6bbe20dc1588c3e7bb53f875f73db713a18f04b7492da1cf30d77e0f16e94b"
REPORT_SHA256 = "9bc2b377a99e1391844efe5dccf9c4232f40e38a3e72b55ceedc7d63db29f0cf"
MARKDOWN_SHA256 = "f32519b2033eb3efe550dda270fc30120534d8e0d2c0180ce444af5969014d4e"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    spec = importlib.util.spec_from_file_location("kira_installed_public", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class KiraCurrentInstalledPublicClosureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load()
        cls.report = json.loads(REPORT.read_text())

    def reject(self, mutation) -> None:
        changed = copy.deepcopy(self.report)
        mutation(changed)
        with self.assertRaises(RuntimeError):
            self.generator.validate(changed)

    def test_default_live_read_only(self) -> None:
        before = REPORT.read_bytes()
        run = subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn(self.generator.STATUS, run.stdout)
        self.assertEqual(REPORT.read_bytes(), before)

    def test_canonical_artifact_hashes(self) -> None:
        self.assertEqual(sha256(GENERATOR), GENERATOR_SHA256)
        self.assertEqual(sha256(REPORT), REPORT_SHA256)
        self.assertEqual(sha256(MARKDOWN), MARKDOWN_SHA256)

    def test_complete_installed_relation(self) -> None:
        self.assertEqual(len(self.report["positive_cells"]), 42)
        self.assertEqual(self.report["negative_relation"]["row_count"], 765)
        self.assertEqual(len(self.report["request_controls"]), 3)
        self.assertEqual(set(self.report["architecture_relations"]), {"arm64", "x86_64"})
        self.assertTrue(self.report["scope"]["installed_x86_64"])
        self.assertEqual(self.report["after_effects_processes"], [])

    def test_positive_recanonicalization_rejected(self) -> None:
        def mutate(row):
            row["positive_cells"][0]["smart_sha256"] = "0" * 64
            row["positive_cells_sha256"] = self.generator.load_base().canonical(row["positive_cells"])
        self.reject(mutate)

    def test_negative_and_authority_tamper_rejected(self) -> None:
        self.reject(lambda row: row["negative_relation"].__setitem__("rows_sha256", "0" * 64))
        self.reject(lambda row: row["architecture_relations"]["x86_64"].__setitem__("negative_rows", 764))
        self.reject(lambda row: row["authorities"].__setitem__("installed_binary", "0" * 64))
        self.reject(lambda row: row.__setitem__("extra", True))

    def test_scope_escalation_rejected(self) -> None:
        self.reject(lambda row: row["scope"].__setitem__("native_after_effects", True))
        self.reject(lambda row: row["scope"].__setitem__("arbitrary_tuple_source_geometry", True))


if __name__ == "__main__":
    unittest.main()
