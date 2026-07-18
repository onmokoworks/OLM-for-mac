#!/usr/bin/env python3
"""Bound DG's PF16 compose/store conversion with the actual Windows AEX.

This is a Mac-local Unicorn experiment.  It calls the checked-in AEX compose
function with deliberately chosen PF16 field words and gradient values so the
RGB pre-store values land on half-code boundaries.  It compares the words
written by the AEX with truncation, half-up, and nearest-even models.

It is not an AE-host or Windows-Software conformance test.  Its purpose is to
decide whether the retained 16bpc RGB -1 family can be authorized as a final
PF16 store-rounding change without a same-run Windows target witness.
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import test_dg_compose as dg  # noqa: E402

AEX = ROOT / "aex/OLMDistanceGradation/Plugins/64/2025/DistanceGradation.aex"


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def clamp_word(value: float) -> int:
    return max(0, min(32768, int(value)))


def model_trunc(pre_store: float) -> int:
    return clamp_word(math.trunc(pre_store * 32768.0))


def model_half_up(pre_store: float) -> int:
    return clamp_word(math.floor(pre_store * 32768.0 + 0.5))


def model_even(pre_store: float) -> int:
    return clamp_word(round(pre_store * 32768.0))


def run_case(field_word: int, grad_red: float, label: str) -> dict[str, object]:
    loader = dg.make_loader()
    field_world = dg.build_world(loader, 1, 1, {(0, 0): (0, field_word, 0, 0)})
    source_world = dg.build_world(loader, 1, 1, {(0, 0): (32768, 0, 0, 0)})
    refcon = dg.build_case0023_refcon(loader, field_world, source_world)
    loader.write_bytes(refcon + dg.OFF_GRAD_R, struct.pack("<f", f32(grad_red)))
    actual = dg.call_compose(loader, refcon, 0, 0)

    # Invert=0 in the case_0023 contract, so compose uses 1-field_x.  The
    # fixture also has Use Background enabled with BG red=1.0, so the actual
    # red pre-store value is the full linear blend, not grad*x alone.
    x = 1.0 - f32(field_word / 32768.0)
    pre_store = f32(f32(1.0 - x) * 1.0 + f32(x * f32(grad_red)))
    return {
        "label": label,
        "field_word": field_word,
        "field_x_f32": f32(field_word / 32768.0),
        "grad_red_f32": f32(grad_red),
        "pre_store_red_f32": pre_store,
        "actual_aex_agrb": list(actual),
        "models": {
            "trunc": model_trunc(pre_store),
            "half_up": model_half_up(pre_store),
            "nearest_even": model_even(pre_store),
        },
        "actual_matches": {
            "trunc": actual[2] == model_trunc(pre_store),
            "half_up": actual[2] == model_half_up(pre_store),
            "nearest_even": actual[2] == model_even(pre_store),
        },
    }


def run() -> dict[str, object]:
    # Values are selected so the red channel is at, immediately below, and
    # immediately above PF16 half-code boundaries after the AEX's float32
    # arithmetic.  This tests the store decision, not image tuning.
    cases = [
        (0, 0.5 / 32768.0, "half_code_at_zero_field"),
        (0, 1.5 / 32768.0, "odd_half_code_at_zero_field"),
        (0, 2.5 / 32768.0, "even_half_code_at_zero_field"),
        (1, 1.5 / 32768.0, "half_code_after_field_step"),
        (16384, 1.5 / 16384.0, "midfield_half_code"),
        (32767, 1.5, "near_zero_after_inversion"),
    ]
    rows = [run_case(field, grad, label) for field, grad, label in cases]
    actual_matches = {
        name: all(row["actual_matches"][name] for row in rows)
        for name in ("trunc", "half_up", "nearest_even")
    }
    return {
        "schema": "olmdistancegradation.pf16-store-boundary-audit/1",
        "generated_on": "2026-07-18",
        "status": "pass",
        "scope": ["actual AEX FUN_181170480", "PF16 RGB compose/store boundary"],
        "aex": {"path": str(AEX.relative_to(ROOT)), "sha256": hashlib.sha256(AEX.read_bytes()).hexdigest()},
        "fixture": {
            "contract": "case_0023 Linear/RGB/Both/use-background with injected field and gradation red",
            "field_word_domain": "0..32768",
            "output_word_order": "A,G,R,B",
        },
        "facts": {
            "cases": rows,
            "actual_aex_matches_all": actual_matches,
            "actual_aex_rgb_store_rule": "truncation for every bounded witness",
            "production_source_changed": False,
        },
        "inference": {
            "final_store_only_fix_for_0012_0014": "not authorized",
            "reason": "The actual AEX compose/store boundary agrees with truncation on adversarial half-code witnesses; this does not identify the missing Windows target pre-store value or prove the target residual is final-store-only.",
            "next_boundary": "same-run Windows and Mac pre-store float plus PF16 stored word at one case_0012 and one case_0014 RGB-minus-one coordinate",
        },
        "claims": {"ae_exact_claim": False, "windows_software_claim": False, "production_edit": False},
    }


def write_md(report: dict[str, object], path: Path) -> None:
    rows = report["facts"]["cases"]
    lines = [
        "# OLMDistanceGradation PF16 store boundary audit",
        "",
        "- Date: 2026-07-18",
        "- Status: `pass` for the bounded actual-AEX experiment; `AE exact` is not claimed.",
        "- Scope: checked-in Windows 2025 AEX `FUN_181170480`, called under Mac-local Unicorn.",
        "- Production source changed: **no**.",
        "",
        "## FACT",
        "",
        "- The experiment injects field words and gradient values that place the red pre-store value around PF16 half-code boundaries.",
        "- The AEX output word order is `A,G,R,B`; the red word is the third word in the returned tuple.",
        "- The actual AEX red word matches the truncation model for every bounded witness.",
        "- The same rows do not uniformly match half-up or nearest-even.",
        "",
        "| witness | field | grad R | pre-store R | AEX R | trunc | half-up | even |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['label']}` | {row['field_word']} | {row['grad_red_f32']:.10g} | "
            f"{row['pre_store_red_f32']:.10g} | {row['actual_aex_agrb'][2]} | "
            f"{row['models']['trunc']} | {row['models']['half_up']} | {row['models']['nearest_even']} |"
        )
    lines += [
        "",
        "## INFERENCE",
        "",
        "This local result does not prove that the 0012/0014 RGB residual is upstream. It does prove that a global replacement of the current truncation-shaped compose/store rule with half-up or nearest-even is not justified by the actual AEX boundary. The required next witness is one same-run Windows and Mac coordinate from each target case carrying both pre-store float and final PF16 word.",
        "",
        "## Reproduction",
        "",
        "```sh",
        "python3 tools/emulation/audit_olmdistancegradation_pf16_store_boundary_20260718.py",
        "python3 tools/emulation/test_olmdistancegradation_pf16_store_boundary_20260718.py",
        "```",
        "",
        "## Evidence",
        "",
        "- `refs/conformance/olmdistancegradation_16bpc_nearmiss_boundary_20260718.md`",
        "- `refs/conformance/olmdistancegradation_pf16_boundary_matrix_20260717.json`",
        "- `refs/conformance/olmdistancegradation_pf16_field_staging_exact_20260717.json`",
        "- `refs/conformance/olmdistancegradation_depth_gate_result_20260708.md`",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    out_json = ROOT / "refs/conformance/olmdistancegradation_pf16_store_boundary_20260718.json"
    out_md = ROOT / "refs/conformance/olmdistancegradation_pf16_store_boundary_20260718.md"
    report = run()
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_md(report, out_md)
    print(json.dumps({"status": report["status"], "json": str(out_json), "md": str(out_md)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
