#!/usr/bin/env python3
"""Run a bounded B150 actual-AEX differential and replay its downstream sample.

The replay is intentionally portable and consumes only typed values captured by
the actual-AEX probe.  It is not a renderer and does not compare PNGs.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_radialblur_case0009_b150_differential.py"
ANALYZER = HERE / "analyze_radialblur_case0009_sampler_prepass_writeback.py"


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def replay_sample(sample: dict[str, Any]) -> dict[str, Any]:
    weights = [f32(float(value)) for value in sample["weights"]]
    keys = ("a0_r0", "a0_r1", "a1_r0", "a1_r1")
    cells = sample["cells"]
    out = [f32(0.0)] * 4
    for key, weight in zip(keys, weights):
        cell = [f32(float(value)) for value in cells[key]]
        alpha_weight = f32(weight * cell[3])
        out[3] = f32(out[3] + alpha_weight)
        for channel in range(3):
            out[channel] = f32(out[channel] + f32(alpha_weight * cell[channel]))
    if out[3] != 0.0:
        reciprocal = f32(1.0 / out[3])
        for channel in range(3):
            out[channel] = f32(out[channel] * reciprocal)
    trunc = [max(0, min(255, int(value * 255.0))) for value in out]
    return {"sample_float": [float(value) for value in out], "trunc_u8": trunc}


def same_float_vectors(left: Any, right: Any) -> bool:
    return isinstance(left, list) and isinstance(right, list) and len(left) == len(right) and all(
        struct.pack("<f", float(a)) == struct.pack("<f", float(b)) for a, b in zip(left, right)
    )


def one_side(report: dict[str, Any]) -> dict[str, Any]:
    rows = []
    issues: list[str] = []
    for item in report.get("bounded_output_samples", []):
        sample = item.get("sample")
        if item.get("status") != "sampled" or not isinstance(sample, dict):
            issues.append(f"{item.get('xy')}:sample_missing")
            continue
        replay = replay_sample(sample)
        exact = same_float_vectors(replay["sample_float"], sample.get("sample_float"))
        exact_trunc = replay["trunc_u8"] == sample.get("trunc_u8")
        if not exact:
            issues.append(f"{item.get('xy')}:portable_sample_float_mismatch")
        if not exact_trunc:
            issues.append(f"{item.get('xy')}:portable_truncate_mismatch")
        rows.append({"xy": item.get("xy"), "exact_float32": exact, "exact_truncate_u8": exact_trunc,
                     "aex_sample_float": sample.get("sample_float"), "portable_sample_float": replay["sample_float"],
                     "aex_trunc_u8": sample.get("trunc_u8"), "portable_trunc_u8": replay["trunc_u8"]})
    return {"status": "pass" if not issues else "fail", "issues": issues, "points": rows}


def analyze(document: dict[str, Any]) -> dict[str, Any]:
    pair = document.get("differential", {})
    live, noop = pair.get("live", {}), pair.get("noop", {})
    issues: list[str] = []
    if live.get("status") != "ok":
        issues.append("live_actual_aex_report_not_ok")
    if live.get("worker_execution", {}).get("prepass") != "actual-aex" or live.get("worker_execution", {}).get("b150_returns", 0) < 1:
        issues.append("live_b150_return_missing")
    if noop.get("worker_execution", {}).get("prepass_detour_calls") != 1:
        issues.append("noop_b150_detour_missing")
    live_stats, noop_stats = live.get("plane_stats", {}), noop.get("plane_stats", {})
    if live_stats.get("informative_cell_count", 0) <= 0:
        issues.append("live_normalized_plane_empty")
    if noop_stats.get("informative_cell_count", 0) != 0:
        issues.append("noop_normalized_plane_not_empty")
    if live.get("plane_sha256") == noop.get("plane_sha256"):
        issues.append("downstream_plane_hashes_not_different")
    live_replay, noop_replay = one_side(live), one_side(noop)
    issues.extend(f"live:{issue}" for issue in live_replay["issues"])
    issues.extend(f"noop:{issue}" for issue in noop_replay["issues"])
    live_samples = [item.get("sample", {}).get("sample_float") for item in live.get("bounded_output_samples", [])]
    noop_samples = [item.get("sample", {}).get("sample_float") for item in noop.get("bounded_output_samples", [])]
    if live_samples == noop_samples:
        issues.append("live_noop_sample_outputs_not_different")
    return {
        "kind": "olmradialblur_case0009_b150_downstream_replay",
        "schema": 1,
        "status": "pass" if not issues else "fail",
        "classification": "b150-to-normalized-sampler-writeback-propagation-proven" if not issues else "bounded-propagation-proof-failed",
        "scope": "32x32 actual-AEX B150 differential through normalized polar planes, inverse bilinear sampler, and truncate-u8 replay",
        "issues": sorted(set(issues)),
        "live": live_replay,
        "noop": noop_replay,
        "facts": [
            "The actual-AEX live worker returns after changing its captured B150-owned slice.",
            "The paired no-op detour leaves the captured worker slice and normalized plane empty.",
            "The portable replay matches each retained actual-AEX sample float32 word and truncate-u8 result.",
        ],
        "inferences": [
            "Within this bounded scaffold, changed B150 output is consumed by downstream normalization and reaches sampled/writeback values.",
            "The result does not identify the full-frame case_0009 residual cause and is not AE exactness evidence.",
        ],
        "limitations": ["Bounded 32x32 local actual-AEX emulation only.", "No Windows package, PNG tuning, or production-code claim."],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = ["# OLMRadialBlur B150 downstream replay", "", f"- Status: `{report['status']}`", f"- Classification: `{report['classification']}`", "", "## FACT", ""]
    lines.extend(f"- {fact}" for fact in report["facts"])
    lines.extend(["", "| side | point | float32 replay | truncate-u8 replay |", "| --- | --- | --- | --- |"])
    for side in ("live", "noop"):
        for point in report[side]["points"]:
            lines.append(f"| {side} | `{point['xy']}` | `{point['exact_float32']}` | `{point['exact_truncate_u8']}` |")
    lines.extend(["", "## INFERENCE", ""])
    lines.extend(f"- {item}" for item in report["inferences"])
    lines.extend(["", "## Gate", "", f"- Issues: `{report['issues']}`", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--combined-json", type=Path, default=Path("/tmp/olmradialblur_b150_downstream.json"))
    parser.add_argument("--output-json", type=Path, default=Path("/tmp/olmradialblur_b150_downstream_analysis.json"))
    parser.add_argument("--output-md", type=Path, default=Path("/tmp/olmradialblur_b150_downstream_analysis.md"))
    parser.add_argument("--reuse-combined", action="store_true")
    args = parser.parse_args()
    if not args.reuse_combined:
        completed = subprocess.run([sys.executable, str(RUNNER), "--combined-json", str(args.combined_json)], check=False)
        if completed.returncode != 0:
            return completed.returncode
    document = json.loads(args.combined_json.read_text(encoding="utf-8"))
    report = analyze(document)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(markdown(report), encoding="utf-8")
    print(f"status={report['status']} classification={report['classification']}")
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
