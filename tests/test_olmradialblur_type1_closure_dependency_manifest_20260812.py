#!/usr/bin/env python3
"""Current-workspace handoff checks for the Radial Rotation Type-1 chain."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "refs/conformance/olmradialblur_type1_closure_dependency_manifest_20260812.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Type1WorkspaceHandoffDependencyManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_manifest_identity_and_self_artifacts(self) -> None:
        self.assertEqual(
            self.manifest["schema"],
            "olm.radialblur-type1-workspace-handoff-dependency-manifest/1",
        )
        self.assertEqual(self.manifest["status"], "COMPLETE_WORKSPACE_HANDOFF_CHAIN")
        boundary = self.manifest["claim_boundary"]
        self.assertIn("Current workspace artifacts", boundary)
        self.assertIn("git tracked or clean-checkout availability is not claimed", boundary)
        for relative in self.manifest["self_artifacts"]:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_all_pinned_dependencies_exist_and_match(self) -> None:
        entries = self.manifest["exact_files"] + self.manifest["release_consumers"]
        self.assertEqual(len({entry["path"] for entry in entries}), len(entries))
        for entry in entries:
            path = ROOT / entry["path"]
            self.assertTrue(path.is_file(), entry["path"])
            self.assertEqual(sha256(path), entry["sha256"], entry["path"])

    def test_release_consumers_name_the_new_chain(self) -> None:
        for consumer in self.manifest["release_consumers"]:
            text = (ROOT / consumer["path"]).read_text(encoding="utf-8")
            for token in consumer["required_text"]:
                self.assertIn(token, text, f"{consumer['path']}: {token}")

    def test_old_ulp_language_is_not_a_current_claim(self) -> None:
        stale_exact = {
            "KNOWN_LIMITATIONS.md": (
                "sampled source scalarには1〜4 ULP差が残る",
                "SV25 diagnostic source scalarには既知1 ULP差",
            ),
            "refs/conformance/OLM_MAC_RELEASE_NOTES_20260806.md": (
                "source scalarに既知の1〜4 ULP差があります",
                "各ケース1326／8186 float中に既知の1 ULP差",
                "source scalarに残る診断ULP差",
            ),
            "notes/CONFORMANCE_LEDGER.md": (
                "current limitation: sampled-source scalar 1-4 ULP",
                "current limitation: inactive-only Type-1",
            ),
        }
        for relative, phrases in stale_exact.items():
            text = (ROOT / relative).read_text(encoding="utf-8")
            for phrase in phrases:
                self.assertNotIn(phrase, text, f"stale current wording in {relative}")

    def test_reports_form_one_hash_bound_chain(self) -> None:
        relations = self.manifest["relations"]
        closure = json.loads((ROOT / relations["closure_report"]).read_text(encoding="utf-8"))
        install = json.loads((ROOT / relations["incremental_install_report"]).read_text(encoding="utf-8"))
        smoke = json.loads((ROOT / relations["post_radial_smoke_relation"]).read_text(encoding="utf-8"))

        self.assertEqual(
            closure["production_source_sha256"],
            relations["current_production_source_sha256"],
        )
        self.assertEqual(
            closure["core_sampler_source"]["sha256"],
            relations["core_sampler_source_sha256"],
        )
        self.assertEqual(
            install["production_source_sha256"],
            relations["historical_install_source_sha256"],
        )
        self.assertNotEqual(
            relations["current_production_source_sha256"],
            relations["historical_install_source_sha256"],
        )
        self.assertEqual(
            install["core_header_sha256"],
            relations["core_sampler_source_sha256"],
        )
        self.assertEqual(
            install["bundles"]["installed"]["binary_sha256"],
            relations["installed_radial_executable_sha256"],
        )
        self.assertEqual(
            smoke["relations"]["radial_executable_sha256"],
            relations["installed_radial_executable_sha256"],
        )
        install_binding = smoke["bindings"]["radial_incremental_install"]
        self.assertEqual(install_binding["path"], relations["incremental_install_report"])
        self.assertEqual(
            install_binding["sha256"],
            sha256(ROOT / relations["incremental_install_report"]),
        )

    def test_manifest_does_not_expand_into_gate_or_live_host_actions(self) -> None:
        boundary = self.manifest["claim_boundary"]
        self.assertIn("does not rerun AE", boundary)
        self.assertIn("formal release gate", boundary)
        paths = {entry["path"] for entry in self.manifest["exact_files"]}
        self.assertNotIn("refs/conformance/olm_release_gate_status_20260806.json", paths)
        self.assertNotIn("refs/conformance/olm_release_gate_manifest_20260806.json", paths)

    def test_install_metadata_and_signing_claims_are_narrow(self) -> None:
        evidence = self.manifest["install_evidence_boundary"]
        self.assertIn("observed retained-bundle bytes", evidence["backup_flags"])
        self.assertIn("provided transaction metadata", evidence["backup_flags"])
        self.assertIn("do not independently prove the historical ditto invocation", evidence["backup_flags"])
        self.assertIn("strict validation of an ad-hoc signature", evidence["signing"])
        self.assertIn("not a Developer ID signature or Apple notarization claim", evidence["signing"])

    def test_incremental_timestamp_is_not_misrepresented_as_all_ten_acceptance(self) -> None:
        install = json.loads(
            (ROOT / self.manifest["relations"]["incremental_install_report"]).read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(install["generated_at"], "2026-08-12T11:05:06.285179+00:00")
        notes = (ROOT / "refs/conformance/OLM_MAC_RELEASE_NOTES_20260806.md").read_text(
            encoding="utf-8"
        )
        matrix = (ROOT / "refs/conformance/olm_release_completion_matrix_20260806.md").read_text(
            encoding="utf-8"
        )
        for text in (notes, matrix):
            self.assertIn("all-ten baseline", text)
            self.assertIn("Radial-row-only", text)
            self.assertIn("2026-08-12 11:05:06 UTC", text)
        self.assertIn("top-levelの2時刻と非Radial 9行だけを維持", notes)
        self.assertIn("Radial行の2 hash fieldを更新", notes)
        self.assertIn("formal gate inputsもpost-Radial smokeへretarget済み", notes)
        self.assertIn("preserves only the two top-level timestamps and the nine", matrix)
        self.assertIn("updates the Radial row's two hash fields", matrix)
        self.assertIn("inputs are retargeted to the post-Radial smoke", matrix)


if __name__ == "__main__":
    unittest.main()
