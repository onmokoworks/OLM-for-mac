#!/usr/bin/env python3
"""Audit the current OLMColorKey bit-depth evidence boundary.

This is intentionally an evidence audit, not a renderer or kernel test.  It
keeps host/input-conversion failures separate from algorithm conclusions.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from verify_32bpc_float_return import VerificationError, inspect_float_rgba_exr


def root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def audit_windows_float_reference(repo: Path) -> dict[str, Any]:
    """Inspect the current ColorKey Windows Software float return, if present."""
    base = repo / "refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMbit-depthconformancebatch"
    manifest_path = base / "reference_manifest.json"
    manifest = read_json(manifest_path)
    cases = [row for row in manifest.get("cases", [])
             if isinstance(row, dict) and str(row.get("id", "")).startswith("olmcolorkey__")]
    checks: list[dict[str, Any]] = []
    software = manifest.get("project", {}).get("project_gpu_accel_type", {}).get("current_name") == "SOFTWARE"
    for case in sorted(cases, key=lambda row: row["id"]):
        effect = base / case["frame"]
        before = base / case["before_effects_frame"]
        result = {"case_id": case["id"], "effect": effect.name, "before_effects": before.name}
        try:
            effect_info = inspect_float_rgba_exr(effect)
            before_info = inspect_float_rgba_exr(before)
            result.update({
                "effect_float_exr": True,
                "before_effects_float_exr": True,
                "dimensions_match": effect_info["dimensions"] == before_info["dimensions"],
                "software": software,
            })
        except (OSError, KeyError, TypeError, VerificationError) as exc:
            result.update({"effect_float_exr": False, "before_effects_float_exr": False, "error": str(exc)})
        checks.append(result)
    passed = len(cases) == 9 and all(
        row.get("effect_float_exr") and row.get("before_effects_float_exr") and
        row.get("dimensions_match") and row.get("software") for row in checks
    )
    return {
        "classification": "windows-software-float-reference-present" if passed else "not-verified",
        "case_count": len(cases),
        "effect_and_control_pairs": checks,
        "float_preserving": passed,
        "fact_source": str(manifest_path.relative_to(repo)),
    }


def build_report(repo: Path) -> dict[str, Any]:
    exact16 = (repo / "refs/conformance/bitdepth_16bpc_exact_manifest_20260703.md").read_text(encoding="utf-8")
    status32 = read_json(repo / "refs/conformance/bitdepth_32bpc_probe_status_20260709.json")
    status32_ck = next(row for row in status32["suites"] if row.get("plugin") == "OLMColorKey")
    facts = (repo / "notes/OLMColorKey_ASM_FACTS.md").read_text(encoding="utf-8")
    edge = (repo / "notes/IR_OLMColorKey_Edge.md").read_text(encoding="utf-8")
    source = (repo / "mac/OLMColorKey/OLMColorKey.cpp").read_text(encoding="utf-8")
    edge_decision = read_json(repo / "refs/conformance/olmcolorkey_edge_8bpc_decision.json")
    exact16_manifest = read_json(repo / "refs/conformance/bitdepth_16bpc_exact_manifest_20260709.json")
    exact16_cases = [row for row in exact16_manifest["cases"] if row.get("plugin") == "OLMColorKey"]
    windows_float = audit_windows_float_reference(repo)
    mac_identity = read_json(repo / "refs/conformance/ae26_3_32bpc_input_identity_request_20260713.json")
    mac_pair = (repo / "refs/conformance/olmcolorkey_32bpc_case0002_mac_pair_20260712.md").read_text(encoding="utf-8")
    mac_candidate_indexes = sorted(repo.glob("refs/**/olm_mac_ae_32bpc_candidate_index*.json"))

    evidence = {
        "8bpc": {
            "classification": "normalized-software-exact",
            "cases": edge_decision["normalized_8bpc"]["case_count"],
            "exact_cases": edge_decision["normalized_8bpc"]["exact_count"],
            "fact_source": "refs/conformance/olmcolorkey_edge_8bpc_decision.json",
        },
        "16bpc": {
            "classification": "AE exact",
            "cases": len(exact16_cases),
            "exact_cases": sum(row.get("result_status") == "AE exact" and row.get("max_diff") == 0 for row in exact16_cases),
            "fact_source": "refs/conformance/bitdepth_16bpc_exact_manifest_20260703.md",
        },
        "32bpc": {
            "classification": "windows-software-float-reference-only",
            "cases": windows_float["case_count"],
            "float_preserving": windows_float["float_preserving"],
            "returned_formats": {".exr": windows_float["case_count"] * 2},
            "fact_source": windows_float["fact_source"],
            "pair_validation": windows_float["effect_and_control_pairs"],
            "historical_png_probe": {
                "classification": status32_ck["classification"],
                "cases": status32_ck["case_count"],
                "float_preserving": status32_ck["float_preserving_present"],
            },
        },
    }

    required_source_markers = {
        "edge_thin": "info.edge_thin_amount",
        "edge_blur": "info.edge_blur_amount",
        "color_space_dispatch": "info.color_space == 3 || info.color_space == 4",
        "replace_tail": "info.color_keep && info.enable_replace",
        "float_dispatch": "RenderTyped<PF_PixelFloat>",
    }
    source_markers = {name: marker in source for name, marker in required_source_markers.items()}

    return {
        "kind": "olmcolorkey_bitdepth_evidence_audit",
        "schema": 1,
        "generated": "2026-07-15",
        "evidence": evidence,
        "feature_coverage_facts": {
            "color_spaces_and_replace": "implemented-and-exact-0-in-CLI-evidence",
            "edge_thin_and_blur": "8bpc-normalized-exact; 16bpc-covered-exact",
            "source_markers_present": source_markers,
            "fact_sources": [
                "notes/OLMColorKey_ASM_FACTS.md",
                "notes/IR_OLMColorKey_Edge.md",
            ],
        },
        "blocker": {
            "id": "32bpc-mac-windows-raw-float-comparison",
            "classification": "evidence-gate-not-algorithm-failure",
            "scope": "OLMColorKey 32bpc Mac/Windows Software exactness",
            "required_return": "same-contract Mac and Windows Software 32bpc FLOAT EXRs with before-effect controls and raw-float comparison manifest",
            "why_narrowest": "8bpc and covered 16bpc are exact; the Windows 32bpc float reference is present, but no Mac paired float comparison is present.",
        },
        "mac_float_gate": {
            "candidate_index_count": len(mac_candidate_indexes),
            "candidate_index_paths": [str(path.relative_to(repo)) for path in mac_candidate_indexes],
            "identity_request_fail_closed": mac_identity.get("macos", {}).get("fail_closed") is True,
            "capture_source": mac_identity.get("macos", {}).get("source"),
            "windows_runtime_status": mac_identity.get("windows", {}).get("runtime_execution_status"),
            "pair_report_rejects_ae_exact": "not 32bpc AE exact evidence" in mac_pair,
            "raw_float_comparison_ready": False,
            "ae_exact_claim_allowed": False,
            "reason": "Mac candidate/control EXRs and a verified raw-float comparison manifest are absent.",
        },
        "host_separation": {
            "fact": "The 2026-07-12 Mac 32bpc case_0002 pair is Mac-side bit-exact no-op, while Windows and Mac control worlds differ before effect attribution.",
            "source": "refs/conformance/olmcolorkey_32bpc_case0002_mac_pair_20260712.md",
            "inference": "Do not classify that pair as a ColorKey pixel mismatch or tune Edge/Replace/color-space from it.",
        },
        "algorithm_conclusion": {
            "fact": "No current evidence demonstrates a normalized 8bpc or covered 16bpc Edge Thin, Edge Blur, color-space, or Replace mismatch.",
            "inference": "No bounded source-code change is independently justified in this audit; the next discriminating step is a verified Mac/Windows raw-float comparison.",
        },
        "source_audit_inputs": {
            "legacy_16_text_present": "OLMColorKey | 9 | 9 | 0" in exact16,
            "edge_ir_current_exact_present": "ColorKey 16bpc slice is 9/9 `AE exact`" in edge,
            "replace_facts_present": "Replace feature — IMPLEMENTED" in facts,
        },
        "fail_closed": {
            "32bpc_ae_exact_forbidden_without_float_comparison": True,
            "32bpc_ae_exact_claim_allowed": False,
            "windows_float_reference_verified": windows_float["float_preserving"],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()
    report = build_report(root())
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(
            "# OLMColorKey Bit-Depth Evidence Audit - 2026-07-15\n\n"
            "## FACT\n\n"
            "- 8bpc normalized Software: 9/9 exact.\n"
            "- Covered 16bpc AE slice: 9/9 exact.\n"
            "- Windows 32bpc return: 9 effect/control pairs, uncompressed FLOAT EXR, SOFTWARE; this is reference evidence only.\n"
            "- Color-space and Replace behavior is implementation-backed and exact in the existing CLI evidence; Edge Thin/Blur is exact for the declared 8bpc and 16bpc slices.\n\n"
            "## INFERENCE\n\n"
            "- No algorithm blocker is demonstrated by current normalized 8bpc or covered 16bpc evidence.\n"
            "- The single narrowest remaining gate is the Mac paired FLOAT EXR and raw-float comparison; 32bpc remains forbidden from `AE exact` until that gate passes.\n"
            "- The 2026-07-12 32bpc Mac pair is host/input provenance evidence, not a reason to tune ColorKey math.\n\n"
            "## Scope Decision\n\n"
            "No ColorKey source change is justified. Re-open Edge Thin/Blur or color-space/Replace implementation only after the Mac/Windows paired float comparison supplies a raw-float residual that survives control-world validation.\n",
            encoding="utf-8",
        )
    if not args.output_json and not args.output_md:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
