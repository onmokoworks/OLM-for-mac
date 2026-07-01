#!/usr/bin/env python3
"""Parse OLMKiraKira Mac debug dumps and summarize a local compose neighborhood."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


LINE_RE = re.compile(
    r"OLMKIRAKIRA_DEBUG_POINT "
    r"bitdepth=(?P<bitdepth>-?\d+) .*? "
    r"x=(?P<x>-?\d+) y=(?P<y>-?\d+) "
    r"src=\((?P<src>[^)]*)\) .*? "
    r"glow_norm=\((?P<glow>[^)]*)\) .*? "
    r"glow_alpha_after_opacity=(?P<glow_alpha>[-+0-9.eE]+) .*? "
    r"out_prequantized=\((?P<out_pre>[^)]*)\) .*? "
    r"out_u8=\((?P<out_u8>[^)]*)\)"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--debug-log", type=Path, required=True)
    parser.add_argument("--center", required=True, help="Neighborhood center as X,Y.")
    parser.add_argument("--radius", type=int, default=1)
    parser.add_argument("--windows-target-u8", type=int, default=None)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser.parse_args()


def parse_xy(text: str) -> tuple[int, int]:
    parts = [part.strip() for part in text.split(",", 1)]
    if len(parts) != 2:
        raise ValueError(f"expected X,Y: {text}")
    return int(parts[0]), int(parts[1])


def parse_float_tuple(text: str) -> list[float]:
    return [float(part.strip()) for part in text.split(",")]


def parse_int_tuple(text: str) -> list[int]:
    return [int(part.strip()) for part in text.split(",")]


def load_points(path: Path) -> dict[tuple[int, int], dict]:
    points: dict[tuple[int, int], dict] = {}
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = LINE_RE.search(raw_line)
        if not match:
            continue
        x = int(match.group("x"))
        y = int(match.group("y"))
        points[(x, y)] = {
            "bitdepth": int(match.group("bitdepth")),
            "src_rgba_float": parse_float_tuple(match.group("src")),
            "glow_rgba_float": parse_float_tuple(match.group("glow")),
            "glow_alpha_after_opacity": float(match.group("glow_alpha")),
            "out_prequantized_rgba_float": parse_float_tuple(match.group("out_pre")),
            "out_u8": parse_int_tuple(match.group("out_u8")),
        }
    if not points:
        raise ValueError(f"no OLMKIRAKIRA_DEBUG_POINT lines found in {path}")
    return points


def build_report(points: dict[tuple[int, int], dict], center: tuple[int, int], radius: int, windows_target_u8: int | None) -> dict:
    cx, cy = center
    center_point = points.get(center)
    if center_point is None:
        raise ValueError(f"center point {center} not found in debug log")

    neighborhood = []
    missing = []
    alpha_values = []
    out_values = []
    for y in range(cy - radius, cy + radius + 1):
        row = []
        for x in range(cx - radius, cx + radius + 1):
            point = points.get((x, y))
            if point is None:
                row.append(None)
                missing.append([x, y])
                continue
            alpha = float(point["glow_alpha_after_opacity"])
            out_r = int(point["out_u8"][0])
            alpha_values.append(alpha)
            out_values.append(out_r)
            row.append(
                {
                    "x": x,
                    "y": y,
                    "src_u8": [int(round(channel * 255.0)) for channel in point["src_rgba_float"][:3]],
                    "glow_alpha_after_opacity": alpha,
                    "out_u8": point["out_u8"],
                    "delta_out_r_vs_center": out_r - int(center_point["out_u8"][0]),
                    "delta_alpha_vs_center": alpha - float(center_point["glow_alpha_after_opacity"]),
                }
            )
        neighborhood.append(row)

    alpha_min = min(alpha_values)
    alpha_max = max(alpha_values)
    out_min = min(out_values)
    out_max = max(out_values)

    reading = [
        f"Captured {len(alpha_values)} / {(2 * radius + 1) ** 2} points around the hotspot.",
        f"Glow alpha spans {alpha_min:.9f} .. {alpha_max:.9f}; output R spans {out_min} .. {out_max}.",
    ]
    if windows_target_u8 is not None:
        center_out = int(center_point["out_u8"][0])
        reading.append(
            f"Center output R is {center_out}; Windows target would need delta {windows_target_u8 - center_out}."
        )
    if missing:
        reading.append(f"Missing {len(missing)} requested points; rerun with a complete neighborhood point list.")

    return {
        "kind": "olmkirakira_compose_debug_neighborhood",
        "status": "diagnostic",
        "debug_log": str(args.debug_log),
        "center_xy": [cx, cy],
        "radius": radius,
        "windows_target_u8": windows_target_u8,
        "center_point": {
            "glow_alpha_after_opacity": center_point["glow_alpha_after_opacity"],
            "out_u8": center_point["out_u8"],
            "out_prequantized_rgba_float": center_point["out_prequantized_rgba_float"],
        },
        "neighborhood": neighborhood,
        "missing_points": missing,
        "summary": {
            "alpha_min": alpha_min,
            "alpha_max": alpha_max,
            "out_r_min": out_min,
            "out_r_max": out_max,
        },
        "reading": reading,
    }


def write_markdown(path: Path, report: dict) -> None:
    lines = [
        "# OLMKiraKira Compose Debug Neighborhood",
        "",
        f"- Debug log: `{report['debug_log']}`",
        f"- Center: `{tuple(report['center_xy'])}`",
        f"- Radius: `{report['radius']}`",
        "",
        "## Center point",
        "",
        f"- glow_alpha_after_opacity: `{report['center_point']['glow_alpha_after_opacity']:.9f}`",
        f"- out_u8: `{report['center_point']['out_u8']}`",
        f"- out_prequantized_rgba_float: `{report['center_point']['out_prequantized_rgba_float']}`",
        "",
        "## Neighborhood grid",
        "",
        "| y/x | entries |",
        "| --- | --- |",
    ]
    for row in report["neighborhood"]:
        y_value = "?"
        cells = []
        for cell in row:
            if cell is None:
                cells.append("missing")
                continue
            y_value = str(cell["y"])
            cells.append(
                f"`x={cell['x']} a={cell['glow_alpha_after_opacity']:.6f} r={cell['out_u8'][0]} "
                f"da={cell['delta_alpha_vs_center']:+.6f} dr={cell['delta_out_r_vs_center']:+d}`"
            )
        lines.append(f"| `{y_value}` | {'<br>'.join(cells)} |")
    lines.extend(["", "## Reading", ""])
    lines.extend(f"- {line}" for line in report["reading"])
    if report["missing_points"]:
        lines.extend(
            [
                "",
                "## Missing points",
                "",
                f"`{report['missing_points']}`",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    global args
    args = parse_args()
    points = load_points(args.debug_log)
    center = parse_xy(args.center)
    report = build_report(points, center, args.radius, args.windows_target_u8)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.output_md, report)
    print(f"report_json={args.output_json}")
    print(f"report_md={args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
