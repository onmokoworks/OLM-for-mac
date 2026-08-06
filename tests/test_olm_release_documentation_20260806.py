#!/usr/bin/env python3
"""Fail closed when release-facing claims drift from the frozen gate/package."""

from __future__ import annotations

import hashlib
import json
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROOT_README = ROOT / "README.md"
REFS_README = ROOT / "refs/README.md"
SCRIPTS_README = ROOT / "scripts/README.md"
REQUESTS_README = ROOT / "refs/reference_requests/README.md"
AGENT_GUIDE = ROOT / "AGENT_GUIDE.md"
NOTES = ROOT / "refs/conformance/OLM_MAC_RELEASE_NOTES_20260806.md"
MATRIX = ROOT / "refs/conformance/olm_release_completion_matrix_20260806.md"
STATUS = ROOT / "refs/conformance/olm_release_gate_status_20260806.json"
PACKAGE = ROOT / "refs/reference_requests/olm_windows_ae_release_boundary_minimal_20260806.zip"
PACKAGE_SHA256 = "6a060641dc867cbb5cb858136f6fd294fb49d274fa252cec71459bc9b20a4652"
EXPECTED_ROWS = {
    ("ColorKeep", "colorkeep_opaque_cells_red_darkgray", depth)
    for depth in (8, 16, 32)
} | {
    ("OLMKiraKira", "kk_mapped_bm4_mm1_hi_r5_orange_opaque", depth)
    for depth in (8, 16, 32)
} | {("OLMSmoother v1", "case_0001", 16)}


class ReleaseDocumentationConsistencyTest(unittest.TestCase):
    def test_notes_pin_host_and_do_not_promote_smoother_v1_pf32(self) -> None:
        text = NOTES.read_text(encoding="utf-8")
        for phrase in (
            "After Effects `26.3x87`",
            "CPU `SOFTWARE`",
            "Windows AE 7行だけが保留",
            "AEXにnative PF32 callbackはなく",
            "32bpc projectではAEがclassic integer pluginの前後をhost-convertする",
            "PF8 centered neutral Inner Strength 1〜64",
            "PF16 Type 3 Layerは16×16",
        ):
            self.assertIn(phrase, text)

    def test_japanese_entry_documents_point_to_current_release(self) -> None:
        documents = {
            ROOT_README: ("Macリリース候補", "release_gate_pass", "Windows AEで取得する7行"),
            REFS_README: ("日本語リリースノート", "最小7行パッケージ"),
            SCRIPTS_README: ("現在のリリース作業で使う入口", "run_olm_release_gate_20260806.py"),
            REQUESTS_README: ("現在実行するパッケージ", "取得対象は次の7行"),
            AGENT_GUIDE: ("現在の正本", "過去のpending queueを再送しない"),
        }
        for path, phrases in documents.items():
            text = path.read_text(encoding="utf-8")
            for phrase in phrases:
                self.assertIn(phrase, text, f"{path}: missing {phrase}")

    def test_release_facing_markdown_links_resolve(self) -> None:
        import re

        documents = (
            ROOT_README, REFS_README, SCRIPTS_README, REQUESTS_README,
            AGENT_GUIDE, NOTES,
        )
        broken = []
        for path in documents:
            text = path.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
                if "://" in target or target.startswith("#"):
                    continue
                resolved = (path.parent / target.split("#", 1)[0]).resolve()
                if not resolved.exists():
                    broken.append((str(path.relative_to(ROOT)), target))
        self.assertEqual(broken, [])

    def test_matrix_has_no_superseded_release_holes(self) -> None:
        text = MATRIX.read_text(encoding="utf-8")
        self.assertNotIn("**Missing Inner representative**", text)
        self.assertNotIn("Real production/host hole", text)
        self.assertIn("PF8 Inner is geometry-generic only inside its admitted", text)
        self.assertIn("PF16 Type3 Layer is exact only for 16x16", text)

    def test_gate_and_seven_row_package_match_release_notes(self) -> None:
        status = json.loads(STATUS.read_text(encoding="utf-8"))
        self.assertEqual(status["status"], "release_gate_pass")
        self.assertTrue(status["releasable"])
        self.assertEqual(status["mac_ae_representative"]["counts"], {
            "invalid": 0, "pending": 0, "proven": 10,
        })
        self.assertEqual(status["universal_installs"]["bundle_count"], 10)
        self.assertEqual(hashlib.sha256(PACKAGE.read_bytes()).hexdigest(), PACKAGE_SHA256)
        with zipfile.ZipFile(PACKAGE) as archive:
            contract = json.loads(archive.read("BATCH_CONTRACT.json"))
        rows = {(r["plugin"], r["case_id"], r["depth"]) for r in contract["acquire"]}
        self.assertEqual(rows, EXPECTED_ROWS)


if __name__ == "__main__":
    unittest.main()
