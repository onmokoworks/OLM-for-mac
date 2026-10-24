from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ColorKeyPublicSourceBoundDocs(unittest.TestCase):
    def test_authoritative_chain(self) -> None:
        expected = {
            "mac/OLMColorKey/OLMColorKey.cpp": "4dbd264501a0d5d990a3726d16223c01c1996677b925f8546157b6a91ce677d1",
            "mac/OLMColorKey/Mac/OLMColorKey.xcodeproj/project.pbxproj": "b5b77f24dec0a1ec9d426c20d68384f03d3381145f1494fec59c491bcec2d72b",
            "tools/emulation/test_olmcolorkey_public_source_bound_closure_20260813.py": "8d30702c279a87633084572d0e9e729b2c0c629bfb6118da1c2ff682713dbbd8",
            "refs/conformance/olmcolorkey_public_source_bound_closure_20260813.json": "423d1ea02e5aa40b78264ba7ba4cfd28ff42fde472f0d6ff99ba33ef7514a4a0",
            "handoffs/olmcolorkey_toggle24_universal_candidate_20260814/build_identity.json": "f768e6b3413e4b6ebaee285ea478040a26311c7a6ff8e3b33b0d2dacf728bdec",
        }
        self.assertEqual({path: sha(ROOT / path) for path in expected}, expected)

    def test_claim_scope_and_counts(self) -> None:
        report = json.loads((ROOT / "refs/conformance/olmcolorkey_public_source_bound_closure_20260813.json").read_text())
        self.assertEqual(len(report["canonical_rows"]), 63)
        self.assertEqual(report["lifecycle"]["classic_positive_cells"], 63)
        self.assertEqual(report["lifecycle"]["smart_positive_cells"], 63)
        self.assertEqual(report["negative_closure"]["source_tuple_world_atomic_cases"], 567)
        self.assertEqual(report["negative_closure"]["smart_callback_error_or_throw_cases"], 13)
        self.assertFalse(report["scope"]["native_after_effects"])
        self.assertFalse(report["scope"]["installed_binary"])
        self.assertFalse(report["scope"]["arbitrary_source_or_tuple"])

    def test_release_docs_name_current_boundary(self) -> None:
        docs = {
            "docs/archive/README_20260822.md": ("OLMColorKey 63セル", "Classic／Smart各63セル"),
            "docs/archive/KNOWN_LIMITATIONS_20260822.md": ("Classic／Smart各63セル", "installed版は60セル"),
            "notes/CONFORMANCE_LEDGER.md": ("OLMColorKey fixed-source public-entry closure", "Direct arm64 and Rosetta x86_64"),
            "refs/conformance/OLM_MAC_RELEASE_NOTES_20260806.md": ("Classic／Smart両public route", "Classic 63／Smart 63"),
            "refs/conformance/olm_release_completion_matrix_20260806.md": ("Classic and Smart: exact-source Edge Blur", "701ae919"),
            "refs/conformance/olm_mac_port_orchestrator_boundary_20260805.md": ("fixed-source raw exact for 63 named cells", "intentionally deferred"),
        }
        for path, needles in docs.items():
            text = (ROOT / path).read_text()
            for needle in needles:
                self.assertIn(needle, text, f"{path}: {needle}")

    def test_official_lane_uses_read_only_current_closure(self) -> None:
        runner = (ROOT / "scripts/run_olm_mac_fixed_fixture_regression_20260805.py").read_text()
        self.assertIn('test_olmcolorkey_public_source_bound_closure_20260813.py", "--validate-only"', runner)
        self.assertIn("test_olmcolorkey_current_installed_public_closure_20260813.py", runner)
        self.assertIn("tests.test_olmcolorkey_public_entries_real_sdk_20260813", runner)
        self.assertNotIn("olmcolorkey_toggle24_universal_candidate_20260814/test_build_identity.py", runner)
        self.assertNotIn("audit_olmcolorkey_toggle24_transactional_install_20260814.py", runner)
        self.assertNotIn('"tools/emulation/audit_olmcolorkey_pf16_edge_blur_internal_plane_20260805.py"', runner)


if __name__ == "__main__":
    unittest.main()
