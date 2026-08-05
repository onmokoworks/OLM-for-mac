#!/usr/bin/env python3
"""Audit current OLMColorKey binary identity against retained AE-exact evidence.

This is identity/preflight evidence only.  It never renders or promotes the
historical 16bpc result to a current-binary claim.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXACT32 = ROOT / "refs/conformance/olmcolorkey_32bpc_all9_ae_exact_20260728.json"
EXACT16 = ROOT / "refs/conformance/bitdepth_16bpc_exact_manifest_20260709.json"
PRODUCTION_SOURCE = ROOT / "mac/OLMColorKey/OLMColorKey.cpp"
SMART_RENDER_FIXTURE = ROOT / "tools/emulation/test_olmcolorkey_mac_smartrender_adapter_20260717.py"
PINNED_SOURCE_SHA256 = "52febf06cefea8b281ab9b2b6060c783ea77e45321b7c63ff755848151e55c05"
PINNED_FIXTURE_SHA256 = "477c2f8c380a63a66fcd3916e19d06dce71682caf29d25a64f0600e4bb39b0af"
DEFAULT_PLUGIN = Path.home() / (
    "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/"
    "OLMColorKey.plugin"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def executable(bundle_or_executable: Path) -> tuple[Path, Path]:
    path = bundle_or_executable.expanduser().resolve()
    if path.suffix == ".plugin":
        binary = path / "Contents/MacOS/OLMColorKey"
        bundle = path
    else:
        binary = path
        bundle = path.parents[2]
    if not binary.is_file():
        raise FileNotFoundError(binary)
    return bundle, binary


def ae_mapping(binary: Path) -> dict[str, object]:
    proc = subprocess.run(["pgrep", "-x", "After Effects"], text=True, capture_output=True)
    pids = [int(item) for item in proc.stdout.split() if item.isdigit()]
    result: dict[str, object] = {"pids": pids, "exact_mapping": False}
    if len(pids) != 1:
        return result
    pid = pids[0]
    started = subprocess.run(
        ["ps", "-p", str(pid), "-o", "lstart="], text=True, capture_output=True
    )
    started_text = " ".join(started.stdout.split())
    result.update({"pid": pid, "process_started_local": started_text})
    if started.returncode == 0 and started_text:
        started_at = dt.datetime.strptime(started_text, "%a %b %d %H:%M:%S %Y").timestamp()
        result["binary_predates_process_start"] = binary.stat().st_mtime <= started_at + 1
    mapped = subprocess.run(["vmmap", str(pid)], text=True, capture_output=True, timeout=120)
    resolved = str(binary)
    exact = mapped.returncode == 0 and any(
        re.search(r"\s" + re.escape(resolved) + r"$", line)
        for line in mapped.stdout.splitlines()
    )
    result["exact_mapping"] = exact
    if exact:
        result.update({
            "method": "vmmap_exact_path",
            "module_path": resolved,
            "module_sha256": sha256(binary),
        })
    return result


def binary_smart_render_symbols(binary: Path) -> dict[str, object]:
    proc = subprocess.run(["nm", "-an", str(binary)], text=True, capture_output=True, timeout=30)
    if proc.returncode != 0:
        raise RuntimeError(f"nm failed: {proc.stderr.strip()}")
    required = {
        "EffectMain": "_EffectMain",
        "SmartRender": "__ZL11SmartRenderP9PF_InDataP10PF_OutDataP19PF_SmartRenderExtra",
        "RenderWorld": "__ZL11RenderWorldP11PF_LayerDefS0_RK15OLMColorKeyInfos",
        "PF32_entry_capture": "__ZL33CapturePixelFloatEntryIfRequestedPK11PF_LayerDefs",
    }
    return {
        "method": "nm_local_and_external_symbols",
        "required": required,
        "present": {key: value in proc.stdout for key, value in required.items()},
    }


def installed_binary_shape(bundle: Path, binary: Path) -> dict[str, object]:
    lipo = subprocess.run(["lipo", "-archs", str(binary)], text=True, capture_output=True, timeout=30)
    sign = subprocess.run(["codesign", "--verify", "--deep", "--strict", str(bundle)],
                          text=True, capture_output=True, timeout=30)
    architectures = lipo.stdout.split() if lipo.returncode == 0 else []
    return {
        "architectures": architectures,
        "universal_arm64_x86_64": set(architectures) == {"arm64", "x86_64"},
        "codesign_deep_strict_valid": sign.returncode == 0,
    }


def run_source_typed_fixture() -> dict[str, object]:
    proc = subprocess.run(
        ["python3", str(SMART_RENDER_FIXTURE)], cwd=ROOT,
        text=True, capture_output=True, timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"SmartRender typed fixture failed: {proc.stderr.strip() or proc.stdout.strip()}")
    result = json.loads(proc.stdout)
    cases = result.get("cases", [])
    passed = (
        result.get("status") == "pass"
        and [row.get("case") for row in cases] == [
            "no_edge_pf32", "edge_blur_pf32", "no_edge_pf16", "enabled_black_key_pf16",
            "enabled_black_key_edge_blur_1_pf16",
            "enabled_black_key_edge_blur_1_single_pf32",
            "enabled_black_key_edge_blur_1_line_pf32",
            "enabled_black_key_edge_blur_1_all_pf32",
            "enabled_black_key_edge_blur_1_single_pf8",
            "enabled_black_key_edge_blur_1_line_pf8",
            "enabled_black_key_edge_blur_1_all_pf8",
            "enabled_black_key_edge_blur_2_single_pf8",
            "enabled_black_key_edge_blur_2_single_pf16",
            "enabled_black_key_edge_blur_2_single_pf32",
            "enabled_black_key_edge_blur_1.5_single_pf8",
            "enabled_black_key_edge_blur_1.5_single_pf16",
            "enabled_black_key_edge_blur_1.5_single_pf32",
            "enabled_black_key_edge_blur_0.5_single_pf8",
            "enabled_black_key_edge_blur_0.5_single_pf16",
            "enabled_black_key_edge_blur_0.5_single_pf32",
            "enabled_black_key_edge_blur_2.5_single_pf8",
            "enabled_black_key_edge_blur_2.5_single_pf16",
            "enabled_black_key_edge_blur_2.5_single_pf32",
            "enabled_black_key_edge_blur_3_single_pf8",
            "enabled_black_key_edge_blur_3_single_pf16",
            "enabled_black_key_edge_blur_3_single_pf32",
            "enabled_black_key_edge_blur_3.5_single_pf8",
            "enabled_black_key_edge_blur_3.5_single_pf16",
            "enabled_black_key_edge_blur_3.5_single_pf32",
            "enabled_black_key_edge_blur_4_single_pf8",
            "enabled_black_key_edge_blur_4_single_pf16",
            "enabled_black_key_edge_blur_4_single_pf32",
            "enabled_black_key_edge_blur_2_single_direction_1_pf8",
            "enabled_black_key_edge_blur_2_single_direction_1_pf16",
            "enabled_black_key_edge_blur_2_single_direction_1_pf32",
            "enabled_black_key_edge_blur_2_single_direction_3_pf8",
            "enabled_black_key_edge_blur_2_single_direction_3_pf16",
            "enabled_black_key_edge_blur_2_single_direction_3_pf32",
            "enabled_black_key_edge_blur_2_single_direction_4_pf8",
            "enabled_black_key_edge_blur_2_single_direction_4_pf16",
            "enabled_black_key_edge_blur_2_single_direction_4_pf32",
            "enabled_black_key_edge_blur_2_single_direction_0_pf8",
            "enabled_black_key_edge_blur_2_single_direction_0_pf16",
            "enabled_black_key_edge_blur_2_single_direction_0_pf32",
            "enabled_black_key_edge_blur_1_single_direction_1_pf8",
            "enabled_black_key_edge_blur_1_single_direction_1_pf16",
            "enabled_black_key_edge_blur_1_single_direction_1_pf32",
            "enabled_black_key_edge_blur_2_center_pf8",
            "enabled_black_key_edge_blur_2_center_pf16",
            "enabled_black_key_edge_blur_2_center_pf32",
        ]
        and [row.get("pixel_format") for row in cases] == [
            "PF32", "PF32", "PF16", "PF16", "PF16", "PF32", "PF32", "PF32",
            "PF8", "PF8", "PF8",
            "PF8", "PF16", "PF32",
            "PF8", "PF16", "PF32",
            "PF8", "PF16", "PF32",
            "PF8", "PF16", "PF32",
            "PF8", "PF16", "PF32",
            "PF8", "PF16", "PF32",
            "PF8", "PF16", "PF32",
            "PF8", "PF16", "PF32",
            "PF8", "PF16", "PF32",
            "PF8", "PF16", "PF32",
            "PF8", "PF16", "PF32",
            "PF8", "PF16", "PF32",
            "PF8", "PF16", "PF32",
        ]
        and all(row.get("pf_cmd_render_fallbacks") == 0 for row in cases)
        and all(row.get("parameter_checkout_order") == "verified" for row in cases)
        and all(row.get("input_padding_preserved") is True for row in cases)
        and all(row.get("output_padding_preserved") is True for row in cases)
    )
    return {"passed": passed, "result": result}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin-path", type=Path, default=DEFAULT_PLUGIN)
    parser.add_argument(
        "--json",
        type=Path,
        default=ROOT / "refs/conformance/olmcolorkey_current_binary_identity_20260805.json",
    )
    args = parser.parse_args()
    try:
        bundle, binary = executable(args.plugin_path)
        exact32 = json.loads(EXACT32.read_text(encoding="utf-8"))
        exact16 = json.loads(EXACT16.read_text(encoding="utf-8"))
        installed_hash = sha256(binary)
        expected32 = exact32["binaries"]["mac_macho_sha256"]
        color16 = [row for row in exact16["cases"] if row["plugin"] == "OLMColorKey"]
        mapping = ae_mapping(binary)
        symbols = binary_smart_render_symbols(binary)
        binary_shape = installed_binary_shape(bundle, binary)
        typed_fixture = run_source_typed_fixture()
        checks = {
            "installed_binary_exists": binary.is_file(),
            "installed_binary_universal_arm64_x86_64": binary_shape["universal_arm64_x86_64"],
            "installed_bundle_codesign_valid": binary_shape["codesign_deep_strict_valid"],
            "installed_matches_32bpc_exact_binary": installed_hash == expected32,
            "retained_32bpc_all9_exact": (
                exact32.get("ae_exact_claim") is True
                and exact32.get("summary", {}).get("exact_gate_count") == 18
                and exact32.get("summary", {}).get("max_raw_u32_delta") == 0
            ),
            "retained_16bpc_all9_exact": (
                len(color16) == 9
                and all(row.get("result_status") == "AE exact" and row.get("max_diff") == 0
                        for row in color16)
            ),
            "retained_16bpc_loaded_binary_hash_available": False,
            "single_ae_process": len(mapping["pids"]) == 1,
            "current_binary_exactly_mapped": mapping["exact_mapping"] is True,
            "mapped_binary_predates_process_start": mapping.get("binary_predates_process_start") is True,
            "production_source_hash_pinned": sha256(PRODUCTION_SOURCE) == PINNED_SOURCE_SHA256,
            "typed_fixture_hash_pinned": sha256(SMART_RENDER_FIXTURE) == PINNED_FIXTURE_SHA256,
            "exact_binary_contains_smart_render_production_symbols": all(symbols["present"].values()),
            "source_included_pf16_pf32_smart_render_typed_fixture_passes": typed_fixture["passed"],
        }
        ready = all(checks[key] for key in (
            "installed_binary_exists",
            "installed_matches_32bpc_exact_binary",
            "retained_32bpc_all9_exact",
            "single_ae_process",
            "current_binary_exactly_mapped",
            "mapped_binary_predates_process_start",
        ))
        report = {
            "kind": "olmcolorkey_current_binary_identity_audit",
            "schema_version": 1,
            "status": "ready" if ready else "restart_required",
            "ae_exact_claim": False,
            "installed": {
                "bundle_path": str(bundle), "binary_path": str(binary), "sha256": installed_hash,
                **binary_shape,
            },
            "retained_32bpc": {
                "evidence": str(EXACT32.relative_to(ROOT)),
                "mac_macho_sha256": expected32,
                "identity_relation": "same_binary" if installed_hash == expected32 else "different_binary",
            },
            "retained_16bpc": {
                "evidence": str(EXACT16.relative_to(ROOT)),
                "exact_case_count": len(color16),
                "loaded_mac_binary_sha256": None,
                "identity_relation": "unprovable_from_historical_evidence",
            },
            "ae_process": mapping,
            "source_typed_fixture": {
                "production_source": str(PRODUCTION_SOURCE.relative_to(ROOT)),
                "production_source_sha256": sha256(PRODUCTION_SOURCE),
                "fixture": str(SMART_RENDER_FIXTURE.relative_to(ROOT)),
                "fixture_sha256": sha256(SMART_RENDER_FIXTURE),
                "execution": typed_fixture,
            },
            "installed_binary_smart_render_symbols": symbols,
            "actual_aex_oracle_boundary": {
                "pf8_combined_numerical_stages": {
                    "evidence": "refs/conformance/olmcolorkey_combined_numerical_stage_witness_20260716.json",
                    "sha256": "4a8ffa2ce77fa48b3fbb4d31a932f17cedcb12ab988a66787cd49c990c402865",
                    "status": "pass",
                },
                "pf16_edge_thin_caller": {
                    "evidence": "refs/conformance/olmcolorkey_edge_thin_actual_caller_20260717.json",
                    "sha256": "74185f27a9ac247b68a17495660e264b70fc2bce498e2bde3d52d2ae2ba5d3f5",
                    "status": "pass_with_explicit_world_argument_repair",
                },
                "pf16_bounded_full_worker": {
                    "evidence": "refs/conformance/olmcolorkey_pf16_full_worker_actual_aex_20260805.json",
                    "sha256": "b36b4a288271f49d761392ec78c2ca76de11072386300dc15888545010853939",
                    "status": "pass",
                    "boundary": "FUN_1800018E0 -> FUN_180009000 plus direct FUN_1800029D0/FUN_1800035B0; parameter materialization and host Iterate16 are fixture shims",
                },
                "pf16_source_fixture_vs_actual_aex_exact": True,
                "scope": (
                    "4x3 PF16 no-key passthrough plus one enabled zero-threshold black key: "
                    "the black first pixel is cleared, the other 11 active pixels are byte-exact, "
                    "and row padding is preserved; not full AE case0001"
                ),
            },
            "checks": checks,
            "boundary": (
                "32bpc retained exact evidence is binary-identical to the installed executable; "
                "16bpc retained pixels remain exact but cannot be attributed to this executable "
                "because the historical result lacks loaded-module identity. The source-included PF32 "
                "typed fixture proves the production SmartRender adapter, not Windows numerical equality. "
                "No current AE render was run."
            ),
        }
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if ready else 2
    except (OSError, KeyError, ValueError, RuntimeError, json.JSONDecodeError,
            subprocess.SubprocessError) as exc:
        print(f"[FAIL_CLOSED] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
