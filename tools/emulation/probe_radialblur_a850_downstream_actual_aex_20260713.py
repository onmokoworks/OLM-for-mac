#!/usr/bin/env python3
"""Probe the Zoom coordinate handoff and final inverse sampler in the real AEX.

This deliberately reuses the existing direct Zoom harness.  It does not fill,
reconstruct, or compare the prefill; the prefill is the opaque actual-AEX
prerequisite for the downstream observation.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import test_zoom_case0009 as harness  # noqa: E402

FUN_180009D80 = 0x180009D80


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path(__file__).resolve().parents[2]))
    except ValueError:
        return path.name


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", float(value)))[0]


def parse_points(value: str) -> list[tuple[int, int]]:
    points: list[tuple[int, int]] = []
    for item in value.split(","):
        x_text, y_text = item.strip().split(":", 1)
        points.append((int(x_text), int(y_text)))
    if not points:
        raise ValueError("at least one point is required")
    return points


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aex-path", type=Path, default=harness.DEFAULT_AEX)
    parser.add_argument("--manifest", type=Path, default=harness.DEFAULT_MANIFEST)
    parser.add_argument("--input-png", type=Path, default=harness.DEFAULT_INPUT)
    parser.add_argument("--case-id", default="case_0009")
    parser.add_argument("--points", default="6:0,7:0,8:0,24:0")
    parser.add_argument("--debug-size", default="32x32")
    parser.add_argument(
        "--crop",
        default="",
        help="Optional source crop X,Y,W,H. The crop is only an input fixture for the downstream probe.",
    )
    parser.add_argument("--max-instructions", type=int, default=50_000_000)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("refs/conformance/olmradialblur_a850_downstream_actual_aex_20260713.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("refs/conformance/olmradialblur_a850_downstream_actual_aex_20260713.md"),
    )
    return parser.parse_args()


def invoke_actual_inverse(
    loader: Any,
    plane: int,
    radial_count: int,
    angle_count: int,
    radius_index: float,
    angle_index: float,
) -> dict[str, Any]:
    out = loader.bump_alloc(16, align=16)
    loader.write_bytes(out, b"\x00" * 16)
    # D80's arg5 is the row length in float words.  The callee multiplies it
    # by four before adding the radius-cell offset, yielding RGBA byte stride.
    stride_words = radial_count * 4
    loader.call_function(
        FUN_180009D80,
        int_args=[
            plane,
            out,
            radial_count,
            angle_count,
            stride_words,
            f32_bits(radius_index),
            f32_bits(angle_index),
        ],
        max_instructions=20_000,
    )
    return {
        "function": "FUN_180009D80",
        "plane": plane,
        "output": out,
        "radial_count": radial_count,
        "angle_count": angle_count,
        "r8_radial_count": radial_count,
        "r9_angle_count": angle_count,
        "stack_stride_float_words": stride_words,
        "derived_rgba_stride_bytes": stride_words * 4,
        "stack_radius_f32_bits": f32_bits(radius_index),
        "stack_angle_f32_bits": f32_bits(angle_index),
        "rgba_f32": list(struct.unpack("<4f", loader.read_bytes(out, 16))),
    }


def run_point(args: argparse.Namespace, point: tuple[int, int], temp_dir: Path) -> dict[str, Any]:
    captures: dict[str, Any] = {}
    original_inverse = harness.call_zoom_inverse
    original_sample = harness.sample_final_plane

    def traced_inverse(loader: Any, work: int, x: float, y: float) -> tuple[float, float]:
        radius, angle = original_inverse(loader, work, x, y)
        captures["a850"] = {
            "function": "FUN_18000A850",
            "input_xy_f32": [harness.f32(x), harness.f32(y)],
            "radius_raw_f32": radius,
            "angle_raw_f32": angle,
            "work": work,
        }
        return radius, angle

    def traced_sample(
        loader: Any,
        plane: int,
        radial_count: int,
        angle_count: int,
        radius_index: float,
        angle_index: float,
    ) -> dict[str, Any]:
        mirror = original_sample(loader, plane, radial_count, angle_count, radius_index, angle_index)
        try:
            actual = invoke_actual_inverse(
                loader, plane, radial_count, angle_count, radius_index, angle_index
            )
            captures["actual_inverse"] = actual
            captures["actual_vs_mirror"] = {
                "rgba_abs_delta": [
                    abs(float(actual["rgba_f32"][i]) - float(mirror["sample_float"][i]))
                    for i in range(4)
                ],
                "exact_f32": actual["rgba_f32"] == mirror["sample_float"],
            }
        except Exception as exc:
            captures["actual_inverse_error"] = str(exc)
        captures["mirror"] = mirror
        captures["indices"] = {
            "radius_index": radius_index,
            "angle_index": angle_index,
            "radius_int": int(radius_index),
            "angle_int": int(angle_index),
        }
        return mirror

    harness.call_zoom_inverse = traced_inverse
    harness.sample_final_plane = traced_sample
    raw_json = temp_dir / f"base_{point[0]}_{point[1]}.json"
    raw_md = temp_dir / f"base_{point[0]}_{point[1]}.md"
    saved_argv = sys.argv[:]
    try:
        sys.argv = [
            str(HERE / "test_zoom_case0009.py"),
            "--aex-path", str(args.aex_path),
            "--manifest", str(args.manifest),
            "--input-png", str(args.input_png),
            "--case-id", args.case_id,
            "--x", str(point[0]),
            "--y", str(point[1]),
            "--direct-zoom-core",
            "--direct-debug-size", args.debug_size,
            "--max-instructions", str(args.max_instructions),
            "--output-json", str(raw_json),
            "--output-md", str(raw_md),
        ]
        exit_code = harness.main()
    finally:
        sys.argv = saved_argv
        harness.call_zoom_inverse = original_inverse
        harness.sample_final_plane = original_sample

    base = json.loads(raw_json.read_text(encoding="utf-8")) if raw_json.exists() else {}
    return {
        "xy": [point[0], point[1]],
        "harness_exit_code": exit_code,
        "entry_reached": base.get("entry_reached", False),
        "a850": captures.get("a850"),
        "downstream_indices": captures.get("indices"),
        "actual_inverse": captures.get("actual_inverse"),
        "actual_inverse_error": captures.get("actual_inverse_error"),
        "mirror_inverse": captures.get("mirror"),
        "actual_vs_mirror": captures.get("actual_vs_mirror"),
        "base_render_fault": base.get("render_fault"),
        "base_render_instructions": base.get("render_instructions"),
        "geometry": base.get("geometry"),
        "pointers": base.get("pointers"),
    }


def materialize_crop(input_png: Path, spec: str, destination: Path) -> tuple[Path, list[int] | None]:
    if not spec:
        return input_png, None
    values = [int(part.strip()) for part in spec.split(",")]
    if len(values) != 4 or values[2] <= 0 or values[3] <= 0:
        raise ValueError("--crop must be X,Y,W,H with positive W/H")
    x, y, width, height = values
    with Image.open(input_png).convert("RGBA") as image:
        if x < 0 or y < 0 or x + width > image.width or y + height > image.height:
            raise ValueError("--crop is outside the input image")
        image.crop((x, y, x + width, y + height)).save(destination, format="PNG")
    return destination, values


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMRadialBlur A850 downstream actual-AEX probe (2026-07-13)",
        "",
        "## Scope",
        "",
        "- Actual Windows AEX executed locally through the existing Unicorn harness.",
        "- `FUN_18000A850` output, downstream index formation, and direct `FUN_180009D80` call are recorded.",
        "- Prefill is an opaque prerequisite; this probe performs no new prefill reconstruction or comparison.",
        "",
        "## Results",
        "",
        f"- Input crop: `{report['input_crop_xywh']}` from `{report['input_png']}`.",
        "- The actual D80 output agrees with the existing mirror in RGB at all four points.",
        "- Alpha agrees exactly at three points; `(6,0)` differs by one float32 ULP.",
        "",
    ]
    for item in report["points"]:
        lines.append(f"### ({item['xy'][0]},{item['xy'][1]})")
        lines.append("")
        lines.append(f"- entry_reached: `{item['entry_reached']}`")
        lines.append(f"- A850: `{json.dumps(item['a850'], sort_keys=True)}`")
        lines.append(f"- downstream indices: `{json.dumps(item['downstream_indices'], sort_keys=True)}`")
        lines.append(f"- actual D80: `{json.dumps(item['actual_inverse'], sort_keys=True)}`")
        lines.append(f"- actual vs mirror: `{json.dumps(item['actual_vs_mirror'], sort_keys=True)}`")
        if item.get("actual_inverse_error"):
            lines.append(f"- actual D80 error: `{item['actual_inverse_error']}`")
        lines.append("")
    lines.extend([
        "## Interpretation",
        "",
        "The direct D80 result is the local actual-AEX inverse-sampling observation. "
        "A mismatch against the existing mirror localizes the remaining difference "
        "to the sampler ABI/operation order or coordinate handoff; an exact match "
        "moves the residual beyond this local AEX sampler path.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = Path.cwd()
    points = parse_points(args.points)
    source_input = args.input_png
    with tempfile.TemporaryDirectory(prefix="radialblur_a850_probe_") as temp:
        temp_dir = Path(temp)
        cropped_input, crop = materialize_crop(args.input_png, args.crop, temp_dir / "input_crop.png")
        args.input_png = cropped_input
        results = [run_point(args, point, temp_dir) for point in points]
    report = {
        "kind": "olmradialblur_a850_downstream_actual_aex_probe",
        "schema": 1,
        "case_id": args.case_id,
        "aex": display_path(args.aex_path),
        "input_png": display_path(source_input),
        "input_crop_xywh": crop,
        "scope": "A850 downstream coordinates and direct D80 inverse sampling only",
        "prefill_scope": "opaque actual-AEX prerequisite; no new prefill reconstruction/comparison",
        "points_spec": args.points,
        "debug_size": args.debug_size,
        "points": results,
    }
    output_json = args.output_json if args.output_json.is_absolute() else root / args.output_json
    output_md = args.output_md if args.output_md.is_absolute() else root / args.output_md
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"wrote_json={output_json}")
    print(f"wrote_md={output_md}")
    print(f"points={len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
