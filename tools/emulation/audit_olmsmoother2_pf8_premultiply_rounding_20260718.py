#!/usr/bin/env python3
"""Audit the PF_Pixel8 host-premultiply rounding required by Smoother2.

This is intentionally independent of the Mac plug-in source.  It reads the
retained source and Windows before-effects PNGs, evaluates byte-level
premultiply candidates, and checks the retained Mac trace for the same witness
coordinates.  It does not modify source, install a plug-in, or claim AE
exactness for the whole effect.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Callable

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
WINDOWS_ROOT = ROOT / (
    "refs/win_references/olm_reference_return_windows_smoother2_legacy_full_current_aex_recapture_20260621/"
    "OLMSmootherv2"
)
SOURCE = WINDOWS_ROOT / "input\\current_olm_cells.png"
WINDOWS_BEFORE = WINDOWS_ROOT / (
    "smoother2_legacy_full_current_aex_recapture_20260621__software__fr24__"
    "legacy_case_0012_gamma5_red_blue_current_aex_before_effects.png"
)
TRACE_JSON = ROOT / "refs/conformance/olmsmoother2_mac_actual_ae_boundary_20260717.json"
WITNESS = (92, 840)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("FAIL_CLOSED: " + message)


def pf8_round_nearest(value: int, alpha: int) -> int:
    """Round value*alpha/255 to the nearest PF_Pixel8 code.

    Because 255 is odd, an integer product can never land exactly halfway
    between two byte codes.  +127 followed by integer division therefore
    implements the unique nearest-code rule without a tie policy.
    """

    return (value * alpha + 127) // 255


def pf8_truncate(value: int, alpha: int) -> int:
    return (value * alpha) // 255


def pf8_float_then_nearest(value: int, alpha: int) -> int:
    # Equivalent to round-half-up for this nonnegative, finite witness.
    return int((value / 255.0) * (alpha / 255.0) * 255.0 + 0.5)


def exhaustive_mapping_check() -> dict[str, int | bool]:
    """Compare the two nonnegative PF8 implementations over all byte pairs."""

    mismatches = 0
    for value in range(256):
        for alpha in range(256):
            if pf8_round_nearest(value, alpha) != pf8_float_then_nearest(value, alpha):
                mismatches += 1
    return {"pairs": 256 * 256, "mismatches": mismatches, "equivalent": mismatches == 0}


def load_rgba(path: Path, coordinate: tuple[int, int]) -> list[int]:
    require(path.is_file(), f"missing fixture: {path}")
    with Image.open(path) as image:
        image = image.convert("RGBA")
        return list(image.getpixel(coordinate))


def trace_lines() -> list[str]:
    require(TRACE_JSON.is_file(), f"missing trace evidence: {TRACE_JSON}")
    data = json.loads(TRACE_JSON.read_text(encoding="utf-8"))
    lines = data.get("mac_internal_trace", {}).get("lines", [])
    require(isinstance(lines, list), "trace lines are not a list")
    return [str(line) for line in lines]


def audit() -> dict:
    source_rgba = load_rgba(SOURCE, WITNESS)
    windows_before_rgba = load_rgba(WINDOWS_BEFORE, WITNESS)
    require(source_rgba == [174, 174, 174, 174], f"unexpected raw witness: {source_rgba}")
    require(windows_before_rgba == [119, 119, 119, 174], f"unexpected Windows witness: {windows_before_rgba}")

    rgb, _, _, alpha = source_rgba
    product = rgb * alpha
    quotient, remainder = divmod(product, 255)
    candidates: dict[str, int] = {
        "truncate_floor": pf8_truncate(rgb, alpha),
        "nearest_integer_plus_127": pf8_round_nearest(rgb, alpha),
        "float_normalized_then_nearest": pf8_float_then_nearest(rgb, alpha),
    }
    matching = [name for name, result in candidates.items() if result == windows_before_rgba[0]]
    exhaustive = exhaustive_mapping_check()
    require(exhaustive["equivalent"], "float and integer nearest mappings diverge in the PF8 domain")

    lines = trace_lines()
    required_trace_fragments = [
        "trace neighborhood sample (92,840)=0.42325333,0.42325333,0.42325333,0.68234253",
        "trace append src=(92,839) dst_center=(92,841)",
    ]
    trace_presence = {fragment: any(fragment in line for line in lines) for fragment in required_trace_fragments}
    require(all(trace_presence.values()), "Mac trace does not contain the retained raw-input witness")

    return {
        "schema": 1,
        "date": "2026-07-18",
        "scope": "OLMSmoother2 PF_Pixel8 host-premultiply byte rounding at one accepted witness",
        "verdict": "REQUIRED_BYTE_RULE_IDENTIFIED_NOT_AE_EXACT",
        "fact": {
            "source_rgba": source_rgba,
            "windows_before_effects_rgba": windows_before_rgba,
            "source_sha256": sha256(SOURCE),
            "windows_before_effects_sha256": sha256(WINDOWS_BEFORE),
            "product_rgb_times_alpha": product,
            "quotient": quotient,
            "remainder": remainder,
            "trace_fragments_present": trace_presence,
            "exhaustive_integer_vs_float_pairs": exhaustive,
        },
        "candidate_results": candidates,
        "matching_candidates": matching,
        "identified_rule": {
            "expression": "(rgb * alpha + 127) // 255",
            "mathematical_form": "nearest_integer(rgb * alpha / 255)",
            "witness_result": pf8_round_nearest(rgb, alpha),
            "why_plus_127_is_exact_for_integer_products": "255 is odd, so product/255 cannot have fractional part exactly 0.5; +127 selects remainder >= 128.",
        },
        "inference": [
            "The retained witness requires integer nearest-code premultiplication, not truncation.",
            "Across all 65,536 PF8 value/alpha pairs, the tested normalized-float-nearest and integer +127 mappings are byte-equivalent; the byte mapping is identified even though the internal implementation order is not.",
            "The witness alone cannot prove that every AE host path uses this rule for every pixel format; PF16 and PF32 remain separate contracts.",
            "The rule is a host-boundary correction candidate for Smoother2 and is not yet a permanent Mac plug-in change.",
        ],
        "claims_not_made": [
            "No edit to OLMSmoother2_port.cpp",
            "No Mac AE exactness claim",
            "No claim that this single witness closes the Smoother2 classifier or writer residual",
        ],
    }


def markdown(report: dict) -> str:
    fact = report["fact"]
    rule = report["identified_rule"]
    rows = "\n".join(
        f"| `{name}` | `{value}` | {'MATCH' if name in report['matching_candidates'] else 'no'} |"
        for name, value in report["candidate_results"].items()
    )
    return "\n".join(
        [
            "# OLMSmoother2 PF_Pixel8 premultiply rounding audit - 2026-07-18",
            "",
            f"- Verdict: `{report['verdict']}`",
            "- Scope: one retained Windows Software witness at source coordinate `(92,840)`.",
            "- The plug-in source was not edited.",
            "",
            "## FACT",
            "",
            f"- Raw source RGBA: `{fact['source_rgba']}`.",
            f"- Windows before-effects RGBA: `{fact['windows_before_effects_rgba']}`.",
            f"- Integer product: `174 * 174 = {fact['product_rgb_times_alpha']}` = `255 * {fact['quotient']} + {fact['remainder']}`.",
            f"- Source SHA-256: `{fact['source_sha256']}`.",
            f"- Windows before-effects SHA-256: `{fact['windows_before_effects_sha256']}`.",
            f"- Exhaustive PF8 mapping check: `{fact['exhaustive_integer_vs_float_pairs']['pairs']}` pairs, `{fact['exhaustive_integer_vs_float_pairs']['mismatches']}` mismatches between integer `+127` and normalized-float nearest.",
            "",
            "## Candidate Rules",
            "",
            "| Rule | Result | Windows match |",
            "| --- | ---: | --- |",
            rows,
            "",
            "## Identified Rule",
            "",
            f"- Byte formula: `{rule['expression']}`.",
            f"- Equivalent mathematical description: `{rule['mathematical_form']}`.",
            f"- Witness result: `{rule['witness_result']}`.",
            f"- `{rule['why_plus_127_is_exact_for_integer_products']}`",
            "",
            "## Independent Trace Check",
            "",
            "The retained Mac trace still shows the un-premultiplied normalized sample `(92,840)` as approximately `0.42325333` with alpha `0.68234253`, and records a neighboring source sample entering the append path. This independently confirms why the current Mac boundary differs from the Windows before-effects byte witness; it does not establish AE exactness.",
            "",
            "## INFERENCE",
            "",
            *[f"- {item}" for item in report["inference"]],
            "",
            "## Claims Not Made",
            "",
            *[f"- {item}" for item in report["claims_not_made"]],
            "",
            "## Reproduction",
            "",
            "```sh",
            "python3 tools/emulation/audit_olmsmoother2_pf8_premultiply_rounding_20260718.py",
            "```",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, default=ROOT / "refs/conformance/olmsmoother2_pf8_premultiply_rounding_20260718.json")
    parser.add_argument("--output-md", type=Path, default=ROOT / "refs/conformance/olmsmoother2_pf8_premultiply_rounding_20260718.md")
    args = parser.parse_args()
    report = audit()
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
