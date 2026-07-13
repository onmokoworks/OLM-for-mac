#!/usr/bin/env python3
"""Compare Mac Debug raw coordinates/cells with the case_0009 actual-AEX witness."""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REFERENCE = ROOT / "refs/conformance/olmradialblur_case0009_fullframe_coordinate_cells_actual_aex_20260713.json"
POINTS = tuple((x, 0) for x in range(32))
LANES = ("production", "aex_f32_candidate")
CELL_SLOTS = ("a0_r0", "a0_r1", "a1_r0", "a1_r1")
OPERATION_FIELDS = ("dy", "dx", "cos_dy", "sin_dx", "ey_numerator", "ey", "sin_dy", "cos_dx",
                    "ex", "ex_squared", "ey_squared", "radius_squared")
BIT_RE = re.compile(r"0x[0-9a-f]{8}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mac-debug-json", type=Path, required=True)
    parser.add_argument("--reference-json", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--require-candidate-exact", action="store_true")
    parser.add_argument("--require-candidate-raw-exact", action="store_true")
    return parser.parse_args()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path}: {exc}") from exc


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def bits(value: float) -> str:
    return f"0x{struct.unpack('<I', struct.pack('<f', float(value)))[0]:08x}"


def points_by_xy(rows: Any, label: str) -> dict[tuple[int, int], dict[str, Any]]:
    if not isinstance(rows, list):
        raise ValueError(f"{label} is missing points[]")
    found: dict[tuple[int, int], dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"{label} contains a non-object point")
        if isinstance(row.get("xy"), list):
            xy = tuple(row["xy"])
        else:
            xy = (row.get("x"), row.get("y"))
        if len(xy) != 2 or not all(isinstance(value, int) and not isinstance(value, bool) for value in xy):
            raise ValueError(f"{label} contains a point without integer coordinates")
        if xy in found:
            raise ValueError(f"{label} contains duplicate point {xy}")
        found[xy] = row
    if set(found) != set(POINTS):
        missing = sorted(set(POINTS) - set(found))
        extra = sorted(set(found) - set(POINTS))
        raise ValueError(f"{label} must contain exactly x=0..31,y=0; missing={missing} extra={extra}")
    return found


def expected_from_reference(point: dict[str, Any]) -> dict[str, Any]:
    a850 = point.get("a850")
    indices = point.get("indices")
    selection = point.get("cell_selection")
    if not all(isinstance(value, dict) for value in (a850, indices, selection)):
        raise ValueError(f"reference point {point.get('xy')} is incomplete")
    radius_index = f32(indices["radius_index"])
    angle_index = f32(indices["angle_index"])
    radius0, radius1 = selection["radius_indices"]
    angle0, angle1 = selection["angle_indices"]
    cells = selection.get("cells")
    if not isinstance(cells, dict) or list(cells) != list(CELL_SLOTS):
        raise ValueError(f"reference point {point.get('xy')} has incomplete ordered cells")
    return {
        "radius_raw_bits": bits(a850["radius_raw_f32"]),
        "angle_raw_bits": bits(a850["angle_raw_f32"]),
        "radius_index_bits": bits(radius_index),
        "angle_index_bits": bits(angle_index),
        "radius_fraction_bits": bits(f32(radius_index - radius0)),
        "angle_fraction_bits": bits(f32(angle_index - angle0)),
        "radius_indices": [radius0, radius1],
        "angle_indices": [angle0, angle1],
        "cell_indices": [[angle0, radius0], [angle0, radius1], [angle1, radius0], [angle1, radius1]],
        "cell_rgba_bits": [[bits(value) for value in cells[slot]] for slot in CELL_SLOTS],
    }


