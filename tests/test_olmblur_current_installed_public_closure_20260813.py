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
GENERATOR = ROOT / "tools/emulation/test_olmblur_current_installed_public_closure_20260813.py"
REPORT = ROOT / "refs/conformance/olmblur_current_installed_public_closure_20260813.json"
MARKDOWN = REPORT.with_suffix(".md")
GENERATOR_SHA256 = "eca5def0e294b6c97499b4b77fb7b8248e81c1ec271eee9175a8db60b3406a29"
REPORT_SHA256 = "898bb7ba09785884a80be7d8ac4deaa967955c6b3e182bb8b4aa47cda45fd5dd"
MARKDOWN_SHA256 = "13f6677e0d6eb167275202ea146dea3d11f6d789399b34a7de52c3f81addee08"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    spec = importlib.util.spec_from_file_location("olmblur_installed_public", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class OLMBlurCurrentInstalledPublicClosureTest(unittest.TestCase):
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

    def test_complete_installed_relation(self) -> None:
        self.assertEqual(
            self.report["summary"],
            {
                "architectures": ["arm64", "x86_64"],
                "numerical_cells_per_slice": 6,
                "numerical_cells_total": 12,
                "positive_controls_per_slice": 12,
                "smart_render_negatives_per_slice": 91,
                "smart_pre_positive_per_slice": 1,
                "smart_pre_negatives_per_slice": 9,
                "source_built_run_byte_identical": True,
            },
        )
        self.assertEqual(self.report["run_sha256"], self.generator.RUN_SHA256)

    def test_recanonicalized_transcript_tamper_rejected(self) -> None:
        def mutate(report):
            report["run_lines"][0] += " tampered=1"
            report["run_sha256"] = hashlib.sha256(
                ("\n".join(report["run_lines"]) + "\n").encode()
            ).hexdigest()
        self.reject(mutate)

    def test_authority_summary_and_unknown_key_rejected(self) -> None:
        self.reject(lambda report: report["authorities"].__setitem__("installed_binary", "0" * 64))
        self.reject(lambda report: report["summary"].__setitem__("numerical_cells_total", 13))
        self.reject(lambda report: report.__setitem__("extra", True))

    def test_scope_escalation_rejected(self) -> None:
        self.reject(lambda report: report["scope"].__setitem__("native_after_effects", True))
        self.reject(lambda report: report["scope"].__setitem__("arbitrary_source_tuple_geometry", True))
        self.reject(lambda report: report["after_effects_processes"].append("After Effects:1"))


if __name__ == "__main__":
    unittest.main()
