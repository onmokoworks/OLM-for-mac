#!/usr/bin/env python3
"""Classify the 16bpc case_0010/0011 one-word alpha-store residual.

This is a Mac-local evidence classifier, not a renderer and not an AE oracle.
It deliberately consumes the retained typed/compose/store evidence instead of
recomputing PNGs or changing production formulas.  A non-zero exit means that
the checked evidence contract was not met.
"""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEFAULT_JSON = ROOT / "refs/conformance/olmdistancegradation_alpha_store_residual_20260716.json"
DEFAULT_MD = ROOT / "refs/conformance/olmdistancegradation_alpha_store_residual_20260716.md"

EVIDENCE = {
    "typed_audit": ROOT / "refs/conformance/olmdistancegradation_0010_0011_opencv_field_prep_audit_20260709.json",
    "compose_contract": ROOT / "refs/conformance/olmdistancegradation_0010_0011_compose_input_pointer_contract_20260709.md",
    "store_return": ROOT / "refs/conformance/olmdistancegradation_0010_0011_writeback_pointer_map_return_intake_20260709.md",
    "writer_boundary": ROOT / "refs/conformance/dg_pf16_writer_boundary_20260716.json",
    "writer_active_path": ROOT / "refs/conformance/dg_pf16_writer_active_path_20260716.json",
    "case0026_manifest": ROOT / "refs/conformance/olmdistancegradation_16bpc_livefield_source_actual_aex_20260713.json",
}

# Values are the retained, coordinate-bound Mac typed evidence and Windows
# PF16 words.  They are inputs to the classifier, not newly inferred words.
POINTS = [
    {
        "case_id": "case_0010",
        "xy": [6, 40],
        "family": "outside_actual_max",
        "mac_field_x": 0.9002838730812073,
        "mac_out_a": 0.0997161269187927,
        "mac_store_a": 3267,
        "windows_store_a": 3268,
    },
    {
        "case_id": "case_0010",
        "xy": [901, 394],
        "family": "inside_threshold_half_boundary",
        "mac_field_x": 0.6985930800437927,
        "mac_out_a": 0.3014069199562073,
        "mac_store_a": 9877,
        "windows_store_a": 9876,
    },
    {
        "case_id": "case_0011",
        "xy": [915, 392],
        "family": "inside_threshold_half_boundary",
        "mac_field_x": 0.1345367729663849,
        "mac_out_a": 0.8654632270336151,
        "mac_store_a": 28360,
        "windows_store_a": 28359,
    },
]


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def classify() -> dict[str, Any]:
    missing = [str(path.relative_to(ROOT)) for path in EVIDENCE.values() if not path.is_file()]
    if missing:
        raise RuntimeError("missing required evidence: " + ", ".join(missing))

    typed = load_json(EVIDENCE["typed_audit"])
    writer = load_json(EVIDENCE["writer_boundary"])
    active = load_json(EVIDENCE["writer_active_path"])
    case26 = load_json(EVIDENCE["case0026_manifest"])

    typed_points = {tuple(row["xy"]): row for row in typed["witnesses"]}
    typed_checks = []
    for point in POINTS:
        row = typed_points.get(tuple(point["xy"]))
        if row is None:
            raise RuntimeError(f"typed audit has no point {point['xy']}")
        typed_checks.append({
            "xy": point["xy"],
            "field_bits_reused": f32(row["mac_field_x"]) == f32(point["mac_field_x"]),
            "field_x": row["mac_field_x"],
            "family": row["family"],
        })

    deltas = [point["windows_store_a"] - point["mac_store_a"] for point in POINTS]
    sign_flip = any(delta < 0 for delta in deltas) and any(delta > 0 for delta in deltas)
    same_global_store_rule = len(set(deltas)) == 1
    active_writer_hits = sum(active["hooks"][key] != "0x0" for key in ("FUN_181458030", "FUN_1814581a0")) if False else len(active["writer_hits"])
    case26_missing_field_words = all(
        row.get("field_raw_words_agrb") is None and row.get("field_word_at_rcx_plus_2") is None
        for row in case26["point_candidates"]
        if row["case_id"] == "case_0026"
    )

    return {
        "schema": "olmdistancegradation.alpha-store-residual-classifier/1",
        "status": "classified_not_closed",
        "classification": "Mac-closable exclusions complete; upstream field/pre-store/store boundary remains unresolved",
        "ae_exact_claim": False,
        "production_edits": False,
        "inputs": {
            "points": POINTS,
            "typed_audit": str(EVIDENCE["typed_audit"].relative_to(ROOT)),
            "compose_contract": str(EVIDENCE["compose_contract"].relative_to(ROOT)),
            "store_return": str(EVIDENCE["store_return"].relative_to(ROOT)),
            "writer_boundary": str(EVIDENCE["writer_boundary"].relative_to(ROOT)),
            "writer_active_path": str(EVIDENCE["writer_active_path"].relative_to(ROOT)),
            "case0026_manifest": str(EVIDENCE["case0026_manifest"].relative_to(ROOT)),
        },
        "checks": {
            "typed_field_values_reproduce_retained_mac_bits": all(row["field_bits_reused"] for row in typed_checks),
            "store_deltas_windows_minus_mac": deltas,
            "sign_flip_present": sign_flip,
            "single_global_store_rule_possible": same_global_store_rule,
            "pf16_writer_direct_boundary_is_code_domain_only": writer["classification"].startswith("Mac-local Unicorn"),
            "pf16_writer_active_on_compose_fixture": active_writer_hits > 0,
            "case0026_exact_replay_fail_closed_without_field_words": case26_missing_field_words,
        },
        "typed_checks": typed_checks,
        "decision": {
            "final_pf16_rounding": "excluded: Windows-minus-Mac deltas are +1,-1,+/-1, not one global rule",
            "channel_layout": "excluded for this residual: accepted pointer map and matching alpha symptom do not identify a layout fault",
            "export": "excluded as the primary store residual: Windows PF16 store words already differ; same-run true16 export remains absent",
            "field_vs_compose_alpha": "not separable locally: typed Mac field values reproduce Mac behavior, but Windows consumed field/pre-store floats are absent",
            "allowed_next": "request or obtain coordinate-bound Windows field word and compose pre-store alpha; do not tune production source",
        },
        "limitations": [
            "The active-path writer census has zero writer hits on its bounded compose fixture; this is inactive_for_fixture, not global dead code.",
            "The direct PF16 writer boundary is actual-AEX code-domain evidence and does not prove the AE host dispatch or upstream scale.",
            "case_0026 remains partial because field raw words are missing; its output cannot be used to invent field words.",
            "No AE exact status is promoted.",
        ],
    }


