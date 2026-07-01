#!/usr/bin/env python3
"""Classify the current DistanceGradation case_0023 residual by raw EDT bucket.

This is a bounded evidence script for the remaining 16bpc Constant
`In/Out=Both` + `Outside Threshold=0` lane. It does not claim a new fix; it
just turns the current sparse residual into a sharper statement about where the
remaining wrong endpoint choices live.
"""

from __future__ import annotations

import importlib.util
import json
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import ndimage


REPO = Path(__file__).resolve().parents[1]
REQUEST_ZIP = REPO / "handoffs" / "ae_host_validation" / "20260625_221356_16bpc_mac_ae_validation" / "bitdepth16_olmdistancegradation_extended_exact.zip"
CURRENT_CANDIDATE = (
    REPO
    / "refs"
    / "reports"
    / "ae_single_case_distancegradation_constant_no_post_20260630"
    / "olmdistancegradation_extended__case_0023"
    / "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0023.png"
)
SUMMARY_JSON = REPO / "refs" / "conformance" / "olmdistancegradation_16bpc_case0023_residual_split_20260630.json"
SUMMARY_MD = REPO / "refs" / "conformance" / "olmdistancegradation_16bpc_case0023_residual_split_20260630.md"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VERIFY = load_module(REPO / "refs" / "scripts" / "verify_manifest.py", "verify_manifest")


def rgba_key(px: np.ndarray) -> str:
    return ",".join(str(int(v)) for v in px.tolist())


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        with zipfile.ZipFile(REQUEST_ZIP) as zf:
            zf.extractall(td_path)
        root = next(p for p in td_path.iterdir() if p.is_dir())
        manifest = json.loads((root / "reference_manifest.json").read_text(encoding="utf-8"))
        case = next(c for c in manifest["cases"] if c["id"] == "olmdistancegradation_extended__case_0023")
        input_img = VERIFY.load_rgba(root / "input" / case["before_effects_frame"]).astype(np.uint16)
        ref_img = VERIFY.load_rgba(root / "expected" / case["frame"]).astype(np.uint16)

    cand_img = VERIFY.load_rgba(CURRENT_CANDIDATE).astype(np.uint16)

    alpha = input_img[..., 3].astype(np.float32) / 65535.0
    mask = (alpha > 0.0).astype(np.uint8)
    inside = ndimage.distance_transform_edt(mask != 0).astype(np.float32)
    outside = ndimage.distance_transform_edt((1 - mask) != 0).astype(np.float32)

    residual = np.any(cand_img != ref_img, axis=-1)
    ys, xs = np.where(residual)

    buckets: dict[str, dict[str, object]] = {}
    by_pair: dict[str, int] = defaultdict(int)
    examples: list[dict[str, object]] = []

    for idx, (y, x) in enumerate(zip(ys.tolist(), xs.tolist(), strict=False)):
        cand_px = cand_img[y, x]
        ref_px = ref_img[y, x]
        inside_v = float(inside[y, x])
        outside_v = float(outside[y, x])
        inside_key = f"{inside_v:.6f}"
        bucket = buckets.setdefault(
            inside_key,
            {
                "inside_distance": inside_v,
                "count": 0,
                "outside_distance_values": set(),
                "candidate_rgba_keys": defaultdict(int),
                "reference_rgba_keys": defaultdict(int),
            },
        )
        bucket["count"] += 1
        bucket["outside_distance_values"].add(round(outside_v, 6))
        bucket["candidate_rgba_keys"][rgba_key(cand_px)] += 1
        bucket["reference_rgba_keys"][rgba_key(ref_px)] += 1
        by_pair[f"{rgba_key(cand_px)} -> {rgba_key(ref_px)}"] += 1
        if idx < 12:
            examples.append(
                {
                    "x": x,
                    "y": y,
                    "inside_distance": inside_v,
                    "outside_distance": outside_v,
                    "candidate_rgba": cand_px.tolist(),
                    "reference_rgba": ref_px.tolist(),
                }
            )

    serializable_buckets = []
    for key, row in sorted(buckets.items(), key=lambda item: float(item[0])):
        serializable_buckets.append(
            {
                "inside_distance": row["inside_distance"],
                "count": row["count"],
                "outside_distance_values": sorted(row["outside_distance_values"]),
                "candidate_rgba_counts": dict(sorted(row["candidate_rgba_keys"].items())),
                "reference_rgba_counts": dict(sorted(row["reference_rgba_keys"].items())),
            }
        )

    payload = {
        "kind": "olmdistancegradation_16bpc_case0023_residual_split",
        "status": "diagnostic",
        "request_zip": str(REQUEST_ZIP),
        "current_candidate": str(CURRENT_CANDIDATE),
        "residual_px": int(residual.sum()),
        "residual_bbox_xyxy": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
        "inside_distance_buckets": serializable_buckets,
        "candidate_to_reference_endpoint_pairs": dict(sorted(by_pair.items())),
        "examples": examples,
    }
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# OLMDistanceGradation 16bpc case_0023 Residual Split - 2026-06-30",
        "",
        "Residual classification for the current Mac single-case output after the no-post-threshold control probe.",
        "",
        f"- Residual pixels: `{int(residual.sum())}`",
        f"- Residual bbox: `{int(xs.min())},{int(ys.min())} .. {int(xs.max())},{int(ys.max())}`",
        "",
        "| Inside raw EDT | Count | Outside raw EDT values | Candidate RGBA counts | Reference RGBA counts |",
        "| ---: | ---: | --- | --- | --- |",
    ]
    for row in serializable_buckets:
        cand_counts = ", ".join(f"`{k}` x{v}" for k, v in row["candidate_rgba_counts"].items())
        ref_counts = ", ".join(f"`{k}` x{v}" for k, v in row["reference_rgba_counts"].items())
        lines.append(
            f"| `{row['inside_distance']:.6f}` | {row['count']} | `{row['outside_distance_values']}` | {cand_counts} | {ref_counts} |"
        )
    lines.extend(
        [
            "",
            "## Reading",
            "",
            "- All 73 residual pixels stay inside the source alpha region: outside raw EDT is always `0.0`.",
            "- The residual splits cleanly into two inside-distance buckets only:",
            "  - `65px` at `inside EDT = 1.0`, where the current Mac output stays on the Gradation-color endpoint while Windows uses the BG-color endpoint.",
            "  - `8px` at `inside EDT = 36.013885...`, just beyond the configured `Inside Threshold = 36`, where the endpoint choice flips the other way.",
            "- That pattern is much more consistent with unresolved field-prep threshold / plateau ownership inside the `Both` Constant helper than with final writeback or a broad compose bug.",
        ]
    )
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"summary_json={SUMMARY_JSON}")
    print(f"summary_md={SUMMARY_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
