#!/usr/bin/env python3
"""Build the single Windows-Codex OLM reference campaign handoff."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ID = "olm_windows_all_plugins_reference_campaign_20260731_r1"
DEST_ROOT = ROOT / "handoffs" / "windows_batch"
PACKAGE_DIR = DEST_ROOT / CAMPAIGN_ID
PACKAGE_ZIP = DEST_ROOT / f"{CAMPAIGN_ID}.zip"
PACKAGE_ZIP_SHA = DEST_ROOT / f"{CAMPAIGN_ID}.zip.sha256"
FIXED_ZIP_TIME = (2026, 7, 31, 0, 0, 0)


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        fail(f"refusing to overwrite {path}")
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def verified_source(relative: str, expected_sha256: str) -> Path:
    path = ROOT / relative
    if not path.exists() or not path.is_file() or path.is_symlink():
        fail(f"missing, non-file, or symlink source: {relative}")
    resolved = path.resolve(strict=True)
    try:
        resolved.relative_to(ROOT.resolve(strict=True))
    except ValueError:
        fail(f"source escapes repository: {relative}")
    actual = sha256(resolved)
    if actual != expected_sha256:
        fail(f"source SHA-256 mismatch: {relative}: {actual}")
    return resolved


def copy_verified(relative: str, expected_sha256: str, destination: Path) -> dict[str, object]:
    source = verified_source(relative, expected_sha256)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        fail(f"refusing to overwrite {destination}")
    shutil.copyfile(source, destination, follow_symlinks=False)
    os.chmod(destination, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    actual = sha256(destination)
    if actual != expected_sha256:
        fail(f"copied SHA-256 mismatch: {destination}")
    return {
        "member": destination.relative_to(PACKAGE_DIR).as_posix(),
        "sha256": actual,
        "bytes": destination.stat().st_size,
        "source_repository_path": relative,
    }


INPUT_SOURCES = [
    (
        "final_random_float_grid.exr",
        "refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMDirectionalBlur/"
        "olm_bitdepth_32bpc_olmdirectionalblur_exr_20260710__software_32bpc__fr24__"
        "final_random10_olm_directionalblur_01_before_effects.exr",
        "70c23365b3984f218c5030a3608a21bd364bda6ea287d8730ef361940ddfe82f",
        "1920x1080 uncompressed FLOAT A/B/G/R; shared odd-case final-random source.",
    ),
    (
        "final_random_float_alternate.exr",
        "refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMDirectionalBlur/"
        "olm_bitdepth_32bpc_olmdirectionalblur_exr_20260710__software_32bpc__fr24__"
        "final_random10_olm_directionalblur_02_before_effects.exr",
        "b51cbe11178adaacbd761ce8b49a9c229b09d75abf4185b7ddc52766d1a19678",
        "1920x1080 uncompressed FLOAT A/B/G/R; shared even-case final-random source.",
    ),
    (
        "distancegradation_float_source.exr",
        "refs/win_references/20260710_190500__ae26_3_32bpc_recap/"
        "OLMbit-depthconformancebatch/"
        "olm_bitdepth_32bpc_full_probe_exr_rerun_20260703__software_32bpc__fr24__"
        "olmdistancegradation_basic__case_0001_before_effects.exr",
        "6b1972a25a1a336f52fe10d627fbe710d97578329112878d0c17a2f6607b6e97",
        "1920x1080 uncompressed FLOAT source shared by the canonical 29-case set.",
    ),
    (
        "distancegradation_nonopaque_rgba8.png",
        "refs/win_references/DistanceGradation/DistanceGradation/case_0001_before_effects.png",
        "9d96a359d987774a398ec27e224650fda83fa00ae3c14bd04b87e2402ea34265",
        "1920x1080 RGBA8 source with alpha coverage from 0 through 1.",
    ),
    (
        "opaque_cells_rgba8.png",
        "refs/win_references/olm_reference_return_windows_20260611/OLMDirectionalBlur/"
        "directionalblur_context_scale_20260606__software__fr24__"
        "db_angle0_no_tail_no_size_before_effects.png",
        "1ec1c0fa672865b43f7869eec196e0442ab77ce3e4d4711a6cb2e6f6e6844021",
        "1920x1080 RGBA8 opaque-cell fixture.",
    ),
    (
        "hard_alpha_edges_rgba8.png",
        "refs/win_references/20260711_directionalblur_front_alpha_current_2025_aex/input/"
        "directionalblur_context_scale_20260606__software__fr24__"
        "db_angle0_alpha_fade_hard_edges_before_effects.png",
        "e8c3c76a746936564bf1aa3b63a47182c0875b14c63024270445ae14dbb3e696",
        "1920x1080 RGBA8 hard-alpha-edge fixture.",
    ),
    (
        "alpha_ramp_rgba8.png",
        "refs/win_references/olm_reference_return_windows_20260611/OLMDirectionalBlur/"
        "directionalblur_context_scale_20260606__software__fr24__"
        "db_diagonal_alpha_ramp_before_effects.png",
        "13da843a8282dda1e26491c4dd9e9a9b9fd34eea80b5380f13897fac664d14d5",
        "1920x1080 RGBA8 alpha-ramp fixture; mean alpha 0.5.",
    ),
    (
        "radial_alpha_grid_rgba8.png",
        "refs/win_references/olm_reference_return_windows_recapture_20260615/"
        "OLMRadialBlur_sizevar/"
        "radialblur_inner_size_variation_20260606__software__fr24__"
        "rb_inner_alpha_sv050_edge025_before_effects.png",
        "a5e7a85130282a726861a2b4bd7685e546ea445a77a1e0db4cad2fb36a964de1",
        "1920x1080 RGBA8 radial alpha-grid fixture.",
    ),
    (
        "colorkey_replace_grid_rgba8.png",
        "refs/win_references/olm_reference_return_windows_20260614/OLMColorKey/"
        "olmcolorkey_replace_colorspace_20260606__software__fr24__"
        "ck_edgeblur_replace_red_with_blue_before_effects.png",
        "43ba897e5058791b0bb1f5412e1ce5600cfe56b515f7a9bc21a853a57c53a3fa",
        "1920x1080 RGBA8 color-grid fixture for the ColorKey replace/color-space set.",
    ),
    (
        "distancegradation_bg_off_rgba8.png",
        "refs/win_references/olmdistancegradation_16bpc_bg_compose_variants_20260626/"
        "DistanceGradation/renders/"
        "olmdistancegradation_16bpc_bg_compose_variants_20260626__software_16bpc__"
        "fr24__olmdistancegradation_case_0020_bg_off_variant_before_effects.png",
        "0fd99810315ac01a2cf38abf9e157418d4552f38e9d237c6677975eb2cc3755e",
        "1920x1080 RGBA8 source for the historical DistanceGradation background-off twins.",
    ),
    (
        "blur_cases_0001_0004_rgba8.png",
        "refs/win_references/20260604_olm/OLMBlur/case_0001_before_effects.png",
        "cc1bf1aa128dea6197405ee722c66198fb5fcbc213bf2569c7af9f30be4fa4f4",
        "960x540 RGBA8 normalized Blur cases 0001-0004 source.",
    ),
    (
        "shared_blur_colorkey_rgba8.png",
        "refs/win_references/20260604_olm/OLMBlur/case_0005_before_effects.png",
        "7e3527fd86e6dc58ceb3477a4fb86b7d25d27c70060359d6b9c08a70eba075c4",
        "1920x1080 RGBA8 normalized Blur 0005-0007 and ColorKey 0001-0008 source.",
    ),
    (
        "colorkey_case0009_rgba16.png",
        "refs/win_references/20260604_olm/OLMColorKey/case_0009_before_effects.png",
        "de522ffb0feb856a866e0b61049516f227d52280981c1d42401a768e2b05a3d0",
        "1920x1080 RGBA16 normalized ColorKey case 0009 source.",
    ),
    (
        "toondilate_case0001_rgba8.png",
        "refs/win_references/20260604_olm/OLMToonDilate/case_0001_before_effects.png",
        "b91b57724e57bfc9b8e751c101dec1febf90221662844e09335b6f72a2850cd8",
        "960x540 nonopaque RGBA8 ToonDilate case 0001 source.",
    ),
    (
        "toondilate_case0002_rgba8.png",
        "refs/win_references/20260604_olm/OLMToonDilate/case_0002_before_effects.png",
        "6eada5d43f9624c5d81b7a7a17ad502b7bcd88c990137cdd5b62d523e4fc2082",
        "960x540 nonopaque RGBA8 ToonDilate case 0002 source.",
    ),
    (
        "toondilate_case0003_rgba16.png",
        "refs/win_references/20260604_olm/OLMToonDilate/case_0003_before_effects.png",
        "34923bcb1eaf444b0788977907b0fec05115d93864f8ae6f11bfbe04685a24be",
        "1920x1080 nonopaque RGBA16 ToonDilate case 0003 source.",
    ),
    (
        "smoother_v1_case0001_rgba8.png",
        "refs/win_references/20260604_olm/OLMSmoother/case_0001_before_effects.png",
        "166cafc8aaa2bb2d78ed26a12fe95b6dcf0f6eeeabd7f3a4daaf0ceece500e4c",
        "960x540 RGBA8 Smoother v1 canonical case 0001 source.",
    ),
    (
        "smoother_v1_case0002_rgba8.png",
        "refs/win_references/20260604_olm/OLMSmoother/case_0002_before_effects.png",
        "dd9c1adc8920f6785e5d4449545c29e5f3b60761244dae6d34293b401e0f0c9c",
        "960x540 RGBA8 Smoother v1 canonical case 0002 source.",
    ),
    (
        "smoother_v1_case0003_rgba8.png",
        "refs/win_references/20260604_olm/OLMSmoother/case_0003_before_effects.png",
        "7dc50c17733999bb952a69f65d6dfe60249694dd449fd9a0acb67411ba30570b",
        "960x540 RGBA8 Smoother v1 canonical case 0003 source.",
    ),
    (
        "smoother_v1_float_odd.exr",
        "refs/mac_validation_runs/olmsmoother_v1_32bpc_20260731_run8/"
        "final_random10_olm_smoother_01__no_effect_control.exr",
        "b67a1ef1d1f3c8572d6d49e61b72e77e6c90c59b16bef143f4ab91becc4e2408",
        "Exact Mac run-8 control for odd Smoother-v1 final-random cases.",
    ),
    (
        "smoother_v1_float_even.exr",
        "refs/mac_validation_runs/olmsmoother_v1_32bpc_20260731_run8/"
        "final_random10_olm_smoother_02__no_effect_control.exr",
        "4ac631c5773d5589b2d04943aba0a6fcaa7a9f29b8d8a2b94663385a2f06e5c8",
        "Exact Mac run-8 control for even Smoother-v1 final-random cases.",
    ),
    (
        "preserve_rgb_template.aep",
        "refs/fixtures/olmsmoother2_32bpc_preserve_rgb_input_template_20260726.aep",
        "51fd5403b0a43825f0f6d189c49154ad756f4c565498f733c1fb725377583679",
        "Hash-bound Preserve-RGB AEP with OLM_COLOR_PROBE_INPUT and OLM_COLOR_PROBE_COMP.",
    ),
    (
        "toondilate_typed_procedural_fixture.jsx",
        "scripts/ae_generate_32bpc_typed_procedural_fixture.jsx",
        "665fa9f05fe652895cb7c7f94064f2471ef992c74751cd11a4254aeb00529d82",
        "Canonical 64x64 typed procedural fixture generator.",
    ),
]


AEX_SOURCES = {
    "ColorKeep.aex": "6d3718868c6c876c3bb370b19cb2bb3c4f89a3a479c29f03ae0d032a5d043b86",
    "DistanceGradation.aex": "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae",
    "OLMBlur.aex": "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b",
    "OLMColorKey.aex": "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c",
    "OLMDirectionalBlur.aex": "d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e",
    "OLMKiraKira.aex": "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7",
    "OLMRadialBlur.aex": "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb",
    "OLMSmoother.aex": "6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82",
    "OLMSmoother2.aex": "7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7",
    "OLMToonDilate.aex": "c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3",
}


REUSE_SOURCES = [
    (
        f"refs/conformance/olmblur_32bpc_case000{case}_ae_exact_20260727.json",
        digest,
        "OLMBlur",
        "32bpc canonical declared case; do not rerender for this campaign.",
    )
    for case, digest in enumerate(
        (
            "bfc16951adcc91fe9e1fbbdcbfd24ff3c7a0962a018fde9423463610382c0fbd",
            "fbafcfcd23490ac98c1ca188488c7bd73c63fe28a202322bc10589e0ff41ca15",
            "47ce1c9cf1d077008e6cdb1a3c3ecd13ebf7f5a5bf4d2b23b478064c3333e19e",
            "664ce93195accc624d96ae81d25d138d86a799592d95453b5053c5be181ae284",
            "cdb233198f44364c913fa1efbaf2b238918c087578b499fd2d89bceddbcf794b",
            "542fd65d9d3730dabd564ea1c486e4c437016f49c32becae34ecd4dbc3b31cd0",
            "04759826e849250c33b0bbcca66027a0755b32bb92115eaa81d614fd3f1760ec",
        ),
        1,
    )
] + [
    (
        "refs/conformance/olmcolorkey_32bpc_all9_ae_exact_20260728.json",
        "09543d5022e4f439eefe1d977d078e0aaf29726bbce3e7050b280955c333f84d",
        "OLMColorKey",
        "32bpc canonical cases 0001-0009; do not rerender.",
    ),
    (
        "refs/conformance/olmtoondilate_32bpc_typed_procedural_ae_exact_20260728.json",
        "4d20742f0e0582d73eb072f656215a582ac42f65518a4ae6e1e5466b1219fbea",
        "OLMToonDilate",
        "32bpc 64x64 Search Radius 13 typed profile only; do not generalize.",
    ),
    (
        "refs/conformance/olmsmoother2_16bpc_case01_10_ae_exact_20260727.json",
        "c992b7d5daf4045711a44555a3aa7dfd16ae25e2fc77a5fa926994460b244047",
        "OLMSmoother2",
        "16bpc Preserve-RGB final-random cases 01-10; do not rerender.",
    ),
    (
        "refs/conformance/olmsmoother2_32bpc_case01_10_ae_exact_20260727.json",
        "51d795a9fa1b8f113938699e5e3e441b827350d4180815ceb5a7f0b70e78caff",
        "OLMSmoother2",
        "32bpc Preserve-RGB final-random cases 01-10; do not rerender.",
    ),
]


LANES = [
    {
        "plugin": "OLMDistanceGradation",
        "priority": 1,
        "status": "thin_blocking",
        "rows_estimate": 99,
        "required": [
            "canonical 29 cases at 8/16/32bpc",
            "four unique background-off twins from the eight-case background request at 8/16/32bpc",
        ],
        "request_seeds": [
            "olm_final_random10_distance_gradation_20260629.json",
            "olmdistancegradation_16bpc_bg_compose_variants_20260626.json",
            "olm_bitdepth_32bpc_full_probe_exr_rerun_20260703.json",
        ],
    },
    {
        "plugin": "OLMDirectionalBlur",
        "priority": 1,
        "status": "thin_blocking",
        "rows_estimate": 54,
        "required": [
            "final-random 10 at 8/16/32bpc",
            "all eight directionalblur_context_scale cases at 8/16/32bpc",
        ],
        "request_seeds": [
            "olm_final_random10_olm_directionalblur_20260629.json",
            "directionalblur_context_scale_20260606.json",
            "olm_bitdepth_32bpc_olmdirectionalblur_exr_20260710.json",
        ],
    },
    {
        "plugin": "OLMRadialBlur",
        "priority": 1,
        "status": "thin_blocking",
        "rows_estimate": 90,
        "required": [
            "final-random 10 at 8/16/32bpc",
            "all ten Inner cases at 8/16/32bpc",
            "all eight Inner/Size Variation cases at 8/16/32bpc",
            "normalized Zoom case 0009 and tiny Rotation case 0010 at 8/16/32bpc",
        ],
        "request_seeds": [
            "olm_final_random10_olm_radialblur_20260629.json",
            "radialblur_inner_20260605.json",
            "radialblur_inner_size_variation_20260606.json",
            "olmradialblur_case0010_gpu0_software_recapture_20260706.json",
            "olm_bitdepth_32bpc_olmradialblur_exr_20260710.json",
        ],
    },
    {
        "plugin": "OLMKiraKira",
        "priority": 1,
        "status": "thin_blocking",
        "rows_estimate": 72,
        "required": [
            "final-random 10 at 8/16/32bpc",
            "nine single-ray/mode cases at 8/16/32bpc",
            "four Strength=0 brightness cases at 8/16/32bpc",
            "one same-source Approximated Input off/on case at 8/16/32bpc",
        ],
        "request_seeds": [
            "olm_final_random10_olm_kira_kira_20260629.json",
            "kirakira_single_ray_20260606.json",
            "kirakira_strength0_brightness_20260614.json",
            "olm_bitdepth_32bpc_olmkirakira_exr_20260710.json",
        ],
    },
    {
        "plugin": "OLMSmoother v1",
        "priority": 1,
        "status": "thin_blocking",
        "rows_estimate": 19,
        "required": [
            "canonical cases 0001-0003 at 8/16/32bpc",
            "32bpc final-random 10 from the exact bundled odd/even FLOAT controls",
        ],
        "request_seeds": [
            "olmsmoother_v1_bitdepth_16_32bpc_software_20260715.json",
            "olm_bitdepth_32bpc_olmsmoother_v1_exr_20260710.json",
            "olm_final_random10_olm_smoother_20260629.json",
        ],
        "special_contract": (
            "Use inputs/smoother_v1_float_odd.exr for odd final-random case IDs and "
            "inputs/smoother_v1_float_even.exr for even IDs through "
            "inputs/preserve_rgb_template.aep. Old Windows controls are rejected."
        ),
    },
    {
        "plugin": "OLMBlur",
        "priority": 2,
        "status": "uniform_provenance_refresh",
        "rows_estimate": 14,
        "required": ["canonical seven cases at 8/16bpc"],
        "reuse": ["all seven canonical 32bpc cases"],
        "request_seeds": ["olm_bitdepth_16bpc_normalized_exact_20260625.json"],
    },
    {
        "plugin": "OLMColorKey",
        "priority": 2,
        "status": "uniform_provenance_refresh",
        "rows_estimate": 69,
        "required": [
            "canonical nine cases at 8/16bpc",
            "all 17 replace/color-space cases at 8/16/32bpc",
        ],
        "reuse": ["canonical nine 32bpc cases"],
        "request_seeds": [
            "olm_bitdepth_16bpc_normalized_exact_20260625.json",
            "olmcolorkey_replace_colorspace_20260606.json",
        ],
    },
    {
        "plugin": "OLMToonDilate",
        "priority": 2,
        "status": "uniform_provenance_refresh",
        "rows_estimate": 6,
        "required": ["canonical cases 0001-0003 at 8/16bpc"],
        "reuse": ["32bpc 64x64 Search Radius 13 typed profile only"],
        "request_seeds": [
            "olm_bitdepth_16bpc_toondilate_exact_20260703.json",
            "olm_bitdepth_32bpc_toondilate_float_20260710.json",
        ],
    },
    {
        "plugin": "OLMSmoother2",
        "priority": 2,
        "status": "uniform_provenance_refresh",
        "rows_estimate": 24,
        "required": [
            "8bpc legacy/key/gamma 12",
            "8bpc no-key 12",
        ],
        "reuse": ["final-random 10 at 16bpc and 32bpc"],
        "request_seeds": [
            "smoother2_legacy_full_current_aex_recapture_20260621.json",
            "smoother2_no_key_grid_20260606.json",
        ],
    },
    {
        "plugin": "ColorKeep",
        "priority": 3,
        "status": "thin_support_reference",
        "rows_estimate": 9,
        "required": [
            "one untouched-default case at 8/16/32bpc after a live full-leaf snapshot",
            "one explicit two-color identity case at 8/16/32bpc",
            "one explicit two-color case at 8/16/32bpc",
        ],
        "fixtures": [
            "inputs/blur_cases_0001_0004_rgba8.png",
            "inputs/opaque_cells_rgba8.png",
        ],
        "expected_plugin_leaf_count": 101,
        "expected_setup_from_binary_and_aexcompat": {
            "num_params_including_input": 102,
            "enabled_color_num": {
                "property_index": 1,
                "disk_id": 1,
                "value_type": "slider_integer",
                "range": [0, 100],
                "default": 1,
            },
            "colors": {
                "property_indices": [2, 101],
                "disk_ids": [2, 101],
                "count": 100,
                "display_name": "Color",
                "value_type": "color",
                "default_rgba": [0.0, 0.0, 0.0, 1.0],
            },
            "claim_boundary": (
                "AEXCompat proves setup/defaults and bounded 8bpc behavior; "
                "Windows AE must still capture every requested depth."
            ),
        },
        "cases": [
            {
                "case_id": "colorkeep_default",
                "fixture": "inputs/blur_cases_0001_0004_rgba8.png",
                "parameter_writes": [],
                "intentional_noop": False,
                "purpose": (
                    "bind the actual 2025-AEX parameter surface/defaults and the "
                    "default-black positive render"
                ),
            },
            {
                "case_id": "colorkeep_two_color_identity",
                "fixture": "inputs/blur_cases_0001_0004_rgba8.png",
                "parameter_writes": [
                    {
                        "property_index": 1,
                        "display_name": "Enabled Color Num",
                        "value_type": "slider_integer",
                        "value": 2,
                    },
                    {
                        "property_index": 2,
                        "display_name": "Color",
                        "value_type": "color",
                        "value_rgba": [0.0, 0.0, 0.0, 1.0],
                        "sample_rgba8": [0, 0, 0, 255],
                    },
                    {
                        "property_index": 3,
                        "display_name": "Color",
                        "value_type": "color",
                        "value_rgba": [1.0, 0.0, 0.0, 1.0],
                        "sample_rgba8": [255, 0, 0, 255],
                    },
                ],
                "intentional_noop": True,
                "purpose": (
                    "retain both exact source colors; the nontrivial sibling below "
                    "is required for effect attribution"
                ),
            },
            {
                "case_id": "colorkeep_opaque_cells_red_darkgray",
                "fixture": "inputs/opaque_cells_rgba8.png",
                "parameter_writes": [
                    {
                        "property_index": 1,
                        "display_name": "Enabled Color Num",
                        "value_type": "slider_integer",
                        "value": 2,
                    },
                    {
                        "property_index": 2,
                        "display_name": "Color",
                        "value_type": "color",
                        "value_rgba": [
                            0.8627450980392157,
                            0.27450980392156865,
                            0.27450980392156865,
                            1.0,
                        ],
                        "sample_rgba8": [220, 70, 70, 255],
                    },
                    {
                        "property_index": 3,
                        "display_name": "Color",
                        "value_type": "color",
                        "value_rgba": [
                            0.11764705882352941,
                            0.11764705882352941,
                            0.11764705882352941,
                            1.0,
                        ],
                        "sample_rgba8": [30, 30, 30, 255],
                    },
                ],
                "intentional_noop": False,
                "purpose": (
                    "retain the red cells and dark ink while rejecting the other "
                    "flat colors"
                ),
            },
        ],
        "known_mac_divergence": (
            "The current Mac source declares Enabled Color Num range 1..100, "
            "default 100, and white color defaults. Do not use those values as the "
            "Windows contract; the 2025 Windows AEX setup above is authoritative."
        ),
        "special_contract": (
            "ColorKeep has no historical request corpus. First capture the live 101-leaf "
            "surface without writes. Apply the explicit cases only if indices 1/2/3, names, "
            "types, defaults, and post-write readback match exactly; otherwise fail closed."
        ),
        "request_seeds": [],
    },
]


README = f"""# {CAMPAIGN_ID}

