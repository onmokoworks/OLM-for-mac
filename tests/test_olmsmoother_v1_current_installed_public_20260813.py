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
GENERATOR = ROOT / "tools/emulation/test_olmsmoother_v1_current_installed_public_20260813.py"
REPORT = ROOT / "refs/conformance/olmsmoother_v1_current_installed_public_20260813.json"
MARKDOWN = REPORT.with_suffix(".md")
GENERATOR_SHA256 = "91aef0fd8fc63631e3dfa614eda7fefcae90f34607b9600b6af02939d8c68756"
REPORT_SHA256 = "5840cd6afd2ff99a3cb97e5ab12cc0b9674857eb44594bf1d381fbd69711d082"
MARKDOWN_SHA256 = "b7177972dcf6c46fc67b0283f426ba5ce25f7a1ba5a0efe508374eb7816c3197"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    spec = importlib.util.spec_from_file_location("olmsmoother_v1_installed", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class OLMSmootherV1CurrentInstalledPublicTest(unittest.TestCase):
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
        self.assertEqual(before, (REPORT.read_bytes(), MARKDOWN.read_bytes()))

    def test_canonical_hashes(self) -> None:
        self.assertEqual(sha256(GENERATOR), GENERATOR_SHA256)
        self.assertEqual(sha256(REPORT), REPORT_SHA256)
        self.assertEqual(sha256(MARKDOWN), MARKDOWN_SHA256)

    def test_relation(self) -> None:
        self.assertEqual(self.report["summary"], self.generator.SUMMARY)
        self.assertEqual(self.report["run_sha256"], self.generator.RUN_SHA256)
        self.assertEqual(self.report["summary"]["architectures"], ["arm64", "x86_64"])
        self.assertEqual(self.report["summary"]["positive_cells_total"], 6)

    def test_recanonicalized_transcript_rejected(self) -> None:
        def mutation(report):
            report["run_lines"][0] += " altered=1"
            report["run_sha256"] = hashlib.sha256(("\n".join(report["run_lines"]) + "\n").encode()).hexdigest()
        self.reject(mutation)

    def test_authority_summary_unknown_rejected(self) -> None:
        self.reject(lambda report: report["authorities"].__setitem__("source", "0" * 64))
        self.reject(lambda report: report["summary"].__setitem__("positive_cells_total", 7))
        self.reject(lambda report: report.__setitem__("extra", True))

    def test_scope_escalation_rejected(self) -> None:
        self.reject(lambda report: report["scope"].__setitem__("native_after_effects", True))
        self.reject(lambda report: report["scope"].__setitem__("complete_admission_union", True))
        self.reject(lambda report: report["after_effects_processes"].append("After Effects:1"))


if __name__ == "__main__":
    unittest.main()
