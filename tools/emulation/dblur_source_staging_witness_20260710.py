#!/usr/bin/env python3
"""Bounded source/staging/final-source witness for DirectionalBlur row 169.

This deliberately reuses the existing real-AEX rowdriver capture and writes
only new artifacts.  It does not modify Mac source, PNGs, or the conformance
ledger.  "Final source" means the A buffer observed after the rowdriver
returns; final host pixel storage remains outside this rowdriver probe.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from probe_dblur_case0001_row169_boundary_capture import run as run_capture

ROOT = Path(__file__).resolve().parents[2]
ROW = 169
SOURCE_X = 959
TARGETS = (494, 579)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aex", type=Path, default=ROOT / "plugins_2025/OLMDirectionalBlur.aex")
    parser.add_argument("--source", type=Path, default=ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png")
    parser.add_argument("--reference", type=Path, default=ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001.png")
    parser.add_argument("--output-json", type=Path, default=ROOT / "refs/conformance/dblur_source_staging_witness_20260710.json")
    parser.add_argument("--output-md", type=Path, default=ROOT / "refs/conformance/dblur_source_staging_witness_20260710.md")
    args = parser.parse_args()

    source = Image.open(args.source).convert("RGBA")
    reference = Image.open(args.reference).convert("RGBA")
    capture = run_capture(SimpleNamespace(aex=args.aex, source=args.source))
    records = []
    for rec in capture.get("records", []):
        x = rec["xy"][0]
        records.append({
            "xy": rec["xy"],
            "source_before_rgba_u8": list(source.getpixel((SOURCE_X, ROW))),
            "source_before_rgba_f32": [v / 255.0 for v in source.getpixel((SOURCE_X, ROW))],
            "source_after_rowdriver_rgba_f32": rec["source"]["rgba"],
            "staging_before_scatter_B_rgba_f32": rec["pre_scatter"]["B_rgba"],
            "staging_after_scatter_B_rgba_f32": rec["post_scatter"]["B_rgba"],
            "staging_writeback_input_B_rgba_f32": rec["writeback_input"]["B_rgba"],
            "staging_classification": rec["classification"],
            "windows_final_rgba_u8": list(reference.getpixel((x, ROW))),
            "windows_red_delta_from_zero": reference.getpixel((x, ROW))[0],
        })

    result = {
        "kind": "dblur_source_staging_witness",
        "schema": 1,
        "status": capture.get("status"),
        "case_id": "case_0001",
        "row_y": ROW,
        "source_xy": [SOURCE_X, ROW],
        "targets": [[x, ROW] for x in TARGETS],
        "aex": {"path": str(args.aex.relative_to(ROOT)), "rowdriver": "FUN_1800038d0", "scatter": "FUN_1800013e0"},
        "inputs": {"source_path": str(args.source.relative_to(ROOT)), "windows_reference_path": str(args.reference.relative_to(ROOT))},
        "records": records,
        "facts": [
            "FACT: source (959,169) is [0,0,0,255] in the Windows before-effects input.",
            "FACT: the real AEX rowdriver capture reaches source_x=959 on row 169 and observes source RGB zero after return.",
            "FACT: with zero-initialized staging, the observed B RGB at (494,169) and (579,169) is zero immediately after scatter and at rowdriver writeback input.",
            "FACT: Windows final reference is red=164 at (494,169) and red=25 at (579,169), both alpha=255.",
            "FACT: disassembly makes the front helper write leftward from a source position: offsets begin at 1 and continue while offset < param_9; the effective span is int(param_9 * param_11), subject to clipping.",
        ],
        "inference": [
            "INFERENCE: source (959,169) is expected zero before scatter under this source/staging model; it cannot itself explain Windows red=164 when A is loaded from the before-effects image.",
            "INFERENCE: red=164 must arise from a different populated source/staging path, a different contributing source coordinate/group, or a later host-store path; it is not evidence for changing coefficients.",
            "INFERENCE: this witness does not identify which of those Windows-side paths produced red=164 because final host pixel storage is not observed by FUN_1800038d0-only capture.",
        ],
        "next_boundary": "Capture one real helper call that writes the target B record for (494,169) or (579,169), with the exact source coordinate, B destination address/record, pre/post B floats, and the final host-store bytes in the same run. Keep the required source coordinate fixed at (959,169) and do not tune coefficients.",
    }
    args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# DirectionalBlur source/staging witness 20260710", "",
        f"- Status: `{result['status']}`", "- Case: `case_0001`, row `169`", "- No Mac source or PNG edits.", "",
        "## FACT", "",
        *[f"- {fact[6:]}" for fact in result["facts"]], "",
        "## Witness", "",
        "| target | source after rowdriver | B after scatter | writeback B | Windows final |", "| --- | --- | --- | --- | --- |",
    ]
    for rec in records:
        lines.append(f"| `{tuple(rec['xy'])}` | `{rec['source_after_rowdriver_rgba_f32']}` | `{rec['staging_after_scatter_B_rgba_f32']}` | `{rec['staging_writeback_input_B_rgba_f32']}` | `{rec['windows_final_rgba_u8']}` |")
    lines += ["", "## INFERENCE", "", *[f"- {item[11:]}" for item in result["inference"]], "", "## Exact Next Boundary", "", result["next_boundary"], ""]
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": result["status"], "json": str(args.output_json), "md": str(args.output_md)}))
    return 0 if result["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
