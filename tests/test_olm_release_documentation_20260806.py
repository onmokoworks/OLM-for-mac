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
KNOWN_LIMITATIONS = ROOT / "KNOWN_LIMITATIONS.md"
LEDGER = ROOT / "notes/CONFORMANCE_LEDGER.md"
REFS_README = ROOT / "refs/README.md"
SCRIPTS_README = ROOT / "scripts/README.md"
REQUESTS_README = ROOT / "refs/reference_requests/README.md"
AGENT_GUIDE = ROOT / "AGENT_GUIDE.md"
NOTES = ROOT / "refs/conformance/OLM_MAC_RELEASE_NOTES_20260806.md"
MATRIX = ROOT / "refs/conformance/olm_release_completion_matrix_20260806.md"
STATUS = ROOT / "refs/conformance/olm_release_gate_status_20260806.json"
GATE_MANIFEST = ROOT / "refs/conformance/olm_release_gate_manifest_20260806.json"
IDENTITY_MANIFEST = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
CURRENT_SMOKE = ROOT / "refs/conformance/olm_all10_post_colorkeep_count9_fresh_ae_smoke_20260813.json"
CURRENT_SMOKE_RAW = ROOT / "refs/conformance/olm_all10_post_colorkeep_count9_fresh_ae_smoke_raw_20260813.json"
CURRENT_SMOKE_RUNNER = ROOT / "scripts/run_olm_all10_current_install_fresh_ae_smoke_20260812.py"
COUNT9_CLOSURE = ROOT / "refs/conformance/colorkeep_nine_color_public_closure_20260813.json"
COUNT9_INSTALL = ROOT / "refs/conformance/colorkeep_source_bound_complete_union_install_20260813.json"
FIXED_FIXTURE_RUNNER = ROOT / "scripts/run_olm_mac_fixed_fixture_regression_20260805.py"
DIRECTIONAL_HISTORICAL_SUMMARY = ROOT / "refs/conformance/olmdirectionalblur_type2_natural64_current_install_smoke_20260812.json"
DIRECTIONAL_HISTORICAL_DOC = ROOT / "refs/conformance/olmdirectionalblur_type2_natural64_current_install_smoke_20260812.md"
EXPECTED_STATUS_SHA256 = "99fef44827d81746b00587dce150fd14b1bef7685d32a374a701ebcb3fb46e87"
EXPECTED_COLORKEEP_SOURCE_SHA256 = "d1c443042998e466b021d6fd2351537a2be63fe95d3e79a2089d82f78217bac3"
EXPECTED_COLORKEEP_INSTALLED_SHA256 = "dae59a6faf54ed18ac803ad042be2cdab688c5f814edf322d64c108d5247f46d"
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
    def test_colorkeep_count9_four_boundaries_are_current_and_bounded(self) -> None:
        closure = json.loads(COUNT9_CLOSURE.read_text(encoding="utf-8"))
        install = json.loads(COUNT9_INSTALL.read_text(encoding="utf-8"))
        smoke = json.loads(CURRENT_SMOKE.read_text(encoding="utf-8"))
        status = json.loads(STATUS.read_text(encoding="utf-8"))

        self.assertEqual(closure["identity"]["production_sha256"], EXPECTED_COLORKEEP_SOURCE_SHA256)
        self.assertEqual(closure["negative"]["rejects"], 136)
        stages = [row["stage"] for row in closure["negative"]["cases"]]
        self.assertEqual(stages.count("pre-iterate"), 131)
        self.assertEqual(stages.count("iterate"), 5)
        self.assertIn("exact 4x3/padding8 worlds", closure["claim_boundary"])
        self.assertIn("91-color default opaque-black inactive tail", closure["claim_boundary"])
        self.assertIn("Existing 11x7 count5/100 lanes remain separate", closure["claim_boundary"])
        self.assertEqual(
            {(row["path"], row["depth"]) for row in closure["public_paths"]},
            {
                ("Classic", "PF8"), ("Classic", "PF16"),
                ("Smart", "PF8"), ("Smart", "PF16"), ("Smart", "PF32"),
            },
        )

        self.assertEqual(install["authorities"]["production_source_sha256"], EXPECTED_COLORKEEP_SOURCE_SHA256)
        installed = install["bundles"]["installed"]
        self.assertEqual(installed["binary_sha256"], EXPECTED_COLORKEEP_INSTALLED_SHA256)
        self.assertEqual(installed["info_plist_minimum_system_version"], "11.0")
        self.assertEqual(installed["macho_slice_minimum_versions"], {"arm64": "11.0", "x86_64": "11.0"})
        self.assertEqual(len(install["identity_transition"]["unchanged_plugins"]), 9)

        color_keep = next(row for row in smoke["plugins"] if row["plugin"] == "ColorKeep")
        self.assertTrue(color_keep["loaded"])
        self.assertTrue(color_keep["applied"])
        self.assertEqual(color_keep["loaded_module_count"], 1)
        self.assertTrue(color_keep["post_render_mapping_exact"])
        self.assertTrue(color_keep["effect_disabled_during_host_frame"])
        self.assertFalse(color_keep["effect_enabled_numerical_render_attempted"])
        self.assertFalse(color_keep["numerical_render_supported"])
        self.assertIsNone(color_keep["numerical_render_succeeded"])

        self.assertEqual(hashlib.sha256(STATUS.read_bytes()).hexdigest(), EXPECTED_STATUS_SHA256)
        self.assertEqual(status["status"], "release_gate_pending_or_invalid")
        self.assertFalse(status["releasable"])
        self.assertEqual(status["universal_installs"]["state"], "proven")
        self.assertEqual(status["mac_ae_representative"]["counts"], {
            "invalid": 10, "pending": 0, "proven": 0,
        })

        documents = (ROOT_README, KNOWN_LIMITATIONS, LEDGER, NOTES, MATRIX)
        for path in documents:
            text = path.read_text(encoding="utf-8")
            for evidence in (
                "colorkeep_nine_color_public_closure_20260813",
                "colorkeep_source_bound_complete_union_install_20260813",
                "olm_all10_post_colorkeep_count9_fresh_ae_smoke_20260813",
            ):
                self.assertIn(evidence, text, f"{path}: missing {evidence}")
            self.assertIn("136", text, f"{path}: missing reject boundary")
            self.assertIn("Classic PF32", text, f"{path}: missing fail-close boundary")
        for path in (ROOT_README, KNOWN_LIMITATIONS, LEDGER, NOTES):
            text = path.read_text(encoding="utf-8")
            self.assertIn("131", text, f"{path}: missing pre-iterate count")
            self.assertIn("5", text, f"{path}: missing iterate-failure count")

        combined = "\n".join(path.read_text(encoding="utf-8") for path in documents)
        self.assertNotIn("現行installed bundleは旧binaryのままです", combined)
        self.assertNotIn("post_distance_power_failclose_fresh_ae_smoke_20260812.json` is\n  the current release input", combined)
        self.assertNotIn("ColorKeep count9 native-AE numerical exact", combined)

        fixed_runner = FIXED_FIXTURE_RUNNER.read_text(encoding="utf-8")
        self.assertIn("test_colorkeep_nine_color_public_closure_20260813.py", fixed_runner)
        self.assertIn("tests.test_colorkeep_nine_color_public_closure_20260813", fixed_runner)

        identity_rows = {
            row["plugin"]: row
            for row in json.loads(IDENTITY_MANIFEST.read_text(encoding="utf-8"))["plugins"]
        }
        directional_current = identity_rows["OLMDirectionalBlur"]["sha256"]
        directional_smoke = next(
            row for row in smoke["plugins"] if row["plugin"] == "OLMDirectionalBlur"
        )
        # The retained smoke is intentionally historical after batch5.  Do not
        # rewrite it or pretend that it observed the newly installed binary.
        self.assertNotEqual(directional_smoke["installed_executable_sha256"], directional_current)
        self.assertNotEqual(directional_smoke["post_render_on_disk_sha256"], directional_current)
        self.assertFalse(directional_smoke["effect_enabled_numerical_render_attempted"])
        self.assertFalse(directional_smoke["numerical_render_expected"])
        self.assertFalse(directional_smoke["numerical_render_supported"])
        self.assertIsNone(directional_smoke["numerical_render_succeeded"])
        historical = json.loads(DIRECTIONAL_HISTORICAL_SUMMARY.read_text(encoding="utf-8"))
        self.assertNotEqual(historical["installed_bundle"]["binary_sha256"], directional_current)
        historical_doc = DIRECTIONAL_HISTORICAL_DOC.read_text(encoding="utf-8")
        self.assertIn("historical install", historical_doc)
        self.assertIn("superseded identity", historical_doc)
        self.assertIn("current install証拠ではありません", historical_doc)
        self.assertIn("pixel exact", historical_doc)
        self.assertIn("行わない", historical_doc)

    def test_notes_pin_host_and_do_not_promote_smoother_v1_pf32(self) -> None:
        text = NOTES.read_text(encoding="utf-8")
        for phrase in (
            "After Effects `26.3x87`",
            "CPU `SOFTWARE`",
            "Windows AE 7行は取得・受領検証済み",
            "Win/Mac pixel equality",
            "AEXにnative PF32 callbackはなく",
            "32bpc projectではAEがclassic integer pluginの前後をhost-convertする",
            "PF8 centered neutral Inner Strength 1〜64",
            "現行release integrationの正本",
            "7／7 accepted、0 invalid、0 pending",
            "PF32 Zoom、固定9×7／rowbytes 160／NV25",
        ):
            self.assertIn(phrase, text)

    def test_radial_type1_supersession_and_incremental_timestamp_boundary(self) -> None:
        notes = NOTES.read_text(encoding="utf-8")
        matrix = MATRIX.read_text(encoding="utf-8")
        combined = "\n".join((notes, matrix))
        for phrase in (
            "olmradialblur_rotation_type1_inverse_cell_closure_20260812",
            "olmradialblur_type1_incremental_install_identity_20260812",
            "olm_all10_post_radial_type1_smoke_relation_20260812",
            "2026-08-12 11:05:06 UTC",
            "03e837e8...d548",
            "all-ten baseline",
            "Radial-row-only",
            "top-levelの2時刻と非Radial 9行だけを維持",
            "Radial行の2 hash fieldを更新",
            "formal gate inputsもpost-Radial smokeへretarget済み",
            "preserves only the two top-level timestamps and the nine",
            "updates the Radial row's two hash fields",
            "inputs are retargeted to the post-Radial smoke",
        ):
            self.assertIn(phrase, combined)
        self.assertIn("旧sampled-source-scalar ULP seam", notes)
        self.assertIn("raw exactへ更新", notes)
        for stale_current in (
            "sampled source scalarには1〜4 ULP差が残る",
            "source scalarに既知の1〜4 ULP差があります",
            "各ケース1326／8186 float中に既知の1 ULP差",
            "source scalarに残る診断ULP差",
        ):
            self.assertNotIn(stale_current, combined)

    def test_japanese_entry_documents_point_to_current_release(self) -> None:
        documents = {
            ROOT_README: ("現行インストールidentity", "valid_for", "Windows AEで取得する7行"),
            REFS_README: ("日本語リリースノート", "受領済みWindows 7観測の固定契約"),
            SCRIPTS_README: ("現在のリリース作業で使う入口", "run_olm_release_gate_20260806.py"),
            REQUESTS_README: ("受領済みの最小7行パッケージ", "受領対象だった7行"),
            AGENT_GUIDE: ("現在の正本", "7／7 accepted", "受領済み7行を再送しない"),
        }
        for path, phrases in documents.items():
            text = path.read_text(encoding="utf-8")
            for phrase in phrases:
                self.assertIn(phrase, text, f"{path}: missing {phrase}")
        entry_text = "\n".join(path.read_text(encoding="utf-8") for path in documents)
        self.assertIn("7／7 accepted", entry_text)
        for stale in ("保留中のWindows 7観測", "7行が返るまでは"):
            self.assertNotIn(stale, entry_text)

    def test_release_facing_markdown_links_resolve(self) -> None:
        import re

        documents = (
            ROOT_README, KNOWN_LIMITATIONS, LEDGER, REFS_README, SCRIPTS_README,
            REQUESTS_README, AGENT_GUIDE, NOTES, MATRIX,
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
        for stale in (
            "exactly seven pending",
            "final same-contract Windows AE calibration is still pending",
            "Type 3 output boundary is not closed",
        ):
            self.assertNotIn(stale, text)
        for current in (
            "7 observations accepted, 0 invalid, 0 pending",
            "Classic and Smart: the same 14 named 5x3 tuples",
            "Current source `b74b3d2c...b0d1` retains fixed 9x7/NV25 Type 3",
            "Universal minOS11 binary `9be59d18...76b5` is full-inventory exact",
            "native-AE numerical exactness is not claimed",
        ):
            self.assertIn(current, text)

    def test_release_state_language_matches_saved_gate(self) -> None:
        status = json.loads(STATUS.read_text(encoding="utf-8"))
        readme = ROOT_README.read_text(encoding="utf-8")
        notes = NOTES.read_text(encoding="utf-8")
        matrix = MATRIX.read_text(encoding="utf-8")
        combined = "\n".join((readme, notes, matrix))
        self.assertIn("2026-08-14時点で", readme)
        current_smoke_path = status["valid_for"]["current_host_smoke_path"]
        self.assertIn(current_smoke_path, notes)
        self.assertIn(current_smoke_path, matrix)
        for stale in (
            "fresh smoke artifact待ち",
            "while missing, the release status",
            "until that fresh artifact exists",
            "現行formal gateはpost-Kira smokeへretarget済み",
            "olm_all10_post_distance_power_failclose_fresh_ae_smoke_20260812.json` is\n  the current release input",
        ):
            self.assertNotIn(stale, combined)
        if status["releasable"]:
            self.assertEqual(status["status"], "release_gate_pass")
            self.assertIn("最終Mac統合ゲート：`release_gate_pass`", readme)
            self.assertIn("現行full release gateは`release_gate_pass`", notes)
            self.assertIn("Full release gate: `release_gate_pass`", matrix)
        else:
            self.assertEqual(status["status"], "release_gate_pending_or_invalid")
            self.assertIn("`release_gate_pending_or_invalid`", readme)
            self.assertIn("full gateが完走するまで", notes)
            self.assertIn("pending/invalid until a full gate run", matrix)

    def test_gate_and_seven_row_package_match_release_notes(self) -> None:
        status = json.loads(STATUS.read_text(encoding="utf-8"))
        valid_for = status["valid_for"]
        bindings = (
            ("release_manifest", GATE_MANIFEST),
            ("installed_identity_manifest", IDENTITY_MANIFEST),
            ("current_host_smoke", CURRENT_SMOKE),
            ("current_host_smoke_raw", CURRENT_SMOKE_RAW),
            ("current_host_smoke_runner", CURRENT_SMOKE_RUNNER),
            ("release_gate_runner", ROOT / "scripts/run_olm_release_gate_20260806.py"),
            ("windows_boundary_intake", ROOT / "refs/conformance/olm_windows_ae_release_boundary_minimal_intake_20260806.json"),
        )
        expected_valid_for_keys = {
            f"{prefix}_{suffix}"
            for prefix, _ in bindings
            for suffix in ("path", "sha256")
        }
        self.assertEqual(set(valid_for), expected_valid_for_keys)
        digest_mismatches = []
        for prefix, path in bindings:
            self.assertEqual(valid_for[f"{prefix}_path"], path.relative_to(ROOT).as_posix())
            if path.is_file():
                live_sha = hashlib.sha256(path.read_bytes()).hexdigest()
                if status["releasable"]:
                    self.assertEqual(valid_for[f"{prefix}_sha256"], live_sha)
                elif valid_for[f"{prefix}_sha256"] != live_sha:
                    digest_mismatches.append(prefix)
            else:
                self.assertFalse(status["releasable"])
                self.assertIsNone(valid_for[f"{prefix}_sha256"])
        if not status["releasable"]:
            self.assertTrue(
                digest_mismatches
                or status["fixed_fixture_regression"]["state"] != "proven"
                or status["mac_ae_representative"]["counts"]["invalid"] > 0
            )
        self.assertEqual(json.loads(GATE_MANIFEST.read_text())["schema"], "olm.release-gate-manifest/2")
        self.assertEqual(status["windows_ae_release_boundary"]["accepted_rows"], 7)
        self.assertEqual(
            status["windows_ae_release_boundary"]["state"],
            "accepted_bounded_plugin_comparisons_complete",
        )
        if status["releasable"]:
            import importlib.util
            spec = importlib.util.spec_from_file_location("fresh_smoke", CURRENT_SMOKE_RUNNER)
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            summary = json.loads(CURRENT_SMOKE.read_text(encoding="utf-8"))
            raw = json.loads(CURRENT_SMOKE_RAW.read_text(encoding="utf-8"))
            self.assertTrue(module.validate_persisted_summary(summary, raw, CURRENT_SMOKE_RAW))
            self.assertEqual(status["status"], "release_gate_pass")
            self.assertEqual(status["mac_ae_representative"]["counts"], {
                "invalid": 0, "pending": 0, "proven": 10,
            })
            self.assertEqual(status["fixed_fixture_regression"]["state"], "proven")
        else:
            self.assertEqual(status["status"], "release_gate_pending_or_invalid")
        self.assertEqual(status["universal_installs"]["bundle_count"], 10)
        self.assertEqual(hashlib.sha256(PACKAGE.read_bytes()).hexdigest(), PACKAGE_SHA256)
        with zipfile.ZipFile(PACKAGE) as archive:
            contract = json.loads(archive.read("BATCH_CONTRACT.json"))
        rows = {(r["plugin"], r["case_id"], r["depth"]) for r in contract["acquire"]}
        self.assertEqual(rows, EXPECTED_ROWS)


if __name__ == "__main__":
    unittest.main()