def compare_lane(actual: dict[str, Any], expected: dict[str, Any]) -> tuple[str | None, dict[str, Any] | None]:
    for field in ("radius_raw_bits", "angle_raw_bits", "radius_index_bits", "angle_index_bits",
                  "radius_fraction_bits", "angle_fraction_bits", "radius_indices", "angle_indices", "cell_indices"):
        if actual.get(field) != expected[field]:
            return field, {"mac": actual.get(field), "aex": expected[field]}
    if actual.get("cell_values_available") is False:
        return "cell_values_available", {"mac": False, "aex": True}
    actual_cells = actual.get("cell_rgba_bits")
    if not isinstance(actual_cells, list) or len(actual_cells) != 4:
        return "cell_rgba_bits", {"mac": actual_cells, "aex": expected["cell_rgba_bits"]}
    for cell_index, (mac_cell, aex_cell) in enumerate(zip(actual_cells, expected["cell_rgba_bits"])):
        if mac_cell != aex_cell:
            return "cell_rgba_bits", {"slot": CELL_SLOTS[cell_index], "mac": mac_cell, "aex": aex_cell}
    return None, None


def compare_raw_a850(actual: dict[str, Any], expected: dict[str, Any]) -> tuple[str | None, dict[str, Any] | None]:
    for field in ("radius_raw_bits", "angle_raw_bits"):
        if actual.get(field) != expected[field]:
            return field, {"mac": actual.get(field), "aex": expected[field]}
    return None, None


def validate_raw_lane(lane: dict[str, Any], label: str, require_operations: bool) -> None:
    bit_fields = ("radius_raw_bits", "angle_raw_bits", "radius_index_bits", "angle_index_bits",
                  "radius_fraction_bits", "angle_fraction_bits")
    for field in bit_fields:
        if not isinstance(lane.get(field), str) or not BIT_RE.fullmatch(lane[field]):
            raise ValueError(f"{label} has invalid {field}")
    cells = lane.get("cell_rgba_bits")
    if not isinstance(cells, list) or len(cells) != 4 or any(
        not isinstance(cell, list) or len(cell) != 4 or
        any(not isinstance(value, str) or not BIT_RE.fullmatch(value) for value in cell)
        for cell in cells
    ):
        raise ValueError(f"{label} has invalid cell_rgba_bits")
    if require_operations:
        operations = lane.get("operation_bits")
        if not isinstance(operations, dict) or tuple(operations) != OPERATION_FIELDS or any(
            not isinstance(value, str) or not BIT_RE.fullmatch(value) for value in operations.values()
        ):
            raise ValueError(f"{label} has incomplete AEX-order operation_bits")


