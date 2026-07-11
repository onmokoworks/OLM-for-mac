#!/usr/bin/env python3
"""Classify the OLMRadialBlur Zoom case_0009 254/255 alpha boundary.

This is a local evidence collector, not a tuning script.  It compares the
top-row witness neighborhood for the current C++ CLI under the narrow variants
that previously looked relevant:

- default current path
- AEX-float/repeat-raw-f32 sampler
- polar-alpha caller-collapse
- polar-alpha plus global alpha truncate

The purpose is to keep the RadialBlur Zoom lane honest: the single witness
pixel can be made to store alpha 254 by global truncation, but that edit is
overbroad.  The report records the local row where that happens.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "refs" / "win_references" / "20260604_olm" / "OLMRadialBlur"
DEFAULT_JSON = ROOT / "refs" / "conformance" / "olmradialblur_zoom_case0009_quantize_locus_20260709.json"
DEFAULT_MD = ROOT / "refs" / "conformance" / "olmradialblur_zoom_case0009_quantize_locus_20260709.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", default="case_0009")
    parser.add_argument("--row-y", type=int, default=0)
    parser.add_argument("--row-x0", type=int, default=0)
    parser.add_argument("--row-x1", type=int, default=30)
    parser.add_argument("--witness-x", type=int, default=6)
    parser.add_argument("--witness-y", type=int, default=0)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    return parser.parse_args()


def load_case(reference_dir: Path, case_id: str) -> dict[str, Any]:
    manifest = json.loads((reference_dir / "reference_manifest.json").read_text(encoding="utf-8-sig"))
    for case in manifest.get("cases", []):
        if isinstance(case, dict) and case.get("id") == case_id:
            return case
    raise RuntimeError(f"case not found: {case_id}")


def run_checked(cmd: list[str], cwd: Path) -> str:
    proc = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stdout}")
    return proc.stdout


def diff_stats(reference: Path, candidate: Path) -> dict[str, int]:
    ref = Image.open(reference).convert("RGBA")
    cand = Image.open(candidate).convert("RGBA")
    diff = ImageChops.difference(ref, cand)
    raw = diff.tobytes()
    return {
        "max_diff": max(channel[1] for channel in diff.getextrema()),
        "nonzero_px": sum(1 for i in range(0, len(raw), 4) if raw[i : i + 4] != b"\x00\x00\x00\x00"),
    }


def pixel(path: Path, x: int, y: int) -> list[int]:
    return list(Image.open(path).convert("RGBA").getpixel((x, y)))


def variant_args() -> dict[str, list[str]]:
    aex_repeat = ["--zoom-grid-mode", "aex-float", "--rgba-sampler-alpha-mode", "repeat-raw-f32"]
    polar_alpha = [*aex_repeat, "--outer-caller-collapse-mode", "polar-alpha"]
    return {
        "default": [],
        "aex_repeat": aex_repeat,
        "polar_alpha": polar_alpha,
        "polar_alpha_truncate": [*polar_alpha, "--outer-alpha-quantize-mode", "truncate"],
    }


def row_probe_by_x(witness: dict[str, Any]) -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    for point in witness.get("row_probe", []):
        if not isinstance(point, dict):
            continue
        if isinstance(point.get("x"), int):
            out[int(point["x"])] = point
            continue
        xy = point.get("xy")
        if isinstance(xy, list) and len(xy) == 2 and isinstance(xy[0], int):
            out[int(xy[0])] = point
    return out


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    case = load_case(REFERENCE_DIR, args.case_id)
    build_output = run_checked([str(ROOT / "refs" / "scripts" / "build_olmradialblur_cli.sh")], ROOT)
    tmp = Path(tempfile.mkdtemp(prefix="olmradialblur_zoom_locus_"))
    try:
        params = tmp / f"{args.case_id}_params.json"
        params.write_text(json.dumps(case, indent=2, ensure_ascii=False), encoding="utf-8")
        input_png = REFERENCE_DIR / case["before_effects_frame"]
        reference_png = REFERENCE_DIR / case["frame"]
        row_center = (args.row_x0 + args.row_x1) // 2
        row_half_span = max(row_center - args.row_x0, args.row_x1 - row_center)

        variants: dict[str, dict[str, Any]] = {}
        for name, extra in variant_args().items():
            output = tmp / f"{name}.png"
            witness_path = tmp / f"{name}.json"
            stdout = run_checked(
                [
                    str(ROOT / "cli" / "OLMRadialBlur" / "olmradialblur_cli"),
                    "--input",
                    str(input_png),
                    "--params",
                    str(params),
                    "--output",
                    str(output),
                    *extra,
                    "--witness-dump",
                    str(witness_path),
                    "--witness-x",
                    str(row_center),
                    "--witness-y",
                    str(args.row_y),
                    "--witness-row-half-span",
                    str(row_half_span),
                ],
                ROOT,
            )
            witness = json.loads(witness_path.read_text(encoding="utf-8"))
            probes = row_probe_by_x(witness)
            row: list[dict[str, Any]] = []
            for x in range(args.row_x0, args.row_x1 + 1):
                probe = probes.get(x, {})
                row.append(
                    {
                        "x": x,
                        "reference": pixel(reference_png, x, args.row_y),
                        "candidate": pixel(output, x, args.row_y),
                        "alpha_float": probe.get("alpha"),
                        "alpha_u8": probe.get("alpha_u8"),
                        "sample_u8": probe.get("sample_u8"),
                        "cell_alpha": probe.get("cell_alpha"),
                        "cell_valid": probe.get("cell_valid"),
                        "radius_index": probe.get("radius_index"),
                        "angle_index": probe.get("angle_index"),
                        "validity_alpha": probe.get("validity_alpha"),
                        "validity_alpha_u8": probe.get("validity_alpha_u8"),
                    }
                )
            variants[name] = {
                **diff_stats(reference_png, output),
                "witness_pixel": pixel(output, args.witness_x, args.witness_y),
                "witness_probe": probes.get(args.witness_x, {}),
                "row": row,
                "stdout_tail": stdout.strip().splitlines()[-3:],
            }

        ref_witness = pixel(reference_png, args.witness_x, args.witness_y)
        ref_alpha254_x = [
            x
            for x in range(args.row_x0, args.row_x1 + 1)
            if pixel(reference_png, x, args.row_y)[3] == 254
        ]
        trunc_matches_reference = [
            point["x"]
            for point in variants["polar_alpha_truncate"]["row"]
            if point["candidate"] == point["reference"]
        ]
        default_alpha_off_by_one = [
            point["x"]
            for point in variants["default"]["row"]
            if point["candidate"][:3] == point["reference"][:3]
            and point["candidate"][3] - point["reference"][3] == 1
        ]
        off_by_one_details: list[dict[str, Any]] = []
        for x in default_alpha_off_by_one:
            detail: dict[str, Any] = {"x": x, "reference": pixel(reference_png, x, args.row_y)}
            for name in ("default", "aex_repeat", "polar_alpha", "polar_alpha_truncate"):
                row_point = next(point for point in variants[name]["row"] if point["x"] == x)
                probe = variants[name]["witness_probe"] if x == row_center else {}
                detail[name] = {
                    "candidate": row_point["candidate"],
                    "alpha": row_point.get("alpha_float"),
                    "alpha_u8": row_point.get("alpha_u8"),
                    "sample_u8": row_point.get("sample_u8"),
                    "cell_alpha": row_point.get("cell_alpha"),
                    "radius_index": row_point.get("radius_index"),
                    "angle_index": row_point.get("angle_index"),
                    "fx": probe.get("fx"),
                    "fy": probe.get("fy"),
                }
            off_by_one_details.append(detail)
        return {
            "kind": "olmradialblur_zoom_case0009_quantize_locus",
            "schema": 1,
            "case_id": args.case_id,
            "row_y": args.row_y,
            "row_range": [args.row_x0, args.row_x1],
            "witness_xy": [args.witness_x, args.witness_y],
            "reference_witness_pixel": ref_witness,
            "reference_alpha254_x": ref_alpha254_x,
            "default_alpha_off_by_one_x": default_alpha_off_by_one,
            "default_alpha_off_by_one_details": off_by_one_details,
            "polar_alpha_truncate_matches_reference_x": trunc_matches_reference,
            "variants": variants,
            "build_output_tail": build_output.strip().splitlines()[-5:],
            "interpretation": (
                "The 254/255 witness can be reproduced locally only by applying a global alpha "
                "truncate to the polar-alpha candidate, but that variant remains broad at full-frame "
                "diff scale.  Therefore the live proof target is the final-polar cell/plane contents "
                "or coordinate sequence that makes only the AEX-relevant cells land just below 1.0, "
                "not a late output-byte conversion change."
            ),
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# OLMRadialBlur Zoom case_0009 Quantize Locus",
        "",
        f"- Case: `{report['case_id']}`",
        f"- Row: `y={report['row_y']}`, `x={report['row_range'][0]}..{report['row_range'][1]}`",
        f"- Witness: `{report['witness_xy']}` reference `{report['reference_witness_pixel']}`",
        f"- Reference alpha=254 x positions: `{report['reference_alpha254_x']}`",
        f"- Default alpha-only +1 x positions: `{report['default_alpha_off_by_one_x']}`",
        f"- Truncate variant row exact x positions: `{report['polar_alpha_truncate_matches_reference_x']}`",
        "",
        "## Variant Summary",
        "",
        "| Variant | max_diff | nonzero_px | witness pixel | witness alpha | witness sample_u8 |",
        "| --- | ---: | ---: | --- | ---: | --- |",
    ]
    for name, data in report["variants"].items():
        probe = data.get("witness_probe") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{name}`",
                    str(data["max_diff"]),
                    str(data["nonzero_px"]),
                    f"`{data['witness_pixel']}`",
                    f"`{probe.get('alpha')}`",
                    f"`{probe.get('sample_u8')}`",
                ]
            )
            + " |"
        )
    lines.extend(["", "## Row Points", ""])
    lines.append("| x | ref | default | polar-alpha | truncate | polar-alpha alpha | truncate alpha |")
    lines.append("| ---: | --- | --- | --- | --- | ---: | ---: |")
    default = {p["x"]: p for p in report["variants"]["default"]["row"]}
    polar = {p["x"]: p for p in report["variants"]["polar_alpha"]["row"]}
    trunc = {p["x"]: p for p in report["variants"]["polar_alpha_truncate"]["row"]}
    for x in range(report["row_range"][0], report["row_range"][1] + 1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(x),
                    f"`{default[x]['reference']}`",
                    f"`{default[x]['candidate']}`",
                    f"`{polar[x]['candidate']}`",
                    f"`{trunc[x]['candidate']}`",
                    f"`{polar[x].get('alpha_float')}`",
                    f"`{trunc[x].get('alpha_float')}`",
                ]
            )
            + " |"
        )
    lines.extend(["", "## Alpha Off-By-One Details", ""])
    lines.append(
        "| x | ref | default alpha/sample | polar-alpha alpha/sample | polar-alpha cell alpha | radius | angle |"
    )
    lines.append("| ---: | --- | --- | --- | --- | ---: | ---: |")
    for detail in report["default_alpha_off_by_one_details"]:
        polar = detail["polar_alpha"]
        default = detail["default"]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(detail["x"]),
                    f"`{detail['reference']}`",
                    f"`{default.get('alpha')}` / `{default.get('sample_u8')}`",
                    f"`{polar.get('alpha')}` / `{polar.get('sample_u8')}`",
                    f"`{polar.get('cell_alpha')}`",
                    f"`{polar.get('radius_index')}`",
                    f"`{polar.get('angle_index')}`",
                ]
            )
            + " |"
        )
    lines.extend(["", "## Interpretation", "", report["interpretation"], ""])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    report = build_report(args)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_md(report), encoding="utf-8")
    print(f"report_json={args.output_json}")
    print(f"report_md={args.output_md}")
    print(f"default_nonzero={report['variants']['default']['nonzero_px']}")
    print(f"truncate_nonzero={report['variants']['polar_alpha_truncate']['nonzero_px']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
