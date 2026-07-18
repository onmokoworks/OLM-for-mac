#!/usr/bin/env python3
"""Fail-closed ownership test for the stale ColorKey case_0005/0006 trace."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex"
DECOMP = ROOT / "decomp/OLMColorKey.aex.c.txt"
TRACE = ROOT / "refs/reports/runtime_trace_comparisons/olmcolorkey_edge_trace_latest.json"
VALIDATION = ROOT / (
    "refs/reports/ae_host_validation_20260618_232926/"
    "ae_pixel_olmcolorkey_20260606/reports/ae_pixel_edgethin_residual.json"
)
AMOUNT_AUDIT = ROOT / "refs/conformance/olmcolorkey_edge_thin_caller_amount_20260718.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> dict:
    trace = json.loads(TRACE.read_text(encoding="utf-8"))
    validation = json.loads(VALIDATION.read_text(encoding="utf-8"))
    amount_audit = json.loads(AMOUNT_AUDIT.read_text(encoding="utf-8"))
    decomp = DECOMP.read_text(encoding="utf-8")

    rows = {case: trace["local"]["cases"][case] for case in ("case_0005", "case_0006")}
    assert all(row and row[0]["edge_blur_amount"] == 0 for row in rows.values())
    assert all(row[0]["edge_thin_amount"] == -16 for row in rows.values())
    assert all(row[0]["edge_thin_dist"] == row[0]["edge_thin_limit"] for row in rows.values())

    validation_rows = {row["id"]: row for row in validation["cases"]}
    assert all(validation_rows[case]["max_diff"] == 0 for case in ("case_0005", "case_0006"))
    assert all(validation_rows[case]["nonzero_px"] == 0 for case in ("case_0005", "case_0006"))

    # These are the current AEX's two mutually exclusive orchestration arms.
    blur_bypass = "if (*(float *)(param_5 + 0x40) == 0.0)" in decomp
    blur_apply_call = "FUN_1800085b0(param_1,puVar8" in decomp
    thin_negative_compare = "if (fVar14 <= 0.0)" in decomp and "!= *local_238" in decomp
    assert blur_bypass and blur_apply_call and thin_negative_compare

    assert amount_audit["status"] == "pass"
    assert amount_audit["matrix_counts"] == {"amounts": 7, "comparisons": 54, "distance_types": 3}

    return {
        "kind": "olmcolorkey_edge_residual_20260718",
        "schema": 1,
        "status": "pass",
        "scope": "Mac-only provenance and current-AEX ownership test; no PNG or production-source mutation",
        "aex": {"path": str(AEX.relative_to(ROOT)), "sha256": sha256(AEX)},
        "evidence": {
            "stale_trace": str(TRACE.relative_to(ROOT)),
            "later_validation": str(VALIDATION.relative_to(ROOT)),
            "amount_audit": str(AMOUNT_AUDIT.relative_to(ROOT)),
            "decomp": str(DECOMP.relative_to(ROOT)),
        },
        "case_matrix": {
            case: {
                "trace_edge_thin_amount": rows[case][0]["edge_thin_amount"],
                "trace_edge_thin_distance": rows[case][0]["edge_thin_dist"],
                "trace_edge_blur_amount": rows[case][0]["edge_blur_amount"],
                "later_validation_max_diff": validation_rows[case]["max_diff"],
                "later_validation_nonzero_px": validation_rows[case]["nonzero_px"],
            }
            for case in ("case_0005", "case_0006")
        },
        "binary_facts": {
            "zero_edge_blur_bypasses_apply": True,
            "edge_blur_apply_leaf": "FUN_1800085b0",
            "negative_edge_thin_branch_is_inline": True,
            "negative_edge_thin_equality_is_retained": True,
        },
        "finding": "The old 9,860-pixel case_0005/0006 alpha difference is stale trace-pair evidence, not a current Edge Blur residual: both cases have Edge Blur Amount 0, the current AEX bypasses the blur apply leaf, the active negative Edge Thin witness is equality-retaining, and the later Mac validation is exact for both cases.",
        "claims": {"ae_exact_claim": False, "production_edit": False, "png_tuning": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    try:
        report = run()
    except Exception as error:
        print(json.dumps({"status": "blocked", "error": str(error)}, sort_keys=True))
        return 2
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "aex_sha256": report["aex"]["sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
