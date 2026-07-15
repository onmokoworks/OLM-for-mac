#!/usr/bin/env python3
"""Audit one binary-grounded boundary for the remaining DG 16bpc families.

The audit checks only the recorded compose-float -> PF16 store transition at
the four live case_0026 points. It never derives a field word from an image.
The 0012/0013/0014 rows are retained as bounded residual context.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = ROOT / "refs/conformance/olmdistancegradation_opencv_pf16_boundary_20260711.json"
LIVEFIELD = ROOT / "refs/conformance/olmdistancegradation_16bpc_livefield_source_actual_aex_20260713.json"
FIELD_REPORT = ROOT / "tools/emulation/DG_FIELD_GEN_REPORT.md"
TARGETS = ("case_0012", "case_0013", "case_0014", "case_0024", "case_0025", "case_0026", "case_0027")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} is not a JSON object")
    return value


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def store_word(value: float, alpha: bool) -> int:
    """Reproduce the observed typed store: RGB 15-bit, alpha full 16-bit."""
    scale = 65535.0 if alpha else 32768.0
    return max(0, min(65535, round(value * scale)))


def build_report() -> dict[str, Any]:
    boundary = load(BOUNDARY)
    live = load(LIVEFIELD)
    if not FIELD_REPORT.exists():
        raise ValueError(f"missing binary-grounded report: {FIELD_REPORT}")
    rows = {row["case_id"]: row for row in boundary["ae_16bpc"]["rows"]}
    for case in TARGETS:
        if case not in rows:
            raise ValueError(f"missing residual row for {case}")

    candidates = [item for item in live["point_candidates"] if item["case_id"] == "case_0026"]
    checks = []
    for item in candidates:
        pre = item.get("pre_pf16_output_rgba_float")
        carried = item.get("carried_pf_pixel16_words_after_store")
        if not isinstance(pre, list) or not isinstance(carried, list) or len(pre) != 4 or len(carried) != 4:
            raise ValueError(f"incomplete carried boundary record at {item.get('xy')}")
        expected = [store_word(float(value), alpha=index == 3) for index, value in enumerate(pre)]
        checks.append({
            "xy": item["xy"],
            "expected_store_rgba16": expected,
            "carried_store_agrb16": carried,
            "store_matches": expected == carried,
            "field_raw_words_present": item.get("field_raw_words_agrb") is not None,
            "field_x_consumed": item.get("field_value_consumed_by_fun_181170480"),
        })
    if not checks or not all(item["store_matches"] for item in checks):
        raise ValueError("recorded case_0026 compose/store boundary is not deterministic")

    return {
        "kind": "olmdistancegradation_16bpc_family_boundary_audit",
        "schema": 1,
        "scope": "binary-grounded local compose-float to PF16 store audit; no PNG tuning",
        "inputs": {"boundary": rel(BOUNDARY), "livefield": rel(LIVEFIELD), "binary_report": rel(FIELD_REPORT)},
        "FACT": {
            "binary_functions": ["FUN_181174760", "FUN_18117ca50", "FUN_181170480"],
            "pf16_conversion": boundary["binary_facts"]["pf16_conversion"],
            "case_0012_0013_0014_residuals": {case: rows[case] for case in ("case_0012", "case_0013", "case_0014")},
            "case_0024_0025_0026_0027_residuals": {case: rows[case] for case in ("case_0024", "case_0025", "case_0026", "case_0027")},
            "case_0026_store_checks": checks,
            "case_0026_raw_field_word_status": "missing at every audited point",
        },
        "INFERENCE": {
            "case_0012_0013_0014": "bounded even PF16 residuals remain compatible with a pre-store/store/export boundary; this audit does not choose ownership",
            "case_0024_0025_0026_0027": "case_0026 has no observed compose-float-to-store mismatch at four live points, so the remaining max-2 family boundary is upstream field-word capture or field generation; 0024/0025/0027 remain unbound",
        },
        "guardrails": [
            "No PNG path is an input to the audit.",
            "Missing field raw words are not reconstructed from field X, carried words, or images.",
            "A matching local store conversion does not promote the case to exact or prove Windows field generation.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    fact = report["FACT"]
    lines = [
        "# OLMDistanceGradation 16bpc Family Boundary Audit",
        "",
        "Scope: binary-grounded local compose-float to PF16 store check; no PNG tuning.",
        "",
        "## FACT",
        "",
        f"- Binary functions: `{', '.join(fact['binary_functions'])}`.",
        f"- PF16 conversion fact: `{fact['pf16_conversion']}`; the recorded typed store uses RGB scale `32768` and alpha scale `65535`.",
        "- `case_0026` recorded store words match recomputed normalized-float-to-uint16 words at all four live points.",
        "- The raw field word is missing at every audited point; no exact replay is claimed.",
        "",
        "| Family | Current residual / boundary result |",
        "| --- | --- |",
        "| `0012/0013/0014` | bounded even PF16 residuals; boundary ownership remains open |",
        "| `0024/0025/0026/0027` | `0026` store boundary matches at 4 points; field input remains unbound for all four |",
        "",
        "## INFERENCE",
        "",
        f"- `0012/0013/0014`: {report['INFERENCE']['case_0012_0013_0014']}.",
        f"- `0024/0025/0026/0027`: {report['INFERENCE']['case_0024_0025_0026_0027']}.",
        "",
        "## Guardrails",
        "",
        *[f"- {item}" for item in report["guardrails"]],
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    report = build_report()
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(markdown(report), encoding="utf-8")
    print(f"audit_json={args.output_json}")
    print(f"audit_md={args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