This is one consolidated, non-executing handoff for Windows Codex. It contains
the exact input bytes selected for this campaign, the exact Windows AEX
binaries, all 40 historical request JSONs as case-definition seeds, the modern
evidence that should be reused, and the fail-closed return contract.

## Why this recapture exists

The old Windows corpus is broad but thin. The audit found 57 imported
`reference_manifest.json` files; none binds an input hash, loaded-AEX proof, or
the render process, and only ten record an output contract. Of 40 historical
request JSONs, only one pins both a source and AEX hash, and none binds the
actual rendering process. Those artifacts remain useful for case definitions
and diagnosis, but most cannot independently promote a new cross-host AE-exact
claim.

This campaign closes that provenance gap in one automated pass. It is not a
request for manual case-by-case UI work. Windows Codex should construct a
headless batch around fresh `aerender` processes and return one consolidated
archive only.

## Scope

- Priority 1: OLMDistanceGradation, OLMDirectionalBlur, OLMRadialBlur,
  OLMKiraKira, and OLMSmoother v1.
- Priority 2: uniform low-depth recapture for OLMBlur, OLMColorKey,
  OLMToonDilate, and OLMSmoother2.
- Priority 3: a nine-row ColorKeep discovery/reference lane. ColorKeep remains
  support-only and excluded from the nine-plugin release population, but this
  campaign now captures its thin Windows surface instead of leaving it empty.
