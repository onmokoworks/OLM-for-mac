#!/usr/bin/env python3
"""Classify the bounded OLMDistanceGradation 16bpc residual families.

This is an evidence index, not a renderer or a source-tuning tool.  It reads
existing conformance JSON/Markdown artifacts and deliberately records missing
Windows boundaries instead of filling them with inferred values.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BOUNDARY_JSON = ROOT / "refs" / "conformance" / "olmdistancegradation_opencv_pf16_boundary_20260711.json"
ROUNDING_JSON = ROOT / "refs" / "conformance" / "olmdistancegradation_16bpc_export_rounding_residual_audit_20260709.json"
COMPOSE_JSON = ROOT / "refs" / "conformance" / "olmdg_compose_exact_address_witness_20260710.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def evidence(path: Path, kind: str, claim: str, status: str = "present") -> dict[str, str]:
    return {"path": rel(path), "kind": kind, "status": status, "claim": claim}


def build_report() -> dict[str, Any]:
    boundary = read_json(BOUNDARY_JSON)
    rounding = read_json(ROUNDING_JSON)
    compose = read_json(COMPOSE_JSON)
    ae = boundary["ae_16bpc"]
    rows = {row["case_id"].removeprefix("case_"): row for row in ae["rows"]}
    exact = [case.removeprefix("case_") for case in ae["exact_cases"]]
    expected_exact = ["0008", "0010", "0011", "0020", "0021", "0022", "0023"]
    if exact != expected_exact:
        raise ValueError(f"unexpected exact set: {exact}")

    families = [
        {
            "id": "exact",
            "cases": exact,
            "classification": "ae-exact-control",
            "measured": {case: rows[case] for case in exact},
            "typed_evidence": [
                evidence(BOUNDARY_JSON, "typed", "Current Mac AE 16bpc result reports max=0 and nonzero_pixels=0 for all seven cases."),
            ],
            "binary_evidence": [
                evidence(COMPOSE_JSON, "binary", "The bounded actual-AEX compose witness validates the 16bpc callback shape for the 0010/0011 control lane; it is local evidence, not a Windows live return."),
            ],
            "next_missing_boundary": "none-for-this-control-slice",
            "next_evidence": "Preserve these seven cases as controls while closing the three unresolved families.",
        },
        {
            "id": "layer-no-bg",
            "cases": ["0012", "0013", "0014", "0016"],
            "classification": "residual-max-2-with-case-0014-max-4",
            "measured": {case: rows[case] for case in ["0012", "0013", "0014", "0016"]},
            "typed_evidence": [
                evidence(BOUNDARY_JSON, "typed", "Current AE rows are small even-valued residuals: 0012/0013/0016 max=2 and 0014 max=4."),
                evidence(ROUNDING_JSON, "typed", "Existing samples show the Layer/no-bg residual at the exported true16 words, including the 0012 +/-2 and 0014 -4 RGB witnesses."),
                evidence(ROOT / "refs" / "conformance" / "olmdistancegradation_0012_0014_store_export_local_audit_20260710.md", "typed", "Local audit keeps both cases open and records the representative store/export values without claiming Windows pre-store values."),
            ],
            "binary_evidence": [
                evidence(ROOT / "refs" / "conformance" / "olmdistancegradation_16bpc_rejected_layer_unpremultiply_20260629.md", "binary", "The rejected Layer unpremultiply experiment rules out a broad ownership change from the existing evidence."),
            ],
            "next_missing_boundary": "Windows source RGBA16 -> normalized source -> composed RGBA float -> PF16 store words -> same-run true16 export",
            "next_evidence": "One same-run typed witness at case_0012 (438,0) and case_0014 (448,0), with all six stages bound.",
        },
        {
            "id": "max-2",
            "cases": ["0024", "0025", "0026", "0027"],
            "classification": "broad-field-export-residual-max-2",
            "measured": {case: rows[case] for case in ["0024", "0025", "0026", "0027"]},
            "typed_evidence": [
                evidence(BOUNDARY_JSON, "typed", "Current AE rows report max=2 for each case; the family remains non-exact despite the PF16 boundary improvement."),
                evidence(ROOT / "refs" / "conformance" / "olmdistancegradation_depthgate_nearmiss_family_20260708.md", "typed", "Earlier max=1 byte-view/depthgate witnesses identify contour-region controls, but are not promoted over the canonical true16 result."),
            ],
            "binary_evidence": [
                evidence(BOUNDARY_JSON, "binary", "AEX facts identify FUN_181174760, FUN_18117ca50, and FUN_181170480 plus the OpenCV 4.5.5 round-to-nearest-even PF16 boundary."),
                evidence(ROOT / "tools" / "emulation" / "DG_FIELD_GEN_REPORT.md", "binary", "Disassembly-grounded field generation and threshold facts exist, but no case-specific Windows live field value is present for 0024..0027."),
            ],
            "next_missing_boundary": "case-0024..0027 Windows field-world value -> compose input -> PF16 store/export true16 binding",
            "next_evidence": "A paired typed witness for 0026/0027 should bind field value, interpolation output, render-mode branch, PF16 store, and same-run true16 export; do not reuse the stale max=1 classification as proof.",
        },
        {
            "id": "outlier-0028",
            "cases": ["0028"],
            "classification": "separate-large-field-source-or-premultiply-residual",
            "measured": {"0028": rows["0028"]},
            "typed_evidence": [
                evidence(BOUNDARY_JSON, "typed", "Current AE row reports max=3080 and 461476 nonzero pixels, separating 0028 from the max-2 family."),
                evidence(ROOT / "refs" / "conformance" / "olmdistancegradation_16bpc_case0027_analysis_20260628.md", "typed", "Existing neighboring power/layer analysis identifies source-zero and background contribution witnesses, but does not close 0028."),
            ],
            "binary_evidence": [
                evidence(ROOT / "notes" / "IR_OLMDistanceGradation.md", "binary", "The IR records the binary-backed field, source-mask, and compose stages relevant to separating field shape from source/premultiply ownership."),
                evidence(ROOT / "tools" / "emulation" / "DG_FIELD_GEN_REPORT.md", "binary", "Binary field-generation facts constrain the next probe without supplying an invented Windows value for 0028."),
            ],
            "next_missing_boundary": "case-0028 Windows source/premultiply ownership versus field-X shape at composed RGBA float",
            "next_evidence": "One 0028 witness must bind source alpha/RGB, field X, composed RGBA float, PF16 store, and true16 export in one run before choosing source or field ownership.",
        },
    ]
    covered = [case for family in families for case in family["cases"]]
    expected_cases = exact + ["0012", "0013", "0014", "0016", "0024", "0025", "0026", "0027", "0028"]
    if covered != expected_cases:
        raise ValueError(f"family partition is incomplete: {covered}")
    return {
        "kind": "olmdistancegradation_16bpc_residual_family_classifier",
        "schema": 1,
        "scope": "bounded residual-family audit using existing reports/results only",
        "bit_depth": 16,
        "source_results": {
            "current_boundary_report": rel(BOUNDARY_JSON),
            "rounding_report": rel(ROUNDING_JSON),
            "compose_witness": rel(COMPOSE_JSON),
        },
        "current_exact_cases": exact,
        "unresolved_family_ids": ["layer-no-bg", "max-2", "outlier-0028"],
        "families": families,
        "guardrails": [
            "No PNG-only tuning or production edits are part of this classifier.",
            "A local AEX/binary witness is labeled binary evidence and is never promoted to a Windows live value.",
            "Missing boundaries are named explicitly; no Windows values are invented.",
        ],
        "compose_status_observed": compose.get("status"),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMDistanceGradation 16bpc Residual-Family Classifier",
        "",
        "Scope: existing reports/results only; no PNG tuning, production edits, ledger edits, or invented Windows values.",
        "",
        f"- Exact control set: `{', '.join(report['current_exact_cases'])}`",
        "- Unresolved families: `layer-no-bg`, `max-2`, `outlier-0028`",
        "",
        "| Family | Cases | Classification | Next missing boundary |",
        "| --- | --- | --- | --- |",
    ]
    for family in report["families"]:
        lines.append(f"| `{family['id']}` | `{', '.join(family['cases'])}` | {family['classification']} | {family['next_missing_boundary']} |")
    for family in report["families"]:
        lines.extend(["", f"## `{family['id']}`", "", f"Next evidence: {family['next_evidence']}", "", "### Evidence", ""])
        for item in family["typed_evidence"] + family["binary_evidence"]:
            lines.append(f"- `{item['kind']}` `{item['status']}`: `{item['path']}` - {item['claim']}")
        lines.extend(["", "Measured rows:", "", "| Case | Max diff | Nonzero pixels |", "| --- | ---: | ---: |"])
        for case, row in family["measured"].items():
            lines.append(f"| `{case}` | {row['max_diff']} | {row['nonzero_pixels']} |")
    lines.extend(["", "## Boundary Discipline", "", *[f"- {guardrail}" for guardrail in report["guardrails"]], ""])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    report = build_report()
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"report_json={args.output_json}")
    print(f"report_md={args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
