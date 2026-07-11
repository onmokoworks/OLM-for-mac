#!/usr/bin/env python3
"""Create the focused OLMBlur 32bpc request from the authoritative 48-case request."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_REQUEST = ROOT / "refs/reference_requests/olm_bitdepth_32bpc_full_probe_exr_rerun_20260703.json"
SOURCE_MANIFEST = ROOT / "refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMBlur/reference_manifest.json"
SOURCE_DIR = SOURCE_MANIFEST.parent
OUTPUT = ROOT / "refs/reference_requests/olmblur_32bpc_mac_windows_float_focus_20260711.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    source = json.loads(SOURCE_REQUEST.read_text(encoding="utf-8-sig"))
    manifest_hash = sha256(SOURCE_MANIFEST)
    cases = [copy.deepcopy(case) for case in source["cases"] if case.get("plugin") == "OLMBlur"]
    inputs = [copy.deepcopy(item) for item in source["inputs"] if item.get("id", "").startswith("olmblur_")]
    for item in inputs:
        frame = SOURCE_DIR / item["before_effects_frame"]
        item["sha256"] = sha256(frame)
        item["hash_algorithm"] = "sha256"
        item["source_manifest_sha256"] = manifest_hash

    result = {
        "request_id": "olmblur_32bpc_mac_windows_float_focus_20260711",
        "scope": {
            "bit_depth": "32bpc",
            "plugin_filters": ["OLMBlur"],
            "feature_filters": [],
            "plugin_count": 1,
            "case_count": len(cases),
        },
        "effect": {"name": "OLM Blur", "match_name": "OLM OLM Blur"},
        "why": [
            "Focused OLMBlur extraction of the authoritative 48-case 32bpc request/return.",
            "Preserves the authoritative case IDs, input IDs, effect property manifests, and parameter values.",
            "Mac and Windows runs must use 32bpc SOFTWARE rendering and float-preserving output; PNG-only output is probe-only.",
        ],
        "source_provenance": {
            "authoritative_request": str(SOURCE_REQUEST),
            "authoritative_request_id": source["request_id"],
            "authoritative_case_count": source["scope"]["case_count"],
            "focused_plugin": "OLMBlur",
            "focused_case_ids": [case["id"] for case in cases],
            "normalized_input_manifest": str(SOURCE_MANIFEST),
            "normalized_input_manifest_sha256": manifest_hash,
            "normalized_input_directory": str(SOURCE_DIR),
            "input_format": "png",
            "float_exr_status": {
                "normalized_input_directory": False,
                "windows_answered_partial_return": True,
                "windows_return_directory": "refs/win_references/20260710_185500__RETURN__olm_32bpc_existing48_exr_20260710__answered_partial_portable/OLMbit-depthconformancebatch",
                "windows_return_cases": 7,
                "windows_return_output_format": "exr",
                "windows_return_float_preserving": True,
            },
        },
        "render_sets": [copy.deepcopy(item) for item in source["render_sets"]],
        "inputs": inputs,
        "cases": cases,
        "compare_policy": {
            "path": "refs/conformance/bitdepth_32bpc_compare_policy_20260703.md",
            "mode": "float-preserving-required",
            "png_only_classification": "probe-only",
            "ae_exact_claim": False,
            "mac_windows_comparison": "required before any exactness claim",
        },
        "output_requirements": {
            "preferred_formats": ["exr"],
            "acceptable_float_preserving_fallbacks": ["tiff", "tif", "hdr", "raw-float-rgba"],
            "png_only_allowed": True,
            "png_only_classification": "probe-only",
            "float_preserving_required_for_ae_exact": True,
            "record_exact_format_used": True,
        },
        "artifact_integrity": {
            "sha256_required": True,
            "sha256_scope": ["input", "effect_output", "before_effects_output", "manifest"],
            "header_metadata_required": True,
            "required_float_header": {
                "container_format": "OpenEXR",
                "channel_order": "RGBA",
                "channel_count": 4,
                "sample_type": "float",
                "bits_per_channel": 32,
            },
        },
        "manifest_requirements": source["manifest_requirements"],
        "mac_follow_up": source["mac_follow_up"],
        "stop_lines": source["stop_lines"],
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] wrote {OUTPUT}")
    print(f"[OK] focused cases: {len(cases)}")
    print(f"[OK] source manifest sha256: {manifest_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
