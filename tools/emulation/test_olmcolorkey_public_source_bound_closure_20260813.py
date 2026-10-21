#!/usr/bin/env python3
"""Durable hostless closure for fixed-source OLMColorKey public entries."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/olmcolorkey_public_source_bound_closure_20260813.json"
DOC = REPORT.with_suffix(".md")

FILES = {
    "production_source": ROOT / "mac/OLMColorKey/OLMColorKey.cpp",
    "sdk_header": ROOT / "Headers/AE_Effect.h",
    "windows_aex": ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex",
    "aex_guest_worker": Path(
        "/Users/onmk/Documents/Projects/Personal/04_Tools/"
        "AEXCompat-issue851-smart-primary-checkout/guest/target/release/aex-guest-worker"
    ),
    "probe_source_bound_atomic": ROOT / "tools/emulation/probe_olmcolorkey_source_bound_atomic_20260813.cpp",
    "probe_public_entries": ROOT / "tools/emulation/probe_olmcolorkey_public_entries_real_sdk_20260813.cpp",
    "probe_suite_lifecycle": ROOT / "tools/emulation/probe_olmcolorkey_real_sdk_suite_lifecycle_20260813.cpp",
    "unit_source_bound_atomic": ROOT / "tests/test_olmcolorkey_source_bound_atomic_20260813.py",
    "unit_public_entries": ROOT / "tests/test_olmcolorkey_public_entries_real_sdk_20260813.py",
    "unit_suite_lifecycle": ROOT / "tests/test_olmcolorkey_real_sdk_suite_lifecycle_20260813.py",
    "evidence_covering": ROOT / "refs/conformance/olmcolorkey_exported_owner_edge_blur_covering_20260812.json",
    "evidence_geometry_transfer": ROOT / "refs/conformance/olmcolorkey_exported_owner_edge_blur_geometry_transfer_20260812.json",
    "evidence_second_source": ROOT / "refs/conformance/olmcolorkey_exported_owner_edge_blur_second_source_20260814.json",
    "evidence_lab76_historical_oracle": ROOT / "refs/conformance/olmcolorkey_lab76_multikey_order_closure_20260812.json",
    "evidence_keep_premult_replace": ROOT / "refs/conformance/olmcolorkey_exported_owner_keep_premult_replace_20260811.json",
}

EXPECTED_IDENTITIES = {
    "production_source": "4dbd264501a0d5d990a3726d16223c01c1996677b925f8546157b6a91ce677d1",
    "sdk_header": "a6d5cdeba53f6934a9bac19c2c1b46b1478266f39995795c59244e3d9a355a0d",
    "windows_aex": "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c",
    "aex_guest_worker": "46ab907d286ad4e0e1c2065557100f02c37e0b68df4c22202a825f3fea13ef61",
    "probe_source_bound_atomic": "ec1823bd2b162b2329653335d66d30ed334b6e3355c196f8c0bfa4a6e8fc5be8",
    "probe_public_entries": "8193b267695107b42a8b32751e6fb016a50bb24e121d378159d2604bf4582372",
    "probe_suite_lifecycle": "ae5523a37ffe3e2a50b3d34c0b1f8c09bb7cdd543899a2df047eccceb424f90a",
    "unit_source_bound_atomic": "0079ada3ab852b194a4fcc9349ba32c0b6a1c8f3daf4e70cfb2ae0234055d0fc",
    "unit_public_entries": "73a11c8d969ac12838abff46af2bf4ff00c3bf3a4b50aad0c58a39bf3cf1c75d",
    "unit_suite_lifecycle": "a42132beba365c9e78d5b44c58793821b242572c36b4a1318ae11721edeace3a",
    "evidence_covering": "e2fdd20abecf3160ade533e3d3d4ee18ffa59672a794ed0e264143a0d599434d",
    "evidence_geometry_transfer": "8f9f6486bffcb591624f7c3c00c252dfaae29cc889ce847566735eccb80f5209",
    "evidence_second_source": "ddb11fc57cb0b402e5aee0362a81a0b0916f9fd5894e9c581d0e6b6c9159b55f",
    "evidence_lab76_historical_oracle": "98f7f5b43b7986eb24455110d67dc00c0aedab097da77112a39bce4ab772bc1f",
    "evidence_keep_premult_replace": "9d24139134d0e1149e84959f23ff38818d004cfbd121da124425943fc16046e6",
}

PROBES = {
    "source_bound_atomic": FILES["probe_source_bound_atomic"],
    "public_entries": FILES["probe_public_entries"],
    "public_entries_x86_64": FILES["probe_public_entries"],
    "suite_lifecycle": FILES["probe_suite_lifecycle"],
}
PROBE_EXPECTED = {
    "source_bound_atomic": [408408, "e7b5210d9389e144148ce44bbd06b41589c4136b3fe461e705e9671adf14e6dd", "SOURCE_BOUND_ATOMIC pass=1 positives=63 negatives=567"],
    "public_entries": [816816, "dca1d6fccca2145456e8eb19cd9ab8f1b8994d8622cdb3679b777f92c2a973c7", "COLORKEY_PUBLIC_ENTRIES pass=1 classic=63 smart=63 callback_negatives=13"],
    "public_entries_x86_64": [816816, "dca1d6fccca2145456e8eb19cd9ab8f1b8994d8622cdb3679b777f92c2a973c7", "COLORKEY_PUBLIC_ENTRIES pass=1 classic=63 smart=63 callback_negatives=13"],
    "suite_lifecycle": [5806, "8d938d902f484afaa112704864ba344feffa219adc4c7fb2624230fa04579286", ""],
}

TOP_KEYS = {
    "schema", "status", "generated_at", "claim", "identities",
    "canonical_rows", "canonical_rows_sha256", "probe_runs",
    "negative_closure", "lifecycle", "world_contract", "scope",
}
ROW_KEYS = {
    "family", "case", "depth", "width", "height", "rowbytes",
    "active_bytes", "raw_sha256", "public_routes", "status",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def live_identities() -> dict[str, str]:
    return {name: sha(path) for name, path in FILES.items()}


def canonical_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path, width, height in (
        (FILES["evidence_covering"], 32, 18),
        (FILES["evidence_geometry_transfer"], 64, 36),
        (FILES["evidence_second_source"], 48, 27),
    ):
        source_rows = json.loads(path.read_text())["cases"]
        for row in source_rows:
            pixel_bytes = {"PF8": 4, "PF16": 8, "PF32": 16}[row["depth"]]
            rows.append({
                "family": "edge_blur", "case": row["case"],
                "depth": row["depth"], "width": width, "height": height,
                "rowbytes": width * pixel_bytes + 8,
                "active_bytes": row["bytes"],
                "raw_sha256": row["actual_exported_raw_sha256"],
                "public_routes": ["PF_Cmd_RENDER", "PF_Cmd_SMART_RENDER"],
                "status": "raw_exact",
            })
    lab = json.loads(FILES["evidence_lab76_historical_oracle"].read_text())
    for row in lab["production_effectmain"]["rows"]:
        rows.append({
            "family": "lab76_two_key_order",
            "case": f"lab76_{row['order']}", "depth": row["depth"],
            "width": 1, "height": 1,
            "rowbytes": row["raw_pixel_bytes"] + 8,
            "active_bytes": row["raw_pixel_bytes"],
            "raw_sha256": row["raw_pixel_sha256"],
            "public_routes": ["PF_Cmd_RENDER", "PF_Cmd_SMART_RENDER"],
            "status": "raw_exact",
        })
    toggles = json.loads(FILES["evidence_keep_premult_replace"].read_text())
    for row in toggles["cases"]:
        rows.append({
            "family": "keep_premult_replace",
            "case": row["case"], "depth": row["depth"],
            "width": 11, "height": 7,
            "rowbytes": row["bytes"] // 7 + 8,
            "active_bytes": row["bytes"],
            "raw_sha256": row["actual_exported_raw_sha256"],
            "public_routes": ["PF_Cmd_RENDER", "PF_Cmd_SMART_RENDER"],
            "status": "raw_exact",
        })
    return rows


def run_probe(name: str, source: Path) -> dict[str, Any]:
    sdk = subprocess.run(
        ["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True,
    ).stdout.strip()
    with tempfile.TemporaryDirectory(prefix=f"olmck-{name}.") as raw:
        executable = Path(raw) / "probe"
        architecture = "x86_64" if name.endswith("_x86_64") else "arm64"
        command = [
            "clang++", "-std=c++17", "-arch", architecture, "-O2",
            "-Wno-pragma-pack", "-Wno-deprecated-declarations",
            "-isysroot", sdk, "-IHeaders", "-IHeaders/SP", "-IUtil",
            "-IResources", "-Imac/OLMColorKey", str(source),
            "mac/OLMColorKey/OLMColorKey_Strings.cpp",
            "Util/AEGP_SuiteHandler.cpp", "Util/MissingSuiteError.cpp",
            "-framework", "Cocoa", "-o", str(executable),
        ]
        subprocess.run(command, cwd=ROOT, check=True)
        execute = (["arch", "-x86_64", str(executable)]
                   if architecture == "x86_64" else [str(executable)])
        run = subprocess.run(execute, cwd=ROOT, capture_output=True, check=True)
    observed = {
        "stdout_bytes": len(run.stdout),
        "stdout_sha256": hashlib.sha256(run.stdout).hexdigest(),
        "stderr": run.stderr.decode().strip(),
        "returncode": run.returncode,
    }
    size, stdout_sha, stderr = PROBE_EXPECTED[name]
    expected = {"stdout_bytes": size, "stdout_sha256": stdout_sha,
                "stderr": stderr, "returncode": 0}
    if observed != expected:
        raise RuntimeError(f"{name} probe drift: {observed}")
    return observed


def build_report() -> dict[str, Any]:
    identities = live_identities()
    if identities != EXPECTED_IDENTITIES:
        raise RuntimeError(f"identity drift: {identities}")
    rows = canonical_rows()
    probes = {name: run_probe(name, path) for name, path in PROBES.items()}
    return {
        "schema": "olmcolorkey_public_source_bound_closure_v1",
        "status": "pass_hostless_public_source_bound_raw_exact",
        "generated_at": "2026-08-13T23:30:00+09:00",
        "claim": (
            "Exactly 63 fixed source/tuple/depth cells are raw exact through both "
            "Mac public Classic and Smart entries against the pinned Windows exported "
            "Smart owner. Unlisted source, tuple, geometry, format, layout, and error "
            "paths fail closed before atomic output commit."
        ),
        "identities": identities,
        "canonical_rows": rows,
        "canonical_rows_sha256": digest(rows),
        "probe_runs": probes,
        "negative_closure": {
            "source_tuple_world_atomic_cases": 567,
            "smart_callback_error_or_throw_cases": 13,
            "world_and_color_suite_cases": 12,
            "smart_param_success_cases": 1,
            "smart_param_checkout_failure_ordinals": 33,
            "smart_param_checkin_failure_ordinals": 33,
            "all_negative_output_uncommitted": True,
        },
        "lifecycle": {
            "classic_positive_cells": 63, "smart_positive_cells": 63,
            "smart_param_checkout_checkin_success": [33, 33],
            "smart_layer_output_checkin": [1, 1, 1],
            "first_error_preserved": True, "bad_alloc_maps_to_oom": True,
            "unknown_exception_maps_to_internal": True,
        },
        "world_contract": {
            "pixel_formats": ["ARGB32", "ARGB64", "ARGB128"],
            "rowbytes": "width_times_pixel_size_plus_8",
            "full_extent_zero_origin": True, "downsample": "1/1",
            "input_output_full_payload_disjoint": True,
            "active_commit_only": True,
        },
        "scope": {
            "hostless_real_ae_sdk": True,
            "windows_aex_exported_smart_oracle": True,
            "arm64_and_rosetta_x86_public_entries": True,
            "native_after_effects": False, "installed_binary": False,
            "arbitrary_source_or_tuple": False, "gpu": False,
            "install_or_ae_run_performed": False,
        },
    }


def validate_report(report: dict[str, Any], live: bool = False) -> bool:
    if set(report) != TOP_KEYS:
        return False
    if report.get("schema") != "olmcolorkey_public_source_bound_closure_v1":
        return False
    if report.get("status") != "pass_hostless_public_source_bound_raw_exact":
        return False
    rows = canonical_rows()
    if report.get("canonical_rows") != rows or len(rows) != 63:
        return False
    if any(set(row) != ROW_KEYS for row in rows):
        return False
    if report.get("canonical_rows_sha256") != digest(rows):
        return False
    if report.get("identities") != EXPECTED_IDENTITIES:
        return False
    if set(report.get("probe_runs", {})) != set(PROBES):
        return False
    for name, values in PROBE_EXPECTED.items():
        size, stdout_sha, stderr = values
        if report["probe_runs"].get(name) != {
            "stdout_bytes": size, "stdout_sha256": stdout_sha,
            "stderr": stderr, "returncode": 0,
        }:
            return False
    expected_nested = {
        "negative_closure": {
            "source_tuple_world_atomic_cases", "smart_callback_error_or_throw_cases",
            "world_and_color_suite_cases", "smart_param_success_cases",
            "smart_param_checkout_failure_ordinals", "smart_param_checkin_failure_ordinals",
            "all_negative_output_uncommitted",
        },
        "lifecycle": {
            "classic_positive_cells", "smart_positive_cells",
            "smart_param_checkout_checkin_success", "smart_layer_output_checkin",
            "first_error_preserved", "bad_alloc_maps_to_oom",
            "unknown_exception_maps_to_internal",
        },
        "world_contract": {
            "pixel_formats", "rowbytes", "full_extent_zero_origin", "downsample",
            "input_output_full_payload_disjoint", "active_commit_only",
        },
        "scope": {
            "hostless_real_ae_sdk", "windows_aex_exported_smart_oracle",
            "arm64_and_rosetta_x86_public_entries",
            "native_after_effects", "installed_binary", "arbitrary_source_or_tuple",
            "gpu", "install_or_ae_run_performed",
        },
    }
    if any(set(report.get(name, {})) != keys for name, keys in expected_nested.items()):
        return False
    if report["negative_closure"] != build_report_static()["negative_closure"]:
        return False
    if report["lifecycle"] != build_report_static()["lifecycle"]:
        return False
    if report["world_contract"] != build_report_static()["world_contract"]:
        return False
    if report["scope"] != build_report_static()["scope"]:
        return False
    if live:
        try:
            fresh = build_report()
        except Exception:
            return False
        fresh["generated_at"] = report["generated_at"]
        return fresh == report
    return True


def build_report_static() -> dict[str, Any]:
    """Return expected non-probe fields without invoking a compiler."""
    rows = canonical_rows()
    return {
        "negative_closure": {
            "source_tuple_world_atomic_cases": 567,
            "smart_callback_error_or_throw_cases": 13,
            "world_and_color_suite_cases": 12, "smart_param_success_cases": 1,
            "smart_param_checkout_failure_ordinals": 33,
            "smart_param_checkin_failure_ordinals": 33,
            "all_negative_output_uncommitted": True,
        },
        "lifecycle": {
            "classic_positive_cells": 63, "smart_positive_cells": 63,
            "smart_param_checkout_checkin_success": [33, 33],
            "smart_layer_output_checkin": [1, 1, 1],
            "first_error_preserved": True, "bad_alloc_maps_to_oom": True,
            "unknown_exception_maps_to_internal": True,
        },
        "world_contract": {
            "pixel_formats": ["ARGB32", "ARGB64", "ARGB128"],
            "rowbytes": "width_times_pixel_size_plus_8",
            "full_extent_zero_origin": True, "downsample": "1/1",
            "input_output_full_payload_disjoint": True, "active_commit_only": True,
        },
        "scope": {
            "hostless_real_ae_sdk": True,
            "windows_aex_exported_smart_oracle": True,
            "arm64_and_rosetta_x86_public_entries": True,
            "native_after_effects": False, "installed_binary": False,
            "arbitrary_source_or_tuple": False, "gpu": False,
            "install_or_ae_run_performed": False,
        },
        "canonical_rows": rows,
    }


def render_doc(report: dict[str, Any]) -> str:
    source = report["identities"]["production_source"]
    return (
        "# OLMColorKey public source-bound closure (2026-08-13)\n\n"
        f"Status: `{report['status']}`\n\n"
        "Exactly 63 fixed cells (33 edge-blur, six Lab76 order, and 24 "
        "Color Keep / Premultiplied / Replace toggle cells) are raw "
        "exact through both public Classic and Smart entries. Production source: "
        f"`{source}`.\n\n"
        "The hostless real-SDK closure covers 567 source/tuple/world negatives, "
        "13 Smart callback errors or throws, 12 suite cases, and every one of "
        "33 parameter checkout plus 33 checkin failure ordinals. Output is not "
        "committed on failure. The public-entry output stream is identical on "
        "native arm64 and Rosetta x86_64.\n\n"
        "This does not claim installed or native-AE execution, arbitrary sources "
        "or tuples, or GPU behavior. Install and AE smoke are deferred to a later "
        "batched checkpoint.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.write:
        report = build_report()
        REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        DOC.write_text(render_doc(report))
        print("PASS_OLMCOLORKEY_PUBLIC_SOURCE_BOUND_CLOSURE_WRITTEN")
        return 0
    if not REPORT.is_file():
        print("FAIL_OLMCOLORKEY_PUBLIC_SOURCE_BOUND_CLOSURE_MISSING")
        return 2
    report = json.loads(REPORT.read_text())
    if not validate_report(report, live=True):
        print("FAIL_OLMCOLORKEY_PUBLIC_SOURCE_BOUND_CLOSURE")
        return 1
    print("PASS_OLMCOLORKEY_PUBLIC_SOURCE_BOUND_CLOSURE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
