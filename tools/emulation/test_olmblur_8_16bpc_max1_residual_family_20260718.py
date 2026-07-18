#!/usr/bin/env python3
"""Bound the OLMBlur 8/16bpc max=1 residual family on Mac."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_olmblur_case0006_border_order_writer_differential_20260716 import (  # noqa: E402
    model,
    run_actual,
    source_bytes,
    summarize,
)

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMBlur.aex"
ASM = ROOT / "disasm/OLMBlur.aex.asm.txt"
DECOMP = ROOT / "decomp/OLMBlur.aex.c.txt"
CPP16 = ROOT / "core/olmblur_worker16_nonlegacy.cpp"
CPP8 = ROOT / "core/olmblur_worker8_legacy.cpp"
BASELINE = ROOT / "refs/conformance/olmblur_current_word_baseline_20260629.json"
DECISION = ROOT / "refs/conformance/olmblur_8bpc_decision.json"
REPORT = ROOT / "refs/conformance/olmblur_8_16bpc_max1_residual_family_20260718.json"
REPORT_MD = ROOT / "refs/conformance/olmblur_8_16bpc_max1_residual_family_20260718.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def static_contract() -> dict[str, object]:
    asm = ASM.read_text()
    decomp = DECOMP.read_text()
    cpp16 = CPP16.read_text()
    cpp8 = CPP8.read_text()
    required = {
        "aex_16_writer_add_half_floor": "floorf(pfVar9[-2] + fVar22)" in decomp,
        "aex_8_writer_add_half_floor": "floorf(pfVar10[-2] + fVar20)" in decomp,
        "aex_pf16_cvttss2si": "1800030f0  CVTTSS2SI EAX,XMM0" in asm,
        "aex_exp_coefficients": "expf((float)((uint)(float)(iVar15 * iVar15) ^ uVar1)" in decomp,
        "cpp16_add_half_floor": "std::floor(value + 0.5f)" in cpp16,
        "cpp8_add_half_floor": "std::floor(rgb[0] + 0.5f)" in cpp8,
    }
    assert all(required.values()), required
    return required


def retained_residual_contract() -> dict[str, object]:
    baseline = json.loads(BASELINE.read_text())
    decision = json.loads(DECISION.read_text())
    case_8 = next(c for c in baseline["cases"] if c["case_id"] == "case_0007")
    case_16 = next(c for c in baseline["cases"] if c["case_id"] == "olmblur__case_0007")
    point_8 = next(p for p in case_8["samples"] if p["x"] == 488 and p["y"] == 941)
    point_16 = next(p for p in case_16["samples"] if p["x"] == 345 and p["y"] == 672)
    assert point_8["trace"].startswith("OLMBLUR_TRACE x=488 y=941 rgb=(250.499985")
    assert point_16["probe"]["raw"][2] == "12544.5"
    assert decision["cli_residuals"]["max_diff"] == 1
    return {
        "8bpc": {
            "case": "case_0007",
            "xy": [488, 941],
            "pre_store": "250.499985",
            "stored_candidate": point_8["candidate"][0],
            "reference": point_8["reference"][0],
        },
        "16bpc": {
            "case": "case_0007",
            "xy": [345, 672],
            "pre_store": point_16["probe"]["raw"][2],
            "stored_word_candidate": point_16["probe"]["stored"][2],
            "stored_word_reference": 12544,
            "reference_png": point_16["reference"][2],
        },
        "retained_cli_max_diff": decision["cli_residuals"]["max_diff"],
    }


def actual_radius_one() -> dict[str, object]:
    cases = [
        {"id": "interior_order", "kind": "order", "width": 9, "height": 7,
         "blur_amount": 1.0, "repeat": 1, "bias_direction": 1},
        {"id": "edge_border", "kind": "border", "width": 7, "height": 5,
         "blur_amount": 1.0, "repeat": 1, "bias_direction": 1},
    ]
    results = {}
    for case in cases:
        source = source_bytes(case["width"], case["height"], case["kind"])
        actual, instructions = run_actual(case, source)
        baseline, _ = model(source, case)
        reverse, _ = model(source, case, order="reverse")
        results[case["id"]] = {
            "geometry": [case["width"], case["height"]],
            "parameters": {k: case[k] for k in ("blur_amount", "repeat", "bias_direction")},
            "instructions": instructions,
            "source_sha256": hashlib.sha256(source).hexdigest(),
            "actual_sha256": hashlib.sha256(actual).hexdigest(),
            "truncated_edge_cpp_model": summarize(actual, baseline),
            "reverse_accumulation_cpp_model": summarize(actual, reverse),
        }
    assert results["interior_order"]["truncated_edge_cpp_model"]["equal"]
    assert results["interior_order"]["reverse_accumulation_cpp_model"]["equal"]
    edge = results["edge_border"]["truncated_edge_cpp_model"]
    assert not edge["equal"]
    assert any(d["actual"][2] > 32768 for d in edge["first_diffs"])
    return results


def main() -> int:
    report = {
        "schema": "olmblur.8-16bpc-max1-residual-family/1",
        "scope": "Mac-only actual-AEX radius-1 fixture plus retained 8/16bpc CLI evidence",
        "aex": {"path": str(AEX.relative_to(ROOT)), "sha256": sha256(AEX), "entry": "0x180002280"},
        "static_contract": static_contract(),
        "retained_residuals": retained_residual_contract(),
        "actual_aex_radius_one": actual_radius_one(),
        "bounded_fact": "The radius-1 interior/order fixture is exact under the current C++ model and its reversed accumulation variant, but the radius-1 edge fixture is not exact and exposes out-of-range PF16 words; therefore the 8/16bpc max=1 family is not classified as a final-writer-only issue and border/helper state remains live.",
        "claim_boundary": "This is not AE exactness and does not identify the exact border rule or justify a source change.",
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    lines = [
        "# OLMBlur 8/16bpc max=1 residual family (2026-07-18)", "",
        "## New bounded fact", "",
        report["bounded_fact"], "",
        "## Evidence", "",
        f"- Actual AEX: `{report['aex']['path']}` SHA-256 `{report['aex']['sha256']}`.",
        "- AEX/decomp and current C++ both retain the add-half/floor writer contract.",
        "- The retained 8bpc witness is `(488,941)`, pre-store `250.499985`; the retained 16bpc witness is `(345,672)`, pre-store blue `12544.5`.",
        "- At radius 1, the interior/order actual-AEX output equals both the current C++ model and reversed accumulation model.",
        "- At radius 1, the edge actual-AEX output differs from the truncated-edge C++ model and includes out-of-range PF16 words in the bounded synthetic world.",
        "",
        "## Classification", "",
        "- Coefficient: not implicated by the interior/order equality in this bounded probe.",
        "- Accumulation order: not implicated by the tested reversal.",
        "- Final writeback: not sufficient to explain the family; both retained witnesses straddle different pre-store conditions.",
        "- Border/helper: remains the live candidate, without an exact rule identified.",
        "",
        "## Boundary", "",
        "Mac-only, actual-AEX/portable fixture evidence. No Windows work, no plugin/source change, and no AE-exact promotion.",
        "",
        "## Reproduce", "",
        "`python3 tools/emulation/test_olmblur_8_16bpc_max1_residual_family_20260718.py`",
    ]
    REPORT_MD.write_text("\n".join(lines) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
