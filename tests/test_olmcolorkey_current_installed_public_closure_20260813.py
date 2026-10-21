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
GENERATOR = ROOT / "tools/emulation/test_olmcolorkey_current_installed_public_closure_20260813.py"
REPORT = ROOT / "refs/conformance/olmcolorkey_current_installed_public_closure_20260813.json"
MARKDOWN = REPORT.with_suffix(".md")
GENERATOR_SHA256 = "729b8603fff1e284f9f4dfa4510744ea33ad4566fcbbaa5d1ed4327d895c443f"
REPORT_SHA256 = "3c32200f9c2590ad21e259fe961292004337c4f04bfac5350760e4eb7568b333"
MARKDOWN_SHA256 = "95c75f7f5cc512c4549fff4b9f464932713ee9a3f63cf110e4cb136f8736095d"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    spec = importlib.util.spec_from_file_location("olmcolorkey_installed_public", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class OLMColorKeyCurrentInstalledPublicClosureTest(unittest.TestCase):
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
        before = (REPORT.read_bytes(), MARKDOWN.read_bytes())
        run = subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn(self.generator.STATUS, run.stdout)
        self.assertEqual(before, (REPORT.read_bytes(), MARKDOWN.read_bytes()))

    def test_canonical_artifact_hashes(self) -> None:
        self.assertEqual(sha256(GENERATOR), GENERATOR_SHA256)
        self.assertEqual(sha256(REPORT), REPORT_SHA256)
        self.assertEqual(sha256(MARKDOWN), MARKDOWN_SHA256)

    def test_both_slices_complete(self) -> None:
        self.assertEqual(self.report["slice_runs"], {"arm64": self.generator.RUN, "x86_64": self.generator.RUN})
        self.assertEqual(self.report["summary"]["classic_cells_per_slice"], 60)
        self.assertEqual(self.report["summary"]["smart_cells_per_slice"], 60)
        self.assertEqual(self.report["summary"]["callback_negatives_per_slice"], 13)

    def test_slice_transcript_tamper_rejected(self) -> None:
        self.reject(lambda report: report["slice_runs"]["arm64"].__setitem__("stdout_sha256", "0" * 64))
        self.reject(lambda report: report["slice_runs"]["x86_64"].__setitem__("stdout_bytes", 0))

    def test_authority_summary_and_unknown_key_rejected(self) -> None:
        self.reject(lambda report: report["authorities"].__setitem__("installed_binary", "0" * 64))
        self.reject(lambda report: report["summary"].__setitem__("classic_cells_per_slice", 35))
        self.reject(lambda report: report.__setitem__("extra", True))

    def test_scope_escalation_rejected(self) -> None:
        self.reject(lambda report: report["scope"].__setitem__("native_after_effects", True))
        self.reject(lambda report: report["scope"].__setitem__("arbitrary_source_tuple_geometry", True))
        self.reject(lambda report: report["after_effects_processes"].append("After Effects:1"))


if __name__ == "__main__":
    unittest.main()
