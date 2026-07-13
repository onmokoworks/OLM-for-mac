#!/usr/bin/env python3
"""Fail-closed smoke for the executable ColorKey 32bpc identity package."""

from __future__ import annotations

import copy
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/package_ae26_3_32bpc_input_identity_request_20260713.py"
STEM = "olm_ae26_3_32bpc_input_identity_request_20260713"
CASE = "olmcolorkey__case_0002"
AEX_HASH = "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c"
NONCE = "a" * 32
PID = 123


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_helper(helper: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(helper), *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def common_provenance() -> dict[str, object]:
    return {
        "kind": "olm_pf_pixel_float_entry_capture_provenance",
        "schema": 3,
        "case": CASE,
        "nonce": NONCE,
        "pid": PID,
        "bitdepth": 32,
        "pixel_type": "PF_PixelFloat",
        "channel_order": ["alpha", "red", "green", "blue"],
        "endianness": "little",
        "pixel_stride_bytes": 16,
        "width": 64,
        "height": 64,
        "rowbytes": 1024,
        "bytes": 65536,
    }


def windows_trace(**overrides: object) -> str:
    fields: dict[str, object] = {
        "nonce": NONCE,
        "case": CASE,
        "pid": PID,
        "hash": AEX_HASH,
        "rva": "0x9960",
        "world": "00000000`00100000",
        "data": "00000000`00200000",
        "rowbytes": 1024,
        "width": 64,
        "height": 64,
    }
    fields.update(overrides)
    return (
        "OLM_CK_BREAKPOINT_ARMED\n"
        "OLM_CK_ENTRY nonce={nonce} case={case} pid={pid} aex_sha256={hash} rva={rva} "
        "input_world={world} data={data} rowbytes={rowbytes} width={width} height={height}\n"
    ).format(**fields)


def windows_provenance(trace: Path) -> dict[str, object]:
    provenance = common_provenance()
    provenance.update(
        {
            "producer": "cdb.exe",
            "capture_method": "windows-hash-pinned-cdb-rva-hook",
            "capture_point": "OLMColorKey.aex+0x9960",
            "aex_sha256": AEX_HASH,
            "float_render_entry_rva": "0x9960",
            "input_world_register": "r8",
            "input_world_address": "0x100000",
            "data_address": "0x200000",
            "cdb_trace_sha256": digest(trace),
            "launch_binding": {
                "nonce": NONCE,
                "case": CASE,
                "actual_afterfx_pid": PID,
                "launcher_pid": PID,
                "session_id": 7,
                "relation": "launcher-pid",
                "fresh_process": True,
                "fixture_commandline_bound": True,
            },
        }
    )
    return provenance


def expect_rejected(helper: Path, dump: Path, provenance: Path, manifest: Path, *args: str) -> None:
    manifest.write_text("stale acceptance", encoding="utf-8")
    result = run_helper(
        helper,
        "--dump", str(dump),
        "--provenance", str(provenance),
        "--manifest", str(manifest),
        *args,
    )
    assert result.returncode != 0, result.stdout
    assert not manifest.exists(), f"rejection left acceptance manifest: {result.stdout}"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_input_identity_smoke_") as temp_name:
        temp = Path(temp_name)
        output = temp / "request.zip"
        output2 = temp / "request2.zip"
        subprocess.run([sys.executable, str(SCRIPT), "--output", str(output)], cwd=ROOT, check=True)
        subprocess.run([sys.executable, str(SCRIPT), "--output", str(output2)], cwd=ROOT, check=True)
        assert output.read_bytes() == output2.read_bytes(), "package is not deterministic"
        expected = {f"{STEM}/{name}" for name in (
            "README.md", "CONTRACT.json", "REQUEST_MANIFEST.json", "RETURN_MANIFEST_TEMPLATE.json",
            "fixture/ae_generate_32bpc_typed_procedural_fixture.jsx", "capture_pf_pixel_float_entry.py",
            "run_windows_ae26_3_32bpc_input_identity.ps1", "run_macos_ae26_3_32bpc_input_identity.sh",
        )}
        with zipfile.ZipFile(output) as archive:
            assert expected <= set(archive.namelist())
            contract = json.loads(archive.read(f"{STEM}/CONTRACT.json"))
            request = json.loads(archive.read(f"{STEM}/REQUEST_MANIFEST.json"))
            readme = archive.read(f"{STEM}/README.md").decode()
            helper_text = archive.read(f"{STEM}/capture_pf_pixel_float_entry.py").decode()
            windows = archive.read(f"{STEM}/run_windows_ae26_3_32bpc_input_identity.ps1").decode()
            mac = archive.read(f"{STEM}/run_macos_ae26_3_32bpc_input_identity.sh").decode()
            fixture = archive.read(f"{STEM}/fixture/ae_generate_32bpc_typed_procedural_fixture.jsx").decode()
        assert contract["schema"] == 3 and contract["capture_target"]["case"] == CASE
        assert contract["entry_buffer"]["identity"].startswith("raw-float32-bits")
        assert contract["ae"]["bit_depth"] == "32bpc" and contract["ae"]["linear_light"] is False
        assert contract["capture_paths"]["windows"] == {"aex_sha256": AEX_HASH, "float_render_entry_rva": "0x9960", "input_world_register": "r8", "method": "hash-pinned-cdb-rva-hook", "world_offsets": {"data": "0x08", "height": "0x28", "rowbytes": "0x10", "width": "0x24"}}
        assert [case["id"] for case in request["cases"]] == [CASE]
        assert request["cases"][0]["artifacts"]["no_effect"]["effect_enabled"] is False
        assert "OLM_PF_PIXELFLOAT_ENTRY_CAPTURE_COMMAND" not in readme + helper_text + windows + mac
        for token in ("same-run nonce", "SmartRender", "0x9960", AEX_HASH, "dladdr"):
            assert token in readme
        for token in ("missing instrument provenance", "contract-only dump rejected", "launch_binding", "cdb_trace_sha256", "loaded_plugin_executable"):
            assert token in helper_text
        for token in ("Get-LaunchRelation", "ready marker PID", "CommandLine", "SessionId", "case=$CaseId", "--trace $trace"):
            assert token in windows
        for token in ("OLM_PF_PIXELFLOAT_ENTRY_EXPECTED_PLUGIN_SHA256", "expected_plugin_sha256", "--plugin-executable"):
            assert token in mac
        for token in ("OLM_PF_ENTRY_NONCE", "OLM_PF_ENTRY_CASE", "readyPid", f"fixture={Path('ae_generate_32bpc_typed_procedural_fixture.jsx').name}"):
            assert token in fixture

        helper = temp / "capture.py"
        helper.write_text(helper_text, encoding="utf-8")
        dump = temp / "entry.bin"
        dump.write_bytes(struct.pack("<4f", 0.0, 1.0, 0.5, 0.25) * (64 * 64))
        manifest = temp / "entry.json"

        missing = temp / "missing.json"
        expect_rejected(helper, dump, missing, manifest, "--nonce", NONCE, "--platform", "macos", "--pid", str(PID))
        old = temp / "old.json"
        old.write_text(json.dumps(common_provenance() | {"schema": 2, "producer": "shell"}), encoding="utf-8")
        expect_rejected(helper, dump, old, manifest, "--nonce", NONCE, "--platform", "macos", "--pid", str(PID))

        trace = temp / "trace.log"
        trace.write_text(windows_trace(), encoding="utf-8")
        provenance = temp / "windows.json"
        provenance.write_text(json.dumps(windows_provenance(trace)), encoding="utf-8")
        windows_args = ("--nonce", NONCE, "--platform", "windows", "--pid", str(PID), "--trace", str(trace))
        accepted = run_helper(helper, "--dump", str(dump), "--provenance", str(provenance), "--manifest", str(manifest), *windows_args)
        assert accepted.returncode == 0, accepted.stdout
        assert json.loads(manifest.read_text())["cdb_trace_sha256"] == digest(trace)

        trace_mutations = {
            "wrong_nonce": {"nonce": "b" * 32},
            "wrong_pid": {"pid": PID + 1},
            "wrong_hash": {"hash": "0" * 64},
            "wrong_rva": {"rva": "0x9961"},
            "wrong_input_world": {"world": "00000000`00300000"},
            "wrong_data": {"data": "00000000`00400000"},
            "wrong_rowbytes": {"rowbytes": 1040},
            "wrong_width": {"width": 63},
            "wrong_height": {"height": 63},
        }
        for name, mutation in trace_mutations.items():
            bad_trace = temp / f"{name}.log"
            bad_trace.write_text(windows_trace(**mutation), encoding="utf-8")
            bad_provenance = temp / f"{name}.json"
            data = windows_provenance(bad_trace)
            # Provenance remains bound to the expected run; only the independently parsed trace is mutated.
            bad_provenance.write_text(json.dumps(data), encoding="utf-8")
            bad_args = ("--nonce", NONCE, "--platform", "windows", "--pid", str(PID), "--trace", str(bad_trace))
            expect_rejected(helper, dump, bad_provenance, manifest, *bad_args)

        wrong_process = copy.deepcopy(windows_provenance(trace))
        wrong_process["launch_binding"]["relation"] = "unrelated"  # type: ignore[index]
        wrong_process_path = temp / "wrong_process.json"
        wrong_process_path.write_text(json.dumps(wrong_process), encoding="utf-8")
        expect_rejected(helper, dump, wrong_process_path, manifest, *windows_args)

        plugin = temp / "OLMColorKey"
        plugin.write_bytes(b"instrumented-plugin-executable")
        plugin_hash = digest(plugin)
        mac_provenance = common_provenance() | {
            "producer": "OLMColorKey.plugin",
            "capture_method": "macos-env-gated-plugin-instrumentation",
            "capture_point": "SmartRender.after_checkout_layer_pixels.before_checkout_output",
            "loaded_plugin_executable": str(plugin.resolve()),
            "launch_expected_plugin_sha256": plugin_hash,
        }
        mac_path = temp / "mac.json"
        mac_path.write_text(json.dumps(mac_provenance), encoding="utf-8")
        mac_args = ("--nonce", NONCE, "--platform", "macos", "--pid", str(PID), "--expected-plugin-sha256", plugin_hash, "--plugin-executable", str(plugin))
        accepted = run_helper(helper, "--dump", str(dump), "--provenance", str(mac_path), "--manifest", str(manifest), *mac_args)
        assert accepted.returncode == 0, accepted.stdout
        wrong_hash_args = ("--nonce", NONCE, "--platform", "macos", "--pid", str(PID), "--expected-plugin-sha256", "0" * 64, "--plugin-executable", str(plugin))
        wrong_hash_provenance = copy.deepcopy(mac_provenance)
        wrong_hash_provenance["launch_expected_plugin_sha256"] = "0" * 64
        mac_path.write_text(json.dumps(wrong_hash_provenance), encoding="utf-8")
        expect_rejected(helper, dump, mac_path, manifest, *wrong_hash_args)

    print("[OK] executable AE 26.3 ColorKey PF_PixelFloat identity package smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
