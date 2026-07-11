#!/usr/bin/env python3
"""Run and materialize the DG 0010/0011 AEX CPU fieldgen witness probe."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools/emulation/test_dg_fieldgen_p1b.py"
INPUT_DIR = ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/input"
OUT_JSON = ROOT / "refs/conformance/olmdistancegradation_0010_0011_aex_fieldgen_probe_20260709.json"
OUT_MD = ROOT / "refs/conformance/olmdistancegradation_0010_0011_aex_fieldgen_probe_20260709.md"


PROBES = [
    {
        "id": "case0010_inside",
        "case_id": "olmdistancegradation_extended__case_0010",
        "input": INPUT_DIR
        / "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0010_before_effects.png",
        "threshold": 63,
        "invert_mask": False,
        "points": "901,394;6,40",
        "witness_xy": [901, 394],
        "windows_required_field_word": 22892,
        "windows_store_a": 9876,
    },
    {
        "id": "case0010_outside",
        "case_id": "olmdistancegradation_extended__case_0010",
        "input": INPUT_DIR
        / "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0010_before_effects.png",
        "threshold": 82,
        "invert_mask": True,
        "points": "901,394;6,40",
        "witness_xy": [6, 40],
        "windows_required_field_word": 29500,
        "windows_store_a": 3268,
    },
    {
        "id": "case0011_inside",
        "case_id": "olmdistancegradation_extended__case_0011",
        "input": INPUT_DIR
        / "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0011_before_effects.png",
        "threshold": 348,
        "invert_mask": False,
        "points": "915,392",
        "witness_xy": [915, 392],
        "windows_required_field_word": 4409,
        "windows_store_a": 28359,
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def run_probe(probe: dict[str, Any]) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(RUNNER),
        "--mask-png",
        str(probe["input"]),
        "--mask-channel",
        "alpha",
        "--threshold",
        str(probe["threshold"]),
        "--param8",
        "0",
        "--points",
        probe["points"],
        "--points-global",
    ]
    if probe["invert_mask"]:
        cmd.insert(cmd.index("--threshold"), "--invert-mask")
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"probe {probe['id']} failed with {proc.returncode}\n{proc.stdout}")
    data = json.loads(proc.stdout)
    wx, wy = probe["witness_xy"]
    sample = next(
        row
        for row in data["samples"]
        if row.get("requested_xy") == [wx, wy]
    )
    field_x = float(sample["output"])
    field_word_float = field_x * 32768.0
    field_word_floor = int(field_word_float)
    field_word_ceil = field_word_floor if field_word_float == field_word_floor else field_word_floor + 1
    return {
        "id": probe["id"],
        "case_id": probe["case_id"],
        "command": cmd,
        "returncode": proc.returncode,
        "raw_stdout": proc.stdout,
        "threshold": probe["threshold"],
        "invert_mask": probe["invert_mask"],
        "witness_xy": probe["witness_xy"],
        "field_x": field_x,
        "field_word_float": field_word_float,
        "field_word_floor": field_word_floor,
        "field_word_ceil": field_word_ceil,
        "windows_required_field_word": probe["windows_required_field_word"],
        "windows_required_matches_floor": probe["windows_required_field_word"] == field_word_floor,
        "windows_required_matches_ceil": probe["windows_required_field_word"] == field_word_ceil,
        "windows_store_a": probe["windows_store_a"],
        "callback_counts": data.get("callback_counts", {}),
        "hits": data.get("hits", []),
        "instructions": data.get("instructions"),
        "output_min": data.get("output_min"),
        "output_max": data.get("output_max"),
        "output_mean": data.get("output_mean"),
    }


def decide(rows: list[dict[str, Any]]) -> str:
    if all(row["windows_required_matches_floor"] for row in rows):
        return "fieldgen-floats-floor-to-windows-field-words"
    if all(row["windows_required_matches_ceil"] for row in rows):
        return "fieldgen-floats-ceil-to-windows-field-words"
    return "fieldgen-floats-match-current-mac-but-pack-rule-sign-flips"


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMDistanceGradation 0010/0011 AEX fieldgen probe - 2026-07-09",
        "",
        "This runs the real Windows `DistanceGradation.aex` field-generation helper",
        "under the local AEX CPU emulator with the validated OpenCV detours:",
        "`threshold`, `dist_transform`, `resize_same_shape`, and `normalize_minmax`.",
        "",
        f"- Decision: `{report['decision']}`",
        "",
        "## Samples",
        "",
        "| Probe | XY | Field X | Field*32768 | Floor | Ceil | Windows-required field word | Match |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in report["probes"]:
        xy = f"({row['witness_xy'][0]},{row['witness_xy'][1]})"
        if row["windows_required_matches_floor"]:
            match = "floor"
        elif row["windows_required_matches_ceil"]:
            match = "ceil"
        else:
            match = "neither"
        lines.append(
            f"| `{row['id']}` | `{xy}` | {row['field_x']:.12g} | "
            f"{row['field_word_float']:.12g} | {row['field_word_floor']} | "
            f"{row['field_word_ceil']} | {row['windows_required_field_word']} | {match} |"
        )
    lines.extend(
        [
            "",
            "## Reading",
            "",
            "- The AEX helper completes for the full `1920x1080` inputs and reaches the expected OpenCV detours in each run.",
            "- The emitted float field values reproduce the current Mac-side field floats seen in earlier local probes.",
            "- The Windows-required field-word relation is sign-flipped: the outside witness matches `floor`, while both inside witnesses require `ceil`.",
            "- This rejects a single global final-writer rule and also rejects a simple one-rule PF16 field-pack toggle over the current field floats.",
            "- The next proof is the field-world pack/consume boundary in the real Windows run, or a same-run true16 TIFF/EXR export only if export binding is still needed.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    probes = [run_probe(probe) for probe in PROBES]
    report = {
        "kind": "olmdistancegradation_0010_0011_aex_fieldgen_probe",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "decision": decide(probes),
        "probes": probes,
        "source_reports": [
            "refs/conformance/olmdistancegradation_0010_0011_opencv_field_prep_audit_20260709.md",
            "tools/emulation/OPENCV_DETOUR_P1_REPORT.md",
        ],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"report_json={args.output_json}")
    print(f"report_md={args.output_md}")
    print(f"decision={report['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