def compare(mac: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    if mac.get("kind") != "olmradialblur_debug_points":
        raise ValueError("Mac input is not an analyze_radialblur_debug_points report")
    if reference.get("kind") != "olmradialblur_case0009_fullframe_coordinate_cells_actual_aex_probe":
        raise ValueError("reference is not the case_0009 full-frame actual-AEX coordinate witness")
    mac_points = points_by_xy(mac.get("points"), "Mac report")
    ref_points = points_by_xy(reference.get("points"), "reference")
    index_cell_semantic = reference.get("index_cell_semantic") is True
    rows: list[dict[str, Any]] = []
    first = {lane: None for lane in LANES}
    match_counts = {lane: 0 for lane in LANES}
    raw_first = {lane: None for lane in LANES}
    raw_match_counts = {lane: 0 for lane in LANES}
    for xy in POINTS:
        raw = mac_points[xy].get("coordinate_raw")
        if not isinstance(raw, dict):
            raise ValueError(f"Mac point {xy} has no coordinate_raw capture")
        expected = expected_from_reference(ref_points[xy])
        lane_results: dict[str, Any] = {}
        for lane in LANES:
            actual = raw.get(lane)
            if not isinstance(actual, dict):
                raise ValueError(f"Mac point {xy} has no {lane} lane")
            validate_raw_lane(actual, f"Mac point {xy} {lane}", lane == "aex_f32_candidate")
            raw_field, raw_detail = compare_raw_a850(actual, expected)
            raw_status = "match" if raw_field is None else "differ"
            if raw_field is None:
                raw_match_counts[lane] += 1
            elif raw_first[lane] is None:
                raw_first[lane] = {"xy": list(xy), "field": raw_field, "detail": raw_detail}
            if index_cell_semantic:
                field, detail = compare_lane(actual, expected)
                status = "match" if field is None else "differ"
                if field is None:
                    match_counts[lane] += 1
                elif first[lane] is None:
                    first[lane] = {"xy": list(xy), "field": field, "detail": detail}
            else:
                field = None
                detail = {
                    "debug_size": reference.get("debug_size"),
                    "input_size": reference.get("input_size"),
                    "quality_step_override_degrees": reference.get("quality_step_override_degrees", 90.0),
                }
                status = "blocked-nonsemantic-reference"
            lane_results[lane] = {
                "status": status,
                "first_differing_field": field,
                "detail": detail,
                "raw_a850_status": raw_status,
                "raw_a850_first_differing_field": raw_field,
                "raw_a850_detail": raw_detail,
            }
        rows.append({"xy": list(xy), "lanes": lane_results})
    classifications = {
        lane: (
            "raw-bit-exact" if index_cell_semantic and first[lane] is None
            else "first-difference-found" if index_cell_semantic
            else "blocked-nonsemantic-reduced-geometry-reference"
        )
        for lane in LANES
    }
    raw_classifications = {
        lane: "raw-a850-exact" if raw_first[lane] is None else "raw-a850-difference-found" for lane in LANES
    }
    return {
        "kind": "olmradialblur_case0009_mac_a850_coordinate_comparison",
        "schema": 1,
        "case_id": "case_0009",
        "point_count": len(POINTS),
        "index_cell_semantic": index_cell_semantic,
        "index_cell_classification": (
            "eligible-for-comparison" if index_cell_semantic
            else "blocked-nonsemantic-reduced-geometry-reference"
        ),
        "classifications": classifications,
        "match_counts": match_counts,
        "first_differences": first,
        "raw_a850_classifications": raw_classifications,
        "raw_a850_match_counts": raw_match_counts,
        "raw_a850_first_differences": raw_first,
        "points": rows,
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMRadialBlur case_0009 Mac/AEX Coordinate Comparison", "",
        f"- Points: `{report['point_count']}`",
        f"- Raw A850 production: `{report['raw_a850_classifications']['production']}` ({report['raw_a850_match_counts']['production']}/32 exact)",
        f"- Raw A850 candidate: `{report['raw_a850_classifications']['aex_f32_candidate']}` ({report['raw_a850_match_counts']['aex_f32_candidate']}/32 exact)",
        f"- Index/cell evidence: `{report['index_cell_classification']}`",
        f"- Production: `{report['classifications']['production']}` ({report['match_counts']['production']}/32 exact)",
        f"- AEX-order f32 candidate: `{report['classifications']['aex_f32_candidate']}` ({report['match_counts']['aex_f32_candidate']}/32 exact)",
        f"- Production first difference: `{report['first_differences']['production']}`",
        f"- Candidate first difference: `{report['first_differences']['aex_f32_candidate']}`", "",
        "| x | production | candidate |", "| ---: | --- | --- |",
    ]
    for row in report["points"]:
        lines.append(f"| {row['xy'][0]} | `{row['lanes']['production']['status']}` | `{row['lanes']['aex_f32_candidate']['status']}` |")
    lines.append("")
    return "\n".join(lines)


def write_blocked(args: argparse.Namespace, reason: str) -> int:
    report = {"kind": "olmradialblur_case0009_mac_a850_coordinate_comparison", "schema": 1,
              "classification": "blocked-invalid-evidence", "reason": reason}
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(f"# OLMRadialBlur case_0009 Mac/AEX Coordinate Comparison\n\n- Classification: `blocked-invalid-evidence`\n- Reason: {reason}\n", encoding="utf-8")
    print(f"[FAIL-CLOSED] {reason}", file=sys.stderr)
    return 2


def main() -> int:
    args = parse_args()
    try:
        report = compare(read_json(args.mac_debug_json), read_json(args.reference_json))
    except (KeyError, TypeError, ValueError) as exc:
        return write_blocked(args, str(exc))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(markdown(report), encoding="utf-8")
    print(f"[OK] production={report['classifications']['production']} candidate={report['classifications']['aex_f32_candidate']}")
    if args.require_candidate_exact and not report["index_cell_semantic"]:
        print("[FAIL-CLOSED] candidate index/cell exactness requires a semantic full-frame reference", file=sys.stderr)
        return 2
    if args.require_candidate_exact and report["classifications"]["aex_f32_candidate"] != "raw-bit-exact":
        return 1
    if args.require_candidate_raw_exact and report["raw_a850_classifications"]["aex_f32_candidate"] != "raw-a850-exact":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