- `CAMPAIGN_MANIFEST.json` is authoritative for the requested rows. Historical
  files under `requests/` are seeds, not trusted provenance.

Estimated campaign size is 456 case/depth rows and 912 off/on renders. This is
deliberately automated. Each row still needs its own fresh identity and render
process so cache reuse cannot masquerade as evidence.

## Non-negotiable exactness rule

CLI or AEXCompat exactness is intermediate evidence, never a substitute for AE
exactness. A row is eligible only when the same hash-bound input, parameters,
project/color contract, and output contract produce:

1. an exact no-effect control, and
2. an exact effect-on output,

with zero raw FLOAT32 word mismatch. A missing or failed control prevents
effect attribution.

## Before doing any work

1. Run `powershell -ExecutionPolicy Bypass -File .\\VERIFY_REQUEST.ps1`.
2. Read `WINDOWS_CODEX_PROMPT.md`, `CAMPAIGN_MANIFEST.json`, and
   `RETURN_CONTRACT.json`.
3. Do not run anything automatically merely because this ZIP was extracted.
4. Do not return partial per-plugin ZIPs. Keep checkpoints in the Windows
   workspace and return one parent ZIP after all requested rows have a terminal
   pass/fail record.
"""


WINDOWS_CODEX_PROMPT = f"""# Prompt for Windows Codex

