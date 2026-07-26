#!/usr/bin/env python3
"""Package a macOS AE-host pixel validation request from existing refs.

The output zip is meant to travel with a packaged macOS plug-in build to an AE
host. It contains input PNGs, expected Windows output PNGs, the reference
manifest, and a small result template. The returned AE render PNGs can then be
checked with scripts/verify_ae_pixel_validation_result.py without launching AE.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path


OLMBLUR_EXACT_CASES = ["case_0001", "case_0002", "case_0004"]
OLMBLUR_RESIDUAL_CASES = ["case_0003", "case_0005", "case_0006", "case_0007"]
OLMBLUR_ALL_CASES = [
    "case_0001",
    "case_0002",
    "case_0003",
    "case_0004",
    "case_0005",
    "case_0006",
    "case_0007",
]
OLMCOLORKEY_RGB_EXACT_CASES = ["case_0001", "case_0002", "case_0003", "case_0004"]
OLMCOLORKEY_EDGETHIN_EXACT_CASES = ["case_0007"]
OLMCOLORKEY_EDGETHIN_RESIDUAL_CASES = ["case_0005", "case_0006"]
OLMCOLORKEY_EDGEBLUR_RESIDUAL_CASES = ["case_0008", "case_0009"]
OLMCOLORKEY_ALL_CASES = [
    "case_0001",
    "case_0002",
    "case_0003",
    "case_0004",
    "case_0005",
    "case_0006",
    "case_0007",
    "case_0008",
    "case_0009",
]
OLMTOONDILATE_CASES = ["case_0001", "case_0002", "case_0003"]
OLMDISTANCEGRADATION_BASIC_CASES = [
    "case_0001",
    "case_0002",
    "case_0003",
    "case_0004",
    "case_0005",
    "case_0006",
    "case_0007",
    "case_0009",
    "case_0015",
    "case_0017",
    "case_0018",
    "case_0019",
]
OLMDISTANCEGRADATION_EXTENDED_CASES = [
    "case_0008",
    "case_0010",
    "case_0011",
    "case_0012",
    "case_0013",
    "case_0014",
    "case_0016",
    "case_0020",
    "case_0021",
    "case_0022",
    "case_0023",
    "case_0024",
    "case_0025",
    "case_0026",
    "case_0027",
    "case_0028",
]
OLMDISTANCEGRADATION_BLUR_CASES = ["case_0029"]
OLMSMOOTHER_CASES = ["case_0001", "case_0002", "case_0003"]
OLMSMOOTHER2_LEGACY_CASES = [
    "case_0001",
    "case_0002",
    "case_0003",
    "case_0004",
    "case_0010",
    "case_0011",
    "case_0012",
]
OLMSMOOTHER2_CURRENT_AEX_CASES = [
    "legacy_case_0001_current_aex",
    "legacy_case_0002_current_aex",
    "legacy_case_0003_current_aex",
    "legacy_case_0004_current_aex",
    "legacy_case_0005_current_aex",
    "legacy_case_0006_current_aex",
    "legacy_case_0007_current_aex",
    "legacy_case_0008_current_aex",
    "legacy_case_0009_v1mode_current_aex",
    "legacy_case_0010_gamma3_current_aex",
    "legacy_case_0011_gamma5_blue_current_aex",
    "legacy_case_0012_gamma5_red_blue_current_aex",
]
OLMSMOOTHER2_NO_KEY_GRID_CASES = [
    "sm2_no_key_s000_r1",
    "sm2_no_key_s025_r1",
    "sm2_no_key_s050_r1",
    "sm2_no_key_s100_r1",
    "sm2_no_key_s000_r2",
    "sm2_no_key_s025_r2",
    "sm2_no_key_s050_r2",
    "sm2_no_key_s100_r2",
    "sm2_no_key_s000_r3",
    "sm2_no_key_s025_r3",
    "sm2_no_key_s050_r3",
    "sm2_no_key_s100_r3",
]
BITDEPTH16_OLMBLUR_CASES = [f"olmblur__{case_id}" for case_id in OLMBLUR_ALL_CASES]
BITDEPTH16_OLMCOLORKEY_CASES = [f"olmcolorkey__{case_id}" for case_id in OLMCOLORKEY_ALL_CASES]
BITDEPTH16_OLMDISTANCEGRADATION_BASIC_CASES = [
    f"olmdistancegradation_basic__{case_id}" for case_id in OLMDISTANCEGRADATION_BASIC_CASES
]
BITDEPTH16_OLMDISTANCEGRADATION_EXTENDED_CASES = [
    f"olmdistancegradation_extended__{case_id}" for case_id in OLMDISTANCEGRADATION_EXTENDED_CASES
]
BITDEPTH16_OLMDISTANCEGRADATION_BLUR_CASES = [
    f"olmdistancegradation_blur__{case_id}" for case_id in OLMDISTANCEGRADATION_BLUR_CASES
]
PRESETS = [
    "olmblur",
    "olmblur_exact",
    "olmcolorkey",
    "olmcolorkey_exact",
    "olmtoondilate",
    "olmtoondilate_exact",
    "olmdistancegradation",
    "olmdistancegradation_exact",
    "olmdistancegradation_extended",
    "olmdistancegradation_extended_exact",
    "olmdistancegradation_blur",
    "olmdistancegradation_blur_exact",
    "olmsmoother",
    "olmsmoother2",
    "olmsmoother2_current_aex",
    "olmsmoother2_no_key_grid",
    "bitdepth16_olmblur_exact",
    "bitdepth16_olmcolorkey_exact",
    "bitdepth16_olmdistancegradation_basic_exact",
    "bitdepth16_olmdistancegradation_extended_exact",
    "bitdepth16_olmdistancegradation_blur_exact",
]
REFERENCE_PROFILES = ["legacy", "normalized-20260618"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preset",
        choices=PRESETS,
        default="olmblur",
        help="Known validation preset to package.",
    )
    parser.add_argument(
        "--reference",
        type=Path,
        default=None,
        help="Reference directory containing reference_manifest.json and PNGs.",
    )
    parser.add_argument(
        "--reference-profile",
        choices=REFERENCE_PROFILES,
        default="legacy",
        help="Known reference set profile. Ignored when --reference is passed.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output zip path. Defaults to /tmp/olm_ae_pixel_validation_<preset>_YYYYMMDD.zip.",
    )
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_manifest(reference: Path) -> dict:
    manifest_path = reference / "reference_manifest.json"
    if not manifest_path.exists():
        raise ValueError(f"missing reference manifest: {manifest_path}")
    with manifest_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("reference manifest top-level JSON must be an object")
    if not isinstance(data.get("cases"), list) or not data["cases"]:
        raise ValueError("reference manifest must contain cases")
    return data


def effect_matches(case: dict, effect_name: str) -> bool:
    for effect in case.get("effects", []):
        if effect.get("name") == effect_name or effect.get("match_name") == effect_name:
            return True
    return False


def find_png(reference: Path, frame: str) -> Path:
    candidates = [reference / frame, reference / "png" / frame, reference / "reference" / frame]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"missing PNG for frame {frame!r} in {reference}")


def profile_reference(root: Path, preset: str, profile: str) -> Path | None:
    if profile == "legacy":
        return None
    normalized_root = root / "refs" / "reports" / "ae_host_validation_20260618_232926" / "normalized_refs"
    refs = {
        "olmblur": normalized_root / "OLMBlur",
        "olmblur_exact": normalized_root / "OLMBlur",
        "olmcolorkey": normalized_root / "OLMColorKey",
        "olmcolorkey_exact": normalized_root / "OLMColorKey",
        "olmtoondilate": normalized_root / "OLMToonDilate",
        "olmtoondilate_exact": normalized_root / "OLMToonDilate",
        "olmdistancegradation": normalized_root / "OLMDistanceGradation_basic",
        "olmdistancegradation_exact": normalized_root / "OLMDistanceGradation_basic",
        "olmdistancegradation_extended": normalized_root / "OLMDistanceGradation_extended",
        "olmdistancegradation_extended_exact": normalized_root / "OLMDistanceGradation_extended",
        "olmdistancegradation_blur": normalized_root / "OLMDistanceGradation_blur",
        "olmdistancegradation_blur_exact": normalized_root / "OLMDistanceGradation_blur",
        "olmsmoother": root / "refs" / "win_references" / "20260604_olm" / "OLMSmoother",
        "olmsmoother2": root / "refs" / "win_references" / "20260605_extra" / "OLMSmoother2",
        "olmsmoother2_no_key_grid": (
            root
            / "refs"
            / "win_references"
            / "olm_reference_return_windows_recapture_20260615"
            / "OLMSmoother2"
        ),
    }
    if profile == "normalized-20260618":
        return refs[preset]
    raise ValueError(f"unsupported reference profile: {profile}")


def preset_config(root: Path, preset: str, reference: Path | None, reference_profile: str) -> dict:
    bitdepth16_reference = (
        root
        / "refs"
        / "win_references"
        / "olm_bitdepth_16bpc_normalized_exact_20260625"
        / "OLMbit-depthconformancebatch"
    )
    configs = {
        "olmblur": {
            "request_id": "ae_pixel_olmblur_20260606",
            "effect_name": "OLM Blur",
            "effect_match_name": "OLM OLM Blur",
            "reference": root / "refs" / "win_references" / "20260604_olm" / "OLMBlur",
            "threshold_groups": [
                {
                    "name": "exact",
                    "case_ids": OLMBLUR_EXACT_CASES,
                    "max_diff": 0,
                    "mean_diff": 0.0,
                    "nonzero_px_percent": 0.0,
                },
                {
                    "name": "residual_max1",
                    "case_ids": OLMBLUR_RESIDUAL_CASES,
                    "max_diff": 1,
                    "mean_diff": 0.01,
                    "nonzero_px_percent": 3.0,
                },
            ],
        },
        "olmblur_exact": {
            "request_id": "ae_pixel_olmblur_exact_20260619",
            "effect_name": "OLM Blur",
            "effect_match_name": "OLM OLM Blur",
            "reference": root / "refs" / "win_references" / "20260604_olm" / "OLMBlur",
            "threshold_groups": [
                {
                    "name": "all_exact",
                    "case_ids": OLMBLUR_ALL_CASES,
                    "max_diff": 0,
                    "mean_diff": 0.0,
                    "nonzero_px_percent": 0.0,
                },
            ],
        },
        "olmcolorkey": {
            "request_id": "ae_pixel_olmcolorkey_20260606",
            "effect_name": "OLM Color Key",
            "effect_match_name": "OLM OLM Color Key",
            "reference": root / "refs" / "win_references" / "20260604_olm" / "OLMColorKey",
            "threshold_groups": [
                {
                    "name": "rgb_exact",
                    "case_ids": OLMCOLORKEY_RGB_EXACT_CASES,
                    "max_diff": 0,
                    "mean_diff": 0.0,
                    "nonzero_px_percent": 0.0,
                },
                {
                    "name": "edgethin_exact",
                    "case_ids": OLMCOLORKEY_EDGETHIN_EXACT_CASES,
                    "max_diff": 0,
                    "mean_diff": 0.0,
                    "nonzero_px_percent": 0.0,
                },
                {
                    "name": "edgethin_residual",
                    "case_ids": OLMCOLORKEY_EDGETHIN_RESIDUAL_CASES,
                    "max_diff": 255,
                    "mean_diff": 0.31,
                    "nonzero_px_percent": 0.49,
                },
                {
                    "name": "edgeblur_residual",
                    "case_ids": OLMCOLORKEY_EDGEBLUR_RESIDUAL_CASES,
                    "max_diff": 255,
                    "mean_diff": 1.26,
                    "nonzero_px_percent": 50.0,
                },
            ],
        },
        "olmcolorkey_exact": {
            "request_id": "ae_pixel_olmcolorkey_exact_20260619",
            "effect_name": "OLM Color Key",
            "effect_match_name": "OLM OLM Color Key",
            "reference": root / "refs" / "win_references" / "20260604_olm" / "OLMColorKey",
            "threshold_groups": [
                {
                    "name": "all_exact",
                    "case_ids": OLMCOLORKEY_ALL_CASES,
                    "max_diff": 0,
                    "mean_diff": 0.0,
                    "nonzero_px_percent": 0.0,
                },
            ],
        },
        "olmtoondilate": {
            "request_id": "ae_pixel_olmtoondilate_20260606",
            "effect_name": "OLM Toon Dilate",
            "effect_match_name": "OLM OLM Toon Dilate",
            "reference": root / "refs" / "win_references" / "20260604_olm" / "OLMToonDilate",
            "threshold_groups": [
                {
                    "name": "guarded",
                    "case_ids": OLMTOONDILATE_CASES,
                    "max_diff": 255,
                    "mean_diff": 3.2,
                    "nonzero_px_percent": 1.7,
                },
            ],
        },
        "olmtoondilate_exact": {
            "request_id": "ae_pixel_olmtoondilate_exact_20260619",
            "effect_name": "OLM Toon Dilate",
            "effect_match_name": "OLM OLM Toon Dilate",
            "reference": root / "refs" / "win_references" / "20260604_olm" / "OLMToonDilate",
            "threshold_groups": [
                {
                    "name": "all_exact",
                    "case_ids": OLMTOONDILATE_CASES,
                    "max_diff": 0,
                    "mean_diff": 0.0,
                    "nonzero_px_percent": 0.0,
                },
            ],
        },
        "olmdistancegradation": {
            "request_id": "ae_pixel_olmdistancegradation_20260606",
            "effect_name": "OLM Distance Gradation",
            "effect_match_name": "OLM Distance Gradation",
            "reference": root / "refs" / "win_references" / "20260605_extra" / "OLMDistanceGradation",
            "threshold_groups": [
                {
                    "name": "basic_guarded",
                    "case_ids": OLMDISTANCEGRADATION_BASIC_CASES,
                    "max_diff": 7,
                    "mean_diff": 0.11,
                    "nonzero_px_percent": 22.0,
                },
            ],
        },
        "olmdistancegradation_exact": {
            "request_id": "ae_pixel_olmdistancegradation_basic_exact_20260619",
            "effect_name": "OLM Distance Gradation",
            "effect_match_name": "OLM Distance Gradation",
            "reference": root / "refs" / "win_references" / "20260605_extra" / "OLMDistanceGradation",
            "threshold_groups": [
                {
                    "name": "basic_exact",
                    "case_ids": OLMDISTANCEGRADATION_BASIC_CASES,
                    "max_diff": 0,
                    "mean_diff": 0.0,
                    "nonzero_px_percent": 0.0,
                },
            ],
        },
        "olmdistancegradation_extended": {
            "request_id": "ae_pixel_olmdistancegradation_extended_20260618",
            "effect_name": "OLM Distance Gradation",
            "effect_match_name": "OLM Distance Gradation",
            "reference": root / "refs" / "win_references" / "20260605_extra" / "OLMDistanceGradation",
            "threshold_groups": [
                {
                    "name": "extended_guarded",
                    "case_ids": OLMDISTANCEGRADATION_EXTENDED_CASES,
                    "max_diff": 255,
                    "mean_diff": 0.72,
                    "nonzero_px_percent": 51.0,
                },
            ],
        },
        "olmdistancegradation_extended_exact": {
            "request_id": "ae_pixel_olmdistancegradation_extended_exact_20260619",
            "effect_name": "OLM Distance Gradation",
            "effect_match_name": "OLM Distance Gradation",
            "reference": root / "refs" / "win_references" / "20260605_extra" / "OLMDistanceGradation",
            "threshold_groups": [
                {
                    "name": "extended_exact",
                    "case_ids": OLMDISTANCEGRADATION_EXTENDED_CASES,
                    "max_diff": 0,
                    "mean_diff": 0.0,
                    "nonzero_px_percent": 0.0,
                },
            ],
        },
        "olmdistancegradation_blur": {
            "request_id": "ae_pixel_olmdistancegradation_blur_20260618",
            "effect_name": "OLM Distance Gradation",
            "effect_match_name": "OLM Distance Gradation",
            "reference": root / "refs" / "win_references" / "20260605_extra" / "OLMDistanceGradation",
            "threshold_groups": [
                {
                    "name": "blur_guarded",
                    "case_ids": OLMDISTANCEGRADATION_BLUR_CASES,
                    "max_diff": 23,
                    "mean_diff": 0.29,
                    "nonzero_px_percent": 12.0,
                },
            ],
        },
        "olmdistancegradation_blur_exact": {
            "request_id": "ae_pixel_olmdistancegradation_blur_exact_20260619",
            "effect_name": "OLM Distance Gradation",
            "effect_match_name": "OLM Distance Gradation",
            "reference": root / "refs" / "win_references" / "20260605_extra" / "OLMDistanceGradation",
            "threshold_groups": [
                {
                    "name": "blur_exact",
                    "case_ids": OLMDISTANCEGRADATION_BLUR_CASES,
                    "max_diff": 0,
                    "mean_diff": 0.0,
                    "nonzero_px_percent": 0.0,
                },
            ],
        },
        "olmsmoother": {
            "request_id": "ae_pixel_olmsmoother_v1_20260619",
            "effect_name": "OLM Smoother",
            "effect_match_name": "OLM Smoother",
            "reference": root / "refs" / "win_references" / "20260604_olm" / "OLMSmoother",
            "threshold_groups": [
                {
                    "name": "exact",
                    "case_ids": OLMSMOOTHER_CASES,
                    "max_diff": 0,
                    "mean_diff": 0.0,
                    "nonzero_px_percent": 0.0,
                },
            ],
        },
        "olmsmoother2": {
            "request_id": "ae_pixel_olmsmoother2_legacy_20260619",
            "effect_name": "OLM Smoother v2",
            "effect_match_name": "OLM Smoother v2",
            "reference": root / "refs" / "win_references" / "20260605_extra" / "OLMSmoother2",
            "threshold_groups": [
                {
                    "name": "legacy_exact",
                    "case_ids": OLMSMOOTHER2_LEGACY_CASES,
                    "max_diff": 0,
                    "mean_diff": 0.0,
                    "nonzero_px_percent": 0.0,
                },
            ],
        },
        "olmsmoother2_current_aex": {
            "request_id": "ae_pixel_olmsmoother2_current_aex_20260726_r3",
            "effect_name": "OLM Smoother v2",
            "effect_match_name": "OLM Smoother v2",
            "bits_per_channel": 8,
            "disable_project_color_management": True,
            "input_alpha_mode": "straight",
            "reference": (
                root
                / "refs"
                / "win_references"
                / "olm_reference_return_windows_smoother2_legacy_full_current_aex_recapture_20260621"
                / "OLMSmootherv2"
            ),
            "input_override": (
                root
                / "refs"
                / "win_references"
                / "olm_reference_return_windows_smoother2_legacy_full_current_aex_recapture_20260621"
                / "OLMSmootherv2"
                / "input\\current_olm_cells.png"
            ),
            "threshold_groups": [
                {
                    "name": "current_aex_8bpc_exact",
                    "case_ids": OLMSMOOTHER2_CURRENT_AEX_CASES,
                    "max_diff": 0,
                    "mean_diff": 0.0,
                    "nonzero_px_percent": 0.0,
                },
            ],
        },
        "olmsmoother2_no_key_grid": {
            "request_id": "ae_pixel_olmsmoother2_no_key_grid_20260619",
            "effect_name": "OLM Smoother v2",
            "effect_match_name": "OLM Smoother v2",
            "reference": (
                root
                / "refs"
                / "win_references"
                / "olm_reference_return_windows_recapture_20260615"
                / "OLMSmoother2"
            ),
            "threshold_groups": [
                {
                    "name": "no_key_grid_exact",
                    "case_ids": OLMSMOOTHER2_NO_KEY_GRID_CASES,
                    "max_diff": 0,
                    "mean_diff": 0.0,
                    "nonzero_px_percent": 0.0,
                },
            ],
        },
        "bitdepth16_olmblur_exact": {
            "request_id": "ae_pixel_bitdepth16_olmblur_exact_20260625",
            "effect_name": "OLM Blur",
            "effect_match_name": "OLM OLM Blur",
            "reference": bitdepth16_reference,
            "threshold_groups": [
                {
                    "name": "16bpc_all_exact",
                    "case_ids": BITDEPTH16_OLMBLUR_CASES,
                    "max_diff": 0,
                    "mean_diff": 0.0,
                    "nonzero_px_percent": 0.0,
                },
            ],
        },
        "bitdepth16_olmcolorkey_exact": {
            "request_id": "ae_pixel_bitdepth16_olmcolorkey_exact_20260625",
            "effect_name": "OLM Color Key",
            "effect_match_name": "OLM Color Key",
            "reference": bitdepth16_reference,
            "threshold_groups": [
                {
                    "name": "16bpc_all_exact",
                    "case_ids": BITDEPTH16_OLMCOLORKEY_CASES,
                    "max_diff": 0,
                    "mean_diff": 0.0,
                    "nonzero_px_percent": 0.0,
                },
            ],
        },
        "bitdepth16_olmdistancegradation_basic_exact": {
            "request_id": "ae_pixel_bitdepth16_olmdistancegradation_basic_exact_20260625",
            "effect_name": "Distance Gradation",
            "effect_match_name": "OLM Distance Gradation",
            "reference": bitdepth16_reference,
            "threshold_groups": [
                {
                    "name": "16bpc_basic_exact",
                    "case_ids": BITDEPTH16_OLMDISTANCEGRADATION_BASIC_CASES,
                    "max_diff": 0,
                    "mean_diff": 0.0,
                    "nonzero_px_percent": 0.0,
                },
            ],
        },
        "bitdepth16_olmdistancegradation_extended_exact": {
            "request_id": "ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625",
            "effect_name": "Distance Gradation",
            "effect_match_name": "OLM Distance Gradation",
            "reference": bitdepth16_reference,
            "threshold_groups": [
                {
                    "name": "16bpc_extended_exact",
                    "case_ids": BITDEPTH16_OLMDISTANCEGRADATION_EXTENDED_CASES,
                    "max_diff": 0,
                    "mean_diff": 0.0,
                    "nonzero_px_percent": 0.0,
                },
            ],
        },
        "bitdepth16_olmdistancegradation_blur_exact": {
            "request_id": "ae_pixel_bitdepth16_olmdistancegradation_blur_exact_20260625",
            "effect_name": "Distance Gradation",
            "effect_match_name": "OLM Distance Gradation",
            "reference": bitdepth16_reference,
            "threshold_groups": [
                {
                    "name": "16bpc_blur_exact",
                    "case_ids": BITDEPTH16_OLMDISTANCEGRADATION_BLUR_CASES,
                    "max_diff": 0,
                    "mean_diff": 0.0,
                    "nonzero_px_percent": 0.0,
                },
            ],
        },
    }
    if preset not in configs:
        raise ValueError(f"unsupported preset: {preset}")
    config = configs[preset]
    selected_reference = reference or profile_reference(root, preset, reference_profile)
    if selected_reference:
        config = {**config, "reference": selected_reference, "reference_profile": reference_profile}
    else:
        config = {**config, "reference_profile": reference_profile}
    return config


def build_readme(request_manifest: dict) -> str:
    groups = request_manifest["threshold_groups"]
    lines = [
        "# OLM AE Pixel Validation Request",
        "",
        f"Request id: `{request_manifest['request_id']}`",
        f"Effect: `{request_manifest['effect_name']}` / `{request_manifest['effect_match_name']}`",
        "",
        "Use the packaged macOS plug-in in After Effects, recreate the listed cases",
        "from `reference_manifest.json`, render each output PNG, and return the PNGs",
        "plus a filled `AE_PIXEL_VALIDATION_RESULT.template.json`.",
        "",
        "Input PNGs are in `input/`; Windows expected outputs are in `expected/`.",
        "Returned render PNGs should keep the same frame names, for example",
        "`case_0001.png`.",
        "",
        "Gate kind: `host_smoke_pixel_tolerance`.",
        "This is an AE-host integration smoke using the listed thresholds, not a final exact-equivalence claim.",
        "",
        "Threshold groups:",
        "",
    ]
    for group in groups:
        lines.append(
            f"- `{group['name']}`: {', '.join(group['case_ids'])}; "
            f"max <= {group['max_diff']}, mean <= {group['mean_diff']}, "
            f"nonzero_px_percent <= {group['nonzero_px_percent']}"
        )
    lines.extend(
        [
            "",
            "Important metadata to record:",
            "",
            "- AE version",
            "- macOS version",
            "- Project Settings renderer / `project_gpu_accel_type` if available",
            "- Whether AE was launched cleanly after installing the plug-in",
            "- Any missing UI parameter, render error, or crash",
            "",
            "Do not use hidden `ADBE Force CPU GPU` as proof of GPU/CPU execution.",
            "Record it only as reference metadata if it appears.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def package_request(config: dict, output: Path) -> None:
    reference = Path(config["reference"]).resolve()
    input_override = Path(config["input_override"]).resolve() if config.get("input_override") else None
    if input_override is not None and not input_override.is_file():
        raise FileNotFoundError(f"missing input override: {input_override}")
    manifest = load_manifest(reference)
    effect_name = config["effect_name"]
    cases = []
    allowed_ids = {case_id for group in config["threshold_groups"] for case_id in group["case_ids"]}
    for index, case in enumerate(manifest.get("cases", []), start=1):
        case_id = case.get("id") or f"case_{index:04d}"
        if case_id not in allowed_ids:
            continue
        if not effect_matches(case, effect_name):
            raise ValueError(f"{case_id} does not contain expected effect {effect_name!r}")
        frame = case.get("frame") or f"{case_id}.png"
        before_frame = case.get("before_effects_frame")
        if not before_frame:
            raise ValueError(f"{case_id} is missing before_effects_frame")
        cases.append({"id": case_id, "frame": frame, "before_effects_frame": before_frame})

    found_ids = {case["id"] for case in cases}
    missing_ids = sorted(allowed_ids - found_ids)
    if missing_ids:
        raise ValueError(f"reference manifest is missing requested cases: {', '.join(missing_ids)}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="olm_ae_pixel_request_") as tmp:
        tmp_path = Path(tmp)
        stage = tmp_path / config["request_id"]
        input_dir = stage / "input"
        expected_dir = stage / "expected"
        input_dir.mkdir(parents=True)
        expected_dir.mkdir()

        shutil.copy2(reference / "reference_manifest.json", stage / "reference_manifest.json")
        for case in cases:
            input_path = input_override or find_png(reference, case["before_effects_frame"])
            shutil.copy2(input_path, input_dir / case["before_effects_frame"])
            shutil.copy2(find_png(reference, case["frame"]), expected_dir / case["frame"])

        request_manifest = {
            "kind": "olm_ae_pixel_validation_request",
            "gate_kind": "host_smoke_pixel_tolerance",
            "request_id": config["request_id"],
            "created_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "reference_profile": config.get("reference_profile", "legacy"),
            "effect_name": config["effect_name"],
            "effect_match_name": config["effect_match_name"],
            "reference_manifest": "reference_manifest.json",
            "input_dir": "input",
            "expected_dir": "expected",
            "candidate_dir_hint": "candidate",
            "bits_per_channel": config.get("bits_per_channel"),
            "disable_project_color_management": bool(config.get("disable_project_color_management", False)),
            "input_alpha_mode": config.get("input_alpha_mode", "default"),
            "input_provenance": (
                {
                    "kind": "shared_source_override",
                    "source_name": input_override.name,
                }
                if input_override is not None
                else {"kind": "before_effects_frame"}
            ),
            "cases": cases,
            "threshold_groups": config["threshold_groups"],
        }
        write_json(stage / "request_manifest.json", request_manifest)
        write_json(
            stage / "AE_PIXEL_VALIDATION_RESULT.template.json",
            {
                "kind": "olm_ae_pixel_validation_result",
                "gate_kind": "host_smoke_pixel_tolerance",
                "request_id": config["request_id"],
                "ae_version": "",
                "macos_version": "",
                "machine": "",
                "project_gpu_accel_type": {"current_name": "", "raw": None},
                "clean_ae_launch_after_install": None,
                "notes": "",
                "candidate_dir": "candidate",
                "cases": [
                    {"id": case["id"], "frame": case["frame"], "rendered": None, "error": ""}
                    for case in cases
                ],
            },
        )
        (stage / "AE_PIXEL_VALIDATION_REQUEST.md").write_text(build_readme(request_manifest), encoding="utf-8")

        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(stage.rglob("*")):
                archive.write(path, path.relative_to(tmp_path))


def main() -> int:
    args = parse_args()
    root = repo_root()
    config = preset_config(root, args.preset, args.reference, args.reference_profile)
    output = args.output
    if output is None:
        stamp = dt.datetime.now().strftime("%Y%m%d")
        output = Path("/tmp") / f"olm_ae_pixel_validation_{args.preset}_{stamp}.zip"
    output = output.resolve()

    try:
        package_request(config, output)
    except Exception as exc:  # noqa: BLE001 - command-line packager should show exact failure.
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    print(f"wrote {output}")
    print(f"- preset: {args.preset}")
    print(f"- request_id: {config['request_id']}")
    print(f"- reference_profile: {config.get('reference_profile', 'legacy')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
