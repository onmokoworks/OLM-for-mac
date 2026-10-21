#!/usr/bin/env python3
"""Focused smoke tests for the consolidated Windows owner retry v2 packager."""

from __future__ import annotations

import importlib.util
import hashlib
import json
import subprocess
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "package_windows_codex_owner_retry_v2_20260730.py"
SPEC = importlib.util.spec_from_file_location("retry_v2", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)
ORIGINAL = ROOT / "refs/handoffs/windows_codex_batches_20260728/olm_windows_batch_20260728_r1.zip"


class RetryV2Smoke(unittest.TestCase):
    def write_canonical_zip(self, output: Path, members: dict[str, bytes], *, archive_comment: bytes = b""):
        members = dict(members)
        members["CHECKSUMS.sha256"] = "".join(
            f"{hashlib.sha256(members[name]).hexdigest()}  {name}\n"
            for name in sorted(members)
        ).encode()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            archive.comment = archive_comment
            for name in sorted(members):
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = (0o100644 << 16)
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, members[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    def make_fake_return(self, request: Path, output: Path, *, zip_suffix: bool = False, bom: bool = False, duplicate_path: bool = False):
        with zipfile.ZipFile(request) as archive:
            request_manifest = archive.read("REQUEST_MANIFEST.json")
            return_contract = archive.read("RETURN_CONTRACT.json")
            validator = archive.read("validate_windows_owner_retry_return_v2_20260730.py")
        lanes = []
        members = {
            "REQUEST_MANIFEST.json": request_manifest,
            "RETURN_CONTRACT.json": return_contract,
        }
        for lane_id in (
            "radial_cleanup_20260730_v2",
            "directional_store_render_20260730_v2",
            "dg_raw_typed_coordinate_20260730_v2",
        ):
            suffix = "claim.ZIP" if zip_suffix else "claim.json"
            path = f"lanes/{lane_id}/{suffix}"
            data = json.dumps({"claim": "answered", "all_gates": True}).encode()
            members[path] = data
            lane_record = {
                "id": lane_id,
                "status": "answered",
                "claims": {"ae_exact": True},
                "gates": {"same_run_raw_runtime": True, "exact_owned_process": True},
                "evidence": [{
                    "path": path,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "kind": "claim_only",
                }],
            }
            if duplicate_path:
                lane_record["evidence"].append({**lane_record["evidence"][0], "kind": "second_claim"})
            lanes.append(lane_record)
        record = json.dumps(
            {"schema": "olm_windows_owner_retry_return_v2_20260730", "lanes": lanes},
            sort_keys=True,
        ).encode()
        members["RETURN_MANIFEST.json"] = (b"\xef\xbb\xbf" + record) if bom else record
        self.write_canonical_zip(output, members)
        validator_path = output.with_suffix(".validator.py")
        validator_path.write_bytes(validator)
        return validator_path

    def make_identical_artifact_fake(self, request: Path, output: Path):
        with zipfile.ZipFile(request) as archive:
            request_manifest = archive.read("REQUEST_MANIFEST.json")
            return_contract = archive.read("RETURN_CONTRACT.json")
            validator = archive.read("validate_windows_owner_retry_return_v2_20260730.py")
        request_sha = hashlib.sha256(request_manifest).hexdigest()
        def chunk(kind, payload):
            return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)
        png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00\xff")) + chunk(b"IEND", b"")
        members = {"REQUEST_MANIFEST.json": request_manifest, "RETURN_CONTRACT.json": return_contract}
        lane_ids = ("radial_cleanup_20260730_v2", "directional_store_render_20260730_v2", "dg_raw_typed_coordinate_20260730_v2")
        lanes = []
        for lane_id in lane_ids:
            binding = {
                "schema": "olm_same_run_binding_v2_20260730", "request_manifest_sha256": request_sha,
                "run_id": "r1", "project_sha256": "1"*64, "case_id": "case", "afterfx_pid": 123,
                "afterfx_creation_time": "time", "aex_path": "C:/x.aex", "aex_sha256": "2"*64,
                "aex_base": "0x1", "renderer": "classic", "bit_depth": 8, "source_sha256": "3"*64,
            }
            evidence = []
            def add(kind, name, payload):
                data = payload if isinstance(payload, bytes) else json.dumps(payload, sort_keys=True).encode()
                path = f"lanes/{lane_id}/{name}"
                members[path] = data
                evidence.append({"path": path, "sha256": hashlib.sha256(data).hexdigest(), "kind": kind})
            add("binding_json", "binding.json", binding)
            add("process_identity_json", "process.json", {"schema":"olm_exact_owned_process_v2_20260730","binding":binding,"executable_path":"AfterFX.exe","command_line":"owned","parent_pid":1,"run_nonce":"n"})
            add("module_identity_json", "module.json", {"schema":"olm_loaded_aex_identity_v2_20260730","binding":binding,"installed_path":"C:/x.aex","loaded_path":"C:/x.aex","loaded_sha256":"2"*64,"loaded_base":"0x1"})
            add("no_effect_image", "control.png", png)
            add("effect_image", "effect.png", png)
            add("raw_image_comparison_json", "compare.json", {"schema":"olm_raw_image_comparison_v2_20260730","binding":binding,"no_effect_sha256":hashlib.sha256(png).hexdigest(),"effect_sha256":hashlib.sha256(png).hexdigest(),"raw_comparison_performed":True,"images_differ":True,"metrics":{}})
            add("cleanup_json", "cleanup.json", {"schema":"olm_exact_owned_cleanup_v2_20260730","binding":binding,"identity_revalidated":True,"cleanup_complete":True,"unrelated_processes_touched":False})
            if lane_id.startswith("radial"):
                add("radial_raw_sampler_json","raw.json",{"schema":"olm_radial_raw_sampler_v2_20260730","binding":binding,"coordinates":[1,2],"sampler_words":[1],"cdb_detached":True})
            elif lane_id.startswith("directional"):
                add("directional_raw_store_json","raw.json",{"schema":"olm_directional_raw_store_v2_20260730","binding":binding,"coordinate":[494,169],"writer_rva":"x","target_address":"x","pre_bytes":"00","post_bytes":"01","thread_id":"1","breakpoint_slot":"0"})
            else:
                add("dg_raw_entry_json","raw.json",{"schema":"olm_dg_raw_entry_v2_20260730","binding":binding,"rip":"x","rcx":"x","rdx":"x","r8":"x","r9":"x","rsp_20":"x","rsp_28":"x","rsp_30":"x","stack_trace":"x","disassembly":"x","address_info":"x","lmvm":"x","raw_entry_hit_count":1})
                add("dg_typed_coordinate_json","typed.json",{"schema":"olm_dg_typed_coordinate_v2_20260730","binding":binding,"typed_hit_count":1,"coordinate_contract":"x"})
            lanes.append({"id":lane_id,"status":"answered","claims":{"ae_exact":True},"evidence":evidence})
        members["RETURN_MANIFEST.json"] = json.dumps({"schema":"olm_windows_owner_retry_return_v2_20260730","lanes":lanes}, sort_keys=True).encode()
        self.write_canonical_zip(output, members)
        validator_path = output.with_suffix(".validator.py")
        validator_path.write_bytes(validator)
        return validator_path

    def test_deterministic_and_self_validating(self):
        with tempfile.TemporaryDirectory() as temp:
            one = Path(temp) / "one.zip"
            two = Path(temp) / "two.zip"
            MODULE.build(ORIGINAL, one)
            MODULE.build(ORIGINAL, two)
            self.assertEqual(one.read_bytes(), two.read_bytes())
            result = MODULE.validate_request(one)
            self.assertEqual(result["status"], "accepted")
            with zipfile.ZipFile(one) as archive:
                names = archive.namelist()
                self.assertEqual(names, sorted(names))
                readme = archive.read("README_FIRST.md").decode()
                self.assertIn("CLI exact never substitutes for AE exact", readme)
                self.assertIn("no-effect control and effect output", readme)
                self.assertIn("three lane `run.ps1`", readme)
                self.assertIn("fail closed", readme)
                checks = archive.read("CHECKSUMS.sha256").decode().splitlines()
                self.assertEqual(
                    [line.split("  ", 1)[1] for line in checks],
                    sorted(name for name in names if name != "CHECKSUMS.sha256"),
                )
                compile(
                    archive.read("pack_windows_owner_retry_return_v2_20260730.py"),
                    "pack_windows_owner_retry_return_v2_20260730.py",
                    "exec",
                )
                compile(
                    archive.read("validate_windows_owner_retry_return_v2_20260730.py"),
                    "validate_windows_owner_retry_return_v2_20260730.py",
                    "exec",
                )

    def test_checksum_order_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            good = Path(temp) / "good.zip"
            bad = Path(temp) / "bad.zip"
            MODULE.build(ORIGINAL, good)
            with zipfile.ZipFile(good) as source, zipfile.ZipFile(bad, "w") as target:
                for info in source.infolist():
                    data = source.read(info)
                    if info.filename == "CHECKSUMS.sha256":
                        lines = data.decode().splitlines()
                        data = ("\n".join(reversed(lines)) + "\n").encode()
                    target.writestr(info, data)
            with self.assertRaisesRegex(MODULE.ContractError, "lexical order"):
                MODULE.validate_request(bad)

    def test_reviewer_fake_claim_only_return_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            request = Path(temp) / "request.zip"
            fake = Path(temp) / "fake.zip"
            MODULE.build(ORIGINAL, request)
            validator = self.make_fake_return(request, fake)
            result = subprocess.run(
                [sys.executable, str(validator), str(fake)],
                text=True, capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing common raw same-run evidence kinds", result.stderr)

    def test_uppercase_zip_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            request = Path(temp) / "request.zip"
            fake = Path(temp) / "fake.zip"
            MODULE.build(ORIGINAL, request)
            validator = self.make_fake_return(request, fake, zip_suffix=True)
            result = subprocess.run(
                [sys.executable, str(validator), str(fake)],
                text=True, capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid direct evidence path", result.stderr)

    def test_utf8_bom_return_manifest_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            request = Path(temp) / "request.zip"
            fake = Path(temp) / "fake.zip"
            MODULE.build(ORIGINAL, request)
            validator = self.make_fake_return(request, fake, bom=True)
            result = subprocess.run(
                [sys.executable, str(validator), str(fake)],
                text=True, capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("BOM/UTF-16/UTF-32 forbidden", result.stderr)

    def test_duplicate_direct_evidence_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            request = Path(temp) / "request.zip"
            fake = Path(temp) / "fake.zip"
            MODULE.build(ORIGINAL, request)
            validator = self.make_fake_return(request, fake, duplicate_path=True)
            result = subprocess.run([sys.executable, str(validator), str(fake)], text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("evidence path referenced more than once", result.stderr)

    def test_identical_artifacts_with_bogus_images_differ_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            request = Path(temp) / "request.zip"
            fake = Path(temp) / "identical_fake.zip"
            MODULE.build(ORIGINAL, request)
            validator = self.make_identical_artifact_fake(request, fake)
            result = subprocess.run([sys.executable, str(validator), str(fake)], text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("control/effect artifacts must be distinct", result.stderr)

    def test_archive_comment_breaks_byte_canonical_return(self):
        with tempfile.TemporaryDirectory() as temp:
            request = Path(temp) / "request.zip"
            fake = Path(temp) / "fake.zip"
            MODULE.build(ORIGINAL, request)
            validator = self.make_fake_return(request, fake)
            with zipfile.ZipFile(fake) as source:
                members = {name: source.read(name) for name in source.namelist() if name != "CHECKSUMS.sha256"}
            self.write_canonical_zip(fake, members, archive_comment=b"hidden-comment")
            result = subprocess.run([sys.executable, str(validator), str(fake)], text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not byte-canonical", result.stderr)

    def test_reparse_guard_checks_volume_root_before_descendants_and_handles_root_workroot(self):
        with tempfile.TemporaryDirectory() as temp:
            request = Path(temp) / "request.zip"
            MODULE.build(ORIGINAL, request)
            with zipfile.ZipFile(request) as archive:
                script = archive.read("RUN_WINDOWS_CODEX_OWNER_RETRY_V2_20260730.ps1").decode()
            explicit_root_check = "Get-Item -LiteralPath $volumeRoot -Force"
            descendant_join = "$current = Join-Path $current $part"
            self.assertIn("$rootExpanded -ceq $volumeRoot", script)
            self.assertIn("$rootFull -ceq $volumeRoot", script)
            self.assertIn(explicit_root_check, script)
            self.assertLess(script.index(explicit_root_check), script.index(descendant_join))


if __name__ == "__main__":
    unittest.main()
