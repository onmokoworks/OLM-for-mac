#!/usr/bin/env python3
"""Audit the OLMDistanceGradation 0010/0011 OpenCV field-prep boundary."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECOMP = ROOT / "decomp/DistanceGradation.aex.c.txt"
MAC_CPP = ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
OPENCV_IMPLS = ROOT / "tools/emulation/opencv_impls.py"
OUT_JSON = ROOT / "refs/conformance/olmdistancegradation_0010_0011_opencv_field_prep_audit_20260709.json"
OUT_MD = ROOT / "refs/conformance/olmdistancegradation_0010_0011_opencv_field_prep_audit_20260709.md"


FACTS = [
    {
        "id": "fieldgen_entry",
        "file": "decomp/DistanceGradation.aex.c.txt",
        "line": 3542506,
        "marker": "void FUN_181174760",
        "reading": "DistanceGradation field-prep helper entry.",
    },
    {
        "id": "first_distance_transform",
        "file": "decomp/DistanceGradation.aex.c.txt",
        "line": 3542536,
        "marker": "FUN_1812b15a0(local_48[0],local_88[0],2,0,0,0,0);",
        "reading": "First OpenCV distanceTransform call shape: uint8 source to float32 destination, DIST_L2, DIST_MASK_PRECISE.",
    },
    {
        "id": "trunc_threshold",
        "file": "decomp/DistanceGradation.aex.c.txt",
        "line": 3542540,
        "marker": "uVar2 = 2;",
        "reading": "Non-constant path starts with THRESH_TRUNC mode for the later threshold/normalize wrapper.",
    },
    {
        "id": "constant_switch",
        "file": "decomp/DistanceGradation.aex.c.txt",
        "line": 3542544,
        "marker": "if (param_8 == 1)",
        "reading": "Constant interpolation switches the mode used by the final wrapper.",
    },
    {
        "id": "final_wrapper_call",
        "file": "decomp/DistanceGradation.aex.c.txt",
        "line": 3542553,
        "marker": "FUN_1812b6a40(local_68[0],local_a8[0],(double)fVar4,(double)fVar3,CONCAT44(uVar5,uVar2));",
        "reading": "The helper emits the field through the wrapper fed by fVar4/fVar3 and threshold mode.",
    },
    {
        "id": "cvthreshold_string",
        "file": "decomp/DistanceGradation.aex.c.txt",
        "line": 3797673,
        "marker": '"cvThreshold"',
        "reading": "FUN_1812b6a40 assertion path names cvThreshold.",
    },
    {
        "id": "cvnormalize_path",
        "file": "tools/emulation/opencv_impls.py",
        "line": 227,
        "marker": "def cvnormalize_minmax_native",
        "reading": "The repo already has a limited cvNormalize NORM_MINMAX detour and sidecar gate for the fieldgen path.",
    },
    {
        "id": "current_mac_dt",
        "file": "mac/OLMDistanceGradation/OLMDistanceGradation.cpp",
        "line": 484,
        "marker": "static void dt_to_normalized",
        "reading": "Current Mac source computes EDT, clamps to threshold, finds raw max, then divides in float.",
    },
]


WITNESS_CLASSIFICATION = [
    {
        "case_id": "olmdistancegradation_extended__case_0010",
        "xy": [6, 40],
        "family": "outside_actual_max",
        "mac_raw_distance": 41.0,
        "mac_field_x": 0.9002838730812073,
        "required_field_word": 29500,
        "windows_store_a": 3268,
        "meaning": "The denominator behaves like an actual outside-field max near 45.54, not the UI threshold 82.",
    },
    {
        "case_id": "olmdistancegradation_extended__case_0010",
        "xy": [901, 394],
        "family": "inside_threshold_half_boundary",
        "mac_raw_distance": 44.0113639831543,
        "mac_field_x": 0.6985930800437927,
        "required_field_word": 22892,
        "windows_store_a": 9876,
        "meaning": "The witness is threshold-limited by 63 and sits on the opposite half-boundary sign.",
    },
    {
        "case_id": "olmdistancegradation_extended__case_0011",
        "xy": [915, 392],
        "family": "inside_threshold_half_boundary",
        "mac_raw_distance": 46.81879806518555,
        "mac_field_x": 0.1345367729663849,
        "required_field_word": 4409,
        "windows_store_a": 28359,
        "meaning": "A second inside threshold witness with the same sign as case_0010 (901,394).",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def contains_marker(path: Path, marker: str) -> bool:
    return marker in path.read_text(encoding="utf-8", errors="replace")


def collect_fact_status() -> list[dict[str, object]]:
    roots = {
        "decomp/DistanceGradation.aex.c.txt": DECOMP,
        "mac/OLMDistanceGradation/OLMDistanceGradation.cpp": MAC_CPP,
        "tools/emulation/opencv_impls.py": OPENCV_IMPLS,
    }
    rows: list[dict[str, object]] = []
    for fact in FACTS:
        path = roots[fact["file"]]
        rows.append(
            {
                **fact,
                "path": str(path.relative_to(ROOT)),
                "marker_found": path.exists() and contains_marker(path, fact["marker"]),
            }
        )
    return rows


def decide(facts: list[dict[str, object]]) -> str:
    if not all(row["marker_found"] for row in facts):
        return "blocked-missing-source-marker"
    return "field-prep-structural-boundary-not-final-writer"


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# OLMDistanceGradation 0010/0011 OpenCV field-prep audit - 2026-07-09",
        "",
        "This audit connects the new Windows PF16 writer witness to the AEX field-prep",
        "shape. It is evidence classification only; it does not authorize a Mac source",
        "change by itself.",
        "",
        f"- Decision: `{report['decision']}`",
        "",
        "## Source Facts",
        "",
        "| Fact | Source | Marker | Status | Reading |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report["facts"]:
        status = "found" if row["marker_found"] else "missing"
        marker = str(row["marker"]).replace("|", "\\|")
        lines.append(
            f"| `{row['id']}` | `{row['path']}:{row['line']}` | `{marker}` | {status} | {row['reading']} |"
        )
    lines.extend(
        [
            "",
            "## Witness Families",
            "",
            "| Case | XY | Family | Mac raw | Mac field | Required field word | Windows store A |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in report["witnesses"]:
        xy = f"({row['xy'][0]},{row['xy'][1]})"
        lines.append(
            f"| `{row['case_id']}` | `{xy}` | `{row['family']}` | "
            f"{row['mac_raw_distance']:.12g} | {row['mac_field_x']:.12g} | "
            f"{row['required_field_word']} | {row['windows_store_a']} |"
        )
    lines.extend(
        [
            "",
            "## Reading",
            "",
            "- The accepted Windows return already proves the final output address/writeback formula for the sampled PF16 pixels, so the current residual should not be treated as a broad final-writer bug.",
            "- The sign-flipped one-word residuals reject a single global output rounding rule.",
            "- Current Mac EDT and the repository OpenCV-compatible `cvDistTransform` agree at the checked local fields, so the remaining difference is narrower than simply replacing Meijster with the current detour.",
            "- The remaining open boundary is how the AEX/OpenCV field-prep path clamps, normalizes, and stores/feeds the field world before `FUN_181170480` consumes it.",
            "",
            "## Next Proof",
            "",
            "Run the DG AEX CPU fieldgen probe for `case_0010` and `case_0011` with the existing OpenCV detours registered through `normalize_minmax`, then sample the emitted field words at `(6,40)`, `(901,394)`, and `(915,392)`. If the emulated helper reproduces the Windows-required field words, patch the Mac source to mirror that helper. If it reproduces the current Mac values, request a Windows primitive trace for the field-prep max/normalize/pack boundary instead of changing compose/writeback.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    facts = collect_fact_status()
    report = {
        "kind": "olmdistancegradation_0010_0011_opencv_field_prep_audit",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "decision": decide(facts),
        "facts": facts,
        "witnesses": WITNESS_CLASSIFICATION,
        "source_reports": [
            "refs/conformance/olmdistancegradation_0010_0011_writeback_pointer_map_return_intake_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_field_pack_read_audit_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_normalization_denominator_audit_20260709.md",
            "refs/conformance/olmdistancegradation_0010_0011_local_field_normalization_probe_20260709.md",
            "tools/emulation/OPENCV_DETOUR_P1_REPORT.md",
        ],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"report_json={args.output_json}")
    print(f"report_md={args.output_md}")
    print(f"decision={report['decision']}")
    missing = [row["id"] for row in facts if not row["marker_found"]]
    if missing:
        print("missing_markers=" + ",".join(str(item) for item in missing))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
