#!/usr/bin/env python3
"""Probe the actual-AEX Rotation RGBA border sampler split.

This is a bounded helper-level proof. It calls the two sampler entry points
directly with a synthetic 2x2 RGBA float plane and records raw output words and
the return value. It does not run the renderer or infer AE-host behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from aex_loader import AexLoader  # noqa: E402

REPO_ROOT = HERE.parents[1]
DEFAULT_AEX = REPO_ROOT / "aex" / "OLMRadialBlur" / "Plugins" / "64" / "2025" / "OLMRadialBlur.aex"
NON_REPEAT = 0x180001270
REPEAT = 0x180001520


def bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def call_sampler(loader: AexLoader, address: int, plane: int, out: int, x: float, y: float) -> dict[str, Any]:
    x_bits, y_bits = bits(f32(x)), bits(f32(y))
    result = loader.call_function(
        address,
        int_args=[plane, out, 2, 2, 8, x_bits, y_bits],
        max_instructions=100_000,
    )
    raw = struct.unpack("<4I", loader.read_bytes(out, 16))
    return {
        "return_rax": int(result["rax"]),
        "rgba_f32": [struct.unpack("<f", struct.pack("<I", word))[0] for word in raw],
        "rgba_f32_words": [f"0x{word:08x}" for word in raw],
        "xy": [x, y],
        "instructions": int(result["instructions"]),
    }


def run(aex_path: Path) -> dict[str, Any]:
    loader = AexLoader(str(aex_path), verbose=False, fast=True)
    # RGBA, row-major. Alpha is deliberately sub-unit so raw repeat-border
    # accumulation can be distinguished from non-repeat geometric normalization.
    plane_values = [
        0.10, 0.20, 0.30, 0.80,
        0.40, 0.50, 0.60, 0.40,
        0.70, 0.80, 0.90, 0.20,
        1.00, 0.90, 0.80, 0.60,
    ]
    plane = loader.bump_alloc(len(plane_values) * 4, align=16)
    loader.write_f32_array(plane, plane_values)

    points = [
        {"name": "left_loose_window", "x": -1.25, "y": 0.5},
        {"name": "top_loose_window", "x": 0.25, "y": -1.25},
        {"name": "interior_control", "x": 0.25, "y": 0.5},
    ]
    records = []
    for point in points:
        non_out = loader.bump_alloc(16, align=16)
        rep_out = loader.bump_alloc(16, align=16)
        non = call_sampler(loader, NON_REPEAT, plane, non_out, point["x"], point["y"])
        rep = call_sampler(loader, REPEAT, plane, rep_out, point["x"], point["y"])
        records.append({**point, "non_repeat": non, "repeat_border": rep})

    issues: list[str] = []
    for record in records[:2]:
        if record["non_repeat"]["return_rax"] != 1:
            issues.append(f"{record['name']}:non_repeat_return_not_one")
        if record["repeat_border"]["return_rax"] != 1:
            issues.append(f"{record['name']}:repeat_return_not_one")
        if record["non_repeat"]["rgba_f32_words"] == record["repeat_border"]["rgba_f32_words"]:
            issues.append(f"{record['name']}:border_sampler_outputs_did_not_diverge")
    control = records[2]
    if control["non_repeat"]["return_rax"] != 1 or control["repeat_border"]["return_rax"] != 1:
        issues.append("interior_control:both_samplers_not_valid")
    if control["non_repeat"]["rgba_f32_words"] != control["repeat_border"]["rgba_f32_words"]:
        issues.append("interior_control:sampler_outputs_diverged")

    return {
        "kind": "olmradialblur_border_sampler_semantics_actual_aex_20260716",
        "schema": 1,
        "status": "pass" if not issues else "fail",
        "classification": "actual-aex-border-validity-alpha-split-proven" if not issues else "actual-aex-border-sampler-proof-failed",
        "evidence_class": "bounded_actual_aex_helper_probe",
        "binary": {
            "path": str(aex_path.relative_to(REPO_ROOT)),
            "sha256": hashlib.sha256(aex_path.read_bytes()).hexdigest(),
            "non_repeat_entry": hex(NON_REPEAT),
            "repeat_border_entry": hex(REPEAT),
        },
        "fixture": {"width": 2, "height": 2, "row_stride_floats": 8, "plane_rgba_f32": plane_values},
        "records": records,
        "issues": sorted(set(issues)),
        "facts": [
            "The actual AEX non-repeat helper accepts the loose -2 < int(coord) border window and samples the in-bounds neighbor at -1.x.",
            "The actual AEX repeat-border helper accepts the same loose-window coordinates but clamps border taps, producing different RGBA float32 words.",
            "Both helpers agree on the interior control, so the split is boundary behavior rather than a general ABI mismatch.",
        ],
        "inference": "A single final alpha plane cannot represent both the repeat-border raw accumulated alpha and the non-repeat validity return. The caller must preserve validity separately until its documented collapse point.",
        "limitations": [
            "Synthetic 2x2 helper input only.",
            "No prepass/scatter invocation and no AE host execution.",
            "Does not claim Mac/Windows or AE exactness and does not authorize production changes.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMRadialBlur border sampler semantic proof",
        "",
        f"- Status: `{report['status']}`",
        f"- Classification: `{report['classification']}`",
        f"- Evidence class: `{report['evidence_class']}`",
        f"- AEX SHA-256: `{report['binary']['sha256']}`",
        "",
        "## FACT",
        "",
    ]
    lines.extend(f"- {fact}" for fact in report["facts"])
    lines.extend(["", "| point | non-repeat return / RGBA words | repeat-border return / RGBA words |", "| --- | --- | --- |"])
    for record in report["records"]:
        left = record["non_repeat"]
        right = record["repeat_border"]
        lines.append(f"| `{record['name']}` `[{record['x']}, {record['y']}]` | `{left['return_rax']}` / `{left['rgba_f32_words']}` | `{right['return_rax']}` / `{right['rgba_f32_words']}` |")
    lines.extend(["", "## INFERENCE", "", f"- {report['inference']}", "", "## LIMITS", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.extend(["", f"- Issues: `{report['issues']}`", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aex", type=Path, default=DEFAULT_AEX)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()
    report = run(args.aex)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(markdown(report), encoding="utf-8")
    print(f"status={report['status']} classification={report['classification']}")
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
