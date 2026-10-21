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
GENERATOR = ROOT / "tools/emulation/test_olmradialblur_current_installed_type3_all_depth_closure_20260813.py"
REPORT = ROOT / "refs/conformance/olmradialblur_current_installed_type3_all_depth_closure_20260813.json"
MARKDOWN = REPORT.with_suffix(".md")
GENERATOR_SHA256 = "4d0abe91390ca9114fc1300faedb99bc1f00a3bde19f26f84cf3190a64ff344a"
REPORT_SHA256 = "2e06b303db9541789f2b9d88de38310968859e9d3d0e5bf03d5ce8c5c70e3c6f"
MARKDOWN_SHA256 = "3701432a69194f74c89cc7d7d236e61514d7a65ab8b01b56d6fd46564f1803f0"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    spec = importlib.util.spec_from_file_location("radial_installed_type3", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class RadialCurrentInstalledType3AllDepthTest(unittest.TestCase):
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

    def test_both_slices_complete_45_pair_matrix_and_reject_controls(self) -> None:
        self.assertEqual(len(self.report["rows"]), 90)
        self.assertEqual(
            {(row["architecture"], row["depth"]) for row in self.report["rows"]},
            {(arch, depth) for arch in ("arm64", "x86_64") for depth in (8, 16, 32)},
        )
        self.assertTrue(all(row["padded_output_exact"] for row in self.report["rows"]))
        self.assertTrue(all(row["reject_controls"] for row in self.report["rows"]))
        self.assertEqual(self.report["summary"]["bounded_reject_control_sets_per_slice"], 45)
        self.assertEqual(self.report["summary"]["public_exact_cells_total"], 90)
        self.assertTrue(self.report["summary"]["classic_smart_direct_owner_exact"])

    def test_recanonicalized_row_tamper_rejected(self) -> None:
        def mutate(report):
            report["rows"][0]["installed_smart_sha256"] = "0" * 64
            report["rows_sha256"] = self.generator.canonical(report["rows"])
        self.reject(mutate)

    def test_authority_summary_and_unknown_key_rejected(self) -> None:
        self.reject(lambda report: report["authorities"].__setitem__("installed_binary", "0" * 64))
        self.reject(lambda report: report["summary"].__setitem__("public_exact_cells_total", 7))
        self.reject(lambda report: report.__setitem__("extra", True))

    def test_scope_escalation_rejected(self) -> None:
        self.reject(lambda report: report["scope"].__setitem__("native_after_effects", True))
        self.reject(lambda report: report["scope"].__setitem__("installed_x86_64", False))
        self.reject(lambda report: report["after_effects_processes"].append("After Effects:1"))


if __name__ == "__main__":
    unittest.main()
