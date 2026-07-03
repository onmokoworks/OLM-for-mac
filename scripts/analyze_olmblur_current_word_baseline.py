#!/usr/bin/env python3
"""Freeze the current Mac-side OLMBlur last-word/half-step witness baseline."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from refs.scripts.verify_manifest import load_rgba


REQUEST_DIR_16 = ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmblur_exact_20260625"
PROBE_CASE0006 = ROOT / "refs/reports/ae_single_case_olmblur_16bpc_witness_latest/probe_report.json"
PROBE_CASE0007 = ROOT / "refs/reports/ae_single_case_olmblur_case0007_final1px_probe_20260629/probe_report.json"
OLD8_REF_DIR = ROOT / "refs/reports/ae_host_validation_20260618_232926/cli_checks/olmblur_normalized/reference"
OLD8_PARAM = ROOT / "refs/reports/ae_host_validation_20260618_232926/cli_checks/olmblur_normalized/candidate/_params/case_0007.json"
CLI_BIN = ROOT / "cli/OLMBlur/olmblur_cli"

OUT_JSON = ROOT / "refs/conformance/olmblur_current_word_baseline_20260629.json"
OUT_MD = ROOT / "refs/conformance/olmblur_current_word_baseline_20260629.md"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sample(arr: np.ndarray, x: int, y: int) -> list[int]:
    return [int(v) for v in arr[y, x]]


def load_probe_points(path: Path) -> dict[tuple[int, int], dict]:
    data = read_json(path)
    rows: dict[tuple[int, int], dict] = {}
    for case in data.get("cases", []):
        for point in case.get("debug", {}).get("points", []):
            rows[(int(point["x"]), int(point["y"]))] = point
    return rows


def run_old8_case0007() -> tuple[np.ndarray, dict[tuple[int, int], str]]:
    with tempfile.TemporaryDirectory(prefix="olmblur_case0007_") as td:
        tmp = Path(td)
        out_png = tmp / "out.png"
        out_log = tmp / "trace.log"
        env = dict(**{k: v for k, v in __import__("os").environ.items()})
        env["OLMBLUR_TRACE_PIXELS"] = "488,941;488,942"
        cmd = [
            str(CLI_BIN),
            "--input",
            str(OLD8_REF_DIR / "case_0007_before_effects.png"),
            "--params",
            str(OLD8_PARAM),
            "--output",
            str(out_png),
        ]
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        combined = proc.stdout + proc.stderr
        out_log.write_text(combined, encoding="utf-8")
        traces: dict[tuple[int, int], str] = {}
        for line in combined.splitlines():
            if not line.startswith("OLMBLUR_TRACE "):
                continue
            m = re.search(r"x=(\d+)\s+y=(\d+)\s+", line)
            if m:
                traces[(int(m.group(1)), int(m.group(2)))] = line
        return load_rgba(out_png).astype(np.int64), traces


def compare_case(reference: np.ndarray, candidate: np.ndarray) -> dict[str, object]:
    diff = candidate.astype(np.int64) - reference.astype(np.int64)
    abs_diff = np.abs(diff)
    changed = np.any(diff != 0, axis=2)
    ys, xs = np.where(changed)
    bbox = None
    if xs.size:
        bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    max_witness = None
    if np.any(abs_diff):
        flat = int(abs_diff.reshape(-1).argmax())
        y, x, c = np.unravel_index(flat, abs_diff.shape)
        max_witness = {
            "x": int(x),
            "y": int(y),
            "channel": int(c),
            "reference": sample(reference, int(x), int(y)),
            "candidate": sample(candidate, int(x), int(y)),
            "delta": [int(v) for v in diff[y, x]],
        }
    return {
        "max_diff": int(abs_diff.max()),
        "mean_abs_diff": float(abs_diff.mean()),
        "changed_pixel_count": int(changed.sum()),
        "changed_bbox": bbox,
        "max_witness": max_witness,
    }


def build_payload() -> dict:
    probe6 = load_probe_points(PROBE_CASE0006)
    probe7 = load_probe_points(PROBE_CASE0007)

    ref16_case6 = load_rgba(
        REQUEST_DIR_16 / "expected/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png"
    ).astype(np.int64)
    cand16_case6 = load_rgba(
        ROOT
        / "refs/reports/ae_single_case_olmblur_16bpc_witness_latest/olmblur__case_0006/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png"
    ).astype(np.int64)
    ref16_case7 = load_rgba(
        REQUEST_DIR_16 / "expected/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0007.png"
    ).astype(np.int64)
    cand16_case7 = load_rgba(
        ROOT
        / "refs/reports/ae_single_case_olmblur_case0007_final1px_probe_20260629/olmblur__case_0007/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0007.png"
    ).astype(np.int64)

    ref8_case7 = load_rgba(OLD8_REF_DIR / "case_0007.png").astype(np.int64)
    cand8_case7, trace8_case7 = run_old8_case0007()

    return {
        "kind": "olmblur_current_word_baseline",
        "date": "2026-06-29",
        "cases": [
            {
                "case_id": "olmblur__case_0006",
                "bit_depth": "16bpc",
                "family": "nonlegacy_sign_mixed_one_word",
                "candidate_path": "refs/reports/ae_single_case_olmblur_16bpc_witness_latest/olmblur__case_0006/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png",
                "comparison": compare_case(ref16_case6, cand16_case6),
                "samples": [
                    {
                        "x": 314,
                        "y": 14,
                        "reference": sample(ref16_case6, 314, 14),
                        "candidate": sample(cand16_case6, 314, 14),
                        "probe": probe6[(314, 14)],
                    },
                    {
                        "x": 29,
                        "y": 71,
                        "reference": sample(ref16_case6, 29, 71),
                        "candidate": sample(cand16_case6, 29, 71),
                        "probe": probe6[(29, 71)],
                    },
                ],
                "notes": [
                    "Current live Mac AE non-Legacy writer is still the nearbyint/ties-to-even family at the active witnesses.",
                    "The remaining exported residual is sign-mixed, which still forbids a blind global writer swap without Windows pre-store float evidence.",
                ],
            },
            {
                "case_id": "olmblur__case_0007",
                "bit_depth": "16bpc",
                "family": "legacy_last_pixel_half_step",
                "candidate_path": "refs/reports/ae_single_case_olmblur_case0007_final1px_probe_20260629/olmblur__case_0007/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0007.png",
                "comparison": compare_case(ref16_case7, cand16_case7),
                "samples": [
                    {
                        "x": 345,
                        "y": 672,
                        "reference": sample(ref16_case7, 345, 672),
                        "candidate": sample(cand16_case7, 345, 672),
                        "probe": probe7[(345, 672)],
                    },
                    {
                        "x": 0,
                        "y": 0,
                        "reference": sample(ref16_case7, 0, 0),
                        "candidate": sample(cand16_case7, 0, 0),
                        "probe": probe7[(0, 0)],
                    },
                ],
                "notes": [
                    "The old Legacy (0,0) spill is retired in the current port.",
                    "The remaining 16bpc Legacy witness is a one-word half-step split at blue raw=12544.5.",
                ],
            },
            {
                "case_id": "case_0007",
                "bit_depth": "8bpc-old-normalized",
                "family": "legacy_last_pixel_half_step",
                "candidate_path": "current cli rerun via cli/OLMBlur/olmblur_cli",
                "comparison": compare_case(ref8_case7, cand8_case7),
                "samples": [
                    {
                        "x": 488,
                        "y": 941,
                        "reference": sample(ref8_case7, 488, 941),
                        "candidate": sample(cand8_case7, 488, 941),
                        "trace": trace8_case7[(488, 941)],
                    },
                    {
                        "x": 488,
                        "y": 942,
                        "reference": sample(ref8_case7, 488, 942),
                        "candidate": sample(cand8_case7, 488, 942),
                        "trace": trace8_case7[(488, 942)],
                    },
                ],
                "notes": [
                    "This is the current CLI rerun from the live workspace binary, not a copied historical log.",
                    "The pair of neighbors straddle the half-step boundary cleanly, which supports the pre-store-float-delta hypothesis over a broad structural mismatch.",
                ],
            },
        ],
    }


def write_md(payload: dict) -> None:
    lines = [
        "# OLMBlur Current Word Baseline",
        "",
        "- Date: `2026-06-29`",
        "- Purpose: freeze the current Mac-side witness values as historical baseline context for later OLMBlur closeout and provenance/export decisions.",
        "",
        "## Reading",
        "",
        "- `olmblur__case_0006` is the active non-Legacy sign-mixed one-word family.",
        "- `olmblur__case_0007` 16bpc is the surviving Legacy one-word half-step witness after the carry-prev fix retired the old `(0,0)` blocker.",
        "- old normalized 8bpc `case_0007` is the companion half-step witness from the live CLI binary.",
        "",
    ]
    for row in payload["cases"]:
        cmp = row["comparison"]
        lines.extend(
            [
                f"## {row['case_id']} ({row['bit_depth']})",
                "",
                f"- Family: `{row['family']}`",
                f"- Candidate: `{row['candidate_path']}`",
                f"- max: `{cmp['max_diff']}`",
                f"- mean: `{cmp['mean_abs_diff']}`",
                f"- nonzero_px: `{cmp['changed_pixel_count']}`",
                f"- bbox: `{cmp['changed_bbox']}`",
                f"- max witness: `{cmp['max_witness']}`",
            ]
        )
        for note in row["notes"]:
            lines.append(f"- {note}")
        lines.extend(["", "| Point | reference | candidate | witness |", "| --- | --- | --- | --- |"])
        for sample_row in row["samples"]:
            witness = sample_row.get("probe") or sample_row.get("trace")
            lines.append(
                f"| `({sample_row['x']},{sample_row['y']})` | `{sample_row['reference']}` | "
                f"`{sample_row['candidate']}` | `{witness}` |"
            )
        lines.append("")
    lines.extend(
        [
            "## Next Evidence Boundary",
            "",
            "- The pending Windows proof must capture pre-store float(s), helper/clamp output if present, and final internal word(s) at these exact witnesses.",
            "- If Windows lands slightly below the half-step where current Mac is exactly on or slightly above it, the remaining gap is a narrow pre-store float/state difference rather than a justification for a blind global writer rewrite.",
            "- If Windows instead shows the same pre-store float but different helper/store behavior, only then does a writer-rule change become evidence-backed.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    payload = build_payload()
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_md(payload)
    print(OUT_JSON)
    print(OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
