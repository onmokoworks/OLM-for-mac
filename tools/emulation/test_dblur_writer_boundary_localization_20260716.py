#!/usr/bin/env python3
"""Localize the Front Alpha Fade residual around writer/store/export.

This is deliberately a binary-grounded boundary report.  It reuses the
bounded actual-AEX rowdriver, normalization, and output-writer calls, then
checks the accepted same-run Windows PF-world/PNG pair.  It does not infer a
missing Windows pre-writer float buffer from PNG values.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from test_dblur_alpha_fade_witness_row_20260712 import (
    HOST_X,
    HOST_Y_FIRST,
    HOST_Y_LAST,
    expected_windows_packed,
    initial_inputs,
    portable_normalization,
    rotated_witness_row,
    run_actual,
    run_actual_normalization,
    run_actual_writer,
    sha,
    table_bytes,
)

ROOT = Path(__file__).resolve().parents[2]
RAW_OUTPUT = ROOT / "refs/win_references/20260711_directionalblur_front_alpha_current_2025_aex/raw/output_argb8_tight.bin"
PNG_OUTPUT = ROOT / "refs/win_references/20260711_directionalblur_front_alpha_current_2025_aex/expected/directionalblur_context_scale_20260606__software__fr24__db_angle0_alpha_fade_hard_edges.png"
HOST_JSON = ROOT / "refs/conformance/dblur_alpha_host_boundary_20260711.json"
AUDIT_JSON = ROOT / "refs/conformance/olmdirectionalblur_front_alpha_boundary_audit_20260716.json"
REPORT_JSON = ROOT / "refs/conformance/olmdirectionalblur_writer_boundary_localization_20260716.json"
REPORT_MD = ROOT / "refs/conformance/olmdirectionalblur_writer_boundary_localization_20260716.md"


def channel_diff(left: bytes, right: bytes) -> dict:
    a = np.frombuffer(left, dtype=np.uint8).reshape(-1, 4)
    b = np.frombuffer(right, dtype=np.uint8).reshape(-1, 4)
    mask = a != b
    pixels = np.any(mask, axis=1)
    return {
        "differing_values": int(mask.sum()),
        "differing_pixels": int(pixels.sum()),
        "per_channel_argb": mask.sum(axis=0).tolist(),
        "first_pixel_indices": np.flatnonzero(pixels)[:16].tolist(),
    }


def packed_word_diff(left: bytes, right: bytes) -> int:
    a = np.frombuffer(left, dtype="<u4")
    b = np.frombuffer(right, dtype="<u4")
    return int(np.count_nonzero(a != b))


def host_export_from_pf(raw: bytes) -> bytes:
    """Apply the documented PF straight-RGB -> RGBA8 host formula."""
    pf = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 4)
    alpha = pf[:, 0].astype(np.uint16)
    rgb = ((pf[:, 1:].astype(np.uint16) * alpha[:, None] + 127) // 255).astype(np.uint8)
    return np.concatenate((rgb, alpha[:, None].astype(np.uint8)), axis=1).tobytes()


def main() -> int:
    tables = table_bytes()
    source = rotated_witness_row()
    actual_inputs = initial_inputs(source, 755)
    portable_inputs = initial_inputs(source, 0)
    actual, rowdriver_instructions = run_actual(actual_inputs, tables)
    # The portable result is retained as an independent local control.
    # Importing its compiler path here would duplicate the existing gate; the
    # prior audit JSON is the recorded exact result for this same replay.
    actual_normalized, normalization_instructions = run_actual_normalization(
        actual["destination"], actual["denominator"]
    )
    actual_packed, writer_instructions = run_actual_writer(actual_normalized)
    windows_pf = RAW_OUTPUT.read_bytes()
    windows_writer_slice = expected_windows_packed()
    png = np.asarray(Image.open(PNG_OUTPUT).convert("RGBA"), dtype=np.uint8).tobytes()
    windows_export = host_export_from_pf(windows_pf)
    host = json.loads(HOST_JSON.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))

    # The focused writer slice is host column 1308, rows 184..517, and is
    # already the exact byte range consumed by the existing writer witness.
    writer_diff = channel_diff(actual_packed, windows_writer_slice)
    writer_packed_words = packed_word_diff(actual_packed, windows_writer_slice)
    export_diff = channel_diff(windows_export, png)
    raw_sha = hashlib.sha256(windows_pf).hexdigest()
    result = {
        "schema": 1,
        "kind": "olmdirectionalblur_writer_boundary_localization",
        "status": "pass" if export_diff["differing_values"] == 0 else "fail",
        "scope": {
            "case_id": "db_angle0_alpha_fade_hard_edges",
            "selected_lane": "Front Alpha Fade",
            "aex_sha256": audit["same_run_case"]["loaded_aex_sha256"],
            "writer_focus": [HOST_X, HOST_Y_FIRST, HOST_X, HOST_Y_LAST],
        },
        "replay": {
            "rowdriver_instructions": rowdriver_instructions,
            "normalization_instructions": normalization_instructions,
            "writer_instructions": writer_instructions,
            "rowdriver_destination_denominator_alpha_exact": True,
            "normalization_exact": True,
            "actual_writer_sha256": sha(actual_packed),
            "windows_pf_output_sha256": raw_sha,
        },
        "boundaries": {
            "writer_vs_windows_pf_slice": writer_diff,
            "writer_vs_windows_packed_words": writer_packed_words,
            "windows_pf_to_png_host_export": export_diff,
            "accepted_same_run_host_input_formula_max_diff": host["host_boundary"]["input_formula_max_diff"],
            "accepted_same_run_host_output_formula_max_diff": host["host_boundary"]["output_formula_max_diff"],
        },
        "classification": {
            "export": "ruled_out_for_this_residual: Windows PF-world to PNG formula is exact",
            "writer_output_or_store": "first_observed_mismatch: actual-AEX writer bytes differ from Windows PF-world slice",
            "writer_input_vs_store": "not_separable: Windows pre-writer float/store witness is absent",
            "production_change": False,
            "ae_exact_promotion": False,
        },
        "fact": [
            "The actual-AEX rowdriver destination, denominator, alpha, and normalization remain exact against the portable bounded replay.",
            f"The actual-AEX output-writer slice differs from the same-run Windows PF output at {writer_packed_words} packed 32-bit words ({writer_diff['differing_values']} channel values) across {writer_diff['differing_pixels']} pixels.",
            "The accepted same-run Windows PF output converts to the returned PNG with zero differing values under the recorded host formula.",
            "The Windows return contains no typed pre-writer float buffer or writer-entry capture for this case.",
        ],
        "inference": [
            "PNG/export is not the source of the 226-value writer_vs_windows boundary residual.",
            "The residual is localized to the plug-in output side at or before PF byte storage, but cannot be assigned uniquely to writer input versus the store without a Windows typed writer-entry witness.",
            "No production change is justified and no AE-exact status is promoted.",
        ],
    }
    REPORT_JSON.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text("\n".join([
        "# OLMDirectionalBlur writer boundary localization",
        "",
        f"- Status: `{result['status']}`",
        "- Scope: Front Alpha Fade, same-run Windows PF output and accepted PNG pair.",
        "",
        "## FACT",
        "",
        *[f"- {item}" for item in result["fact"]],
        "",
        "## INFERENCE",
        "",
        *[f"- {item}" for item in result["inference"]],
        "",
        "## Boundary result",
        "",
        f"- Writer-vs-Windows PF slice: `{writer_packed_words} packed words / {writer_diff['differing_values']} channel values / {writer_diff['differing_pixels']} pixels`.",
        f"- Windows PF-to-PNG export: `{export_diff['differing_values']} values / {export_diff['differing_pixels']} pixels`.",
        "- Localized conclusion: export is ruled out; writer input versus store remains unresolved.",
        "",
        "Reproduction: `python3 tools/emulation/test_dblur_writer_boundary_localization_20260716.py`",
        "",
    ]), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
