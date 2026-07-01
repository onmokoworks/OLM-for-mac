#!/usr/bin/env python3
"""Parse OLMDistanceGradation debug dumps into a structured point report."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


HEADER_RE = re.compile(
    r"w=(?P<w>-?\d+) h=(?P<h>-?\d+) pixel_size=(?P<pixel_size>\d+) "
    r"invert=(?P<invert>-?\d+) in_out=(?P<in_out>-?\d+) inside=(?P<inside>-?\d+) "
    r"outside=(?P<outside>-?\d+) render_mode=(?P<render_mode>-?\d+) use_bg=(?P<use_bg>-?\d+) "
    r"interp=(?P<interp>-?\d+) power=(?P<power>[-+0-9.eE]+) blur_mode=(?P<blur_mode>-?\d+) blur_size=(?P<blur_size>-?\d+)"
)
POINT_RE = re.compile(
    r"point x=(?P<x>-?\d+) y=(?P<y>-?\d+) alpha=(?P<alpha>[-+0-9.eE]+) d_alpha=(?P<d_alpha>[-+0-9.eE]+) "
    r"field_x=(?P<field_x>[-+0-9.eE]+) raw_inside=(?P<raw_inside>[-+0-9.eE]+) raw_outside=(?P<raw_outside>[-+0-9.eE]+)"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--debug-log", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser.parse_args()


def load_dump(path: Path) -> dict:
    header = None
    points = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if header is None:
            match = HEADER_RE.search(line)
            if match:
                header = {
                    "width": int(match.group("w")),
                    "height": int(match.group("h")),
                    "pixel_size": int(match.group("pixel_size")),
                    "invert": int(match.group("invert")),
                    "in_out": int(match.group("in_out")),
                    "inside_threshold": int(match.group("inside")),
                    "outside_threshold": int(match.group("outside")),
                    "render_mode": int(match.group("render_mode")),
                    "use_bg": int(match.group("use_bg")),
                    "interp": int(match.group("interp")),
                    "power": float(match.group("power")),
                    "blur_mode": int(match.group("blur_mode")),
                    "blur_size": int(match.group("blur_size")),
                }
                continue
        match = POINT_RE.search(line)
        if match:
            points.append(
                {
                    "x": int(match.group("x")),
                    "y": int(match.group("y")),
                    "alpha": float(match.group("alpha")),
                    "d_alpha": float(match.group("d_alpha")),
                    "field_x": float(match.group("field_x")),
                    "raw_inside": float(match.group("raw_inside")),
                    "raw_outside": float(match.group("raw_outside")),
                }
            )
    if header is None:
        raise ValueError(f"missing DistanceGradation header in {path}")
    if not points:
        raise ValueError(f"missing DistanceGradation point lines in {path}")
    return {"header": header, "points": points}


def classify_point(point: dict) -> str:
    raw_inside = point["raw_inside"]
    raw_outside = point["raw_outside"]
    if raw_outside == 0.0 and abs(raw_inside - 1.0) < 1e-6:
        return "inside_edge_1px"
    if raw_outside == 0.0 and 35.5 <= raw_inside <= 36.5:
        return "inside_threshold_plateau"
    if raw_inside == 0.0 and raw_outside >= 1.0:
        return "outside_neighbor"
    return "other"


def write_md(path: Path, payload: dict) -> None:
    lines = [
        "# OLMDistanceGradation Debug Point Report",
        "",
        f"- Debug log: `{payload['debug_log']}`",
        f"- Header: `{payload['header']}`",
        "",
        "| class | x | y | alpha | d_alpha | field_x | raw_inside | raw_outside |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["points"]:
        lines.append(
            f"| `{row['class']}` | {row['x']} | {row['y']} | `{row['alpha']:.9g}` | `{row['d_alpha']:.9g}` | `{row['field_x']:.9g}` | `{row['raw_inside']:.9g}` | `{row['raw_outside']:.9g}` |"
        )
    lines.extend(["", "## Reading", ""])
    lines.extend(f"- {line}" for line in payload["reading"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    loaded = load_dump(args.debug_log)
    points = []
    for point in loaded["points"]:
        row = dict(point)
        row["class"] = classify_point(point)
        points.append(row)
    class_counts: dict[str, int] = {}
    for row in points:
        class_counts[row["class"]] = class_counts.get(row["class"], 0) + 1
    payload = {
        "kind": "olmdistancegradation_debug_point_report",
        "debug_log": str(args.debug_log),
        "header": loaded["header"],
        "points": points,
        "class_counts": class_counts,
        "reading": [
            f"Captured {len(points)} witness points.",
            f"Class counts: {class_counts}.",
            "Use this to confirm whether the live residual is already decided in field prep before compose/writeback.",
        ],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_md(args.output_md, payload)
    print(f"report_json={args.output_json}")
    print(f"report_md={args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
