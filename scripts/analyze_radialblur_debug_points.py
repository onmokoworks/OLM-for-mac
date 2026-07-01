#!/usr/bin/env python3
"""Parse OLMRadialBlur Mac AE debug-point logs into JSON/Markdown."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any


POINT_RE = re.compile(
    r"^OLMRADIALBLUR_DEBUG_POINT "
    r"kind=(?P<kind>\w+) w=(?P<w>\d+) h=(?P<h>\d+) x=(?P<x>-?\d+) y=(?P<y>-?\d+) "
    r"radius_index=(?P<radius_index>[-+0-9.eE]+) angle_index=(?P<angle_index>[-+0-9.eE]+) "
    r"fx=(?P<fx>[-+0-9.eE]+) fy=(?P<fy>[-+0-9.eE]+) "
    r"indices=\((?P<indices>[^)]+)\) "
    r"sample_rgba=\((?P<sample_rgba>[^)]+)\) sample_rgba_hex=\((?P<sample_rgba_hex>[^)]+)\) "
    r"sample_u8=\((?P<sample_u8>[^)]+)\) "
    r"alpha=(?P<alpha>[-+0-9.eE]+) alpha_hex=(?P<alpha_hex>\S+) "
    r"validity_alpha=(?P<validity_alpha>[-+0-9.eE]+) validity_alpha_hex=(?P<validity_alpha_hex>\S+) "
    r"cell_valid=\((?P<cell_valid>[^)]+)\) "
    r"cell_alpha=\((?P<cell_alpha>[^)]+)\) "
    r"cell_rgb=\(\((?P<cell_rgb>.+)\)\) "
    r"src_cell_rgba=\(\((?P<src_cell_rgba>.+)\)\)$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser.parse_args()


def parse_tuple(raw: str, cast) -> list[Any]:
    return [cast(part.strip()) for part in raw.split(",") if part.strip()]


def parse_cell_rgb(raw: str) -> list[list[float]]:
    groups = raw.split("),(")
    out: list[list[float]] = []
    for group in groups:
        clean = group.replace("(", "").replace(")", "")
        out.append(parse_tuple(clean, float))
    return out


def parse_cell_rgba(raw: str) -> list[list[float]]:
    groups = raw.split("),(")
    out: list[list[float]] = []
    for group in groups:
        clean = group.replace("(", "").replace(")", "")
        out.append(parse_tuple(clean, float))
    return out


def load_points(path: Path) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = POINT_RE.match(line.strip())
        if not match:
            continue
        data = match.groupdict()
        sample_u8 = parse_tuple(data["sample_u8"], int)
        validity_alpha = float(data["validity_alpha"])
        points.append(
            {
                "kind": data["kind"],
                "width": int(data["w"]),
                "height": int(data["h"]),
                "x": int(data["x"]),
                "y": int(data["y"]),
                "radius_index": float(data["radius_index"]),
                "angle_index": float(data["angle_index"]),
                "fx": float(data["fx"]),
                "fy": float(data["fy"]),
                "indices": parse_tuple(data["indices"], int),
                "sample_rgba": parse_tuple(data["sample_rgba"], float),
                "sample_rgba_hex": [part.strip() for part in data["sample_rgba_hex"].split(",")],
                "sample_u8": sample_u8,
                "alpha": float(data["alpha"]),
                "alpha_hex": data["alpha_hex"],
                "alpha_u8": sample_u8[3],
                "validity_alpha": validity_alpha,
                "validity_alpha_hex": data["validity_alpha_hex"],
                "validity_alpha_u8": max(0, min(255, int(math.floor(validity_alpha * 255.0 + 1.0e-4)))),
                "cell_valid": parse_tuple(data["cell_valid"], float),
                "cell_alpha": parse_tuple(data["cell_alpha"], float),
                "cell_rgb": parse_cell_rgb(data["cell_rgb"]),
                "src_cell_rgba": parse_cell_rgba(data["src_cell_rgba"]),
            }
        )
    return points


def build_report(points: list[dict[str, Any]], log_path: Path) -> dict[str, Any]:
    by_kind: dict[str, list[dict[str, Any]]] = {}
    for point in points:
        by_kind.setdefault(point["kind"], []).append(point)
    for values in by_kind.values():
        values.sort(key=lambda row: (row["y"], row["x"]))
    return {
        "kind": "olmradialblur_debug_points",
        "schema": 1,
        "log_path": str(log_path),
        "point_count": len(points),
        "kinds": sorted(by_kind),
        "points": points,
        "by_kind": by_kind,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMRadialBlur Debug Points",
        "",
        f"- Log: `{report['log_path']}`",
        f"- Points: `{report['point_count']}`",
        f"- Kinds: `{', '.join(report['kinds'])}`",
        "",
    ]
    for kind in report["kinds"]:
        lines.extend(
            [
                f"## {kind}",
                "",
                "| XY | sample_u8 | alpha_u8 | validity_alpha_u8 | indices | cell_valid | cell_alpha | cell_rgb | src_cell_rgba |",
                "| - | - | -: | -: | - | - | - | - | - |",
            ]
        )
        for point in report["by_kind"][kind]:
            lines.append(
                f"| `({point['x']},{point['y']})` | `{point['sample_u8']}` | "
                f"{point['alpha_u8']} | {point['validity_alpha_u8']} | "
                f"`{point['indices']}` | `{point['cell_valid']}` | `{point['cell_alpha']}` | "
                f"`{point['cell_rgb']}` | `{point['src_cell_rgba']}` |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    points = load_points(args.log)
    report = build_report(points, args.log)
    args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"output_json={args.output_json}")
    print(f"output_md={args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