You own the Windows reference side of the OLM Plugins campaign
`{CAMPAIGN_ID}`.

At the start, call `create_goal` with this objective:

> Capture a single modern Windows AE Software reference corpus for all
> in-scope OLM plugins, using the exact bundled inputs and AEX binaries, with
> hash-bound off/on renders, full parameter readback, project/color/output
> settings, and process/module evidence sufficient for fail-closed Mac
> cross-host comparison.

## Intent and history

The Mac port is being advanced from binary-grounded IR, runtime/CPU evidence,
and bit-depth conformance. Several declared slices are already exact, while the
five priority-1 plugins are blocked by either thin Windows provenance or
unfinished Mac algorithms. Earlier Windows runs often captured images and
parameters but did not bind the source bytes, loaded AEX, render child, output
settings, and same-run off/on lineage together. This campaign is designed to
fix that once, in bulk.

## What to build on Windows

Build a fail-closed batch runner from `CAMPAIGN_MANIFEST.json`; do not manually
operate hundreds of cases. Extraction and verification must be read-only.
Execution begins only when the Windows user explicitly starts the batch.

- Adobe After Effects must be exactly 26.3x87.
- Renderer must be Software, raw value 1816.
- Working space must be None; linear blending and blend-colors-using-1.0-gamma
  must be false.
