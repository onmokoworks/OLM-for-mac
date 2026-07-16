#!/usr/bin/env python3
"""Fail-closed OLMColorKey Mac return validator and raw FLOAT32 reporter."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from compare_float_exr import compare  # noqa: E402
from verify_32bpc_float_return import VerificationError, inspect_float_rgba_exr  # noqa: E402
from package_olmcolorkey_32bpc_mac_validation_20260715 import (  # noqa: E402
    REQUEST_INDEX,
    load_cases,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path.name


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--request-manifest", type=Path, default=None)
    args = parser.parse_args()
    root = args.result.parent.resolve()
    errors: list[str] = []
    comparisons: list[dict] = []
    try:
        request = json.loads(REQUEST_INDEX.read_text(encoding="utf-8"))
        result = json.loads(args.result.read_text(encoding="utf-8"))
        request_manifest = args.request_manifest or args.result.parent.parent / "request_manifest.json"
        pinned = json.loads(request_manifest.read_text(encoding="utf-8"))
        _, expected_cases = load_cases()
        expected_ids = [case["id"] for case in expected_cases]
        if result.get("kind") != "olmcolorkey_32bpc_mac_validation_return": errors.append("wrong return kind")
        if result.get("ae_exact_claim") is not False: errors.append("ae_exact_claim must be false")
        if result.get("project") != {"bits_per_channel": 32, "working_space": "None", "linear_blending": False, "renderer": "SOFTWARE"}: errors.append("project/color/renderer contract drift")
        if result.get("output_module", {}).get("template_name") != "OLM EXR 32 Float" or result.get("output_module", {}).get("capture_api") != "OutputModule.getSettings(GetSettingsFormat.STRING)": errors.append("output module contract drift")
        plugin = result.get("plugin", {})
        plugin_path = Path(plugin.get("path", ""))
        if plugin.get("filename") != "OLMColorKey.plugin" or not plugin_path.is_file() or len(plugin.get("sha256", "")) != 64 or plugin.get("expected_sha256") != plugin.get("sha256") or (plugin_path.is_file() and digest(plugin_path) != plugin.get("sha256")): errors.append("installed plugin SHA is missing or not bound to the loaded binary")
        proof = result.get("loaded_plugin_proof", {})
        if proof.get("method") != "vmmap_exact_path" or proof.get("module_path") != plugin.get("path") or proof.get("module_sha256") != plugin.get("sha256") or proof.get("binary_predates_process_start") is not True or not isinstance(proof.get("pid"), int): errors.append("loaded plugin is not bound to the AE process mapping")
        returned = result.get("cases", [])
        if [case.get("id") for case in returned] != expected_ids: errors.append("case set/order mismatch")
        windows = pinned.get("windows_float32_pairs", [])
        if [pair.get("id") for pair in windows] != expected_ids: errors.append("pinned Windows FLOAT32 pair set/order missing")
        for expected, case, pair in zip(expected_cases, returned, windows):
            case_id = expected["id"]
            if case.get("input") != expected["before_effects_frame"]: errors.append(f"{case_id}: input identity drift")
            if case.get("no_effect_control_passed") is not True: errors.append(f"{case_id}: same-context no-effect control missing")
            for branch in ("no_effect", "effect_on"):
                item = case.get("outputs", {}).get(branch, {})
                mac_path = resolve(root, item.get("path", ""))
                win_item = pair.get(branch, {})
                win_path = ROOT / win_item.get("path", "")
                if not mac_path.is_file() or mac_path.suffix.lower() != ".exr": errors.append(f"{case_id}: missing Mac FLOAT EXR {branch}"); continue
                if item.get("sha256") != digest(mac_path): errors.append(f"{case_id}: Mac {branch} hash mismatch")
                settings = item.get("output_module_settings", {})
                settings_path = resolve(root, settings.get("path", ""))
                if not settings_path.is_file() or settings.get("sha256") != digest(settings_path): errors.append(f"{case_id}: {branch} settings hash mismatch")
                try:
                    inspect_float_rgba_exr(mac_path, (expected["comp"]["width"], expected["comp"]["height"]))
                    if not win_path.is_file() or len(win_item.get("sha256", "")) != 64 or digest(win_path) != win_item["sha256"]: raise VerificationError("Windows artifact missing or hash mismatch")
                    comparison = compare(win_path, mac_path)
                    comparisons.append({"case_id": case_id, "branch": branch, "windows": str(win_path), "mac": str(mac_path), "result": comparison})
                    if comparison["mismatched_values"] != 0: errors.append(f"{case_id}: {branch} raw FLOAT32 mismatch")
                except (OSError, ValueError, VerificationError) as exc:
                    errors.append(f"{case_id}: {branch} comparison failed: {exc}")
            outputs = case.get("outputs", {})
            if outputs.get("no_effect", {}).get("output_module_settings", {}).get("sha256") != outputs.get("effect_on", {}).get("output_module_settings", {}).get("sha256"): errors.append(f"{case_id}: Output Module settings differ between control and effect")
        all_equal = len(comparisons) == 18 and not errors and all(item["result"]["mismatched_values"] == 0 for item in comparisons)
        report = {"kind": "olmcolorkey_32bpc_mac_validation_report", "schema_version": 1, "status": "raw_float32_exact_candidate" if all_equal else "fail_closed_pending", "ae_exact_claim": False, "case_count": len(returned), "failures": errors, "raw_float32_comparisons": comparisons, "all_raw_float32_equal": all_equal, "next_gate": "retain the bound installed plugin SHA and all 18 zero-delta raw FLOAT32 comparisons before any exactness decision"}
        destination = args.output or root / "validation_report.json"
        destination.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        print(f"[{('OK' if not errors else 'FAIL_CLOSED')}] wrote {destination}")
        return 0 if not errors else 2
    except (OSError, ValueError, KeyError, json.JSONDecodeError, VerificationError) as exc:
        print(f"[FAIL_CLOSED] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
