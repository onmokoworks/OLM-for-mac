#!/usr/bin/env python3
"""Audit OLMBlur 16bpc residuals in exported PNG space and AE word space."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REF_DIR = (
    ROOT
    / "refs"
    / "win_references"
    / "olm_bitdepth_16bpc_normalized_exact_20260625"
    / "OLMbit-depthconformancebatch"
)
DEFAULT_CAND_DIR = (
    ROOT
    / "handoff"
    / "ae_pixel_validation_20260618"
    / "results"
    / "bitdepth16_olmblur_exact"
)
DEFAULT_OUT_JSON = ROOT / "refs" / "conformance" / "olmblur_16bpc_word_delta_audit_20260628.json"
DEFAULT_OUT_MD = ROOT / "refs" / "conformance" / "olmblur_16bpc_word_delta_audit_20260628.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-dir", type=Path, default=DEFAULT_REF_DIR)
    parser.add_argument("--candidate-dir", type=Path, default=DEFAULT_CAND_DIR)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--summary-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def load_verify_manifest_module():
    path = ROOT / "refs" / "scripts" / "verify_manifest.py"
    spec = importlib.util.spec_from_file_location("verify_manifest", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VERIFY = load_verify_manifest_module()


def count_values(values: np.ndarray) -> dict[str, int]:
    if values.size == 0:
        return {}
    keys, counts = np.unique(values, return_counts=True)
    return {str(int(key)): int(count) for key, count in zip(keys, counts)}


def estimate_ae_word_delta(reference_values: np.ndarray, candidate_values: np.ndarray) -> np.ndarray:
    # AE PF_Pixel16 worlds use 0..32768; exported 16bpc PNGs are 0..65535.
    # Odd exported values map back cleanly with ceil(value / 2), matching the
    # observed OLMBlur residual family.
    return ((reference_values + 1) // 2) - ((candidate_values + 1) // 2)


def case_stem(case_num: int) -> str:
    return (
        "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__"
        f"olmblur__case_{case_num:04d}.png"
    )


def analyze_case(reference_dir: Path, candidate_dir: Path, case_num: int) -> dict[str, Any]:
    frame = case_stem(case_num)
    ref = VERIFY.png_rgba_array(reference_dir / frame).astype(np.int32)
    cand = VERIFY.png_rgba_array(candidate_dir / frame).astype(np.int32)
    delta = ref - cand
    nonzero_px_mask = np.any(delta != 0, axis=2)
    coords = np.argwhere(nonzero_px_mask)
    bbox = None
    if len(coords):
        y0, x0 = coords.min(axis=0)
        y1, x1 = coords.max(axis=0)
        bbox = [int(x0), int(y0), int(x1), int(y1)]

    channel_mask = delta != 0
    ref_values = ref[channel_mask]
    cand_values = cand[channel_mask]
    word_deltas = estimate_ae_word_delta(ref_values, cand_values)
    sample_rows = []
    for y, x in coords[:8]:
        sample_rows.append(
            {
                "xy": [int(x), int(y)],
                "reference_rgba16_export": [int(v) for v in ref[y, x]],
                "candidate_rgba16_export": [int(v) for v in cand[y, x]],
                "delta_reference_minus_candidate": [int(v) for v in delta[y, x]],
                "estimated_word_delta_nonzero_channels": [
                    int(v)
                    for v in estimate_ae_word_delta(ref[y, x][delta[y, x] != 0], cand[y, x][delta[y, x] != 0])
                ],
            }
        )

    classification = "exact"
    if int(np.max(np.abs(delta))) == 2 and set(count_values(word_deltas)) <= {"-1", "1"}:
        classification = "sign-mixed-one-word" if len(count_values(word_deltas)) > 1 else "one-word"
    elif case_num == 7:
        classification = "legacy-border-plus-one-word"
    elif np.any(delta != 0):
        classification = "residual"

    return {
        "case_id": f"case_{case_num:04d}",
        "frame": frame,
        "classification": classification,
        "max_exported_delta": int(np.max(np.abs(delta))),
        "nonzero_px": int(nonzero_px_mask.sum()),
        "total_px": int(delta.shape[0] * delta.shape[1]),
        "bbox_xyxy": bbox,
        "exported_channel_delta_counts": count_values(delta[channel_mask]),
        "reference_export_parity_counts": count_values(ref_values % 2),
        "candidate_export_parity_counts": count_values(cand_values % 2),
        "estimated_ae_word_delta_counts": count_values(word_deltas),
        "samples": sample_rows,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OLMBlur 16bpc Word-Delta Audit - 2026-06-28",
        "",
        "## Summary",
        "",
        "This audit re-reads the 16bpc PNGs through `refs/scripts/verify_manifest.py`",
        "`png_rgba_array`, which uses ImageMagick `-depth 16 -endian MSB` when",
        "available. Plain Pillow reads are not sufficient here because they collapse",
        "the data to 8-bit values.",
        "",
        "The current Mac AE 16bpc OLMBlur residual is mostly a one-word PF_Pixel16",
        "difference:",
        "",
        "- `case_0001..0006`: every nonzero exported PNG channel delta is `+2` or `-2`.",
        "  In AE's 0..32768 16bpc word domain this is an inferred `+1` or `-1` word",
        "  delta.",
        "- All affected `case_0001..0006` exported values are odd on both sides. This is",
        "  consistent with AE's 0..32768 internal 16bpc words being exported to 0..65535",
        "  PNG space.",
        "- `case_0007`: most residual pixels are the same inferred `+/-1` word family,",
        "  but the localized `(0,0)` witness is separate: Windows reference",
        "  `[0,0,0,65535]`, Mac candidate `[383,383,383,65535]`, i.e. roughly",
        "  `-192` internal words on RGB.",
        "",
        "This strengthens the existing rule: do not tune the blur kernel from this",
        "evidence. The non-Legacy 16bpc problem is now narrowed to final float/helper",
        "state or 16bpc writeback order at one-word precision. The Legacy case still has",
        "a separate border/seed/all-same witness.",
        "",
        "## Case Table",
        "",
        "| Case | Class | Max exported delta | Nonzero px | Channel deltas | Inferred word deltas | Bounding box |",
        "| --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for row in payload["cases"]:
        lines.append(
            f"| `{row['case_id']}` | `{row['classification']}` | "
            f"{row['max_exported_delta']} | {row['nonzero_px']} | "
            f"`{row['exported_channel_delta_counts']}` | "
            f"`{row['estimated_ae_word_delta_counts']}` | "
            f"`{row['bbox_xyxy']}` |"
        )
    lines.extend(
        [
            "",
            "## Witnesses",
            "",
        ]
    )
    for case_id in ("case_0006", "case_0007"):
        row = next(row for row in payload["cases"] if row["case_id"] == case_id)
        for sample in row["samples"][:3]:
            lines.append(
                f"- `{case_id} ({sample['xy'][0]},{sample['xy'][1]})`: "
                f"Windows `{sample['reference_rgba16_export']}`, "
                f"Mac `{sample['candidate_rgba16_export']}`, "
                f"delta `{sample['delta_reference_minus_candidate']}`, "
                f"inferred words `{sample['estimated_word_delta_nonzero_channels']}`."
            )
    lines.extend(
        [
            "",
            "## Next Evidence",
            "",
            "- For non-Legacy `case_0001..0006`, prove whether the one-word sign-mixed",
            "  residual comes from final pre-writeback float state, the `+0.5` helper path,",
            "  or an AE 16bpc store/export convention mismatch.",
            "- For Legacy `case_0007`, keep the one-word family separate from the `(0,0)`",
            "  border/seed/all-same state. Do not use the `(0,0)` witness to change the",
            "  general non-Legacy writeback rule.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    cases = [analyze_case(args.reference_dir, args.candidate_dir, case_num) for case_num in range(1, 8)]
    payload = {
        "kind": "olmblur_16bpc_word_delta_audit",
        "date": "2026-06-28",
        "reference_dir": str(args.reference_dir),
        "candidate_dir": str(args.candidate_dir),
        "cases": cases,
        "conclusion": [
            "Non-Legacy 16bpc residuals are sign-mixed one-word PF_Pixel16 deltas.",
            "Legacy case_0007 contains the same one-word family plus a separate localized border/seed/all-same witness.",
            "Do not tune the blur kernel from this evidence; next proof belongs at final float/helper/store order.",
        ],
    }
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.summary_md.write_text(render_markdown(payload), encoding="utf-8")
    print(f"summary_json={args.summary_json}")
    print(f"summary_md={args.summary_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