- Run project depths 8, 16, or 32 exactly as declared.
- Primary output at every depth is uncompressed scanline OpenEXR with physical
  channels A/B/G/R, each channel FLOAT type 2. PNG may exist only as preview.
- Every case/depth row gets a fresh nonce, a fresh unique project/effect
  identity, exactly two embedded render-queue items (effect disabled and
  enabled), and one fresh `aerender` process.
- Do not use one long-lived AE render process for the whole campaign.
- Do not require the user to toggle modals. If a dialog or plugin-load problem
  prevents headless execution, fail that row and preserve diagnostics.

## Bind before and after each render

- bundled input member/path/SHA-256;
- Preserve RGB and alpha/premultiplication interpretation;
- comp size, pixel aspect, frame rate, frame, project depth, renderer, and all
  project color settings;
- effect display name and match name;
- every plugin leaf as `(property_index, match_name, display_name, value_type,
  value)`, with expected, pre-render, and post-render snapshots;
- OutputModule `getSettings(GetSettingsFormat.STRING)` before and after;
- EXR header inspection;
- AfterFX/aerender path, SHA-256, version, PID, start time, command, and nonce;
- ETW parent-to-real-AfterFX-child mapping and that child's AEX image load and
  unload, including the exact bundled AEX SHA-256.

