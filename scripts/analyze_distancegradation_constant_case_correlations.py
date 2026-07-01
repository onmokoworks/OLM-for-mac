#!/usr/bin/env python3
"""Correlate Constant boundary diagnostics with case settings."""

from __future__ import annotations

import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
REF_MANIFEST = REPO / "refs" / "reports" / "ae_host_validation_20260618_232926" / "normalized_refs" / "OLMDistanceGradation_extended" / "reference_manifest.json"
TWO_STAGE_JSON = REPO / "refs" / "conformance" / "olmdistancegradation_16bpc_constant_two_stage_variants_20260630.json"
OUT_JSON = REPO / "refs" / "conformance" / "olmdistancegradation_16bpc_constant_case_correlations_20260630.json"
OUT_MD = REPO / "refs" / "conformance" / "olmdistancegradation_16bpc_constant_case_correlations_20260630.md"

FOCUS = ["case_0020", "case_0021", "case_0022", "case_0023"]


def load_case_params() -> dict[str, dict[str, object]]:
    data = json.loads(REF_MANIFEST.read_text(encoding="utf-8"))
    out: dict[str, dict[str, object]] = {}
    for case in data["cases"]:
        cid = case["id"]
        if cid not in FOCUS:
            continue
        params: dict[str, object] = {}
        for param in case["effects"][0]["params"]:
            if param.get("value") is None:
                continue
            params[param["name"]] = param["value"]
        out[cid] = params
    return out


def load_two_stage_results() -> dict[str, list[dict[str, object]]]:
    data = json.loads(TWO_STAGE_JSON.read_text(encoding="utf-8"))
    out: dict[str, list[dict[str, object]]] = {}
    for row in data["results"]:
        cid = row["case_id"].split("__")[-1]
        out[cid] = row["variant_results"]
    return out


def main() -> int:
    params_by_case = load_case_params()
    results_by_case = load_two_stage_results()

    rows = []
    for cid in FOCUS:
        params = params_by_case[cid]
        variants = results_by_case[cid]
        current = next(v for v in variants if v["variant"] == "current_constant")
        best_nonzero = min(variants, key=lambda r: (r["nonzero_px"], r["mean_diff"], r["max_diff"]))
        best_mean = min(variants, key=lambda r: (r["mean_diff"], r["nonzero_px"], r["max_diff"]))
        rows.append(
            {
                "case_id": cid,
                "in_out": params.get("In/Out"),
                "inside_threshold": params.get("Inside Threshold"),
                "outside_threshold": params.get("Outside Threshold"),
                "best_nonzero_variant": best_nonzero["variant"],
                "best_nonzero_px": best_nonzero["nonzero_px"],
                "current_nonzero_px": current["nonzero_px"],
                "best_mean_variant": best_mean["variant"],
                "best_mean_diff": best_mean["mean_diff"],
                "current_mean_diff": current["mean_diff"],
            }
        )

    payload = {
        "kind": "olmdistancegradation_16bpc_constant_case_correlations",
        "rows": rows,
        "reading": [
            "The only focused case where a plausible two-stage Constant variant improves both nonzero count and mean is case_0023.",
            "Among case_0020..0023, case_0023 is also the only one with `In/Out=Both` and `Outside Threshold=0`.",
            "case_0022 shares `In/Out=Both` and a low outside threshold, but its two-stage win is partial: nonzero count drops slightly while mean worsens sharply.",
            "This does not prove the real AEX rule, but it makes `Both + Outside Threshold=0` the cleanest local correlate for the helper-staging signal.",
        ],
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# OLMDistanceGradation 16bpc Constant Case Correlations - 2026-06-30",
        "",
        "Correlate the focused Constant boundary cases with the two-stage helper diagnostic.",
        "",
        "| Case | In/Out | Inside | Outside | Best by nonzero | Best by mean | Reading |",
        "| --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in rows:
        if row["best_nonzero_variant"] == "current_constant" and row["best_mean_variant"] == "current_constant":
            reading = "current stays best"
        elif row["best_nonzero_variant"] != "current_constant" and row["best_mean_variant"] == "current_constant":
            reading = "partial two-stage signal"
        elif row["best_nonzero_variant"] != "current_constant" and row["best_mean_variant"] != "current_constant":
            reading = "strongest two-stage signal"
        else:
            reading = "mixed"
        lines.append(
            f"| `{row['case_id']}` | {row['in_out']} | {row['inside_threshold']} | {row['outside_threshold']} | `{row['best_nonzero_variant']}` | `{row['best_mean_variant']}` | {reading} |"
        )
    lines.extend(
        [
            "",
            "## Reading",
            "",
            "- `case_0023` is the only focused case where the same two-stage family wins on both nonzero count and mean.",
            "- `case_0023` is also the only focused case with `Outside Threshold = 0`.",
            "- `case_0022` suggests some shared structure, but not a safe implementation rule yet.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"summary_json={OUT_JSON}")
    print(f"summary_md={OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
