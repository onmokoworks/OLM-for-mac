#!/usr/bin/env python3
"""Parse OLMRadialBlur Mac AE debug-point logs into JSON/Markdown."""

from __future__ import annotations

import argparse
import json
import math
import re
import struct
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
    r"brightness_gain=(?P<brightness_gain>[-+0-9.eE]+) "
    r"accum_rgba=\((?P<accum_rgba>[^)]+)\) accum_rgba_hex=\((?P<accum_rgba_hex>[^)]+)\) "
    r"normalized_rgba=\((?P<normalized_rgba>[^)]+)\) normalized_rgba_hex=\((?P<normalized_rgba_hex>[^)]+)\) "
    r"cell_valid=\((?P<cell_valid>[^)]+)\) "
    r"cell_alpha=\((?P<cell_alpha>[^)]+)\) "
    r"cell_rgb=\(\((?P<cell_rgb>.+)\)\) "
    r"src_cell_rgba=\(\((?P<src_cell_rgba>.+)\)\)$"
)
COORD_RAW_PREFIX = "OLMRADIALBLUR_DEBUG_COORD_RAW "


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


def f32_from_bits(raw: str) -> float:
    if not isinstance(raw, str) or not re.fullmatch(r"0x[0-9a-fA-F]{8}", raw):
        raise ValueError(f"invalid float32 bit string: {raw!r}")
    return struct.unpack("<f", struct.pack("<I", int(raw, 16)))[0]


def enrich_raw_lane(lane: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(lane)
    for name, value in list(lane.items()):
        if name.endswith("_bits") and isinstance(value, str):
            enriched[name[:-5] + "_f32"] = f32_from_bits(value)
    operations = lane.get("operation_bits")
    if isinstance(operations, dict):
        enriched["operation_f32"] = {name: f32_from_bits(value) for name, value in operations.items()}
    cells = lane.get("cell_rgba_bits")
    if isinstance(cells, list):
        enriched["cell_rgba_f32"] = [[f32_from_bits(value) for value in cell] for cell in cells]
    return enriched


def load_coordinate_raw(lines: list[str]) -> dict[tuple[str, int, int], dict[str, Any]]:
    records: dict[tuple[str, int, int], dict[str, Any]] = {}
    for line in lines:
        clean = line.strip()
        if not clean.startswith(COORD_RAW_PREFIX):
            continue
        payload = json.loads(clean[len(COORD_RAW_PREFIX):])
        key = (str(payload["kind"]), int(payload["x"]), int(payload["y"]))
        if key in records:
            raise ValueError(f"duplicate coordinate raw record for {key}")
        payload = dict(payload)
        payload["production"] = enrich_raw_lane(payload["production"])
        payload["aex_f32_candidate"] = enrich_raw_lane(payload["aex_f32_candidate"])
        records[key] = payload
    return records


def load_points(path: Path) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    coordinate_raw = load_coordinate_raw(lines)
    for line in lines:
        match = POINT_RE.match(line.strip())
        if not match:
            continue
        data = match.groupdict()
        sample_u8 = parse_tuple(data["sample_u8"], int)
        validity_alpha = float(data["validity_alpha"])
        point = {
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
            "brightness_gain": float(data["brightness_gain"]),
            "accum_rgba": parse_tuple(data["accum_rgba"], float),
            "accum_rgba_hex": [part.strip() for part in data["accum_rgba_hex"].split(",")],
            "normalized_rgba": parse_tuple(data["normalized_rgba"], float),
            "normalized_rgba_hex": [part.strip() for part in data["normalized_rgba_hex"].split(",")],
            "cell_valid": parse_tuple(data["cell_valid"], float),
            "cell_alpha": parse_tuple(data["cell_alpha"], float),
            "cell_rgb": parse_cell_rgb(data["cell_rgb"]),
            "src_cell_rgba": parse_cell_rgba(data["src_cell_rgba"]),
        }
        raw = coordinate_raw.get((point["kind"], point["x"], point["y"]))
        if raw is not None:
            point["coordinate_raw"] = raw
        points.append(point)
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
        "coordinate_raw_count": sum("coordinate_raw" in point for point in points),
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
        f"- Coordinate raw records: `{report['coordinate_raw_count']}`",
        f"- Kinds: `{', '.join(report['kinds'])}`",
        "",
    ]
    for kind in report["kinds"]:
        lines.extend(
            [
                f"## {kind}",
                "",
                "| XY | sample_u8 | alpha_u8 | validity_alpha_u8 | brightness_gain | accum_rgba | normalized_rgba | indices | cell_valid | cell_alpha |",
                "| - | - | -: | -: | -: | - | - | - | - | - |",
            ]
        )
        for point in report["by_kind"][kind]:
            lines.append(
                f"| `({point['x']},{point['y']})` | `{point['sample_u8']}` | "
                f"{point['alpha_u8']} | {point['validity_alpha_u8']} | "
                f"{point['brightness_gain']:.6g} | `{point['accum_rgba']}` | `{point['normalized_rgba']}` | "
                f"`{point['indices']}` | `{point['cell_valid']}` | `{point['cell_alpha']}` |"
            )
        lines.append("")
        raw_points = [point for point in report["by_kind"][kind] if "coordinate_raw" in point]
        if raw_points:
            lines.extend(
                [
                    "| XY | production radius/angle bits | candidate radius/angle bits | production cells | candidate cells |",
                    "| - | - | - | - | - |",
                ]
            )
            for point in raw_points:
                raw = point["coordinate_raw"]
                production = raw["production"]
                candidate = raw["aex_f32_candidate"]
                lines.append(
                    f"| `({point['x']},{point['y']})` | "
                    f"`{production['radius_raw_bits']}/{production['angle_raw_bits']}` | "
                    f"`{candidate['radius_raw_bits']}/{candidate['angle_raw_bits']}` | "
                    f"`{production['cell_indices']}` | `{candidate['cell_indices']}` |"
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
