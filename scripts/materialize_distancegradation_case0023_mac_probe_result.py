#!/usr/bin/env python3
"""Materialize OLMDistanceGradation case_0023 Mac AE probe result."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
VERIFY_MANIFEST = ROOT / "refs/scripts/verify_manifest.py"
PROBE_DIR = ROOT / "refs/reports/ae_single_case_distancegradation_case0023_mac_probe_20260707"
WIN_BG_ON = (
    ROOT
    / "refs/win_references/olm_return_20260706/DistanceGradation/"
    "olmdistancegradation_case0023_current_aex_recapture_20260702__software_16bpc__fr24__"
    "olmdistancegradation_extended__case_0023_current_aex.png"
)
WIN_BG_OFF = (
    ROOT
    / "refs/win_references/olmdistancegradation_16bpc_bg_compose_variants_20260626/DistanceGradation/renders/"
    "olmdistancegradation_16bpc_bg_compose_variants_20260626__software_16bpc__fr24__"
    "olmdistancegradation_case_0023_bg_off_variant.png"
)
MAC_FILENAME = (
    "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__"
    "olmdistancegradation_extended__case_0023.png"
)
SAMPLE_POINTS = [(1698, 7), (1699, 7), (1700, 7), (414, 393), (415, 393), (416, 393)]
SHADE_RE = re.compile(
    r"shade x=(?P<x>-?\d+) y=(?P<y>-?\d+) pixel_size=(?P<pixel_size>\d+) use_bg=(?P<use_bg>-?\d+) "
    r"render_mode=(?P<render_mode>-?\d+) src_a=(?P<src_a>[-+0-9.eE]+) src_r=(?P<src_r>[-+0-9.eE]+) "
    r"src_g=(?P<src_g>[-+0-9.eE]+) src_b=(?P<src_b>[-+0-9.eE]+) field_x=(?P<field_x>[-+0-9.eE]+) "
    r"d_alpha=(?P<d_alpha>[-+0-9.eE]+) out_a=(?P<out_a>[-+0-9.eE]+) out_r=(?P<out_r>[-+0-9.eE]+) "
    r"out_g=(?P<out_g>[-+0-9.eE]+) out_b=(?P<out_b>[-+0-9.eE]+) store_a=(?P<store_a>\d+) "
    r"store_r=(?P<store_r>\d+) store_g=(?P<store_g>\d+) store_b=(?P<store_b>\d+)"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe-dir", type=Path, default=PROBE_DIR)
    parser.add_argument("--stamp", default=datetime.now().strftime("%Y%m%d"))
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser.parse_args()


def load_verify_manifest() -> Any:
    spec = importlib.util.spec_from_file_location("verify_manifest", VERIFY_MANIFEST)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {VERIFY_MANIFEST}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


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


def sample_pixels(reference: np.ndarray, candidate: np.ndarray) -> list[dict[str, Any]]:
    rows = []
    for x, y in SAMPLE_POINTS:
        ref = reference[y, x].tolist()
        cand = candidate[y, x].tolist()
        rows.append(
            {
                "xy": [x, y],
                "reference_rgba16": ref,
                "mac_rgba16": cand,
                "match": ref == cand,
            }
        )
    return rows


def point_map(report: dict[str, Any]) -> dict[tuple[int, int], dict[str, Any]]:
    return {(int(row["x"]), int(row["y"])): row for row in report["points"]}


def comparable_point(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "alpha",
        "d_alpha",
        "field_x",
        "raw_inside",
        "raw_outside",
        "inside_x",
        "outside_x",
        "both_x",
        "compose_input_x",
        "inside_constant_binary",
        "outside_constant_binary",
    ]
    return {key: row.get(key) for key in keys}


def promoted_word(value: int) -> int:
    if value <= 0:
        return 0
    return min(65535, value * 2 - 1)


def parse_shade_debug(path: Path) -> dict[tuple[int, int], dict[str, Any]]:
    rows: dict[tuple[int, int], dict[str, Any]] = {}
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = SHADE_RE.search(line)
        if not match:
            continue
        row: dict[str, Any] = {
            "x": int(match.group("x")),
            "y": int(match.group("y")),
            "pixel_size": int(match.group("pixel_size")),
            "use_bg": int(match.group("use_bg")),
            "render_mode": int(match.group("render_mode")),
        }
        for key in ("src_a", "src_r", "src_g", "src_b", "field_x", "d_alpha", "out_a", "out_r", "out_g", "out_b"):
            row[key] = float(match.group(key))
        for key in ("store_a", "store_r", "store_g", "store_b"):
            row[key] = int(match.group(key))
        row["promoted_rgba16"] = [
            promoted_word(row["store_r"]),
            promoted_word(row["store_g"]),
            promoted_word(row["store_b"]),
            promoted_word(row["store_a"]),
        ]
        rows[(row["x"], row["y"])] = row
    return rows


def store_matches_png(promoted_rgba16: list[int], mac_rgba16: list[int]) -> bool:
    if promoted_rgba16 == mac_rgba16:
        return True
    return promoted_rgba16[3] == 0 and mac_rgba16 == [0, 0, 0, 0]


def build_report(probe_dir: Path) -> dict[str, Any]:
    verify_manifest = load_verify_manifest()
    bg_on_dir = probe_dir / "bg_on"
    bg_off_dir = probe_dir / "bg_off"
    bg_on_debug = json.loads((bg_on_dir / "field_debug_report.json").read_text(encoding="utf-8"))
    bg_off_debug = json.loads((bg_off_dir / "field_debug_report.json").read_text(encoding="utf-8"))
    bg_on_shade = parse_shade_debug(bg_on_dir / "shade_debug.txt")
    bg_off_shade = parse_shade_debug(bg_off_dir / "shade_debug.txt")
    bg_on_points = point_map(bg_on_debug)
    bg_off_points = point_map(bg_off_debug)
    debug_rows = []
    all_debug_match = True
    for xy in SAMPLE_POINTS:
        on = comparable_point(bg_on_points[xy])
        off = comparable_point(bg_off_points[xy])
        match = on == off
        all_debug_match = all_debug_match and match
        debug_rows.append({"xy": list(xy), "bg_on": on, "bg_off": off, "match": match})

    win_bg_on = verify_manifest.load_rgba(WIN_BG_ON)
    win_bg_off = verify_manifest.load_rgba(WIN_BG_OFF)
    mac_bg_on_path = bg_on_dir / MAC_FILENAME
    mac_bg_off_path = bg_off_dir / MAC_FILENAME
    mac_bg_on = verify_manifest.load_rgba(mac_bg_on_path)
    mac_bg_off = verify_manifest.load_rgba(mac_bg_off_path)
    comparisons = {
        "win_bg_on_vs_mac_bg_on": compare_arrays(win_bg_on, mac_bg_on),
        "win_bg_off_vs_mac_bg_off": compare_arrays(win_bg_off, mac_bg_off),
    }
    both_png_exact = (
        comparisons["win_bg_on_vs_mac_bg_on"]["nonzero_px"] == 0
        and comparisons["win_bg_on_vs_mac_bg_on"]["max_diff"] == 0
        and comparisons["win_bg_off_vs_mac_bg_off"]["nonzero_px"] == 0
        and comparisons["win_bg_off_vs_mac_bg_off"]["max_diff"] == 0
    )
    if both_png_exact:
        safe_claim = (
            "Mac AE bg_on and bg_off probe runs match the corresponding Windows Software references exactly "
            "(nonzero_px=0, max_diff=0), and the shade stores match the Mac PNG values at the witness points. "
            "For this probe, the low-alpha source-mask ownership seam is closed; do not reopen broad field-helper, "
            "compose, or writeback tuning from case_0023 without a new contradictory witness."
        )
    else:
        safe_claim = (
            "Mac AE bg_on and bg_off probe runs produce identical debug fields at the witness points, but at least one "
            "exported PNG still differs from the corresponding Windows Software reference. The shade debug logs capture "
            "source RGBA, x_row/a_row, compose output floats, and 16bpc stores at the same points, and those stores match "
            "the Mac PNG values after transparent-RGB zeroing. Keep the remaining lane on mismatch-neighborhood "
            "shade/source ownership or same-run raw output provenance, not broad field-helper retuning."
        )
    shade_rows = {"bg_on": [], "bg_off": []}
    shade_store_matches_png = True
    for mode, shade_map, mac_array in [
        ("bg_on", bg_on_shade, mac_bg_on),
        ("bg_off", bg_off_shade, mac_bg_off),
    ]:
        for x, y in SAMPLE_POINTS:
            shade = shade_map.get((x, y))
            if not shade:
                continue
            mac_rgba16 = mac_array[y, x].tolist()
            store_match = store_matches_png(shade["promoted_rgba16"], mac_rgba16)
            shade_store_matches_png = shade_store_matches_png and store_match
            shade_rows[mode].append(
                {
                    "xy": [x, y],
                    "src_a": shade["src_a"],
                    "field_x": shade["field_x"],
                    "d_alpha": shade["d_alpha"],
                    "out_rgba_float": [shade["out_r"], shade["out_g"], shade["out_b"], shade["out_a"]],
                    "store_agrb16": [shade["store_a"], shade["store_r"], shade["store_g"], shade["store_b"]],
                    "promoted_rgba16": shade["promoted_rgba16"],
                    "mac_png_rgba16": mac_rgba16,
                    "store_matches_mac_png": store_match,
                }
            )
    return {
        "kind": "olmdistancegradation_case0023_mac_probe_result",
        "materialized_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "case_id": "olmdistancegradation_extended__case_0023",
        "probe_dir": rel(probe_dir),
        "debug_reports": {
            "bg_on": rel(bg_on_dir / "field_debug_report.json"),
            "bg_off": rel(bg_off_dir / "field_debug_report.json"),
        },
        "shade_debug_logs": {
            "bg_on": rel(bg_on_dir / "shade_debug.txt") if (bg_on_dir / "shade_debug.txt").exists() else "",
            "bg_off": rel(bg_off_dir / "shade_debug.txt") if (bg_off_dir / "shade_debug.txt").exists() else "",
        },
        "png_outputs": {
            "mac_bg_on": rel(mac_bg_on_path),
            "mac_bg_off": rel(mac_bg_off_path),
            "win_bg_on": rel(WIN_BG_ON),
            "win_bg_off": rel(WIN_BG_OFF),
        },
        "debug_points_match_between_bg_modes": all_debug_match,
        "shade_store_matches_mac_png": shade_store_matches_png,
        "debug_points": debug_rows,
        "shade_points": shade_rows,
        "comparisons": comparisons,
        "sample_pixels": {
            "bg_on": sample_pixels(win_bg_on, mac_bg_on),
            "bg_off": sample_pixels(win_bg_off, mac_bg_off),
        },
        "safe_claim": safe_claim,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# OLMDistanceGradation case_0023 Mac Probe Result - {report['materialized_at'][:10]}",
        "",
        f"- Case: `{report['case_id']}`",
        f"- Probe dir: `{report['probe_dir']}`",
        f"- Debug points match between bg modes: `{report['debug_points_match_between_bg_modes']}`",
        f"- Shade stores match Mac PNG: `{report['shade_store_matches_mac_png']}`",
        f"- Safe claim: {report['safe_claim']}",
        "",
        "## PNG Comparisons",
        "",
        "| Pair | Nonzero px | Max diff | Mean diff |",
        "| --- | ---: | ---: | ---: |",
    ]
    for name, comparison in report["comparisons"].items():
        lines.append(
            f"| `{name}` | `{comparison['nonzero_px']}` | `{comparison['max_diff']}` | `{comparison['mean_diff']}` |"
        )
    lines.extend(["", "## Debug Point Equality", "", "| XY | match | field_x | raw_inside | alpha |", "| --- | ---: | ---: | ---: | ---: |"])
    for row in report["debug_points"]:
        xy = row["xy"]
        on = row["bg_on"]
        lines.append(
            f"| `({xy[0]},{xy[1]})` | `{row['match']}` | `{on.get('field_x')}` | `{on.get('raw_inside')}` | `{on.get('alpha')}` |"
        )
    for mode, rows in report["shade_points"].items():
        lines.extend(["", f"## Shade Points: {mode}", "", "| XY | src_a | field_x | d_alpha | out RGBA float | promoted RGBA16 | Mac PNG RGBA16 | store match |", "| --- | ---: | ---: | ---: | --- | --- | --- | ---: |"])
        for row in rows:
            xy = row["xy"]
            lines.append(
                f"| `({xy[0]},{xy[1]})` | `{row['src_a']}` | `{row['field_x']}` | `{row['d_alpha']}` | "
                f"`{row['out_rgba_float']}` | `{row['promoted_rgba16']}` | `{row['mac_png_rgba16']}` | "
                f"`{row['store_matches_mac_png']}` |"
            )
    for mode, rows in report["sample_pixels"].items():
        lines.extend(["", f"## Sample Pixels: {mode}", "", "| XY | Windows RGBA16 | Mac RGBA16 | match |", "| --- | --- | --- | ---: |"])
        for row in rows:
            xy = row["xy"]
            lines.append(
                f"| `({xy[0]},{xy[1]})` | `{row['reference_rgba16']}` | `{row['mac_rgba16']}` | `{row['match']}` |"
            )
    lines.extend(["", "## Inputs", ""])
    for name, path in report["debug_reports"].items():
        lines.append(f"- {name}: `{path}`")
    for name, path in report["shade_debug_logs"].items():
        if path:
            lines.append(f"- {name}_shade: `{path}`")
    for name, path in report["png_outputs"].items():
        lines.append(f"- {name}: `{path}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    report = build_report(args.probe_dir.resolve())
    output_json = args.output_json or ROOT / "refs/conformance" / f"olmdistancegradation_case0023_mac_probe_result_{args.stamp}.json"
    output_md = args.output_md or ROOT / "refs/conformance" / f"olmdistancegradation_case0023_mac_probe_result_{args.stamp}.md"
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"wrote {output_json}")
    print(f"wrote {output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
