#!/usr/bin/env python3
"""Inspect representative OLMDistanceGradation 16bpc residual witnesses."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REQUEST = ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625"
DEFAULT_RUN = ROOT / "refs/reports/ae_pixel_validation_16bpc_distancegradation_extended_powerfix_20260629_1424"
CASES = {
    "olmdistancegradation_extended__case_0020": {
        "family": "constant-bg-binary-sparse-full-color",
        "points": [(951, 417), (950, 417), (951, 416), (951, 418), (0, 0)],
    },
    "olmdistancegradation_extended__case_0012": {
        "family": "layer-no-bg-source-or-alpha-ownership",
        "points": [(462, 7), (72, 8), (462, 6), (462, 8), (0, 0)],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-dir", type=Path, default=DEFAULT_REQUEST)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=ROOT / "refs/conformance/olmdistancegradation_16bpc_representative_witnesses_20260629.json",
    )
    parser.add_argument(
        "--summary-md",
        type=Path,
        default=ROOT / "refs/conformance/olmdistancegradation_16bpc_representative_witnesses_20260629.md",
    )
    return parser.parse_args()


def load_verify_manifest_module():
    path = ROOT / "refs/scripts/verify_manifest.py"
    spec = importlib.util.spec_from_file_location("verify_manifest", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_case_images(verify, request_dir: Path, run_dir: Path, case_id: str):
    frame = f"olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__{case_id}.png"
    before = f"olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__{case_id}_before_effects.png"
    return {
        "frame": frame,
        "input": verify.load_rgba(request_dir / "input" / before),
        "reference": verify.load_rgba(request_dir / "expected" / frame),
        "candidate": verify.load_rgba(run_dir / "candidate" / frame),
    }


def summarize_case(arrays: dict, points: list[tuple[int, int]]) -> dict:
    ref = arrays["reference"]
    cand = arrays["candidate"]
    inp = arrays["input"]
    delta = cand.astype(np.int64) - ref.astype(np.int64)
    changed = np.any(delta != 0, axis=2)
    ys, xs = np.where(changed)
    bbox = None
    if xs.size:
        bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    samples = []
    for x, y in points:
        samples.append(
            {
                "x": x,
                "y": y,
                "input": [int(v) for v in inp[y, x]],
                "reference": [int(v) for v in ref[y, x]],
                "candidate": [int(v) for v in cand[y, x]],
                "delta": [int(v) for v in delta[y, x]],
            }
        )
    changed_input = inp[changed]
    changed_ref = ref[changed]
    changed_cand = cand[changed]
    return {
        "frame": arrays["frame"],
        "changed_pixel_count": int(xs.size),
        "changed_bbox": bbox,
        "samples": samples,
        "changed_input_alpha_unique": int(len(set(changed_input[:, 3].tolist()))) if xs.size else 0,
        "changed_reference_alpha_unique": int(len(set(changed_ref[:, 3].tolist()))) if xs.size else 0,
        "changed_candidate_alpha_unique": int(len(set(changed_cand[:, 3].tolist()))) if xs.size else 0,
    }


def main() -> int:
    args = parse_args()
    verify = load_verify_manifest_module()
    request_dir = args.request_dir.resolve()
    run_dir = args.run_dir.resolve()
    case_rows = []
    for case_id, meta in CASES.items():
        arrays = load_case_images(verify, request_dir, run_dir, case_id)
        row = summarize_case(arrays, meta["points"])
        row["case_id"] = case_id
        row["family"] = meta["family"]
        case_rows.append(row)

    payload = {
        "kind": "olmdistancegradation_16bpc_representative_witnesses",
        "request_dir": str(request_dir.relative_to(ROOT)),
        "run_dir": str(run_dir.relative_to(ROOT)),
        "cases": case_rows,
        "reading": {
            "case_0020": (
                "Sparse Constant/background mismatch: candidate keeps the input/gradation red endpoint "
                "where Windows selects the blue background endpoint on a narrow opaque-source boundary."
            ),
            "case_0012": (
                "Layer/no-bg mismatch: alpha is mostly shared, but Windows RGB is raised toward the "
                "post-compose alpha/source-owned value while the candidate keeps lower source RGB."
            ),
        },
    }
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# OLMDistanceGradation 16bpc Representative Witnesses (2026-06-29)",
        "",
        f"- Request dir: `{payload['request_dir']}`",
        f"- Run dir: `{payload['run_dir']}`",
        "",
        "## Cases",
        "",
    ]
    for row in case_rows:
        lines.extend(
            [
                f"### {row['case_id']}",
                "",
                f"- Family: `{row['family']}`",
                f"- Changed pixels: `{row['changed_pixel_count']}`",
                f"- Changed bbox: `{row['changed_bbox']}`",
                f"- Changed input alpha unique count: `{row['changed_input_alpha_unique']}`",
                f"- Changed reference alpha unique count: `{row['changed_reference_alpha_unique']}`",
                f"- Changed candidate alpha unique count: `{row['changed_candidate_alpha_unique']}`",
                "",
                "| Point | input | reference | candidate | delta |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for sample in row["samples"]:
            lines.append(
                f"| `({sample['x']},{sample['y']})` | `{sample['input']}` | "
                f"`{sample['reference']}` | `{sample['candidate']}` | `{sample['delta']}` |"
            )
        lines.append("")
    lines.extend(
        [
            "## Reading",
            "",
            f"- case_0020: {payload['reading']['case_0020']}",
            f"- case_0012: {payload['reading']['case_0012']}",
            "- Prefer case_0020 first: it is sparse, fully opaque, and separates branch/color selection from alpha ownership.",
        ]
    )
    args.summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"summary_json={args.summary_json}")
    print(f"summary_md={args.summary_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