def render_md(report: dict[str, Any]) -> str:
    checks = report["checks"]
    lines = [
        "# OLMDistanceGradation alpha-store residual classifier",
        "",
        f"- Status: `{report['status']}`",
        f"- Classification: `{report['classification']}`",
        "- FACT/INFERENCE boundary: the measured words and local evidence checks are FACT; the boundary assignment is INFERENCE constrained by those facts.",
        "- `AE exact` promotion: **No**.",
        "",
        "## FACT",
        "",
        "- Windows PF16 alpha-store words are `3268` at `case_0010 (6,40)`, `9876` at `case_0010 (901,394)`, and `28359` at `case_0011 (915,392)`.",
        "- Retained Mac stores are `3267`, `9877`, and `28360`; Windows-minus-Mac is `+1, -1, -1`.",
        f"- Typed Mac field-bit reuse check: `{checks['typed_field_values_reproduce_retained_mac_bits']}`.",
        f"- PF16 writer direct-boundary check: `{checks['pf16_writer_direct_boundary_is_code_domain_only']}`.",
        f"- Active compose fixture writer hits: `{int(checks['pf16_writer_active_on_compose_fixture'])}`.",
        f"- case_0026 missing-field-word fail-closed check: `{checks['case0026_exact_replay_fail_closed_without_field_words']}`.",
        "",
        "## INFERENCE",
        "",
        "- A single global final-writer rounding change is rejected by the sign-flipped one-word residual.",
        "- The residual is already present at the Windows PF16 store boundary, so PNG/export is not the primary explanation; same-run true16 export is still unproven.",
        "- Mac-side evidence cannot separate Windows field packing from compose pre-store alpha generation. The safe classification is the upstream field/pre-store/store boundary, with no production change authorized.",
        "",
        "## 未証明点",
        "",
        "- Windows coordinate-bound field raw words and the compose pre-store `out_a` for the three points.",
        "- A live AE host dispatch from compose to the PF16 writer; the bounded writer census is `inactive_for_fixture`.",
        "- Same-run true16 TIFF/EXR export values.",
        "",
        "## 実行コマンド/結果",
        "",
        "```sh",
        "python3 -m py_compile tools/emulation/test_olmdistancegradation_alpha_store_residual_20260716.py",
        "python3 tools/emulation/test_olmdistancegradation_alpha_store_residual_20260716.py",
        "```",
        "",
        "The witness exits successfully only when all referenced evidence files and typed checks are present. It writes this JSON and report without changing production source or PNG tuning.",
        "",
        "## 変更ファイル",
        "",
        "- `tools/emulation/test_olmdistancegradation_alpha_store_residual_20260716.py`",
        "- `refs/conformance/olmdistancegradation_alpha_store_residual_20260716.json`",
        "- `refs/conformance/olmdistancegradation_alpha_store_residual_20260716.md`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()
    report = classify()
    args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "ae_exact_claim": report["ae_exact_claim"], "deltas": report["checks"]["store_deltas_windows_minus_mac"]}, indent=2))
    print(f"wrote_json={args.json}")
    print(f"wrote_md={args.md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
