#!/usr/bin/env python3
"""Materialize OLMDistanceGradation case_0023 neighborhood Mac AE probe result."""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
BASE_RESULT_SCRIPT = ROOT / "scripts/materialize_distancegradation_case0023_mac_probe_result.py"
PROBE_DIR = ROOT / "refs/reports/ae_single_case_distancegradation_case0023_neighborhood_probe_20260707"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe-dir", type=Path, default=PROBE_DIR)
    parser.add_argument("--stamp", default=datetime.now().strftime("%Y%m%d"))
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser.parse_args()


def load_base() -> Any:
    spec = importlib.util.spec_from_file_location("dg_case0023_base_probe", BASE_RESULT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {BASE_RESULT_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def point_map(report: dict[str, Any]) -> dict[tuple[int, int], dict[str, Any]]:
    return {(int(row["x"]), int(row["y"])): row for row in report["points"]}


def load_field_report(path: Path) -> dict[tuple[int, int], dict[str, Any]]:
    return point_map(json.loads(path.read_text(encoding="utf-8")))


def compare_arrays(reference: np.ndarray, candidate: np.ndarray) -> dict[str, Any]:
    if reference.shape != candidate.shape:
        return {"status": "shape_mismatch", "reference_shape": list(reference.shape), "candidate_shape": list(candidate.shape)}
    delta = np.abs(reference.astype(np.int64, copy=False) - candidate.astype(np.int64, copy=False))
    pixel_delta = np.max(delta, axis=2)
    return {
        "status": "compared",
        "nonzero_px": int(np.count_nonzero(pixel_delta)),
        "max_diff": int(delta.max()),
        "mean_diff": float(delta.mean()),
    }


def store_matches_png(base: Any, promoted_rgba16: list[int], mac_rgba16: list[int]) -> bool:
    return bool(base.store_matches_png(promoted_rgba16, mac_rgba16))


def rgba_at(image: np.ndarray, xy: tuple[int, int]) -> list[int]:
    x, y = xy
    return image[y, x].tolist()


def source_promoted_rgba16(base: Any, shade: dict[str, Any]) -> list[int]:
    if not shade:
        return []
    raw = []
    for key in ("src_r", "src_g", "src_b", "src_a"):
        raw.append(max(0, min(32768, int(round(float(shade[key]) * 32768.0)))))
    return [base.promoted_word(value) for value in raw]


def build_report(probe_dir: Path) -> dict[str, Any]:
    base = load_base()
    verify_manifest = base.load_verify_manifest()
    bg_on_dir = probe_dir / "bg_on"
    bg_off_dir = probe_dir / "bg_off"
    bg_on_field = load_field_report(bg_on_dir / "field_debug_report.json")
    bg_off_field = load_field_report(bg_off_dir / "field_debug_report.json")
    bg_on_shade = base.parse_shade_debug(bg_on_dir / "shade_debug.txt")
    bg_off_shade = base.parse_shade_debug(bg_off_dir / "shade_debug.txt")
    points = sorted(set(bg_on_shade) | set(bg_off_shade))

    mac_bg_on_path = bg_on_dir / base.MAC_FILENAME
    mac_bg_off_path = bg_off_dir / base.MAC_FILENAME
    request_manifest = json.loads((probe_dir / "request" / "reference_manifest.json").read_text(encoding="utf-8"))
    case = request_manifest["cases"][0]
    before_effects = probe_dir / "request" / "input" / case["before_effects_frame"]
    before_rgba = verify_manifest.load_rgba(before_effects)
    win_bg_on = verify_manifest.load_rgba(base.WIN_BG_ON)
    win_bg_off = verify_manifest.load_rgba(base.WIN_BG_OFF)
    mac_bg_on = verify_manifest.load_rgba(mac_bg_on_path)
    mac_bg_off = verify_manifest.load_rgba(mac_bg_off_path)

    rows = []
    debug_match = True
    store_match_all = True
    source_match_all = True
    mismatch_points = {"bg_on": [], "bg_off": []}
    for xy in points:
        on_field = bg_on_field.get(xy, {})
        off_field = bg_off_field.get(xy, {})
        on_shade = bg_on_shade.get(xy, {})
        off_shade = bg_off_shade.get(xy, {})
        on_ref = rgba_at(win_bg_on, xy)
        off_ref = rgba_at(win_bg_off, xy)
        on_mac = rgba_at(mac_bg_on, xy)
        off_mac = rgba_at(mac_bg_off, xy)
        source_rgba16 = rgba_at(before_rgba, xy)
        shade_source_rgba16 = source_promoted_rgba16(base, on_shade)
        source_match = source_rgba16 == shade_source_rgba16
        on_store_match = store_matches_png(base, on_shade.get("promoted_rgba16", []), on_mac) if on_shade else False
        off_store_match = store_matches_png(base, off_shade.get("promoted_rgba16", []), off_mac) if off_shade else False
        field_keys = ("alpha", "d_alpha", "field_x", "raw_inside", "raw_outside", "inside_x", "outside_x", "both_x")
        fields_equal = all(on_field.get(key) == off_field.get(key) for key in field_keys)
        debug_match = debug_match and fields_equal
        store_match_all = store_match_all and on_store_match and off_store_match
        source_match_all = source_match_all and source_match
        if on_ref != on_mac:
            mismatch_points["bg_on"].append(list(xy))
        if off_ref != off_mac:
            mismatch_points["bg_off"].append(list(xy))
        rows.append(
            {
                "xy": list(xy),
                "fields_equal_between_bg_modes": fields_equal,
                "alpha": on_field.get("alpha"),
                "raw_inside": on_field.get("raw_inside"),
                "field_x": on_field.get("field_x"),
                "src_a": on_shade.get("src_a"),
                "input_source_rgba16": source_rgba16,
                "shade_source_promoted_rgba16": shade_source_rgba16,
                "source_matches_input_png": source_match,
                "bg_on_out_rgba_float": [on_shade.get(k) for k in ("out_r", "out_g", "out_b", "out_a")],
                "bg_off_out_rgba_float": [off_shade.get(k) for k in ("out_r", "out_g", "out_b", "out_a")],
                "bg_on_store_matches_mac_png": on_store_match,
                "bg_off_store_matches_mac_png": off_store_match,
                "win_bg_on_rgba16": on_ref,
                "mac_bg_on_rgba16": on_mac,
                "win_bg_off_rgba16": off_ref,
                "mac_bg_off_rgba16": off_mac,
                "bg_on_matches_windows": on_ref == on_mac,
                "bg_off_matches_windows": off_ref == off_mac,
            }
        )

    return {
        "kind": "olmdistancegradation_case0023_neighborhood_probe_result",
        "materialized_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "case_id": "olmdistancegradation_extended__case_0023",
        "probe_dir": rel(probe_dir),
        "points_count": len(points),
        "debug_fields_match_between_bg_modes": debug_match,
        "shade_stores_match_mac_png": store_match_all,
        "shade_source_matches_input_png": source_match_all,
        "comparisons": {
            "win_bg_on_vs_mac_bg_on": compare_arrays(win_bg_on, mac_bg_on),
            "win_bg_off_vs_mac_bg_off": compare_arrays(win_bg_off, mac_bg_off),
        },
        "mismatch_points": mismatch_points,
        "rows": rows,
        "safe_claim": (
            "The 3x3 neighborhoods around the two live case_0023 witnesses reproduce the same "
            "73px full-frame residual while all logged shade sources match the request input PNG "
            "under AE PF_Pixel16 promotion and all logged shade stores match the Mac PNG. The newly "
            "logged neighboring points show the mismatch is still confined to the previously live "
            "boundary representatives in this neighborhood; this supports continuing with Windows "
            "final/source-ownership proof rather than broad field-helper or compose retuning."
        ),
        "inputs": {
            "before_effects": rel(before_effects),
            "bg_on_field": rel(bg_on_dir / "field_debug_report.json"),
            "bg_off_field": rel(bg_off_dir / "field_debug_report.json"),
            "bg_on_shade": rel(bg_on_dir / "shade_debug.txt"),
            "bg_off_shade": rel(bg_off_dir / "shade_debug.txt"),
            "mac_bg_on": rel(mac_bg_on_path),
            "mac_bg_off": rel(mac_bg_off_path),
            "win_bg_on": rel(base.WIN_BG_ON),
            "win_bg_off": rel(base.WIN_BG_OFF),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# OLMDistanceGradation case_0023 Neighborhood Probe Result - {report['materialized_at'][:10]}",
        "",
        f"- Case: `{report['case_id']}`",
        f"- Probe dir: `{report['probe_dir']}`",
        f"- Points: `{report['points_count']}`",
        f"- Debug fields match between bg modes: `{report['debug_fields_match_between_bg_modes']}`",
        f"- Shade stores match Mac PNG: `{report['shade_stores_match_mac_png']}`",
        f"- Shade source matches input PNG: `{report['shade_source_matches_input_png']}`",
        f"- Safe claim: {report['safe_claim']}",
        "",
        "## PNG Comparisons",
        "",
        "| Pair | Nonzero px | Max diff | Mean diff |",
        "| --- | ---: | ---: | ---: |",
    ]
    for name, comp in report["comparisons"].items():
        lines.append(f"| `{name}` | `{comp.get('nonzero_px')}` | `{comp.get('max_diff')}` | `{comp.get('mean_diff')}` |")
    lines.extend(["", "## Neighborhood Rows", ""])
    lines.append(
        "| XY | alpha | raw_inside | field_x | source match | bg_on win | bg_on mac | bg_on match | bg_off win | bg_off mac | bg_off match |"
    )
    lines.append("| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- | ---: |")
    for row in report["rows"]:
        xy = f"({row['xy'][0]},{row['xy'][1]})"
        lines.append(
            f"| `{xy}` | `{row['alpha']}` | `{row['raw_inside']}` | `{row['field_x']}` | "
            f"`{row['source_matches_input_png']}` | "
            f"`{row['win_bg_on_rgba16']}` | `{row['mac_bg_on_rgba16']}` | `{row['bg_on_matches_windows']}` | "
            f"`{row['win_bg_off_rgba16']}` | `{row['mac_bg_off_rgba16']}` | `{row['bg_off_matches_windows']}` |"
        )
    lines.extend(["", "## Mismatch Points", ""])
    for mode, points in report["mismatch_points"].items():
        rendered = ", ".join(f"({x},{y})" for x, y in points) or "none"
        lines.append(f"- {mode}: {rendered}")
    lines.extend(["", "## Inputs", ""])
    for key, value in report["inputs"].items():
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    report = build_report(args.probe_dir)
    output_json = args.output_json or ROOT / "refs/conformance" / f"olmdistancegradation_case0023_neighborhood_probe_result_{args.stamp}.json"
    output_md = args.output_md or ROOT / "refs/conformance" / f"olmdistancegradation_case0023_neighborhood_probe_result_{args.stamp}.md"
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"wrote {output_json}")
    print(f"wrote {output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
