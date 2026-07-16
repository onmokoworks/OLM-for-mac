#!/usr/bin/env python3
"""Compare reconstructed B150 output with an independent portable spec oracle."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import probe_radialblur_reconstructed_b150_population_20260717 as actual  # noqa: E402

TARGETS = actual.TARGETS
CONTROLS = actual.CONTROLS
POINTS = TARGETS + CONTROLS
ORACLE_SEED = {
    (1047, 1094): (0.125, 0.25, 0.375, 0.875),
    (1047, 1095): (0.25, 0.5, 0.75, 1.0),
    (1047, 1096): (0.5, 0.25, 0.125, 0.5),
    (1048, 1094): (0.375, 0.625, 0.25, 0.625),
    (1048, 1095): (0.75, 0.125, 0.25, 0.75),
    (1048, 1096): (1.0, 0.5, 0.25, 0.25),
}


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def pack_words(values: list[float]) -> list[str]:
    return [f"0x{x:08x}" for x in struct.unpack("<%dI" % len(values), struct.pack("<%df" % len(values), *values))]


def oracle_cell(values: tuple[float, float, float, float]) -> dict[str, Any]:
    # Minimal B150 spec for the captured context: both spans are zero, so the
    # decomp takes no Gaussian-table taps. MULSS/DIVSS results are materialized
    # as float32, matching RadialF32Mul/RadialF32Div in the current Mac source.
    r, g, b, alpha = (f32(value) for value in values)
    out_alpha = f32(alpha / f32(1.0))
    out = [f32(r * out_alpha), f32(g * out_alpha), f32(b * out_alpha), out_alpha]
    return {"rgba_f32": out, "rgba_f32_words": pack_words(out),
            "scalar_f32": [out_alpha], "scalar_f32_words": pack_words([out_alpha])}


def compare(actual_run: dict[str, Any]) -> dict[str, Any]:
    entry = actual_run["entries"][0]
    actual_cells = entry["after_output_cells"]
    comparisons: list[dict[str, Any]] = []
    first_divergence: dict[str, Any] | None = None
    for point in POINTS:
        key = f"{point[0]},{point[1]}"
        expected = oracle_cell(ORACLE_SEED[point])
        observed = actual_cells[key]
        checks = {
            "rgba_words_equal": observed["rgba"]["f32_words"] == expected["rgba_f32_words"],
            "scalar_words_equal": observed["scalar"]["f32_words"] == expected["scalar_f32_words"],
            "input_seed_words_equal": actual_run["entries"][0]["input_cells"][key]["rgba"]["f32_words"] ==
            pack_words([f32(v) for v in ORACLE_SEED[point]]),
        }
        comparisons.append({"cell": list(point), "expected": expected, "observed": observed,
                            "checks": checks, "status": "match" if all(checks.values()) else "diverged"})
        if first_divergence is None:
            for field in ("rgba_words_equal", "scalar_words_equal", "input_seed_words_equal"):
                if not checks[field]:
                    first_divergence = {"cell": list(point), "field": field,
                                        "expected": expected, "observed": observed}
                    break
    return {"comparisons": comparisons, "first_divergence": first_divergence,
            "all_six_raw_words_match": first_divergence is None}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=ROOT / "refs/conformance/olmradialblur_reconstructed_b150_oracle_20260717.json")
    parser.add_argument("--output-md", type=Path, default=ROOT / "refs/conformance/olmradialblur_reconstructed_b150_oracle_20260717.md")
    args = parser.parse_args()
    actual_hash = hashlib.sha256(actual.AEX.read_bytes()).hexdigest()
    report: dict[str, Any] = {
        "kind": "olmradialblur_reconstructed_b150_oracle_20260717", "schema": 1,
        "status": "blocked", "classification": "blocked-fail-closed",
        "claim_boundary": "bounded reconstructed-state B150 equivalence only; no natural prefill, Windows, or AE-exact claim",
        "portable_equivalent": False,
        "oracle": {
            "kind": "minimal-zero-span-b150-spec",
            "source_basis": "AEX FUN_18000B150 decomp/assembly loop and current Mac float32 helper convention",
            "operations": ["seed alpha and weight=1.0f", "no Gaussian taps because span_work+0x4200/+0x4204 are zero",
                            "out_alpha=f32(alpha/1.0f)", "out_rgb=f32(source_rgb*out_alpha)",
                            "scalar=f32(out_alpha)"],
            "rounding": "each multiply/divide is explicitly rounded to float32; raw little-endian words compared",
            "current_mac_source": {"path": "mac/OLMRadialBlur/OLMRadialBlur.cpp", "f32_helpers_lines": [36, 42, 48]},
            "decomp_reference": {"path": "disasm/v1_analysis/21_recon_RadialBlur.md", "lines": [112, 117]},
        },
        "provenance": {"aex_sha256": actual_hash, "pinned_aex_sha256": actual.PINNED_AEX_SHA256,
                       "seed_source": "independent duplicate of the six documented float32 seeds; not actual output"},
        "target": {"width": actual.WIDTH, "row_start": actual.ROW_START, "row_end": actual.ROW_END,
                   "cells": [list(x) for x in TARGETS], "controls": [list(x) for x in CONTROLS]},
    }
    if actual_hash != actual.PINNED_AEX_SHA256:
        report["blocker"] = "pinned AEX hash mismatch"
    else:
        try:
            observed_run = actual.run()
            entry = observed_run["entries"][0]
            report["observed_b150"] = {"abi": entry["abi"], "context_fields": entry["context_fields"],
                                       "input_cells": entry["input_cells"], "scale_cells": entry["scale_cells"],
                                       "output_cells": entry["after_output_cells"],
                                       "output_plane_sha256": entry["output_plane_sha256"]}
            report["comparison"] = compare(observed_run)
            report["gates"] = {
                "pinned_hash": True,
                "one_entry_one_return": len(observed_run["entries"]) == 1 and observed_run["returns"] == 1,
                "exact_abi": entry["abi"]["width"] == actual.WIDTH and entry["abi"]["row_start"] == actual.ROW_START and
                entry["abi"]["row_end"] == actual.ROW_END,
                "spans_zero_for_oracle": entry["context_fields"]["span_work_plus_0x4200"] == 0 and
                entry["context_fields"]["span_work_plus_0x4204"] == 0,
                "all_six_raw_words_match": report["comparison"]["all_six_raw_words_match"],
            }
            report["status"] = "pass" if all(report["gates"].values()) else "blocked"
            report["classification"] = "bounded-reconstructed-b150-equivalence-proven" if report["status"] == "pass" else "bounded-b150-first-divergence"
        except Exception as exc:
            report["blocker"] = f"oracle comparison failed: {exc}"
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# OLMRadialBlur reconstructed B150 portable oracle (2026-07-17)", "",
             f"- Status: `{report['status']}`", f"- Classification: `{report['classification']}`",
             "- The oracle is independent of actual AEX output: it derives expected words from the six seed RGBA values and zero-span decomp operations.",
             "- Promotion requires all six cells and both RGBA/scalar raw float32 word sets to match.", ""]
    if "comparison" in report:
        lines.append(f"- All six raw-word sets match: `{report['comparison']['all_six_raw_words_match']}`.")
        if report["comparison"]["first_divergence"]:
            lines.append(f"- First divergence: `{report['comparison']['first_divergence']}`")
    if "blocker" in report:
        lines.append(f"- Blocker: `{report['blocker']}`")
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"status={report['status']} classification={report['classification']}")
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
