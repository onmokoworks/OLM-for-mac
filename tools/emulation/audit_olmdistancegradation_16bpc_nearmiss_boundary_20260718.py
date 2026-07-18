#!/usr/bin/env python3
"""Audit the Mac-only boundary evidence for DistanceGradation 16bpc near-misses.

This is an evidence classifier, not a renderer and not an AE exactness test.
It deliberately refuses to attribute case_0012/0014 residuals to either host
conversion or the final PF16 store when the required Windows same-run values
are absent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_JSON = ROOT / "refs/conformance/olmdistancegradation_16bpc_nearmiss_boundary_20260718.json"
DEFAULT_MD = ROOT / "refs/conformance/olmdistancegradation_16bpc_nearmiss_boundary_20260718.md"

EVIDENCE = {
    "depth_gate": ROOT / "refs/conformance/olmdistancegradation_depth_gate_result_20260708.md",
    "failed_return": ROOT / "refs/reports/runtime_trace_summary_distancegradation_case0012_case0014_store_export_rounding_20260708_213751.json",
    "writer_boundary": ROOT / "refs/conformance/dg_pf16_writer_boundary_20260716.json",
    "writer_active_path": ROOT / "refs/conformance/dg_pf16_writer_active_path_20260716.json",
    "pf16_matrix": ROOT / "tools/emulation/test_dg_pf16_boundary_matrix_20260717.py",
    "field_staging": ROOT / "tools/emulation/test_dg_pf16_field_staging_differential_20260717.py",
    "adjacent_store_classifier": ROOT / "tools/emulation/test_olmdistancegradation_alpha_store_residual_20260716.py",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def classify() -> dict[str, Any]:
    missing = [str(path.relative_to(ROOT)) for path in EVIDENCE.values() if not path.is_file()]
    if missing:
        raise RuntimeError("missing evidence: " + ", ".join(missing))

    returned = load_json(EVIDENCE["failed_return"])
    result = returned["results"][0]
    cases = result["observations"]["cases"]
    case_ids = {case["case_id"] for case in cases}
    expected_ids = {
        "olmdistancegradation_extended__case_0012",
        "olmdistancegradation_extended__case_0014",
    }
    if case_ids != expected_ids:
        raise AssertionError(f"unexpected returned cases: {sorted(case_ids)}")

    required_missing = set(result["observations"]["directly_observed_vs_inferred"]["not_isolated"])
    required_absent = {
        "direct Windows pre-store float for case_0012 representative",
        "direct Windows PF16 store word for case_0012 representative",
        "same-run exported TIFF/EXR true16 for case_0012 representative",
        "direct Windows pre-store float for case_0014 representative",
        "direct Windows PF16 store word for case_0014 representative",
        "same-run exported TIFF/EXR true16 for case_0014 representative",
    }
    if not required_absent <= required_missing:
        raise AssertionError("failed return no longer has the expected missing-boundary evidence")

    depth_text = EVIDENCE["depth_gate"].read_text(encoding="utf-8")
    for needle in ("0012/0013/0014", "max=64", "0024..0027"):
        if needle not in depth_text:
            raise AssertionError(f"depth-gate report missing {needle!r}")

    writer = load_json(EVIDENCE["writer_boundary"])
    active = load_json(EVIDENCE["writer_active_path"])
    return {
        "schema": "olmdistancegradation.16bpc-nearmiss-boundary-audit/1",
        "generated_on": "2026-07-18",
        "status": "classified_not_separable_locally",
        "scope": ["case_0012", "case_0014"],
        "ae_exact_claim": False,
        "production_source_changed": False,
        "fact": {
            "depth_gate_batch": {
                "case_0012": {"nonzero_px": 272839, "max_diff": 64},
                "case_0014": {"nonzero_px": 377093, "max_diff": 64},
            },
            "returned_windows_package": {
                "status": result["status"],
                "project_renderer": result["observations"]["ae_context"]["project_renderer_name"],
                "bit_depth": result["observations"]["ae_context"]["bit_depth"],
                "same_run_windows_pre_store_float": False,
                "same_run_windows_pf16_store_word": False,
                "same_run_true16_export": False,
                "only_directly_observed": result["observations"]["directly_observed_vs_inferred"]["directly_observed"],
            },
            "mac_local_aex_writer": {
                "classification": writer["classification"],
                "rounding_instruction_observed": writer["conclusion"]["rounding_observation"],
                "upstream_scale": writer["conclusion"]["upstream_scale"],
                "direct_call_xrefs": writer["xref_and_upstream_audit"]["direct_call_or_jmp_xrefs"],
            },
            "mac_local_active_path": {
                "status": active["status"],
                "writer_hits": active["writer_hits"],
                "final_output_written": all(row["final_output_written"] for row in active["final_outputs"]),
            },
            "mac_local_synthetic_boundary": {
                "pf16_matrix_script": str(EVIDENCE["pf16_matrix"].relative_to(ROOT)),
                "field_staging_script": str(EVIDENCE["field_staging"].relative_to(ROOT)),
                "interpretation": "existing scripts assert actual-AEX/source equality on bounded synthetic PF16 fixtures; they do not assert target-case equality against Windows AE",
            },
        },
        "inference": {
            "host_conversion_vs_final_store": "not separable from existing Mac-only evidence",
            "host_conversion_only_explanation": "not proven",
            "final_pf16_store_only_explanation": "not proven",
            "final_writer_global_rounding_fix": "not authorized; adjacent 0010/0011 evidence has sign-flipped deltas and the target cases lack a live Windows store word",
            "safe_boundary": "upstream field/pre-store/store boundary remains unresolved for both target cases",
        },
        "required_next_evidence": [
            "For one coordinate in case_0012 and one in case_0014, capture in one Windows Software AE run: source PF16 words, field raw word or field float, compose pre-store float, PF16 stored word, and same-run true16 TIFF/EXR word.",
            "Capture the Mac AE counterpart at the same coordinates and parameters, preserving the same five boundaries.",
            "Only then compare host input conversion, compose pre-store value, PF16 writer result, and export independently.",
        ],
        "evidence_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in EVIDENCE.values()},
    }


def render_md(report: dict[str, Any]) -> str:
    fact = report["fact"]
    lines = [
        "# OLMDistanceGradation 16bpc near-miss boundary audit",
        "",
        "- Date: 2026-07-18",
        "- Scope: `case_0012` and `case_0014`, Mac-only evidence audit",
        f"- Status: `{report['status']}`",
        "- `AE exact`: **not claimed**",
        "- Production source and ledger: **unchanged**",
        "",
        "## FACT",
        "",
        f"- The depth-gated Mac AE batch records case_0012 as `nonzero_px={fact['depth_gate_batch']['case_0012']['nonzero_px']}`, `max_diff={fact['depth_gate_batch']['case_0012']['max_diff']}`.",
        f"- It records case_0014 as `nonzero_px={fact['depth_gate_batch']['case_0014']['nonzero_px']}`, `max_diff={fact['depth_gate_batch']['case_0014']['max_diff']}`.",
        f"- The returned Windows package is `{fact['returned_windows_package']['status']}` for `{fact['returned_windows_package']['bit_depth']}` / `{fact['returned_windows_package']['project_renderer']}`.",
        "- That return contains PNG bytes only for these representatives; it does not contain a fresh same-run Windows pre-store float, PF16 store word, or true16 TIFF/EXR value for either case.",
        f"- Mac-local direct writer evidence observes `{fact['mac_local_aex_writer']['rounding_instruction_observed']}`.",
        f"- The writer audit explicitly leaves upstream scale as `{fact['mac_local_aex_writer']['upstream_scale']}`.",
        f"- The bounded active-path census is `{fact['mac_local_active_path']['status']}` with writer hits `{fact['mac_local_active_path']['writer_hits']}`; final output was written in that synthetic fixture: `{fact['mac_local_active_path']['final_output_written']}`.",
        "- Existing PF16 matrix/field-staging scripts compare the Windows AEX leaves with the Mac production source on bounded synthetic buffers. They are useful local contract checks, not Windows AE conformance for 0012/0014.",
        "",
        "## INFERENCE",
        "",
        "- Existing evidence cannot separate host conversion from the final PF16 store for the two target cases.",
        "- A host-conversion-only explanation is unproven because the Windows pre-store value is missing.",
        "- A final-store-only explanation is unproven because the Windows store word is missing and the writer's upstream scale/callsite is unresolved.",
        "- The safe classification is the upstream field/pre-store/store boundary, not a PNG/export bug and not a justified global rounding fix.",
        "- Adjacent 0010/0011 store evidence must not be promoted to 0012/0014; its sign-flipped deltas reject one global store rule but do not identify the target-family cause.",
        "",
        "## Required Boundary Capture",
        "",
        "1. One Windows Software AE run per representative: source PF16 words, field raw word or float, compose pre-store float, PF16 stored word, and same-run true16 TIFF/EXR word.",
        "2. The same coordinate, parameters, and five boundaries on Mac AE.",
        "3. Compare each boundary separately before changing production code.",
        "",
        "## Reproduction",
        "",
        "```sh",
        "python3 tools/emulation/audit_olmdistancegradation_16bpc_nearmiss_boundary_20260718.py",
        "```",
        "",
        "The script exits successfully only when the retained evidence still supports the fail-closed classification. It does not build, install, or modify the plugin.",
        "",
        "## Evidence",
        "",
    ]
    lines.extend(f"- `{path}`" for path in report["evidence_sha256"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()
    report = classify()
    args.json.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    args.md.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "ae_exact_claim": report["ae_exact_claim"]}, indent=2))
    print(f"wrote_json={args.json}")
    print(f"wrote_md={args.md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
