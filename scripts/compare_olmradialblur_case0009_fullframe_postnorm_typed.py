#!/usr/bin/env python3
"""Compare the eventual RadialBlur case_0009 typed return to a local model.

This is an evidence comparator, not a model generator.  Missing, placeholder,
mixed-run, or incomplete values are rejected before any comparison is made.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


POINTS = ((7, 0), (8, 0), (24, 0))
SLOTS = ("00", "10", "01", "11")
CELL_FIELDS = ("accum_rgba_f32", "denom_f32", "valid_f32", "final_rgba_f32")
BOUNDARIES = ("inverse-sampler", "cell-selection", "bilinear-weights", "accum", "denom", "valid", "final")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-model", type=Path, required=True)
    parser.add_argument("--return-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--abs-tol", type=float, default=0.0)
    parser.add_argument("--rel-tol", type=float, default=0.0)
    return parser.parse_args()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path}: {exc}") from exc


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def complete_vector(value: Any, length: int) -> bool:
    return isinstance(value, list) and len(value) == length and all(finite(item) for item in value)


def concrete(value: Any) -> bool:
    if value is None or isinstance(value, bool):
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip().lower() not in {"null", "none", "unknown", "0x..."}
    return finite(value) if isinstance(value, (int, float)) else bool(value)


def observations(document: Any, label: str) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ValueError(f"{label} must be a JSON object")
    if document.get("kind") == "olmradialblur_case0009_fullframe_postnorm_typed_local_model":
        value = document.get("model")
    elif document.get("kind") == "olm_runtime_trace_result":
        results = document.get("results")
        value = results[0].get("observations") if isinstance(results, list) and len(results) == 1 and isinstance(results[0], dict) else None
    else:
        value = document.get("observations", document)
    if not isinstance(value, dict):
        raise ValueError(f"{label} has no observations object")
    return value


def points_by_xy(obs: dict[str, Any], label: str) -> dict[tuple[int, int], dict[str, Any]]:
    points = obs.get("points")
    if not isinstance(points, list):
        raise ValueError(f"{label} is missing points[]")
    found: dict[tuple[int, int], dict[str, Any]] = {}
    for point in points:
        if not isinstance(point, dict):
            raise ValueError(f"{label} contains a non-object point")
        xy = point.get("xy")
        if not isinstance(xy, list) or len(xy) != 2 or not all(isinstance(v, int) and not isinstance(v, bool) for v in xy):
            raise ValueError(f"{label} contains a point without integer xy")
        key = (xy[0], xy[1])
        if key in found:
            raise ValueError(f"{label} contains duplicate point {key}")
        found[key] = point
    if set(found) != set(POINTS):
        raise ValueError(f"{label} must contain exactly points {list(POINTS)}")
    return found


def validate_return(obs: dict[str, Any]) -> None:
    if obs.get("classification") != "answered":
        raise ValueError("return classification is not answered")
    if obs.get("same_run") is not True:
        raise ValueError("return does not assert same_run=true")
    for key in ("run_id", "hook_or_watchpoint", "console_artifact"):
        if not concrete(obs.get(key)):
            raise ValueError(f"return binding field {key} is missing")
    geometry = obs.get("geometry")
    if not isinstance(geometry, dict) or geometry.get("width") != 1920 or geometry.get("height") != 1080 or geometry.get("mode") != "full-frame":
        raise ValueError("return geometry is not the required 1920x1080 full-frame run")
    for xy, point in points_by_xy(obs, "return") .items():
        if not complete_vector(point.get("observed_rgba8"), 4):
            raise ValueError(f"return point {xy} has no complete observed_rgba8")
        if not complete_vector(point.get("inverse_sample_xy"), 2):
            raise ValueError(f"return point {xy} has no complete inverse_sample_xy")
        cells = point.get("cells")
        if not isinstance(cells, list) or [cell.get("slot") for cell in cells if isinstance(cell, dict)] != list(SLOTS):
            raise ValueError(f"return point {xy} does not have ordered cells {list(SLOTS)}")
        for cell in cells:
            if not isinstance(cell, dict) or not concrete(cell.get("cell_id")) or not finite(cell.get("bilinear_weight")):
                raise ValueError(f"return point {xy} has incomplete cell identity/weight")
            for field in CELL_FIELDS:
                size = 4 if field.endswith("rgba_f32") else 1
                value = cell.get(field)
                if size == 4 and not complete_vector(value, 4):
                    raise ValueError(f"return point {xy} cell {cell.get('slot')} lacks {field}")
                if size == 1 and not finite(value):
                    raise ValueError(f"return point {xy} cell {cell.get('slot')} lacks {field}")
        if not finite(point.get("final_alpha_sum")) or not finite(point.get("pre_byte_alpha")):
            raise ValueError(f"return point {xy} lacks final alpha fields")


def validate_local_model(obs: dict[str, Any]) -> None:
    geometry = obs.get("geometry")
    if geometry is not None and (
        not isinstance(geometry, dict)
        or geometry.get("width") != 1920
        or geometry.get("height") != 1080
        or geometry.get("mode") != "full-frame"
    ):
        raise ValueError("local model geometry is not the required 1920x1080 full-frame model")
    for xy, point in points_by_xy(obs, "local model").items():
        if not complete_vector(point.get("inverse_sample_xy"), 2):
            raise ValueError(f"local model point {xy} has no complete inverse_sample_xy")
        cells = point.get("cells")
        if not isinstance(cells, list) or [cell.get("slot") for cell in cells if isinstance(cell, dict)] != list(SLOTS):
            raise ValueError(f"local model point {xy} does not have ordered cells {list(SLOTS)}")
        for cell in cells:
            if not isinstance(cell, dict) or not concrete(cell.get("cell_id")) or not finite(cell.get("bilinear_weight")):
                raise ValueError(f"local model point {xy} has incomplete cell identity/weight")
            for field in CELL_FIELDS:
                size = 4 if field.endswith("rgba_f32") else 1
                value = cell.get(field)
                if size == 4 and not complete_vector(value, 4):
                    raise ValueError(f"local model point {xy} lacks {field}")
                if size == 1 and not finite(value):
                    raise ValueError(f"local model point {xy} lacks {field}")


def same(a: Any, b: Any, abs_tol: float, rel_tol: float) -> bool:
    if finite(a) and finite(b):
        return math.isclose(float(a), float(b), abs_tol=abs_tol, rel_tol=rel_tol)
    return a == b


def compare(local: dict[str, Any], returned: dict[str, Any], abs_tol: float, rel_tol: float) -> dict[str, Any]:
    local_points = points_by_xy(local, "local model")
    return_points = points_by_xy(returned, "return")
    rows = []
    first: dict[str, Any] | None = None
    for xy in POINTS:
        expected = local_points[xy]
        actual = return_points[xy]
        boundary = None
        detail = None
        if expected.get("inverse_sample_xy") != actual.get("inverse_sample_xy"):
            boundary, detail = "inverse-sampler", {"local": expected.get("inverse_sample_xy"), "return": actual.get("inverse_sample_xy")}
        elif [c.get("cell_id") for c in expected.get("cells", [])] != [c.get("cell_id") for c in actual.get("cells", [])]:
            boundary, detail = "cell-selection", {"local": [c.get("cell_id") for c in expected["cells"]], "return": [c.get("cell_id") for c in actual["cells"]]}
        elif any(not same(left.get("bilinear_weight"), right.get("bilinear_weight"), abs_tol, rel_tol) for left, right in zip(expected["cells"], actual["cells"])):
            boundary, detail = "bilinear-weights", {"local": [c.get("bilinear_weight") for c in expected["cells"]], "return": [c.get("bilinear_weight") for c in actual["cells"]]}
        else:
            for field, boundary_name in (("accum_rgba_f32", "accum"), ("denom_f32", "denom"), ("valid_f32", "valid"), ("final_rgba_f32", "final")):
                mismatch = next((i for i, (left, right) in enumerate(zip(expected["cells"], actual["cells"])) if not same(left[field], right[field], abs_tol, rel_tol)), None)
                if mismatch is not None:
                    boundary = boundary_name
                    detail = {"slot": SLOTS[mismatch], "field": field, "local": expected["cells"][mismatch][field], "return": actual["cells"][mismatch][field]}
                    break
        row = {"xy": list(xy), "status": "match" if boundary is None else "differ", "first_differing_boundary": boundary, "detail": detail}
        rows.append(row)
        if first is None and boundary is not None:
            first = {"xy": list(xy), "boundary": boundary, "detail": detail}
    return {"classification": "match" if first is None else "first-difference-found", "first_difference": first, "points": rows, "tolerance": {"abs": abs_tol, "rel": rel_tol}}


def markdown(report: dict[str, Any]) -> str:
    first = report.get("first_difference")
    lines = ["# OLMRadialBlur case_0009 Full-Frame Typed Comparison", "", f"- Classification: `{report['classification']}`", f"- First difference: `{first}`", "", "| Point | Status | First differing boundary |", "| --- | --- | --- |"]
    lines.extend(f"| `{row['xy']}` | `{row['status']}` | `{row['first_differing_boundary'] or 'none'}` |" for row in report["points"])
    lines.extend(["", "Comparison order is inverse-sampler, cell-selection, accum, denom, valid, final.", "A report is emitted only after the return passes the same-run and complete-typed-fields gate.", ""])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    try:
        local = observations(read_json(args.local_model), "local model")
        returned = observations(read_json(args.return_json), "return")
        validate_local_model(local)
        validate_return(returned)
        report = compare(local, returned, args.abs_tol, args.rel_tol)
    except ValueError as exc:
        report = {"kind": "olmradialblur_case0009_fullframe_postnorm_typed_comparison", "schema": 1, "classification": "blocked-invalid-evidence", "reason": str(exc)}
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text("# OLMRadialBlur case_0009 Full-Frame Typed Comparison\n\n- Classification: `blocked-invalid-evidence`\n- Reason: " + str(exc) + "\n", encoding="utf-8")
        print(f"[FAIL-CLOSED] {exc}", file=sys.stderr)
        return 2
    report.update({"kind": "olmradialblur_case0009_fullframe_postnorm_typed_comparison", "schema": 1})
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(markdown(report), encoding="utf-8")
    print(f"[OK] {report['classification']}; first_difference={report.get('first_difference')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
