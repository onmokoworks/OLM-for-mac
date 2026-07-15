#!/usr/bin/env python3
"""Check the local, typed RadialBlur sampler/prepass/writeback boundary.

This is an analysis tool, not a renderer.  It accepts either the forthcoming
typed return (``events`` with ``RB9_POINT_TYPED`` fields) or a normalized
``points`` document.  A small existing local typed-plane fixture is accepted
as a producer-only check.  Missing fields fail closed.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
from pathlib import Path
from typing import Any

TARGETS = {(7, 0), (8, 0), (24, 0)}
SLOTS = ("00", "10", "01", "11")


def f32_word(value: Any) -> float:
    text = str(value).strip().lower().removeprefix("0x")
    if len(text) != 8:
        raise ValueError("expected one eight-digit float32 word")
    return struct.unpack("<f", struct.pack("<I", int(text, 16)))[0]


def float_value(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if len(text.replace("0x", "")) == 8 and all(c in "0123456789abcdefABCDEF" for c in text.replace("0x", "")):
        return f32_word(text)
    return float(text)


def vector(value: Any, size: int) -> list[float]:
    if isinstance(value, str):
        values = value.split(",")
    else:
        values = list(value)
    if len(values) != size:
        raise ValueError(f"expected {size} values")
    return [float_value(item) for item in values]


def field(row: dict[str, Any], name: str) -> Any:
    if name in row:
        return row[name]
    raise KeyError(name)


def canonical_points(document: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    if isinstance(document.get("points"), list):
        return document["points"], "fullframe_typed"
    events = [event for event in document.get("events", []) if event.get("prefix") == "RB9_POINT_TYPED"]
    if events:
        return [event.get("fields", {}) for event in events], "fullframe_typed"
    records = document.get("records")
    if isinstance(records, list) and records:
        return records, "local_fixture"
    raise ValueError("no typed points, RB9_POINT_TYPED events, or local records found")


def normalize_point(row: dict[str, Any]) -> dict[str, Any]:
    if "xy" in row:
        xy = [int(v) for v in row["xy"]]
        radius = float_value(row.get("radius_index"))
        angle = float_value(row.get("angle_index"))
        weights = vector(row.get("bilinear_weights"), 4)
        cells = row.get("cells", {})
        result = {"xy": xy, "radius": radius, "angle": angle, "weights": weights}
        for slot in SLOTS:
            cell = cells.get(slot) or cells.get({"00": "cell00", "10": "cell10", "01": "cell01", "11": "cell11"}[slot])
            if not cell:
                raise KeyError(f"cell{slot}")
            result[f"accum{slot}"] = vector(cell.get("accum_rgba_f32"), 4)
            result[f"denom{slot}"] = float_value(cell.get("denom_f32"))
            result[f"valid{slot}"] = float_value(cell.get("valid_f32"))
            result[f"final{slot}"] = vector(cell.get("final_rgba_f32"), 4)
        return result

    result = {
        "xy": [int(field(row, "x")), int(field(row, "y"))],
        "radius": f32_word(field(row, "radius_index")),
        "angle": f32_word(field(row, "angle_index")),
        "weights": vector(field(row, "bilinear_weights"), 4),
    }
    for slot in SLOTS:
        result[f"accum{slot}"] = vector(field(row, f"cell{slot}_accum_rgba"), 4)
        result[f"denom{slot}"] = f32_word(field(row, f"cell{slot}_denom"))
        result[f"valid{slot}"] = f32_word(field(row, f"cell{slot}_valid"))
        result[f"final{slot}"] = vector(field(row, f"cell{slot}_final_rgba"), 4)
    return result


def close(actual: float, expected: float, tolerance: float = 2e-6) -> bool:
    return math.isfinite(actual) and math.isfinite(expected) and abs(actual - expected) <= tolerance


def raw_word_matches(value: float, word: Any) -> bool:
    try:
        return f32_word(word) == struct.unpack("<f", struct.pack("<f", value))[0]
    except (TypeError, ValueError, struct.error, OverflowError):
        return False


def check_worker_slice_capture(capture: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    cells = capture.get("nonzero_cells")
    if not isinstance(cells, list):
        return ["worker_capture_missing_nonzero_cells"]
    for index, cell in enumerate(cells):
        rgba = cell.get("rgba_f32")
        words = cell.get("rgba_f32_words")
        scalar = cell.get("scalar_f32")
        scalar_word = cell.get("scalar_f32_word")
        if not isinstance(rgba, list) or len(rgba) != 4 or not isinstance(words, list) or len(words) != 4:
            issues.append(f"worker_capture_cell[{index}]_rgba_float32_shape")
        elif not all(raw_word_matches(value, word) for value, word in zip(rgba, words)):
            issues.append(f"worker_capture_cell[{index}]_rgba_raw_word_mismatch")
        try:
            scalar_float = float(scalar)
        except (TypeError, ValueError, OverflowError):
            scalar_float = math.nan
        if not raw_word_matches(scalar_float, scalar_word):
            issues.append(f"worker_capture_cell[{index}]_scalar_raw_word_mismatch")
        try:
            finite = all(math.isfinite(float(value)) for value in list(rgba or []) + [scalar])
        except (TypeError, ValueError, OverflowError):
            finite = False
        if not finite:
            issues.append(f"worker_capture_cell[{index}]_nonfinite_float32")
    return sorted(set(issues))


def analyze_differential(document: dict[str, Any]) -> dict[str, Any]:
    pair = document.get("differential")
    if not isinstance(pair, dict) or not isinstance(pair.get("live"), dict) or not isinstance(pair.get("noop"), dict):
        raise ValueError("differential requires live and noop reports")
    live, noop = pair["live"], pair["noop"]
    issues: list[str] = []

    live_exec = live.get("worker_execution", {})
    noop_exec = noop.get("worker_execution", {})
    if live.get("status") != "ok" or live_exec.get("prepass") != "actual-aex":
        issues.append("live_actual_aex_prepass_not_proven")
    if int(live_exec.get("prepass_calls", 0)) < 1 or int(live_exec.get("b150_returns", 0)) < 1:
        issues.append("live_b150_hit_and_return_not_proven")
    if int(noop_exec.get("prepass_detour_calls", 0)) != 1:
        issues.append("noop_b150_detour_hit_not_proven")

    live_records = live.get("b150_input_capture", [])
    noop_records = noop.get("b150_input_capture", [])
    if len(live_records) != 1 or len(noop_records) != 1:
        issues.append("differential_requires_one_b150_record_each")
    else:
        live_abi = live_records[0].get("abi", {})
        noop_abi = noop_records[0].get("abi", {})
        semantic_fields = ("width", "row_limit", "row_start", "row_end")
        for name in semantic_fields:
            if live_abi.get(name) != noop_abi.get(name):
                issues.append(f"b150_{name}_not_reproducible")
        for name in ("source_rgba_f32", "scalar_a_f32", "scalar_b_f32"):
            if live_records[0].get("rows") != noop_records[0].get("rows"):
                issues.append("b150_source_or_scalar_inputs_not_reproducible")
                break
        if live_records[0].get("context_fields") != noop_records[0].get("context_fields"):
            issues.append("b150_spans_not_reproducible")

        live_before = live_records[0].get("worker_owned_before_return")
        noop_before = noop_records[0].get("worker_owned_before_return")
        live_after = live_records[0].get("worker_owned_after_return")
        noop_after = noop_records[0].get("worker_owned_after_return")
        for label, capture in (("live_before", live_before), ("noop_before", noop_before),
                               ("live_after", live_after), ("noop_after", noop_after)):
            if not isinstance(capture, dict):
                issues.append(f"{label}_worker_capture_missing")
            else:
                issues.extend(f"{label}:{issue}" for issue in check_worker_slice_capture(capture))
        if isinstance(live_before, dict) and isinstance(noop_before, dict):
            if (live_before.get("rgba_sha256"), live_before.get("scalar_sha256")) != (noop_before.get("rgba_sha256"), noop_before.get("scalar_sha256")):
                issues.append("worker_owned_inputs_differ_before_b150")
        if isinstance(live_after, dict) and isinstance(noop_after, dict):
            if (live_after.get("rgba_sha256"), live_after.get("scalar_sha256")) == (noop_after.get("rgba_sha256"), noop_after.get("scalar_sha256")):
                issues.append("live_b150_did_not_change_worker_owned_outputs")

    return {
        "kind": "olmradialblur_case0009_sampler_prepass_writeback_analysis",
        "schema": 2,
        "evidence_class": "bounded_actual_aex_differential",
        "status": "pass" if not issues else "fail",
        "classification": "bounded-aex-worker-differential-proven" if not issues else "bounded-aex-worker-differential-failed",
        "scope": "FUN_18000B150 worker-owned RGBA/scalar row-slice differential and float32 word invariants",
        "issues": sorted(set(issues)),
        "limitations": [
            "Bounded direct-core emulator evidence only; not full-frame case_0009 evidence.",
            "Does not compare Windows and Mac outputs or make an AE-exact claim.",
            "Does not authorize PNG tuning or production-code changes.",
        ],
    }


def check_point(point: dict[str, Any]) -> dict[str, Any]:
    radius, angle = point["radius"], point["angle"]
    fr, fa = radius - math.floor(radius), angle - math.floor(angle)
    expected_weights = [(1 - fr) * (1 - fa), fr * (1 - fa), (1 - fr) * fa, fr * fa]
    weights = point["weights"]
    issues: list[str] = []
    if not all(close(a, b) for a, b in zip(weights, expected_weights)):
        issues.append("sampler_weights_do_not_match_fractional_indices")
    if not close(sum(weights), 1.0):
        issues.append("sampler_weights_sum_not_one")
    producer_checks = 0
    for slot in SLOTS:
        accum = point[f"accum{slot}"]
        denom = point[f"denom{slot}"]
        final = point[f"final{slot}"]
        if denom != 0.0:
            producer_checks += 1
            if not close(final[3], denom):
                issues.append(f"cell{slot}_final_alpha_not_denom")
            if accum[3] != 0.0:
                expected_rgb = [channel / accum[3] for channel in accum[:3]]
                if not all(close(final[i], expected_rgb[i]) for i in range(3)):
                    issues.append(f"cell{slot}_final_rgb_not_accum_rgb_over_accum_alpha")
    return {
        "xy": point["xy"],
        "radius_index": radius,
        "angle_index": angle,
        "fractional_indices": [fr, fa],
        "weights": weights,
        "expected_weights": expected_weights,
        "producer_cells_checked": producer_checks,
        "issues": sorted(set(issues)),
        "status": "pass" if not issues else "fail",
    }


def analyze(document: dict[str, Any]) -> dict[str, Any]:
    if "differential" in document:
        return analyze_differential(document)
    rows, evidence_class = canonical_points(document)
    if evidence_class == "local_fixture":
        checks: list[dict[str, Any]] = []
        issues: list[str] = []
        for index, row in enumerate(rows):
            accum = vector(row.get("accum_rgba_f32"), 4)
            denom = float_value(row.get("denom_f32"))
            final = vector(row.get("final_rgba_f32"), 4)
            row_issues: list[str] = []
            if denom != 0.0 and not close(final[3], denom):
                row_issues.append("final_alpha_not_denom")
            if accum[3] != 0.0 and not all(close(final[i], accum[i] / accum[3]) for i in range(3)):
                row_issues.append("final_rgb_not_accum_rgb_over_accum_alpha")
            issues.extend(f"record[{index}]: {issue}" for issue in row_issues)
            checks.append({
                "record": index,
                "angle_index": row.get("angle_idx"),
                "radius_index": row.get("radius_idx"),
                "producer_cells_checked": 1,
                "issues": row_issues,
                "status": "pass" if not row_issues else "fail",
            })
        return {
            "kind": "olmradialblur_case0009_sampler_prepass_writeback_analysis",
            "schema": 1,
            "evidence_class": evidence_class,
            "status": "pass" if not issues else "fail",
            "classification": "local-invariant-proven" if not issues else "local-invariant-failed",
            "scope": "sampler fractional weights, prepass normalization, and final-polar writeback only",
            "checks": checks,
            "issues": issues,
            "limitations": [
                "Does not compare Windows and Mac outputs.",
                "Does not infer AE behavior or authorize a production change.",
                "This fixture has no output-coordinate sampler rows; only producer normalization is checked.",
            ],
        }
    points = [normalize_point(row) for row in rows]
    if evidence_class == "fullframe_typed":
        got = {tuple(point["xy"]) for point in points}
        if got != TARGETS:
            raise ValueError(f"full-frame targets must be exactly {sorted(TARGETS)}, got {sorted(got)}")
    checks = [check_point(point) for point in points]
    issues = [f"{item['xy']}: {issue}" for item in checks for issue in item["issues"]]
    return {
        "kind": "olmradialblur_case0009_sampler_prepass_writeback_analysis",
        "schema": 1,
        "evidence_class": evidence_class,
        "status": "pass" if not issues else "fail",
        "classification": "local-invariant-proven" if not issues else "local-invariant-failed",
        "scope": "sampler fractional weights, prepass normalization, and final-polar writeback only",
        "checks": checks,
        "issues": issues,
        "limitations": [
            "Does not compare Windows and Mac outputs.",
            "Does not infer AE behavior or authorize a production change.",
            "A passing local fixture proves only the stated algebra for that fixture.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()
    result = analyze(json.loads(args.input.read_text(encoding="utf-8")))
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(payload, encoding="utf-8")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# OLMRadialBlur case0009 sampler/prepass/writeback local analysis",
            "",
            f"- Evidence class: `{result['evidence_class']}`",
            f"- Status: `{result['status']}`",
            f"- Classification: `{result['classification']}`",
            "",
            "The analyzer checks bilinear weight geometry and the local producer relation "
            "`final.rgb = accum.rgb / accum.alpha`, `final.alpha = denom` when defined. "
            "For the existing local producer fixture, sampler geometry is intentionally "
            "not claimed because it has no output-coordinate rows. It does not make an "
            "AE-exact claim.",
            "",
        ]
        if result["evidence_class"] == "bounded_actual_aex_differential":
            lines.extend([
                "The bounded differential requires an actual live B150 hit and return, "
                "a paired no-op-detour hit, reproducible typed inputs/spans, changed "
                "worker-owned outputs only, and exact raw float32 word invariants.",
                "",
            ])
        else:
            for check in result["checks"]:
                label = tuple(check["xy"]) if "xy" in check else f"record {check['record']}"
                lines.append(f"- `{label}`: `{check['status']}`, producer cells checked `{check['producer_cells_checked']}`")
        if result["issues"]:
            lines.extend(["", "Issues:", *[f"- {issue}" for issue in result["issues"]]])
        args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"status={result['status']} evidence_class={result['evidence_class']}")
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
