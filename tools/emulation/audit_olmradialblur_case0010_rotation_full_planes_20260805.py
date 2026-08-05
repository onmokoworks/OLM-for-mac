#!/usr/bin/env python3
"""Audit the retained case_0010 actual-AEX Rotation plane fixture."""

from __future__ import annotations

import hashlib
import json
import zlib
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "refs/fixtures/olmradialblur_case0010_rotation_full_planes_20260805"
OUT_JSON = ROOT / "refs/conformance/olmradialblur_case0010_rotation_full_planes_20260805.json"
OUT_MD = ROOT / "refs/conformance/olmradialblur_case0010_rotation_full_planes_20260805.md"
EXPECTED_MANIFEST_SHA256 = "a52ff1a6f3a554ee4613120aa275e6a4ac40b875a0d2194299ec3d03ffef2b6b"
EXPECTED_AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
EXPECTED_INPUT_SHA256 = "7e3527fd86e6dc58ceb3477a4fb86b7d25d27c70060359d6b9c08a70eba075c4"


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def main() -> int:
    manifest_bytes = (FIXTURE / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    checks: dict[str, bool] = {
        "manifest_identity": sha256(manifest_bytes) == EXPECTED_MANIFEST_SHA256,
        "aex_identity": manifest.get("aex_sha256") == EXPECTED_AEX_SHA256,
        "input_identity": manifest.get("input_sha256") == EXPECTED_INPUT_SHA256,
        "stage_order": [stage["stage"] for stage in manifest["stages"]] == [
            "pre_scatter", "post_scatter_pre_gather", "post_normalize",
        ],
    }
    stages = {stage["stage"]: stage for stage in manifest["stages"]}

    def raw(stage: str, plane: str) -> bytes:
        metadata = stages[stage]["planes"][plane]
        encoded = (FIXTURE / metadata["path"]).read_bytes()
        checks[f"{stage}.{plane}.zlib_identity"] = (
            len(encoded) == metadata["zlib_bytes"] and sha256(encoded) == metadata["zlib_sha256"]
        )
        decoded = zlib.decompress(encoded)
        checks[f"{stage}.{plane}.raw_identity"] = (
            len(decoded) == metadata["raw_bytes"] and sha256(decoded) == metadata["raw_sha256"]
        )
        return decoded

    decoded = {
        (stage, plane): raw(stage, plane)
        for stage, value in stages.items()
        for plane in value["planes"]
    }

    def f32(stage: str, plane: str) -> np.ndarray:
        return np.frombuffer(decoded[(stage, plane)], dtype="<f4")

    geometry = {"angular_count": 1800, "radius_count": 1104, "cells": 1987200}
    checks["geometry"] = all(stage["geometry"] == geometry for stage in stages.values())
    pre_polar = f32("pre_scatter", "normalized_or_polar_rgba").reshape(-1, 4)
    post_scatter_polar = f32("post_scatter_pre_gather", "normalized_or_polar_rgba").reshape(-1, 4)
    post_scatter_accum = f32("post_scatter_pre_gather", "accum_rgba").reshape(-1, 4)
    post_scatter_alpha = f32("post_scatter_pre_gather", "slot_0x12")
    post_scatter_max = f32("post_scatter_pre_gather", "max_alpha")
    checks["polar_unchanged_by_scatter"] = np.array_equal(
        pre_polar.view("<u4"), post_scatter_polar.view("<u4"))
    checks["scatter_alpha_equals_max_alpha"] = np.array_equal(
        post_scatter_alpha.view("<u4"), post_scatter_max.view("<u4"))
    seeded = np.empty_like(post_scatter_accum)
    seeded[:, :3] = pre_polar[:, :3] * post_scatter_alpha[:, None]
    seeded[:, 3] = post_scatter_alpha
    checks["post_scatter_seed_relation"] = np.array_equal(
        seeded.view("<u4"), post_scatter_accum.view("<u4"))

    for plane in ("slot_0x10", "slot_0x14"):
        first = f32("pre_scatter", plane).view("<u4")
        checks[f"{plane}_stage_invariant"] = all(
            np.array_equal(first, f32(stage, plane).view("<u4"))
            for stage in ("post_scatter_pre_gather", "post_normalize")
        )

    eligibility = np.frombuffer(
        decoded[("post_scatter_pre_gather", "eligibility_mask")], dtype=np.uint8)
    eligibility_counts = {
        str(int(value)): int(count)
        for value, count in zip(*np.unique(eligibility, return_counts=True))
    }
    checks["eligibility_is_boolean"] = set(eligibility_counts) <= {"0", "1"}

    final_accum = f32("post_normalize", "accum_rgba").reshape(-1, 4)
    final_max = f32("post_normalize", "max_alpha")
    final_polar = f32("post_normalize", "normalized_or_polar_rgba").reshape(-1, 4)
    reconstructed = np.zeros_like(final_polar)
    gate = final_max != np.float32(0.0)
    for channel in range(3):
        np.divide(final_accum[:, channel], final_accum[:, 3],
                  out=reconstructed[:, channel], where=gate)
    reconstructed[:, 3] = final_max
    normalization_diff_words = int(np.count_nonzero(
        reconstructed.view("<u4") != final_polar.view("<u4")))
    checks["normalization_bit_exact"] = normalization_diff_words == 0

    source_alpha = f32("pre_scatter", "slot_0x10")
    size_factor = f32("pre_scatter", "slot_0x14")
    pre_accum = f32("pre_scatter", "accum_rgba")
    pre_max = f32("pre_scatter", "max_alpha")
    pre_scatter_alpha = f32("pre_scatter", "slot_0x12")
    checks["pre_accum_zero"] = bool(np.all(pre_accum == np.float32(0.0)))
    checks["pre_max_zero"] = bool(np.all(pre_max == np.float32(0.0)))
    checks["pre_scatter_alpha_zero"] = bool(np.all(pre_scatter_alpha == np.float32(0.0)))
    checks["size_factor_one"] = bool(np.all(size_factor == np.float32(1.0)))

    result = {
        "kind": "olmradialblur_case0010_rotation_full_planes_20260805",
        "schema": 1,
        "status": "pass" if all(checks.values()) else "fail",
        "fixture": str(FIXTURE.relative_to(ROOT)),
        "manifest_sha256": sha256(manifest_bytes),
        "geometry": geometry,
        "checks": checks,
        "semantics": {
            "normalized_or_polar_rgba": "polar RGBA before workers; normalized polar RGBA after gather",
            "slot_0x10": "sampled source alpha/scalar",
            "slot_0x12": "scatter/prepass alpha",
            "slot_0x14": "sampled size factor (constant one in case_0010)",
            "accum_rgba": "RGBA accumulator",
            "max_alpha": "maximum/output alpha",
            "eligibility_mask": "one-byte boolean polar validity mask",
        },
        "observations": {
            "eligibility_counts": eligibility_counts,
            "source_alpha_non_one_cells": int(np.count_nonzero(source_alpha != np.float32(1.0))),
            "normalization_diff_words": normalization_diff_words,
        },
        "claim_boundary": (
            "case_0010 actual-AEX internal Rotation planes only; this does not prove the legacy "
            "Windows PNG, Mac AE writeback, other parameters, or other bit depths"
        ),
    }
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# OLMRadialBlur case_0010 Rotation full-plane fixture (2026-08-05)",
        "",
        f"- Status: `{result['status']}`",
        f"- Fixture: `{result['fixture']}`",
        f"- Geometry: `{geometry['angular_count']} x {geometry['radius_count']}` ({geometry['cells']} cells)",
        f"- Eligibility mask: `{eligibility_counts}`",
        f"- Source-alpha cells different from 1.0: `{result['observations']['source_alpha_non_one_cells']}`",
        f"- Final normalization differing float32 words: `{normalization_diff_words}`",
        "- Stage contract: pre-scatter polar is preserved through scatter; scatter seeds exact "
        "`RGB=polar.rgb*scatter_alpha, A=scatter_alpha`; gather mutates the accumulator; final "
        "`RGB=accum.rgb/accum.a, A=max_alpha` reconstruction is bit-exact.",
        "- Claim boundary: " + result["claim_boundary"] + ".",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
