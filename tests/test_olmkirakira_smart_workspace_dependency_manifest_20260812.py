#!/usr/bin/env python3
"""Live dependency and relation checks for the bounded Kira Smart closure."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.emulation.olm_assets import resolve_asset

import copy
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "refs/conformance/olmkirakira_smart_workspace_dependency_manifest_20260812.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class KiraSmartWorkspaceDependencyManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_manifest_scope_and_nonrecursive_self_artifacts(self) -> None:
        self.assertEqual(
            self.manifest["schema"],
            "olm.kirakira-smart-workspace-dependency-manifest/1",
        )
        self.assertEqual(self.manifest["status"], "CURRENT_WORKSPACE_CHAIN_HASH_BOUND")
        boundary = self.manifest["claim_boundary"]
        self.assertIn("Current workspace artifacts", boundary)
        self.assertIn("git tracked state", boundary)
        self.assertIn("git cleanliness", boundary)
        self.assertIn("clean-checkout availability are not claimed", boundary)
        self.assertIn("No plugin install", boundary)
        self.assertIn("After Effects host run", boundary)
        pinned = {entry["path"] for entry in self.manifest["exact_files"]}
        for relative in self.manifest["self_artifacts"]:
            self.assertTrue((ROOT / relative).is_file(), relative)
            self.assertNotIn(relative, pinned, "self artifact must not recursively hash itself")

    def test_all_dependency_hashes_match_live_workspace(self) -> None:
        entries = self.manifest["exact_files"]
        self.assertEqual(len(entries), 27)
        self.assertEqual(len({entry["path"] for entry in entries}), len(entries))
        for entry in entries:
            path = ROOT / entry["path"]
            self.assertTrue(path.is_file(), entry["path"])
            self.assertEqual(sha256(path), entry["sha256"], entry["path"])

    def test_each_hash_is_a_tamper_gate(self) -> None:
        for entry in self.manifest["exact_files"]:
            live = (ROOT / entry["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(live).hexdigest(), entry["sha256"])
            tampered = live + b"\x00"
            self.assertNotEqual(hashlib.sha256(tampered).hexdigest(), entry["sha256"])

    def test_smart_report_and_guard_form_one_live_hash_chain(self) -> None:
        relations = self.manifest["relations"]
        smart_path = ROOT / relations["smart_report"]
        guard_path = ROOT / relations["classic_smart_guard_report"]
        smart = json.loads(smart_path.read_text(encoding="utf-8"))
        guard = json.loads(guard_path.read_text(encoding="utf-8"))
        self.assertEqual(sha256(smart_path), relations["smart_report_sha256"])
        self.assertEqual(sha256(guard_path), relations["classic_smart_guard_report_sha256"])
        self.assertEqual(
            smart["identities"]["production_source_sha256"],
            relations["production_source_sha256"],
        )
        self.assertEqual(guard["source_sha256"], relations["production_source_sha256"])
        self.assertEqual(guard["smart"]["evidence_sha256"], relations["smart_report_sha256"])
        self.assertEqual(
            guard["smart"]["canonical_cells_sha256"],
            smart["canonical_cells_sha256"],
        )
        self.assertEqual(
            guard["smart"]["canonical_negative_rows_sha256"],
            smart["canonical_negative_rows_sha256"],
        )
        self.assertEqual(smart["canonical_cells_sha256"], relations["smart_canonical_cells_sha256"])
        self.assertEqual(
            smart["canonical_negative_rows_sha256"],
            relations["smart_canonical_negative_rows_sha256"],
        )
        self.assertEqual(smart["identities"]["aex_sha256"], relations["windows_aex_sha256"])
        self.assertEqual(
            smart["identities"]["aexcompat_worker_sha256"],
            relations["aexcompat_worker_sha256"],
        )
        self.assertEqual(smart["identities"]["aexcompat_commit"], relations["aexcompat_commit"])

    def test_manifest_pins_the_guard_complete_evidence_set(self) -> None:
        guard = json.loads(
            (ROOT / self.manifest["relations"]["classic_smart_guard_report"]).read_text(
                encoding="utf-8"
            )
        )
        guard_evidence = {row["path"]: row["sha256"] for row in guard["evidence"]}
        manifest_guard_evidence = {
            entry["path"]: entry["sha256"]
            for entry in self.manifest["exact_files"]
            if entry["role"].startswith("guard evidence ")
        }
        self.assertEqual(len(manifest_guard_evidence), 12)
        self.assertEqual(manifest_guard_evidence, guard_evidence)
        pf8 = "refs/conformance/olmkirakira_pf8_source_decode_closure_20260812.json"
        pf8_entry = next(
            entry for entry in self.manifest["exact_files"] if entry["path"] == pf8
        )
        self.assertEqual(sha256(ROOT / pf8), pf8_entry["sha256"])

    def test_windows_static_callback_slots_have_exact_anchors(self) -> None:
        abi = self.manifest["windows_callback_abi"]
        assembly = (resolve_asset(ROOT / "disasm/OLMKiraKira.aex.asm.txt")).read_text(encoding="utf-8")
        start = assembly.index("; === FUN_18114c8f0 @ 18114c8f0 ===")
        end = assembly.index("; === FUN_18114ca70 @ 18114ca70 ===", start)
        owner = assembly[start:end]
        self.assertEqual(abi["checkout_layer_pixels"]["callback_slot"], "+0x0")
        self.assertEqual(abi["checkout_output"]["callback_slot"], "+0x10")
        for name in ("checkout_layer_pixels", "checkout_output"):
            for token in abi[name]["anchor_tokens"]:
                self.assertIn(token, owner)
        checkin = abi["checkin_layer_pixels"]
        self.assertEqual(checkin["callback_slot"], "+0x8")
        self.assertFalse(checkin["called"])
        self.assertIn("no load-and-call through callback-table slot +0x8", checkin["dedicated_evidence"])
        self.assertNotIn("MOV R9,qword ptr [RAX + 0x8]", owner)

    def test_sdk_callback_order_and_optional_checkin_match_static_claim(self) -> None:
        abi = self.manifest["windows_callback_abi"]
        header = (resolve_asset(ROOT / "Headers/AE_Effect.h")).read_text(encoding="utf-8")
        start = header.index("PF_Err (*checkout_layer_pixels)(")
        end = header.index("} PF_SmartRenderCallbacks;", start)
        declaration = header[start:end]
        offsets = [declaration.index(name) for name in abi["sdk_field_order"]]
        self.assertEqual(offsets, sorted(offsets))
        self.assertTrue(abi["sdk_checkin_is_optional"])
        self.assertIn("not strictly necessary to call", declaration)

    def test_dynamic_common_owner_json_binds_same_aex(self) -> None:
        dynamic = json.loads(
            (ROOT / "refs/conformance/olmkirakira_mode2_common_owner_20260717.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(dynamic["common_owner"]["function"], "FUN_18114c8f0")
        self.assertEqual(dynamic["inputs"]["aex_sha256"], self.manifest["relations"]["windows_aex_sha256"])
        self.assertFalse(dynamic["ae_exact_claim"])

    def test_relation_tamper_is_detectable_even_if_a_copy_is_rewritten(self) -> None:
        bad = copy.deepcopy(self.manifest)
        bad["relations"]["smart_report_sha256"] = "0" * 64
        live = sha256(ROOT / bad["relations"]["smart_report"])
        self.assertNotEqual(live, bad["relations"]["smart_report_sha256"])

    def test_runner_contract_includes_read_only_smart_and_guard_validation(self) -> None:
        runners = self.manifest["runners"]
        self.assertIn("--validate-only", runners["smart_validate_only"])
        self.assertIn("--validate-only", runners["guard_validate_only"])
        self.assertIn("test_olmkirakira_public_smart_bounded_closure", runners["smart_unit"])
        self.assertIn("test_olmkirakira_classic_smart_admission_guard", runners["guard_unit"])

        fixed_fixture_runner = (
            ROOT / "scripts/run_olm_mac_fixed_fixture_regression_20260805.py"
        ).read_text(encoding="utf-8")
        for command in runners.values():
            tokens = command.split()
            target = next(
                token
                for token in tokens
                if token.startswith("tools/") or token.startswith("tests.")
            )
            self.assertIn(target, fixed_fixture_runner)


if __name__ == "__main__":
    unittest.main()