OLMColorKey's recent accepted plugin-only count is 219. Standard AE compositing
options are separate and must not be mixed into that count.

ColorKeep is a support-only discovery lane. Its expected plugin-only leaf count
is 101 (102 params including the automatic input). The Windows 2025 AEX setup
has Enabled Color Num range 0–100/default 1 and 100 black color defaults; the
current Mac source's range/defaults differ and are not the Windows contract.
Explicit writes are permitted only after the live indices, names, types, and
untouched defaults have been captured and the declared indices have matched;
otherwise fail closed without guessing.

## Cache and output barrier

- Output paths must not preexist.
- Output timestamps must postdate process start.
- Render duration must be nonzero.
- Hash only after AE has closed/finalized the EXR.
- Effect-on must differ raw from control unless the row is explicitly tagged
  `intentional_noop`; an intentional no-op also needs a positive-effect sibling
  for that plugin/depth.

## Return

Use exactly the tree in `RETURN_CONTRACT.json`. Produce one consolidated parent
ZIP, its SHA-256 sidecar, and no smaller return ZIPs. A failed row still needs a
terminal `RETURN_STATUS.json` entry and preserved logs/evidence. Never mark a
row answered or exact when any required hash, readback, process proof, or raw
output is missing.
"""


VERIFY_REQUEST_PS1 = r"""$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Checksums = Join-Path $Root 'CHECKSUMS.sha256'
if (-not (Test-Path -LiteralPath $Checksums -PathType Leaf)) {
  throw 'CHECKSUMS.sha256 missing'
}
$Expected = @{}
Get-Content -LiteralPath $Checksums | ForEach-Object {
  if ($_ -notmatch '^([0-9a-f]{64})  (.+)$') { throw "bad checksum row: $_" }
  $hash = $Matches[1]
  $rel = $Matches[2].Replace('\','/')
  if ($rel.StartsWith('/') -or $rel.Contains('../') -or $rel.Contains('..\\')) {
    throw "unsafe checksum path: $rel"
  }
  if ($Expected.ContainsKey($rel)) { throw "duplicate checksum path: $rel" }
  $Expected[$rel] = $hash
}
$Actual = @{}
Get-ChildItem -LiteralPath $Root -File -Recurse | ForEach-Object {
  $rel = $_.FullName.Substring($Root.Length + 1).Replace('\','/')
  if ($rel -eq 'CHECKSUMS.sha256') { return }
  if ($Actual.ContainsKey($rel)) { throw "duplicate actual path: $rel" }
  $Actual[$rel] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
}
if ($Actual.Count -ne $Expected.Count) {
  throw "file count mismatch expected=$($Expected.Count) actual=$($Actual.Count)"
}
foreach ($rel in $Expected.Keys) {
  if (-not $Actual.ContainsKey($rel)) { throw "missing file: $rel" }
  if ($Actual[$rel] -ne $Expected[$rel]) { throw "hash mismatch: $rel" }
}
Write-Host "[PASS] request verified: $($Expected.Count) files"
"""


RETURN_CONTRACT = {
    "schema_version": 1,
    "campaign_id": CAMPAIGN_ID,
    "single_consolidated_return_only": True,
    "required_tree": [
        "BATCH_MANIFEST.json",
        "INPUTS.sha256",
        "AEX_EXPECTED.sha256",
        "REUSE_INDEX.json",
        "requests/",
        "inputs/",
        "projects/",
        "outputs/<plugin>/<depth>/<case>/no_effect.exr",
        "outputs/<plugin>/<depth>/<case>/effect_on.exr",
        "evidence/<plugin>/<depth>/<case>/params_expected.json",
        "evidence/<plugin>/<depth>/<case>/params_before.json",
        "evidence/<plugin>/<depth>/<case>/params_after.json",
        "evidence/<plugin>/<depth>/<case>/project_before.json",
        "evidence/<plugin>/<depth>/<case>/project_after.json",
        "evidence/<plugin>/<depth>/<case>/output_module_before.json",
        "evidence/<plugin>/<depth>/<case>/output_module_after.json",
        "evidence/<plugin>/<depth>/<case>/exr_header_no_effect.json",
        "evidence/<plugin>/<depth>/<case>/exr_header_effect_on.json",
        "evidence/<plugin>/<depth>/<case>/process.json",
        "evidence/<plugin>/<depth>/<case>/etw.etl",
        "evidence/<plugin>/<depth>/<case>/etw.csv",
        "evidence/<plugin>/<depth>/<case>/aerender_stdout.txt",
        "RETURN_STATUS.json",
        "CHECKSUMS.sha256",
    ],
    "reject_if": [
        "missing hash/readback/process/module proof",
        "loaded AEX SHA-256 differs from bundled allowlist",
        "source member or SHA-256 differs from BATCH_MANIFEST",
        "absolute, traversal, symlink, reparse-point, or extra archive path",
        "primary output is not finite uncompressed FLOAT A/B/G/R EXR",
        "cache-like, preexisting, zero-duration, or pre-process output",
        "effect output lacks a paired no-effect control",
        "intentional no-op lacks an explicit tag and positive-effect sibling",
    ],
    "claim_boundary": (
        "The Windows return is a reference corpus. Cross-host AE exactness is "
        "promoted only after independent Mac no-effect and effect-on raw comparisons."
    ),
}


def build_campaign_manifest(inputs: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "campaign_id": CAMPAIGN_ID,
        "created_date": "2026-07-31",
        "objective": (
            "One modern, hash-bound Windows AE Software reference corpus for all "
            "in-scope OLM plugins, suitable for independent Mac raw comparison."
        ),
        "history": {
            "reference_manifests_audited": 57,
            "manifests_with_input_hash": 0,
            "manifests_with_loaded_aex_proof": 0,
            "manifests_with_render_process_binding": 0,
            "historical_request_jsons": 40,
            "requests_with_source_and_aex_hash": 1,
            "requests_with_render_process_binding": 0,
        },
        "global_contract": {
            "ae_version": "26.3x87",
            "renderer": "SOFTWARE",
            "renderer_raw": 1816,
            "working_space": None,
            "linear_blending": False,
            "blend_colors_using_1_0_gamma": False,
            "depths": [8, 16, 32],
            "primary_output": {
                "format": "OpenEXR",
                "storage": "scanline",
                "compression": "none",
                "physical_channels": ["A", "B", "G", "R"],
                "channel_type": 2,
                "sample_type": "FLOAT32",
            },
            "row_identity": {
                "fresh_project": True,
                "fresh_effect": True,
                "fresh_nonce": True,
                "render_queue_items": ["no_effect", "effect_on"],
                "fresh_aerender_process": True,
            },
            "raw_exact_metric": {
                "mismatched_float32_words": 0,
                "max_raw_u32_delta": 0,
                "epsilon": 0,
                "normalization": False,
            },
        },
        "inputs": inputs,
        "lanes": LANES,
        "row_estimate": sum(int(lane["rows_estimate"]) for lane in LANES),
        "render_estimate": 2 * sum(int(lane["rows_estimate"]) for lane in LANES),
        "support_only": {
            "plugin": "ColorKeep",
            "included_in_release_population": False,
            "reference_lane": (
                "required for this campaign: untouched default, explicit two-color "
                "identity, and explicit nontrivial two-color case at 8/16/32bpc; "
                "does not change release scope"
            ),
        },
    }


def zip_deterministically(source_dir: Path, destination: Path) -> None:
    if destination.exists() or destination.is_symlink():
        fail(f"refusing to overwrite {destination}")
    root_name = source_dir.name
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(source_dir.rglob("*"), key=lambda p: p.relative_to(source_dir).as_posix()):
            if path.is_symlink():
                fail(f"symlink in package: {path}")
            if not path.is_file():
                continue
            relative = Path(root_name) / path.relative_to(source_dir)
            info = zipfile.ZipInfo(relative.as_posix(), FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100644 & 0xFFFF) << 16
            with path.open("rb") as handle:
                archive.writestr(info, handle.read(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)


def main() -> None:
    for target in (PACKAGE_DIR, PACKAGE_ZIP, PACKAGE_ZIP_SHA):
        if target.exists() or target.is_symlink():
            fail(f"refusing to overwrite existing output: {target}")
    PACKAGE_DIR.mkdir(parents=True)

    input_index: list[dict[str, object]] = []
    for name, source, digest, description in INPUT_SOURCES:
        record = copy_verified(source, digest, PACKAGE_DIR / "inputs" / name)
        record["description"] = description
        input_index.append(record)

    aex_index: list[dict[str, object]] = []
    for name, digest in sorted(AEX_SOURCES.items()):
        record = copy_verified(f"plugins_2025/{name}", digest, PACKAGE_DIR / "aex" / name)
        record["plugin"] = name.removesuffix(".aex")
        record["support_only"] = name == "ColorKeep.aex"
        aex_index.append(record)

    reuse_index: list[dict[str, object]] = []
    for source, digest, plugin, scope in REUSE_SOURCES:
        name = Path(source).name
        record = copy_verified(source, digest, PACKAGE_DIR / "reuse_evidence" / name)
        record["plugin"] = plugin
        record["scope"] = scope
        reuse_index.append(record)

    request_sources = sorted((ROOT / "refs" / "reference_requests").glob("*.json"))
    if len(request_sources) != 40:
        fail(f"historical request count drift: {len(request_sources)}")
    request_index: list[dict[str, object]] = []
    for source in request_sources:
        if source.is_symlink():
            fail(f"request symlink: {source}")
        digest = sha256(source)
        record = copy_verified(
            source.relative_to(ROOT).as_posix(),
            digest,
            PACKAGE_DIR / "requests" / source.name,
        )
        request_index.append(record)

    write_text(PACKAGE_DIR / "README_WINDOWS_CAMPAIGN.md", README)
    write_text(PACKAGE_DIR / "WINDOWS_CODEX_PROMPT.md", WINDOWS_CODEX_PROMPT)
    write_text(PACKAGE_DIR / "VERIFY_REQUEST.ps1", VERIFY_REQUEST_PS1)
    write_json(PACKAGE_DIR / "CAMPAIGN_MANIFEST.json", build_campaign_manifest(input_index))
    write_json(PACKAGE_DIR / "RETURN_CONTRACT.json", RETURN_CONTRACT)
    write_json(
        PACKAGE_DIR / "REQUEST_SOURCE_INDEX.json",
        {
            "schema_version": 1,
            "count": len(request_index),
            "claim_boundary": "case-definition seeds only; not modern provenance",
            "files": request_index,
        },
    )
    write_json(
        PACKAGE_DIR / "REUSE_INDEX.json",
        {
            "schema_version": 1,
            "claim_boundary": "reuse only for the exact named cells; never generalize",
            "files": reuse_index,
        },
    )
    write_json(
        PACKAGE_DIR / "AEX_INDEX.json",
        {
            "schema_version": 1,
            "files": aex_index,
        },
    )
    write_text(
        PACKAGE_DIR / "INPUTS.sha256",
        "".join(f"{row['sha256']}  {row['member']}\n" for row in input_index),
    )
    write_text(
        PACKAGE_DIR / "AEX_EXPECTED.sha256",
        "".join(f"{row['sha256']}  {row['member']}\n" for row in aex_index),
    )

    checksum_rows = []
    for path in sorted(PACKAGE_DIR.rglob("*"), key=lambda p: p.relative_to(PACKAGE_DIR).as_posix()):
        if path.is_symlink():
            fail(f"symlink in package: {path}")
        if path.is_file() and path.name != "CHECKSUMS.sha256":
            checksum_rows.append(f"{sha256(path)}  {path.relative_to(PACKAGE_DIR).as_posix()}\n")
    write_text(PACKAGE_DIR / "CHECKSUMS.sha256", "".join(checksum_rows))

    zip_deterministically(PACKAGE_DIR, PACKAGE_ZIP)
    zip_digest = sha256(PACKAGE_ZIP)
    write_text(PACKAGE_ZIP_SHA, f"{zip_digest}  {PACKAGE_ZIP.name}\n")
    print(
        json.dumps(
            {
                "campaign_id": CAMPAIGN_ID,
                "directory": str(PACKAGE_DIR),
                "zip": str(PACKAGE_ZIP),
                "zip_sha256": zip_digest,
                "zip_bytes": PACKAGE_ZIP.stat().st_size,
                "inputs": len(input_index),
                "aex": len(aex_index),
                "historical_requests": len(request_index),
                "reuse_evidence": len(reuse_index),
                "rows_estimate": sum(int(lane["rows_estimate"]) for lane in LANES),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
