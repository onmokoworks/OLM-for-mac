#!/usr/bin/env python3
"""Freeze the Mac AE 16bpc DG Layer-family residual for cases 0012/0014."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625"
PLUGIN = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMDistanceGradation.plugin/Contents/MacOS/OLMDistanceGradation"
CASES = ("olmdistancegradation_extended__case_0012", "olmdistancegradation_extended__case_0014")
DEFAULT_JSON = ROOT / "refs/conformance/olmdistancegradation_16bpc_layer_residual_mac_ae_20260717.json"
DEFAULT_MD = ROOT / "refs/conformance/olmdistancegradation_16bpc_layer_residual_mac_ae_20260717.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_root", type=Path)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()

    rows = []
    for case_id in CASES:
        result_path = args.output_root / case_id / "AE_SINGLE_CASE_RESULT.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        output = Path(result["output_png"])
        expected = REQUEST / "expected" / output.name
        actual_pixels = np.asarray(Image.open(output)).astype(np.int64)
        expected_pixels = np.asarray(Image.open(expected)).astype(np.int64)
        if actual_pixels.shape != expected_pixels.shape:
            raise SystemExit(f"shape mismatch for {case_id}: {actual_pixels.shape} != {expected_pixels.shape}")
        delta = np.abs(actual_pixels - expected_pixels)
        signed = actual_pixels - expected_pixels
        pixel_mask = np.any(delta != 0, axis=-1)
        ys, xs = np.nonzero(pixel_mask)
        channel_names = ("R", "G", "B", "A")
        rows.append({
            "case_id": case_id,
            "ae_version": result["ae_version"],
            "project_bits_per_channel": result["project_bits_per_channel"],
            "project_working_space": result["project_working_space"],
            "project_linear_blending": result["project_linear_blending"],
            "output_sha256": sha256(output),
            "expected_sha256": sha256(expected),
            "max_diff": int(delta.max()),
            "nonzero_samples": int(np.count_nonzero(delta)),
            "nonzero_pixels": int(np.count_nonzero(pixel_mask)),
            "mean_abs_diff": float(delta.mean()),
            "diff_bbox_xyxy": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None,
            "nonzero_samples_by_channel": {
                name: int(np.count_nonzero(delta[..., index])) for index, name in enumerate(channel_names)
            },
            "signed_delta_histogram": {
                str(value): int(count)
                for value, count in zip(*np.unique(signed[delta != 0], return_counts=True))
            },
            "first_diff_samples": [
                {
                    "xy": [int(x), int(y)],
                    "mac_rgba": actual_pixels[y, x].tolist(),
                    "windows_rgba": expected_pixels[y, x].tolist(),
                    "signed_delta_rgba": signed[y, x].tolist(),
                }
                for y, x in zip(ys[:16], xs[:16])
            ],
        })

    exact = all(row["max_diff"] == 0 for row in rows)
    report = {
        "kind": "olmdistancegradation_16bpc_layer_residual_mac_ae",
        "date": "2026-07-17",
        "status": "ae_exact" if exact else "known_red_narrow_layer_family",
        "ae_exact_claim": exact,
        "plugin_sha256": sha256(PLUGIN),
        "reference_kind": "Windows AE 25.2 Software 16bpc PNG",
        "runner_kind": "Mac AE single-case disposable project",
        "cases": rows,
        "claim_boundary": "real Mac AE pixel comparison; max_diff=0 only would be exact",
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# OLMDistanceGradation 16bpc Layer-family Mac AE proof",
        "",
        f"- Status: `{report['status']}`",
        f"- Installed plug-in SHA-256: `{report['plugin_sha256']}`",
        "- Exact requires `max_diff=0`; these residuals are not complete.",
        "",
        "| Case | max diff | nonzero pixels | nonzero samples |",
        "| --- | ---: | ---: | ---: |",
    ]
    lines.extend(
        f"| `{row['case_id']}` | `{row['max_diff']}` | `{row['nonzero_pixels']}` | `{row['nonzero_samples']}` |"
        for row in rows
    )
    lines.extend(["", f"Boundary: {report['claim_boundary']}.", ""])
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": report["status"], "cases": rows}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
