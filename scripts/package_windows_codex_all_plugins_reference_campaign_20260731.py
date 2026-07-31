#!/usr/bin/env python3
"""Build the single Windows-Codex OLM reference campaign handoff."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import struct
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ID = "olm_windows_all_plugins_reference_campaign_20260731_r4"
DEST_ROOT = ROOT / "handoffs" / "windows_batch"
PACKAGE_DIR = DEST_ROOT / CAMPAIGN_ID
PACKAGE_ZIP = DEST_ROOT / f"{CAMPAIGN_ID}.zip"
PACKAGE_ZIP_SHA = DEST_ROOT / f"{CAMPAIGN_ID}.zip.sha256"
FIXED_ZIP_TIME = (2026, 7, 31, 0, 0, 0)
EXPECTED_LANE_ROWS = {
    "OLMDistanceGradation": 99,
    "OLMDirectionalBlur": 54,
    "OLMRadialBlur": 18,
    "OLMKiraKira": 30,
    "OLMSmoother v1": 19,
    "ColorKeep": 9,
}
EXPECTED_TOTAL_ROWS = sum(EXPECTED_LANE_ROWS.values())
EXPECTED_RENDER_COUNT = EXPECTED_TOTAL_ROWS * 2
KIRAKIRA_CONTROLLED_CASE_IDS = [
    "kk_mapped_bm1_mm1_ray_f0_a0_opaque",
    "kk_mapped_bm2_mm1_ray_f0_a0_opaque",
    "kk_mapped_bm2_mm2_ray_f0_a0_opaque",
    "kk_mapped_bm2_mm1_ray_f0_a0_alpha",
    "kk_mapped_bm2_mm1_ray_f0_a1_alpha",
    "kk_mapped_bm2_mm1_ray_f1_a0_alpha",
    "kk_mapped_bm3_mm1_hi_r0_orange_opaque",
    "kk_mapped_bm3_mm1_hi_r5_white_opaque",
    "kk_mapped_bm3_mm1_hi_r5_orange_opaque",
    "kk_mapped_bm4_mm1_hi_r5_orange_opaque",
]
KIRAKIRA_ALPHA_CASE_IDS = {
    "kk_mapped_bm2_mm1_ray_f0_a0_alpha",
    "kk_mapped_bm2_mm1_ray_f0_a1_alpha",
    "kk_mapped_bm2_mm1_ray_f1_a0_alpha",
}
KIRAKIRA_INTENTIONAL_NOOP_IDS = {
    "kk_mapped_bm3_mm1_hi_r0_orange_opaque",
}
PLUGIN_AEX_MEMBERS = {
    "OLMDistanceGradation": "aex/DistanceGradation.aex",
    "OLMDirectionalBlur": "aex/OLMDirectionalBlur.aex",
    "OLMRadialBlur": "aex/OLMRadialBlur.aex",
    "OLMKiraKira": "aex/OLMKiraKira.aex",
    "OLMSmoother v1": "aex/OLMSmoother.aex",
    "OLMBlur": "aex/OLMBlur.aex",
    "OLMColorKey": "aex/OLMColorKey.aex",
    "OLMToonDilate": "aex/OLMToonDilate.aex",
    "OLMSmoother2": "aex/OLMSmoother2.aex",
    "ColorKeep": "aex/ColorKeep.aex",
}
TOOL_SOURCES = [
    (
        "scripts/verify_olm_windows_all_plugins_reference_return_20260731.py",
        "08258845b17a3f8fad6f8e8130fbce457cb8bd29792cadcd6b45f14bfe615428",
        "tools/VERIFY_RETURN.py",
        "Fail-closed request self-test and independent return intake.",
    ),
    (
        "scripts/compare_float_exr.py",
        "f5b9419d7f9a681d590f7797c84681c89eda81ba3df85fdd37ab852fc356b8e4",
        "tools/compare_float_exr.py",
        "Raw semantic-channel FLOAT32 EXR comparator.",
    ),
    (
        "scripts/verify_32bpc_float_return.py",
        "dc70fba531051b8d5f2201ef4c933481b55fa11dd3b5651bc295f270383c0ad8",
        "tools/verify_32bpc_float_return.py",
        "Uncompressed FLOAT32 RGBA EXR parser and inspector.",
    ),
]
COMMON_STANDARD_OPTIONS = [
    {
        "match_name": "ADBE Effect Mask Opacity",
        "property_type": 6417,
        "scope": "effect_compositing_option",
        "value": 100,
        "action": "set",
        "write": True,
        "value_type": "integer",
        "comparison_mode": "exact_integer",
    },
    {
        "match_name": "ADBE Force CPU GPU",
        "property_type": 6417,
        "scope": "effect_compositing_option",
        "value": 1,
        "action": "set",
        "write": True,
        "value_type": "integer",
        "comparison_mode": "exact_integer",
    },
]


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_json_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def float32_value_and_u32(value: object) -> tuple[object, object]:
    if isinstance(value, list):
        canonical: list[float] = []
        words: list[int] = []
        for component in value:
            payload = struct.pack("<f", component)
            canonical.append(struct.unpack("<f", payload)[0])
            words.append(struct.unpack("<I", payload)[0])
        return canonical, words
    payload = struct.pack("<f", value)
    return struct.unpack("<f", payload)[0], struct.unpack("<I", payload)[0]


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
        "distancegradation_bg_off_rgba16.png",
        "refs/win_references/olmdistancegradation_16bpc_bg_compose_variants_20260626/"
        "DistanceGradation/renders/"
        "olmdistancegradation_16bpc_bg_compose_variants_20260626__software_16bpc__"
        "fr24__olmdistancegradation_case_0020_bg_off_variant_before_effects.png",
        "0fd99810315ac01a2cf38abf9e157418d4552f38e9d237c6677975eb2cc3755e",
        "1920x1080 RGBA16 source for the historical DistanceGradation background-off twins.",
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
        "1920x1080 exact Mac run-8 FLOAT control for odd Smoother-v1 final-random cases.",
    ),
    (
        "smoother_v1_float_even.exr",
        "refs/mac_validation_runs/olmsmoother_v1_32bpc_20260731_run8/"
        "final_random10_olm_smoother_02__no_effect_control.exr",
        "4ac631c5773d5589b2d04943aba0a6fcaa7a9f29b8d8a2b94663385a2f06e5c8",
        "1920x1080 exact Mac run-8 FLOAT control for even Smoother-v1 final-random cases.",
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


SUPPORT_SOURCES = [
    (
        "refs/conformance/olmkirakira_parameter_surface_contract_20260717.json",
        "8805dc0894ec5d603945f1c70e2d5270e18c855b456f291a0bd7b9510ff07a40",
        "OLMKiraKira",
        (
            "Authoritative bounded Windows-index to match-name mapping. Index-only "
            "seed rows must be materialized through this table before execution."
        ),
    ),
    (
        "refs/conformance/olmkirakira_approximated_input_20260718.json",
        "e48c7ea97ebcb57b11ddb4482e60fc6d34e846bc40b6b1624775ea958a70a2ab",
        "OLMKiraKira",
        "Binary-shaped half-resolution branch contract; not AE exact evidence.",
    ),
]


LANES = [
    {
        "plugin": "OLMDistanceGradation",
        "priority": 1,
        "status": "thin_blocking",
        "case_count": 33,
        "depths": [8, 16, 32],
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
        "case_count": 18,
        "depths": [8, 16, 32],
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
        "case_count": 6,
        "depths": [8, 16, 32],
        "rows_estimate": 18,
        "required": [
            "normalized Zoom case 0009 and tiny Rotation case 0010 at 8/16/32bpc",
            "opaque Inner Size Variation 0/50 pair at 8/16/32bpc",
            "nonopaque Inner Size Variation 50 Edge Fade 0/25 pair at 8/16/32bpc",
        ],
        "request_seeds": [
            "radialblur_inner_size_variation_20260606.json",
        ],
        "case_definition_overrides": [
            "case_definitions/olmradialblur_minimal_controlled_r4.json",
        ],
        "special_contract": (
            "Execute exactly 22 discriminated parameter actions by recursive exact "
            "match_name: 21 set actions plus one verify_fresh_default action for "
            "Noise Layer 0021. Verify eight NO_VALUE rows without writing them, and "
            "never use display-name aliases or property indices. The selected six "
            "cases replace the underdeclared 90-row random/alias-heavy draft."
        ),
    },
    {
        "plugin": "OLMKiraKira",
        "priority": 1,
        "status": "thin_blocking",
        "case_count": 10,
        "depths": [8, 16, 32],
        "rows_estimate": 30,
        "required": [
            "ten fully materialized, match-name-only controlled cases at 8/16/32bpc",
            "Blur Modes 1/2/3/4, Merge Modes 1/2, Approximated Input, Fade, Highlight Radius, and Highlight Color differentials",
            "all five Use Ramp controls fixed and read back as zero",
        ],
        "request_seeds": [
            "kirakira_single_ray_20260606.json",
        ],
        "case_definition_overrides": [
            "case_definitions/olmkirakira_controlled_ramps_off_matrix.json",
        ],
        "special_contract": (
            "Write and read back exactly the 25 mapped match names in the bundled "
            "controlled matrix. Never address a parameter by property index. Never "
            "write or infer the five label rows, five opaque custom-ramp payload "
            "rows, or five separator rows. The old final-random states that enabled "
            "Use Ramp are historical seeds only and are intentionally excluded until "
            "the custom-ramp serialization ABI is mapped."
        ),
    },
    {
        "plugin": "OLMSmoother v1",
        "priority": 1,
        "status": "thin_blocking",
        "case_count": 13,
        "depths": [8, 16, 32],
        "rows_estimate": 19,
        "row_groups": [
            {"case_count": 3, "depths": [8, 16, 32], "rows": 9},
            {"case_count": 10, "depths": [32], "rows": 10},
        ],
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
        "status": "reuse_only_no_windows_recapture",
        "case_count": 0,
        "depths": [],
        "rows_estimate": 0,
        "required": [],
        "reuse": [
            "declared 8/16/32bpc exact slices; seven 32bpc reports are bundled"
        ],
        "request_seeds": ["olm_bitdepth_16bpc_normalized_exact_20260625.json"],
    },
    {
        "plugin": "OLMColorKey",
        "priority": 2,
        "status": "reuse_only_no_windows_recapture",
        "case_count": 0,
        "depths": [],
        "rows_estimate": 0,
        "required": [],
        "reuse": [
            "declared canonical 8/16/32bpc exact slices; all-nine 32bpc report is bundled"
        ],
        "request_seeds": [
            "olm_bitdepth_16bpc_normalized_exact_20260625.json",
            "olmcolorkey_replace_colorspace_20260606.json",
        ],
    },
    {
        "plugin": "OLMToonDilate",
        "priority": 2,
        "status": "reuse_only_no_windows_recapture",
        "case_count": 0,
        "depths": [],
        "rows_estimate": 0,
        "required": [],
        "reuse": [
            "declared 8/16bpc cases and 32bpc 64x64 Search Radius 13 typed profile"
        ],
        "request_seeds": [
            "olm_bitdepth_16bpc_toondilate_exact_20260703.json",
            "olm_bitdepth_32bpc_toondilate_float_20260710.json",
        ],
    },
    {
        "plugin": "OLMSmoother2",
        "priority": 2,
        "status": "reuse_only_no_windows_recapture",
        "case_count": 0,
        "depths": [],
        "rows_estimate": 0,
        "required": [],
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
        "case_count": 3,
        "depths": [8, 16, 32],
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
                "property_index_range_inclusive": [2, 101],
                "disk_id_range_inclusive": [2, 101],
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
        "mac_alignment_status": (
            "The Mac source was aligned to this binary/AEXCompat setup in commit "
            "479b4214. This remains intermediate evidence; Windows and Mac AE raw "
            "off/on renders are still required."
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
evidence that should be reused, two bounded KiraKira mapping/IR support files,
and the fail-closed return contract.

This r4 archive supersedes r1 and the rejected local r2/r3 drafts. Do not
merge older inputs or instructions into this campaign.

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
- Priority 2: OLMBlur, OLMColorKey, OLMToonDilate, and OLMSmoother2 are
  reuse-only. Their already-declared exact slices are bundled as evidence and
  receive no new Windows rows.
- Priority 3: a nine-row ColorKeep discovery/reference lane. ColorKeep remains
  support-only and excluded from the nine-plugin release population, but this
  campaign now captures its thin Windows surface instead of leaving it empty.
- `CAMPAIGN_MANIFEST.json` is authoritative for the requested rows. Historical
  files under `requests/` are seeds, not trusted provenance.

Estimated campaign size is {EXPECTED_TOTAL_ROWS} case/depth rows and
{EXPECTED_RENDER_COUNT} off/on renders. This is deliberately automated. Each
row still needs its own fresh identity and render process so cache reuse cannot
masquerade as evidence.

## Which images are needed

The two primary OpenEXR files are the Windows reference images. Separate PNGs
are not exactness evidence. They are required only for the three explicitly
named Radial/Kira diagnostic rows when those rows pass; all other pass rows
need no PNG. The Mac intake can derive previews and heatmaps later from the
hash-bound EXRs.

Only preserve a UI screenshot when a modal, missing plug-in, parameter-surface
mismatch, or another UI-only failure cannot be represented by JSON and logs.
That keeps the one consolidated return small without losing diagnostic value.

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
2. Read `WINDOWS_CODEX_PROMPT.md`, `REFERENCE_GAP_MATRIX.md`,
   `CAMPAIGN_MANIFEST.json`, `EXECUTION_ROWS.json`, `ROW_INVENTORY.json`, and
   `RETURN_CONTRACT.json`, then follow `RETURN_FORMAT.md` exactly.
3. Do not run anything automatically merely because this ZIP was extracted.
4. Do not return partial per-plugin ZIPs. Keep checkpoints in the Windows
   workspace and return one parent ZIP only after exactly {EXPECTED_TOTAL_ROWS}
   unique rows have exactly one terminal pass/fail record.
"""


REFERENCE_GAP_MATRIX = """# Windows reference gap matrix

The raw off/on OpenEXR pair is the required image evidence in every requested
row. A display PNG is diagnostic only and can be generated on the Mac after
intake.

| Plug-in | Why Windows AE is still needed | Requested scope | Extra screenshots |
|---|---|---|---|
| OLMDistanceGradation | Thin provenance and unresolved host-world/depth staging | 33 cases at 8/16/32bpc = 99 rows | Failure-only |
| OLMDirectionalBlur | Full writer output and undeclared features/depths are not closed | 18 cases at 8/16/32bpc = 54 rows | Failure-only |
| OLMRadialBlur | Production plane, Rotation/Inner, and depth coverage remain open | 6 fully materialized controlled cases at 8/16/32bpc = 18 rows | One same-run PNG + witness crop for canonical 20260604 case0010@8; otherwise failure-only |
| OLMKiraKira | Outer compose and several modes/controls remain open; custom-ramp states are deferred until serializable | 10 controlled ramps-off cases at 8/16/32bpc = 30 rows | Two same-run PF8 writer PNG/trace pairs; otherwise trace-only or failure-only |
| OLMSmoother v1 | 16bpc and classic-host-converted 32bpc need same-source proof | 3 canonical cases at 8/16/32 plus ten 32bpc cases = 19 rows | Failure-only |
| ColorKeep | Real Windows AE coverage was previously absent | 3 cases at 8/16/32bpc = 9 support-only rows | Parameter/UI mismatch only |
| OLMBlur | Declared slices already have reusable AE-exact evidence | 0 new rows | None |
| OLMColorKey | Declared slices already have reusable AE-exact evidence | 0 new rows | None |
| OLMToonDilate | Declared slices already have reusable AE-exact evidence | 0 new rows | None |
| OLMSmoother2 | Declared 8/16/32 suites are already AE exact | 0 new rows | None |

Do not substitute AEXCompat, a CLI comparison, a display PNG, or a screenshot
for the raw AE Software off/on pair. They are useful intermediate or diagnostic
evidence only.
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

Build a fail-closed batch runner from `CAMPAIGN_MANIFEST.json` and the exact
{EXPECTED_TOTAL_ROWS} fully materialized rows in `EXECUTION_ROWS.json`.
`ROW_INVENTORY.json` is the compact index; do not derive writes from historical
seeds or manually operate hundreds of cases.
Extraction and verification must be read-only. Execution begins only when the
Windows user explicitly starts the batch.

- Before execution, `VERIFY_REQUEST.ps1` must pass. Read the README, gap matrix,
  campaign manifest, return contract, and `RETURN_FORMAT.md`.
- Adobe After Effects must be exactly 26.3x87.
- Renderer must be Software, raw value 1816.
- Working space must serialize as JSON `null` (AE raw value may be empty or
  None and must also be preserved separately); linear blending and
  blend-colors-using-1.0-gamma must be false.
- Pin 24fps and render frame 24 (time 1.0s). Ignore the historical optional
  30fps DirectionalBlur render set.
- Open the bundled Preserve-RGB template, replace its placeholder footage,
  resolving exact item names `OLM_COLOR_PROBE_INPUT` and
  `OLM_COLOR_PROBE_COMP`. Require exactly one layer, layer 1 sourced from that
  footage item, a clean Effect Parade before the requested effect is added,
  Preserve RGB=true, and straight/unmatted alpha interpretation. Prove every
  no-effect EXR round-trips the selected source contract.
- After replacement, apply the exact per-row `ROW_INVENTORY.comp`: resize the
  comp to the source dimensions, keep pixel aspect 1 and full resolution,
  set duration exactly 2.0 seconds, center the sole source layer at 100% scale,
  and verify every field before render. Render only the exact one-frame span
  starting at 1.0 seconds with duration 1/24 second.
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
- for every `float32_u32_*` action, independently encode the live pre/post
  readback into raw IEEE-754 float32 u32 word(s); never echo the outbound
  binary64 seed decimal as if it were host readback;
- OutputModule `getSettings(GetSettingsFormat.STRING)` before and after,
  canonicalized exactly as `RETURN_FORMAT.md` specifies after excluding only
  output-path-dependent fields;
- EXR header inspection;
- AfterFX/aerender path, SHA-256, version, PID, start time, command, and nonce;
- ETW parent-to-real-AfterFX-child mapping and that child's AEX image load and
  unload, including the exact bundled AEX SHA-256, plus the exact normalized
  five-row CSV projection required by `RETURN_FORMAT.md`.

Do not synthesize rows for OLMBlur, OLMColorKey, OLMToonDilate, or
OLMSmoother2. They are reuse-only in this request; their bundled reports do not
expand the exact row inventory.

ColorKeep is a support-only discovery lane. Its expected plugin-only leaf count
is 101 (102 params including the automatic input). The Windows 2025 AEX setup
has Enabled Color Num range 0–100/default 1 and 100 black color defaults. The
Mac source was aligned to that setup in commit 479b4214, but AEXCompat remains
intermediate evidence rather than AE exactness. Explicit writes are permitted
only after the live indices, names, types, and untouched defaults have been
captured and the declared indices have matched; otherwise fail closed without
guessing.

For every plug-in, normalize and compare `params_expected.json`,
`params_before.json`, and `params_after.json`. Names, match names, indices,
types, enabled state, and values must agree after the declared writes. Compare
integer/popup/checkbox values exactly and float controls after explicit
float32 canonicalization. A present but mismatched readback is a failed row,
not usable evidence.

## Cache and output barrier

- Output paths must not preexist.
- Output timestamps must postdate process start.
- Render duration must be nonzero.
- Hash only after AE has closed/finalized the EXR.
- Effect-on must differ raw from control unless the row is explicitly tagged
  `intentional_noop`.
- An `intentional_noop` row must have exactly zero mismatched decoded FLOAT32
  channel words between effect-on and control, and also needs a positive-effect
  sibling for that plugin/depth.
- For every KiraKira differential pair declared in the controlled matrix,
  additionally compare effect-on against effect-on at each depth after proving
  the source and the declared all-other-parameter identity. Return exact raw
  mismatch counts and fail if a declared positive differential is zero.

## Image policy

The raw no-effect/effect-on EXRs are the required Windows reference images.
Do not inflate the return with pass-case PNG duplicates. The only pass-case PNG
sidecars are the two explicitly named RadialBlur/KiraKira diagnostics in the
manifest. Otherwise preserve a screenshot only for a modal, missing plug-in,
property-surface mismatch, or another failure that cannot be represented by
JSON and logs. Any PNG or screenshot is diagnostic only and never satisfies
the raw-output contract.

## Return

Use exactly the tree in `RETURN_CONTRACT.json`. Produce one consolidated parent
ZIP, its SHA-256 sidecar, and no smaller return ZIPs. A failed row still needs a
terminal `RETURN_STATUS.json` entry, its exact row-bound `failure.json`, and
optionally only `diagnostics/<row_id>/failure.png`; do not retain pass artifacts
for a failed row. Never mark a row answered or exact when any required hash,
readback, process proof, or raw output is missing. Before packaging, require exactly {EXPECTED_TOTAL_ROWS}
unique manifest rows and exactly one terminal status for every row; do not
return a partial archive. The bundled `tools/VERIFY_RETURN.py` must pass against
the completed staging tree before the ZIP is created.
"""


RETURN_FORMAT = f"""# Machine-readable return format

This document is normative together with `RETURN_CONTRACT.json`,
`EXECUTION_ROWS.json`, the schemas, and `tools/VERIFY_RETURN.py`. When prose
and the verifier differ, stop and resolve the request rather than weakening
the verifier.

## One staging tree and one archive

1. Copy the complete extracted request tree byte-for-byte to a fresh return
   staging directory.
2. Remove only the copied outbound `CHECKSUMS.sha256`; preserve every other
   outbound member exactly.
3. Add `BATCH_MANIFEST.json`, `RETURN_STATUS.json`, row artifacts, cross-row
   results, and conditional diagnostics.
4. Generate a new `CHECKSUMS.sha256` that covers every regular file other than
   itself exactly once, using lowercase SHA-256, two spaces, and a `/`-separated
   relative path.
5. Run:

   `python -B .\\tools\\VERIFY_RETURN.py --request-root <original-extracted-request> --return-root <return-staging>`

6. Only after that command passes, create one ZIP64 archive named
   `olm_windows_all_plugins_reference_return_20260731_r4.zip` and the sidecar
   `olm_windows_all_plugins_reference_return_20260731_r4.zip.sha256`.

Do not place per-plugin ZIPs inside the parent. Budget at least 25 GB free
space for the uncompressed FLOAT32 EXRs and staging copies.

## Batch and terminal status

`BATCH_MANIFEST.json` has exactly these top-level fields:

- `schema_version`: 1
- `campaign_id`: `{CAMPAIGN_ID}`
- `execution_rows_sha256`, `row_inventory_sha256`,
  `campaign_manifest_sha256`: hashes of the exact outbound files
- `row_count`: {EXPECTED_TOTAL_ROWS}
- `rows`: an exact ordered deep copy of `EXECUTION_ROWS.json#/rows`

Its binding SHA used below is canonical JSON SHA-256 with ASCII escaping,
sorted keys, separators `,` and `:`, no BOM, and no trailing newline.

`RETURN_STATUS.json` follows its bundled schema. It contains exactly
{EXPECTED_TOTAL_ROWS} ordered records. A pass record has both completeness
booleans true and no failure codes. A fail record has both completeness
booleans false and one or more unique, nonempty stable string failure codes.

## Evidence envelope

Every pass JSON under `evidence/<row_id>/` and every `failure.json` is:

- `schema_version`: 1
- `kind`: the filename stem declared by the verifier
- `binding`: exactly `campaign_id`, `row_id`,
  `batch_manifest_sha256`, `execution_row_sha256`, and
  `case_contract_sha256`
- `data`: the payload below

No additional envelope fields are allowed.

Pass payloads:

- `params_expected`, `params_before`, `params_after`: exactly `values` and
  `values_sha256`. `values` is exactly
  `{{"parameter_actions": <row.parameter_writes>,
  "standard_options": <row.standard_options>}}`; readback must be normalized
  into that same ordered form. Booleans never compare equal to numbers.
  Equivalent finite JSON numeric spellings are accepted only for live
  numeric project/parameter evidence; immutable manifests, status counts,
  integer-declared fields, and exact outbound copies remain type-strict. Every
  `float32_u32_*` action contains a generator-canonicalized float32 `value`
  and `value_raw_f32_u32`; before/after evidence must independently encode the
  live readback into the same raw word(s). Each file's `values_sha256` hashes
  its own exact canonical JSON `values` object.
- `params_setup`: exactly `expected_surface_contract`,
  `expected_surface_contract_sha256`, `observed_surface`,
  `observed_surface_sha256`, `surface_gate_passed`, and
  `surface_gate_failures`. The expected contract is copied from the execution
  row. Every observed leaf has exactly `property_index`, `match_name`,
  `display_name`, `property_type`, `enabled`, `active`, `value_available`, and
  `value`, in the exact declared order. A pass has true and an empty failure
  list.
- `project_before`, `project_after`: exactly `expected_project_contract`,
  `expected_project_contract_sha256`, `observed_project`, and
  `observed_project_sha256`. The expected contract is copied from the row;
  both hashes use canonical JSON. `observed_project` has exactly
  `project_return_member`, `project_sha256`, `run_nonce`, `source`, `comp`,
  `source_layer`, `effect`, and `render_queue_items`. The nested source binds
  member/hash/absolute runtime path, named footage item and ID, Preserve RGB,
  straight alpha, and non-premultiplication. The process record repeats the
  same source runtime path. The comp and layer bind the named comp, exact row comp
  contract, one layer, source-item identity, 100% scale/centering, and Effect
  Parade counts 0 before add and 1 after add. The effect binds display/match
  name and property index 1. The two RQ records bind distinct IDs, effect
  enabled false/true, and their exact output members. Each RQ record also
  carries its exact 1-based queue index, observed comp item ID, output-module
  index 1, absolute output path, and a derived ID
  `<run_nonce>:rq:<queue_index>`. It captures canonical compact STRING-format
  Render Settings via
  `RenderQueueItem.getSettings(GetSettingsFormat.STRING)` plus its SHA-256.
  The nested `Effects` setting must occur exactly once and
  normalize to `All Off` for no-effect, and to `Current Settings` or `All On`
  for effect-on. `Color Depth` must occur exactly once and be `Current
  Settings` or the exact row depth; after replacing only the `Effects` value
  with a sentinel, both branches' complete Render Settings must hash
  identically. Before and after live observations must be identical.
- `output_module_before`, `output_module_after`: exactly one top-level
  `branches` object containing `no_effect` and `effect_on`. Each branch has exactly
  `render_queue_item_id`, `output_module_index=1`, `output_member`,
  `normalized_output_contract` copied exactly from the row's primary output,
  `settings_serialization`, and `settings_serialization_sha256` (the SHA-256
  of the UTF-8 STRING-format serialization). The serialization is canonical
  compact JSON with exactly `get_settings_format="STRING"`,
  `path_dependent_fields_excluded=true`, and the nonempty `raw_settings`
  object returned by AE after excluding only output-path-dependent fields.
  Nested raw settings must expose exactly one occurrence each of `Format`,
  `Channels`, `Depth`, and `Color`; `Compression` may be absent because AE
  26.3 OpenEXR STRING readback omits it. If present it must occur exactly once
  and normalize to no compression. The required values must be an allowlisted
  exact AE spelling for OpenEXR/OpenEXR Sequence, RGB+Alpha, floating point,
  and straight alpha. Contradictory, negated, or
  duplicate nested settings are rejected. The serialization must not contain
  the row ID. Both branches use the same
  serialization; both complete branch maps are identical before/after;
  render-queue IDs are distinct between branches and agree with live project
  observation and `process`.
- `exr_header_no_effect`, `exr_header_effect_on`: exactly the result from
  `tools/verify_32bpc_float_return.py::inspect_float_rgba_exr`, excluding its
  machine-local `path` field.
- `raw_off_on_comparison`: exactly `no_effect_sha256`,
  `effect_on_sha256`, `decoded_word_count`, `mismatched_words`, and
  `max_raw_u32_delta`, independently recomputed by the bundled comparator.
  When the selected source member is already FLOAT32 EXR and the row itself
  is 32bpc, the verifier also requires an independent raw-word-exact
  source/no-effect round trip. 8/16bpc controls are not compared directly to
  arbitrary FLOAT32 source words because project-depth quantization is
  expected.
- `process`: the project/source/AEX fields checked by `VERIFY_RETURN.py`, plus
  `project`, `outputs`, `logs`, `process_start_unix_ns`, and
  `process_end_unix_ns`. `project` has exactly `return_path`, `runtime_path`,
  and `sha256`. Each `outputs.no_effect` / `outputs.effect_on` record has
  exactly `return_path`, `runtime_path`, `sha256`, `preexisting=false`,
  `finalized=true`, a post-start `mtime_unix_ns`, positive
  `render_duration_ms`, exact `render_start_unix_ns` /
  `render_end_unix_ns`, and a distinct nonempty `render_queue_item_id`.
  Durations are exact ceiling milliseconds, renders do not overlap, and each
  output satisfies module-load ≤ render-start ≤ finalized file mtime ≤
  render-end ≤ module-unload. Runtime paths for source, project, both EXRs,
  logs, and any diagnostic PNG are pairwise distinct after Windows
  case/slash normalization. Extended/device namespaces, ADS, dot segments,
  and trailing-dot/space aliases are rejected.
  `logs` has exactly `etw_etl`, `etw_csv`, and `aerender_stdout`; each record
  has exactly `return_path`, `runtime_path`, and `sha256`, binding the
  returned log to the runtime capture path. All return paths are
  return-relative; runtime paths are nonempty absolute Windows paths.
  `aerender` also has exact nonempty `command` and `command_argv`; argv must
  include `-project` followed by the exact runtime AEP path.
  `real_afterfx_child` has path/SHA/PID/parent PID/start/stop UTC timestamps and
  mapping method. `etw.csv` is the exact five-row normalized ETW projection
  with header `event_type,pid,parent_pid,image_path,timestamp_utc` and ordered
  events `aerender_start`, `afterfx_child_start`, `aex_image_load`,
  `aex_image_unload`, `afterfx_child_stop`, exactly matching the process JSON.
  The event times must order aerender ≤ child ≤ load < unload ≤ child stop and
  lie within the Unix-ns process barrier. `etw_export` binds an absolute
  exporter/normalizer tool path, SHA, version, exact argv, source ETL runtime
  path/hash, and normalized CSV runtime path/hash. Aerender stdout must contain
  the exact returned AEP basename, both runtime output paths, and both RQ IDs. The retained
  ETL must be at least 1024 bytes and the CSV at least 128 bytes.

A failed row's evidence subtree has only `evidence/<row_id>/failure.json`.
Its `data` has exactly
`failure_codes`, `stage`, `message`, and `diagnostic_paths`; the code list must
equal its status record. `diagnostic_paths` is exactly `[]` or exactly
`["diagnostics/<row_id>/failure.png"]`; no pass project/output/evidence may
remain. The optional screenshot is a fully decodable, CRC-valid,
noninterlaced RGBA8 PNG no larger than 64 MiB compressed or 64 MiB decoded
RGBA8.

## Cross-row and targeted diagnostics

`cross_row/olmkirakira_controlled_matrix.json` always contains all 21 declared
pair/depth records. A comparison whose two member rows pass contains the full
hash/count payload and must be nonzero. If either member failed, its compact
record contains only pair/depth/row IDs, `terminal_status=fail`, and nonempty
`failure_codes`.

The Radial PF8 witness and two Kira PF8 writer traces use their exact bundled
schemas and are required only when their target row passes. Kira PF8 mode 1/2
must independently reproduce the pinned float32 source/glow-weight compose,
raw-zero branch, clamp, writer XMM words, and `CVTTSS2SI(x*255)` bytes
(RN-even f32 operations with DAZ/FTZ disabled and all six SSE exceptions
masked under captured Windows MXCSR).
`post_writer_argb8` is raw destination byte order A/R/G/B and rotates to the
exported PNG's logical R/G/B/A; all three dereferenced pointers are nonzero
x64 values. For each of these three rows, `process.diagnostic_outputs` contains
the PNG's OM index 2, absolute runtime/return path, artifact/settings hashes,
same effect-on RQ ID and render interval, finalized mtime, and canonical raw
PNG settings (PNG/PNG Sequence, RGB+Alpha, Millions of Colors+, straight);
stdout binds its
runtime path/RQ ID. Kira PF32 trace
JSON uses `OLMKIRAKIRA_PF32_TRACE.schema.json`: two exact row bindings plus
typed `instrumentation` and `trace_records`. `instrumentation` has exactly
`capture_method`, `trace_tool`, `trace_session_id`, and
`process_attestation_sha256_by_row`, plus the exact one-control match name and
the `same_xy_same_input_one_control_delta_with_different_stage` predicate.
Every trace record has exactly `row_id`,
nonnegative unique-per-row `record_index`, nonempty `event`, and nonempty
typed payload. The two rows must have the same record indices, XY coordinates,
and input float32 words, while at least one captured stage RGBA differs. Each
diagnostic row binding
has exactly `row_id`, `execution_row_sha256`, `case_contract_sha256`,
`source_sha256`, `aex_sha256`, `project_sha256`, `effect_on_sha256`,
`process_attestation_sha256`, and `render_queue_item_id`. The Gaussian dump is
exactly 84 bytes (21 little-endian float32 words) and its JSON must reproduce
all 21 raw u32 words and bind the exact three declared rows.

Raw uncompressed FLOAT32 A/B/G/R EXRs remain the authoritative images. PNGs
and screenshots are diagnostics only. The verifier computes the exact allowed
member set from pass/fail status and each diagnostic's own bound rows; every
unlisted or stale file is terminal failure.
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
    "schema_version": 3,
    "campaign_id": CAMPAIGN_ID,
    "single_consolidated_return_only": True,
    "row_contract": {
        "expected_total_rows": EXPECTED_TOTAL_ROWS,
        "expected_lane_rows": EXPECTED_LANE_ROWS,
        "batch_manifest": (
            "must reproduce the complete ordered EXECUTION_ROWS rows by exact JSON "
            "deep equality, not only row_ids or lane cardinalities; it must also "
            "bind the outbound EXECUTION_ROWS, ROW_INVENTORY, and "
            "CAMPAIGN_MANIFEST SHA-256 values"
        ),
        "return_status": (
            "must contain exactly one terminal pass or fail record for every "
            "BATCH_MANIFEST row_id and no extra row_id"
        ),
        "immutable_semantic_fields": [
            "row_id",
            "plugin",
            "group_id",
            "case_id",
            "depth",
            "source_member",
            "source_sha256",
            "aex_member",
            "aex_sha256",
            "comp",
            "case_definition_file",
            "case_definition_sha256",
            "case_contract_sha256",
            "intentional_noop",
            "expected_raw_off_on_relation",
        ],
        "canonical_json": {
            "encoding": "UTF-8",
            "ensure_ascii": True,
            "sort_keys": True,
            "separators": [",", ":"],
            "sha256_over": "exact encoded bytes with no BOM or trailing newline",
        },
        "partial_return_allowed": False,
    },
    "raw_outcome_predicates": {
        "intentional_noop_false": (
            "decoded effect_on and no_effect FLOAT32 A/B/G/R words must differ "
            "at one or more positions"
        ),
        "intentional_noop_true": (
            "decoded effect_on and no_effect FLOAT32 A/B/G/R words must have "
            "exactly zero mismatches"
        ),
        "intentional_noop_positive_sibling": (
            "a non-intentional-noop row for the same plugin and depth must pass "
            "and have one or more raw word mismatches"
        ),
    },
    "parameter_predicates": {
        "setup_surface": (
            "live indices, match names, display names, types, enabled/active state, "
            "and plugin-only leaf count must equal the materialized case definition "
            "before writes; an untouched default is compared only when that exact "
            "surface row declares a default"
        ),
        "render_readback": (
            "params_expected must be derived only from the immutable outbound case "
            "definition, never from live readback; params_expected, params_before, "
            "and params_after must agree after declared writes; integer/popup/"
            "checkbox values match exactly and float/color controls compare by exact "
            "IEEE-754 float32 u32 words after explicit canonicalization"
        ),
        "mismatch_is_terminal_failure": True,
    },
    "cross_row_predicates": {
        "olmkirakira_controlled_matrix": (
            "for all seven declared pair invariants at each depth, bind both row IDs, "
            "source hashes, canonical full parameter hashes, effect-on output hashes, "
            "decoded word count, and independently recomputed mismatch count; every "
            "declared differential must be nonzero"
        ),
    },
    "image_policy": {
        "authoritative_images": ["no_effect.exr", "effect_on.exr"],
        "pass_case_png_required": False,
        "targeted_pass_case_diagnostics": [
            "OLMRadialBlur canonical 20260604 case0010 at 8bpc",
            "OLMKiraKira controlled Merge1 and Merge2 PF8 rows at 8bpc",
        ],
        "diagnostic_screenshot_required_only_if": [
            "modal or dialog blocks headless execution",
            "plugin is missing or fails to load",
            "parameter surface mismatch cannot be represented completely in JSON",
            "another UI-only failure needs visual evidence",
        ],
        "png_or_screenshot_can_satisfy_raw_contract": False,
    },
    "required_tree": [
        "complete exact outbound request tree (all members except outbound CHECKSUMS.sha256, which is replaced by the return checksum file)",
        "README_WINDOWS_CAMPAIGN.md",
        "WINDOWS_CODEX_PROMPT.md",
        "REFERENCE_GAP_MATRIX.md",
        "RETURN_FORMAT.md",
        "CAMPAIGN_MANIFEST.json",
        "BATCH_MANIFEST.json",
        "EXECUTION_ROWS.json",
        "ROW_INVENTORY.json",
        "RETURN_CONTRACT.json",
        "INPUTS.sha256",
        "AEX_EXPECTED.sha256",
        "AEX_INDEX.json",
        "REQUEST_SOURCE_INDEX.json",
        "REUSE_INDEX.json",
        "SUPPORT_INDEX.json",
        "TOOL_INDEX.json",
        "aex/",
        "schemas/",
        "tools/",
        "requests/",
        "inputs/",
        "case_definitions/",
        "reuse_evidence/",
        "support_evidence/",
        "cross_row/olmkirakira_controlled_matrix.json (always; 21 terminal comparisons)",
        "diagnostics/OLMRadialBlur/8bpc/canonical_20260604_case0010/effect_on.png (required only if target row passes)",
        "diagnostics/OLMRadialBlur/8bpc/canonical_20260604_case0010/witness_1614_6.json (required only if target row passes)",
        "diagnostics/OLMKiraKira/8bpc/kk_mapped_bm2_mm1_ray_f0_a0_opaque/effect_on.png (required only if target row passes)",
        "diagnostics/OLMKiraKira/8bpc/kk_mapped_bm2_mm1_ray_f0_a0_opaque/writer_trace.json (required only if target row passes)",
        "diagnostics/OLMKiraKira/8bpc/kk_mapped_bm2_mm2_ray_f0_a0_opaque/effect_on.png (required only if target row passes)",
        "diagnostics/OLMKiraKira/8bpc/kk_mapped_bm2_mm2_ray_f0_a0_opaque/writer_trace.json (required only if target row passes)",
        "diagnostics/OLMKiraKira/32bpc/controlled_matrix/approximated_input_trace.json (required only if all bound rows pass)",
        "diagnostics/OLMKiraKira/32bpc/controlled_matrix/highlight_layer_trace.json (required only if all bound rows pass)",
        "diagnostics/OLMKiraKira/32bpc/controlled_matrix/highlight_color_trace.json (required only if all bound rows pass)",
        "diagnostics/OLMKiraKira/32bpc/controlled_matrix/gaussian_kernel_21_f32_le.bin (required only if all bound rows pass)",
        "diagnostics/OLMKiraKira/32bpc/controlled_matrix/gaussian_kernel_21_f32_le.json (required only if all bound rows pass)",
        "diagnostics/OLMKiraKira/32bpc/controlled_matrix/mode4_trace.json (required only if all bound rows pass)",
        "projects/<row_id>.aep (required for terminal pass rows)",
        "outputs/<row_id>/no_effect.exr (required for terminal pass rows)",
        "outputs/<row_id>/effect_on.exr (required for terminal pass rows)",
        "evidence/<row_id>/params_expected.json (required for terminal pass rows)",
        "evidence/<row_id>/params_setup.json (required for terminal pass rows)",
        "evidence/<row_id>/params_before.json (required for terminal pass rows)",
        "evidence/<row_id>/params_after.json (required for terminal pass rows)",
        "evidence/<row_id>/project_before.json (required for terminal pass rows)",
        "evidence/<row_id>/project_after.json (required for terminal pass rows)",
        "evidence/<row_id>/output_module_before.json (required for terminal pass rows)",
        "evidence/<row_id>/output_module_after.json (required for terminal pass rows)",
        "evidence/<row_id>/exr_header_no_effect.json (required for terminal pass rows)",
        "evidence/<row_id>/exr_header_effect_on.json (required for terminal pass rows)",
        "evidence/<row_id>/raw_off_on_comparison.json (required for terminal pass rows)",
        "evidence/<row_id>/process.json (required for terminal pass rows)",
        "evidence/<row_id>/etw.etl (required for terminal pass rows)",
        "evidence/<row_id>/etw.csv (required for terminal pass rows)",
        "evidence/<row_id>/aerender_stdout.txt (required for terminal pass rows)",
        "evidence/<row_id>/failure.json (required for terminal fail rows)",
        "diagnostics/<row_id>/failure.png (failure-only when applicable)",
        "RETURN_STATUS.json",
        "CHECKSUMS.sha256",
    ],
    "reject_if": [
        "missing hash/readback/process/module proof",
        "loaded AEX SHA-256 differs from bundled allowlist",
        "source member or SHA-256 differs from immutable outbound EXECUTION_ROWS",
        "absolute, traversal, symlink, reparse-point, or extra archive path",
        "primary output is not finite uncompressed FLOAT A/B/G/R EXR",
        "cache-like, preexisting, zero-duration, or pre-process output",
        "effect output lacks a paired no-effect control",
        "positive-effect row has zero decoded FLOAT32-word mismatches",
        "intentional no-op row has any decoded FLOAT32-word mismatch",
        "intentional no-op lacks an explicit tag and positive-effect sibling",
        "present setup/readback differs from the declared expected surface or writes",
        "BATCH_MANIFEST ordered row objects are not exact deep-equal copies of EXECUTION_ROWS rows",
        "any immutable semantic field or outbound artifact hash differs",
        "any required schema or schema_version is missing or invalid",
        "any pass row lacks its exact row_id-bound project/output/evidence artifacts",
        "any fail row lacks a row_id-bound failure record",
        "return CHECKSUMS.sha256 lacks exact non-self coverage or contains a mismatch",
        "KiraKira cross-row report is missing, altered, or has a zero declared differential",
        "targeted diagnostic schema, artifact hash, row/process/RQ linkage, or required payload is missing",
        "RETURN_STATUS is partial, duplicated, missing, nonterminal, or contains extra rows",
    ],
    "claim_boundary": (
        "The Windows return is a reference corpus. Cross-host AE exactness is "
        "promoted only after independent Mac no-effect and effect-on raw comparisons."
    ),
}


def build_return_schemas() -> dict[str, dict[str, object]]:
    sha_pattern = "^[0-9a-f]{64}$"
    binding_properties = {
        "campaign_id": {"const": CAMPAIGN_ID},
        "row_id": {"type": "string", "minLength": 1},
        "batch_manifest_sha256": {"type": "string", "pattern": sha_pattern},
        "execution_row_sha256": {"type": "string", "pattern": sha_pattern},
        "case_contract_sha256": {"type": "string", "pattern": sha_pattern},
    }
    evidence_binding_schema: dict[str, object] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "olm-evidence-binding.schema.json",
        "type": "object",
        "required": ["schema_version", "kind", "binding", "data"],
        "properties": {
            "schema_version": {"const": 1},
            "kind": {"type": "string", "minLength": 1},
            "binding": {
                "type": "object",
                "additionalProperties": False,
                "required": list(binding_properties),
                "properties": binding_properties,
            },
            "data": {"type": "object"},
        },
        "additionalProperties": False,
    }
    batch_schema: dict[str, object] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "batch-manifest.schema.json",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "campaign_id",
            "execution_rows_sha256",
            "row_inventory_sha256",
            "campaign_manifest_sha256",
            "row_count",
            "rows",
        ],
        "properties": {
            "schema_version": {"const": 1},
            "campaign_id": {"const": CAMPAIGN_ID},
            "execution_rows_sha256": {"type": "string", "pattern": sha_pattern},
            "row_inventory_sha256": {"type": "string", "pattern": sha_pattern},
            "campaign_manifest_sha256": {"type": "string", "pattern": sha_pattern},
            "row_count": {"const": EXPECTED_TOTAL_ROWS},
            "rows": {
                "type": "array",
                "minItems": EXPECTED_TOTAL_ROWS,
                "maxItems": EXPECTED_TOTAL_ROWS,
                "items": {"type": "object"},
            },
        },
    }
    return_status_schema: dict[str, object] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "return-status.schema.json",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "campaign_id",
            "batch_manifest_sha256",
            "row_count",
            "rows",
        ],
        "properties": {
            "schema_version": {"const": 1},
            "campaign_id": {"const": CAMPAIGN_ID},
            "batch_manifest_sha256": {"type": "string", "pattern": sha_pattern},
            "row_count": {"const": EXPECTED_TOTAL_ROWS},
            "rows": {
                "type": "array",
                "minItems": EXPECTED_TOTAL_ROWS,
                "maxItems": EXPECTED_TOTAL_ROWS,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "row_id",
                        "terminal_status",
                        "execution_row_sha256",
                        "evidence_complete",
                        "outputs_complete",
                        "failure_codes",
                    ],
                    "properties": {
                        "row_id": {"type": "string", "minLength": 1},
                        "terminal_status": {"enum": ["pass", "fail"]},
                        "execution_row_sha256": {
                            "type": "string",
                            "pattern": sha_pattern,
                        },
                        "evidence_complete": {"type": "boolean"},
                        "outputs_complete": {"type": "boolean"},
                        "failure_codes": {
                            "type": "array",
                            "items": {"type": "string", "minLength": 1},
                            "uniqueItems": True,
                        },
                    },
                    "allOf": [
                        {
                            "if": {
                                "properties": {
                                    "terminal_status": {"const": "pass"}
                                }
                            },
                            "then": {
                                "properties": {
                                    "evidence_complete": {"const": True},
                                    "outputs_complete": {"const": True},
                                    "failure_codes": {"maxItems": 0},
                                }
                            },
                            "else": {
                                "properties": {
                                    "evidence_complete": {"const": False},
                                    "outputs_complete": {"const": False},
                                    "failure_codes": {"minItems": 1},
                                }
                            },
                        }
                    ],
                },
            },
        },
    }
    cross_row_identity_properties = {
        "pair_id": {"type": "string", "minLength": 1},
        "depth": {"enum": [8, 16, 32]},
        "left_row_id": {"type": "string", "minLength": 1},
        "right_row_id": {"type": "string", "minLength": 1},
    }
    cross_row_pass_properties = {
        **cross_row_identity_properties,
        "terminal_status": {"const": "pass"},
        "failure_codes": {
            "type": "array",
            "maxItems": 0,
            "items": {"type": "string", "minLength": 1},
            "uniqueItems": True,
        },
        "left_source_sha256": {"type": "string", "pattern": sha_pattern},
        "right_source_sha256": {"type": "string", "pattern": sha_pattern},
        "left_parameter_sha256": {"type": "string", "pattern": sha_pattern},
        "right_parameter_sha256": {"type": "string", "pattern": sha_pattern},
        "left_effect_on_sha256": {"type": "string", "pattern": sha_pattern},
        "right_effect_on_sha256": {"type": "string", "pattern": sha_pattern},
        "decoded_word_count": {"type": "integer", "minimum": 1},
        "mismatched_words": {"type": "integer", "minimum": 1},
        "max_raw_u32_delta": {"type": "integer", "minimum": 1},
    }
    cross_row_fail_properties = {
        **cross_row_identity_properties,
        "terminal_status": {"const": "fail"},
        "failure_codes": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string", "minLength": 1},
            "uniqueItems": True,
        },
    }
    cross_row_schema: dict[str, object] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "olmkirakira-cross-row.schema.json",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "campaign_id",
            "batch_manifest_sha256",
            "comparison_count",
            "comparisons",
        ],
        "properties": {
            "schema_version": {"const": 1},
            "campaign_id": {"const": CAMPAIGN_ID},
            "batch_manifest_sha256": {"type": "string", "pattern": sha_pattern},
            "comparison_count": {"const": 21},
            "comparisons": {
                "type": "array",
                "minItems": 21,
                "maxItems": 21,
                "items": {
                    "oneOf": [
                        {
                            "type": "object",
                            "additionalProperties": False,
                            "required": list(cross_row_pass_properties),
                            "properties": cross_row_pass_properties,
                        },
                        {
                            "type": "object",
                            "additionalProperties": False,
                            "required": list(cross_row_fail_properties),
                            "properties": cross_row_fail_properties,
                        },
                    ],
                },
            },
        },
    }
    radial_witness_schema: dict[str, object] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "olmradialblur-witness.schema.json",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "kind",
            "binding",
            "effect_on_exr",
            "effect_on_png",
            "probe",
            "output_module_settings_sha256",
            "diagnostic_output_module_settings_sha256",
            "process_attestation_sha256",
            "render_queue_item_id",
        ],
        "properties": {
            "schema_version": {"const": 1},
            "kind": {"const": "olmradialblur_tiny_rotation_png_probe_v1"},
            "binding": evidence_binding_schema["properties"]["binding"],
            "effect_on_exr": {
                "type": "object",
                "required": ["path", "sha256"],
                "properties": {
                    "path": {"type": "string"},
                    "sha256": {"type": "string", "pattern": sha_pattern},
                },
                "additionalProperties": False,
            },
            "effect_on_png": {
                "type": "object",
                "required": [
                    "path",
                    "sha256",
                    "same_effect_on_render_queue_item",
                    "same_process",
                ],
                "properties": {
                    "path": {"type": "string"},
                    "sha256": {"type": "string", "pattern": sha_pattern},
                    "same_effect_on_render_queue_item": {"const": True},
                    "same_process": {"const": True},
                },
                "additionalProperties": False,
            },
            "probe": {
                "type": "object",
                "required": [
                    "x",
                    "y",
                    "physical_channel_order",
                    "exr_float32",
                    "exr_raw_u32",
                    "logical_rgba_float32",
                    "png_rgba8",
                ],
                "properties": {
                    "x": {"const": 1614},
                    "y": {"const": 6},
                    "physical_channel_order": {"const": ["A", "B", "G", "R"]},
                    "exr_float32": {
                        "type": "array",
                        "minItems": 4,
                        "maxItems": 4,
                    },
                    "exr_raw_u32": {
                        "type": "array",
                        "minItems": 4,
                        "maxItems": 4,
                        "items": {"type": "integer", "minimum": 0},
                    },
                    "logical_rgba_float32": {
                        "type": "array",
                        "minItems": 4,
                        "maxItems": 4,
                    },
                    "png_rgba8": {
                        "type": "array",
                        "minItems": 4,
                        "maxItems": 4,
                        "items": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 255,
                        },
                    },
                },
                "additionalProperties": False,
            },
            "output_module_settings_sha256": {
                "type": "string",
                "pattern": sha_pattern,
            },
            "diagnostic_output_module_settings_sha256": {
                "type": "string",
                "pattern": sha_pattern,
            },
            "process_attestation_sha256": {
                "type": "string",
                "pattern": sha_pattern,
            },
            "render_queue_item_id": {
                "type": "string",
                "minLength": 1,
            },
        },
    }
    kira_writer_schema: dict[str, object] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "olmkirakira-writer-trace.schema.json",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "kind",
            "binding",
            "writer_call_rva",
            "xy",
            "mxcsr_raw_u32",
            "loaded_aex_sha256",
            "source_sha256",
            "effect_on_exr_sha256",
            "effect_on_png_sha256",
            "same_effect_on_render_queue_item",
            "same_process",
            "output_module_settings_sha256",
            "diagnostic_output_module_settings_sha256",
            "process_attestation_sha256",
            "render_queue_item_id",
            "records",
        ],
        "properties": {
            "schema_version": {"const": 1},
            "kind": {"const": "olmkirakira_pf8_outer_writer_trace_v1"},
            "binding": evidence_binding_schema["properties"]["binding"],
            "writer_call_rva": {
                "enum": ["0x18114e3e9", "0x18114e287"]
            },
            "xy": {"const": [934, 118]},
            "mxcsr_raw_u32": {
                "type": "integer",
                "minimum": 0,
                "maximum": 4294967295,
            },
            "loaded_aex_sha256": {"const": AEX_SOURCES["OLMKiraKira.aex"]},
            "source_sha256": {"type": "string", "pattern": sha_pattern},
            "effect_on_exr_sha256": {"type": "string", "pattern": sha_pattern},
            "effect_on_png_sha256": {"type": "string", "pattern": sha_pattern},
            "same_effect_on_render_queue_item": {"const": True},
            "same_process": {"const": True},
            "output_module_settings_sha256": {
                "type": "string",
                "pattern": sha_pattern,
            },
            "diagnostic_output_module_settings_sha256": {
                "type": "string",
                "pattern": sha_pattern,
            },
            "process_attestation_sha256": {
                "type": "string",
                "pattern": sha_pattern,
            },
            "render_queue_item_id": {
                "type": "string",
                "minLength": 1,
            },
            "records": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "owner_plus_0x44",
                    "owner_plus_0x128_pointer",
                    "owner_plus_0x190_pointer",
                    "source_rgba_f32",
                    "glow_rgba_f32",
                    "xmm0_3",
                    "destination_rsp_plus_0x20",
                    "post_writer_argb8",
                    "exported_rgba8",
                ],
                "properties": {
                    "owner_plus_0x44": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 4294967295,
                    },
                    "owner_plus_0x128_pointer": {
                        "oneOf": [
                            {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 18446744073709551615,
                            },
                            {
                                "type": "string",
                                "pattern": (
                                    "^0x(?=[0-9a-fA-F`]*[1-9a-fA-F])(?:[0-9a-fA-F]{1,16}|"
                                    "[0-9a-fA-F]{1,8}`[0-9a-fA-F]{1,8})$"
                                ),
                            },
                        ],
                    },
                    "owner_plus_0x190_pointer": {
                        "oneOf": [
                            {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 18446744073709551615,
                            },
                            {
                                "type": "string",
                                "pattern": (
                                    "^0x(?=[0-9a-fA-F`]*[1-9a-fA-F])(?:[0-9a-fA-F]{1,16}|"
                                    "[0-9a-fA-F]{1,8}`[0-9a-fA-F]{1,8})$"
                                ),
                            },
                        ],
                    },
                    "source_rgba_f32": {
                        "type": "array",
                        "minItems": 4,
                        "maxItems": 4,
                        "items": {"type": "number"},
                    },
                    "glow_rgba_f32": {
                        "type": "array",
                        "minItems": 4,
                        "maxItems": 4,
                        "items": {"type": "number"},
                    },
                    "xmm0_3": {
                        "type": "array",
                        "minItems": 4,
                        "maxItems": 4,
                        "items": {"type": "number"},
                    },
                    "destination_rsp_plus_0x20": {
                        "oneOf": [
                            {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 18446744073709551615,
                            },
                            {
                                "type": "string",
                                "pattern": (
                                    "^0x(?=[0-9a-fA-F`]*[1-9a-fA-F])(?:[0-9a-fA-F]{1,16}|"
                                    "[0-9a-fA-F]{1,8}`[0-9a-fA-F]{1,8})$"
                                ),
                            },
                        ],
                    },
                    "post_writer_argb8": {
                        "type": "array",
                        "minItems": 4,
                        "maxItems": 4,
                        "items": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 255,
                        },
                    },
                    "exported_rgba8": {
                        "type": "array",
                        "minItems": 4,
                        "maxItems": 4,
                        "items": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 255,
                        },
                    },
                },
            },
        },
    }
    diagnostic_row_binding = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "row_id",
            "execution_row_sha256",
            "case_contract_sha256",
            "source_sha256",
            "aex_sha256",
            "project_sha256",
            "effect_on_sha256",
            "process_attestation_sha256",
            "render_queue_item_id",
        ],
        "properties": {
            "row_id": {"type": "string", "minLength": 1},
            "execution_row_sha256": {
                "type": "string",
                "pattern": sha_pattern,
            },
            "case_contract_sha256": {
                "type": "string",
                "pattern": sha_pattern,
            },
            "source_sha256": {"type": "string", "pattern": sha_pattern},
            "aex_sha256": {"type": "string", "pattern": sha_pattern},
            "project_sha256": {"type": "string", "pattern": sha_pattern},
            "effect_on_sha256": {"type": "string", "pattern": sha_pattern},
            "process_attestation_sha256": {
                "type": "string",
                "pattern": sha_pattern,
            },
            "render_queue_item_id": {"type": "string", "minLength": 1},
        },
    }
    kira_pf32_trace_schema: dict[str, object] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "olmkirakira-pf32-trace.schema.json",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "kind",
            "campaign_id",
            "batch_manifest_sha256",
            "rows",
            "data",
        ],
        "properties": {
            "schema_version": {"const": 1},
            "kind": {
                "enum": [
                    "olmkirakira_pf32_approximated_input_trace_v1",
                    "olmkirakira_pf32_highlight_radius_trace_v1",
                    "olmkirakira_pf32_highlight_color_trace_v1",
                    "olmkirakira_pf32_mode4_trace_v1",
                ]
            },
            "campaign_id": {"const": CAMPAIGN_ID},
            "batch_manifest_sha256": {
                "type": "string",
                "pattern": sha_pattern,
            },
            "rows": {
                "type": "array",
                "minItems": 2,
                "maxItems": 2,
                "items": diagnostic_row_binding,
            },
            "data": {
                "type": "object",
                "additionalProperties": False,
                "required": ["instrumentation", "trace_records"],
                "properties": {
                    "instrumentation": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "capture_method",
                            "trace_tool",
                            "trace_session_id",
                            "declared_only_different_match_name",
                            "trace_point_contract",
                            "process_attestation_sha256_by_row",
                        ],
                        "properties": {
                            "capture_method": {
                                "type": "string",
                                "minLength": 1,
                            },
                            "trace_tool": {
                                "type": "string",
                                "minLength": 1,
                            },
                            "trace_session_id": {
                                "type": "string",
                                "minLength": 1,
                            },
                            "declared_only_different_match_name": {
                                "type": "string",
                                "minLength": 1,
                            },
                            "trace_point_contract": {
                                "const": (
                                    "same_xy_same_input_one_control_delta_"
                                    "with_different_stage"
                                )
                            },
                            "process_attestation_sha256_by_row": {
                                "type": "object",
                                "minProperties": 2,
                                "maxProperties": 2,
                                "additionalProperties": {
                                    "type": "string",
                                    "pattern": sha_pattern,
                                },
                            },
                        },
                    },
                    "trace_records": {
                        "type": "array",
                        "minItems": 2,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "row_id",
                                "record_index",
                                "event",
                                "payload",
                            ],
                            "properties": {
                                "row_id": {
                                    "type": "string",
                                    "minLength": 1,
                                },
                                "record_index": {
                                    "type": "integer",
                                    "minimum": 0,
                                },
                                "event": {
                                    "type": "string",
                                    "enum": [
                                        "approximated_input_stage_sample",
                                        "highlight_radius_stage_sample",
                                        "highlight_color_stage_sample",
                                        "mode4_recurrence_stage_sample",
                                    ],
                                },
                                "payload": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": [
                                        "x",
                                        "y",
                                        "control_match_name",
                                        "control_value",
                                        "input_rgba_f32",
                                        "stage_rgba_f32",
                                    ],
                                    "properties": {
                                        "x": {
                                            "type": "integer",
                                            "minimum": 0,
                                        },
                                        "y": {
                                            "type": "integer",
                                            "minimum": 0,
                                        },
                                        "control_match_name": {
                                            "type": "string",
                                            "minLength": 1,
                                        },
                                        "control_value": {},
                                        "input_rgba_f32": {
                                            "type": "array",
                                            "minItems": 4,
                                            "maxItems": 4,
                                            "items": {"type": "number"},
                                        },
                                        "stage_rgba_f32": {
                                            "type": "array",
                                            "minItems": 4,
                                            "maxItems": 4,
                                            "items": {"type": "number"},
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    }
    kira_kernel_schema: dict[str, object] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "olmkirakira-gaussian-kernel.schema.json",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "kind",
            "campaign_id",
            "batch_manifest_sha256",
            "rows",
            "binary_member",
            "binary_sha256",
            "byte_count",
            "element_count",
            "encoding",
            "float32_u32_le",
        ],
        "properties": {
            "schema_version": {"const": 1},
            "kind": {
                "const": "olmkirakira_gaussian_kernel_21_f32_le_v1"
            },
            "campaign_id": {"const": CAMPAIGN_ID},
            "batch_manifest_sha256": {
                "type": "string",
                "pattern": sha_pattern,
            },
            "rows": {
                "type": "array",
                "minItems": 3,
                "maxItems": 3,
                "items": diagnostic_row_binding,
            },
            "binary_member": {
                "const": (
                    "diagnostics/OLMKiraKira/32bpc/controlled_matrix/"
                    "gaussian_kernel_21_f32_le.bin"
                )
            },
            "binary_sha256": {"type": "string", "pattern": sha_pattern},
            "byte_count": {"const": 84},
            "element_count": {"const": 21},
            "encoding": {
                "const": "IEEE-754 binary32 little-endian"
            },
            "float32_u32_le": {
                "type": "array",
                "minItems": 21,
                "maxItems": 21,
                "items": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 4294967295,
                },
            },
        },
    }
    return {
        "BATCH_MANIFEST.schema.json": batch_schema,
        "EVIDENCE_BINDING.schema.json": evidence_binding_schema,
        "RETURN_STATUS.schema.json": return_status_schema,
        "OLMKIRAKIRA_CROSS_ROW.schema.json": cross_row_schema,
        "OLMRADIALBLUR_WITNESS.schema.json": radial_witness_schema,
        "OLMKIRAKIRA_WRITER_TRACE.schema.json": kira_writer_schema,
        "OLMKIRAKIRA_PF32_TRACE.schema.json": kira_pf32_trace_schema,
        "OLMKIRAKIRA_GAUSSIAN_KERNEL.schema.json": kira_kernel_schema,
    }


def build_campaign_manifest(inputs: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema_version": 2,
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
            "working_space_normalized": None,
            "working_space_raw_accepted": [None, ""],
            "linear_blending": False,
            "blend_colors_using_1_0_gamma": False,
            "frame_rate": 24,
            "frame": 24,
            "time_seconds": 1.0,
            "comp_contract": (
                "authoritative per row in ROW_INVENTORY.comp; comp dimensions "
                "equal the bound source dimensions, source layer is centered at "
                "100% scale, pixel aspect is 1, and resolution factor is [1,1]"
            ),
            "depths": [8, 16, 32],
            "input_interpretation": {
                "method": "hash_bound_aep_template_footage_replace",
                "replace_method": "FootageItem.replace(File)",
                "preserve_rgb": True,
                "alpha_mode": "straight",
                "premultiplied": False,
                "template_member": "inputs/preserve_rgb_template.aep",
                "template_sha256": (
                    "51fd5403b0a43825f0f6d189c49154ad756f4c565498f733c1fb725377583679"
                ),
                "footage_item_name": "OLM_COLOR_PROBE_INPUT",
                "comp_item_name": "OLM_COLOR_PROBE_COMP",
                "comp_layer_index": 1,
                "expected_num_layers": 1,
                "source_identity_gate": (
                    "comp.layer(1).source.id == footage_item.id after replace"
                ),
                "effect_parade_must_be_empty_before_add": True,
                "verification": "paired no-effect raw FLOAT32 gate",
            },
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
            "image_policy": {
                "authoritative_reference_images": [
                    "no_effect.exr",
                    "effect_on.exr",
                ],
                "pass_case_png_required": False,
                "targeted_pass_case_diagnostic_exceptions": [
                    "OLMRadialBlur canonical 20260604 case0010 at 8bpc",
                    "OLMKiraKira controlled Merge1 and Merge2 PF8 rows at 8bpc",
                ],
                "failure_only_ui_screenshot": True,
                "png_is_diagnostic_only": True,
            },
        },
        "inputs": inputs,
        "lanes": LANES,
        "row_inventory": {
            "member": "ROW_INVENTORY.json",
            "expected_rows": EXPECTED_TOTAL_ROWS,
            "must_reproduce_exact_row_ids": True,
            "must_reproduce_exact_ordered_row_objects": True,
        },
        "execution_rows": {
            "member": "EXECUTION_ROWS.json",
            "expected_rows": EXPECTED_TOTAL_ROWS,
            "fully_materialized": True,
            "batch_manifest_must_deep_equal_ordered_rows": True,
        },
        "expected_row_count": sum(int(lane["rows_estimate"]) for lane in LANES),
        "expected_render_count": 2 * sum(int(lane["rows_estimate"]) for lane in LANES),
        "all_rows_terminal_required": True,
        "targeted_diagnostics": [
            {
                "plugin": "OLMRadialBlur",
                "depth": 8,
                "case_id": "olmradialblur__canonical_20260604_case_0010_tiny_rotation",
                "required": [
                    "same-run effect-on PNG",
                    "raw/exr and PNG values at x=1614,y=6",
                    "process/output-module linkage proving the diagnostic belongs to the row",
                ],
                "claim_boundary": "diagnostic only; raw EXR remains authoritative",
            },
            {
                "plugin": "OLMKiraKira",
                "depth": 8,
                "case_ids": [
                    "kk_mapped_bm2_mm1_ray_f0_a0_opaque",
                    "kk_mapped_bm2_mm2_ray_f0_a0_opaque",
                ],
                "required": [
                    "effect-on PNG as a second output module on the same render-queue item and process",
                    "typed outer-writer traces at XY (934,118)",
                    "Merge1 call 0x18114e3e9 and Merge2 call 0x18114e287",
                    "row/process/AEX/source/output hashes plus owner/pointer/source/glow/XMM/destination/post-writer records",
                ],
                "claim_boundary": "diagnostic only; does not substitute for AE raw exactness",
            },
        ],
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


def load_request_cases(name: str) -> list[dict[str, object]]:
    path = ROOT / "refs" / "reference_requests" / name
    if not path.is_file() or path.is_symlink():
        fail(f"missing or unsafe request seed: {name}")
    value = json.loads(path.read_text(encoding="utf-8"))
    cases = value.get("cases")
    if not isinstance(cases, list):
        fail(f"request seed has no cases array: {name}")
    return cases


def case_effect_name(case: dict[str, object]) -> str | None:
    effect = case.get("effect")
    if isinstance(effect, dict):
        name = effect.get("name")
        return name if isinstance(name, str) else None
    return None


def build_row_inventory() -> dict[str, object]:
    input_members = {f"inputs/{name}" for name, _, _, _ in INPUT_SOURCES}
    input_hashes = {
        f"inputs/{name}": digest for name, _, digest, _ in INPUT_SOURCES
    }
    input_dimensions: dict[str, list[int]] = {}
    for name, _, _, description in INPUT_SOURCES:
        first_token = description.split()[0]
        if "x" not in first_token:
            continue
        width_text, height_text = first_token.lower().split("x", 1)
        if width_text.isdigit() and height_text.isdigit():
            input_dimensions[f"inputs/{name}"] = [
                int(width_text),
                int(height_text),
            ]
    groups: list[dict[str, object]] = []
    rows: list[dict[str, object]] = []

    def add_group(
        *,
        plugin: str,
        group_id: str,
        depths: list[int],
        cases: list[dict[str, object]],
        case_definition_file: str,
        source_for: object,
        intentional_noop_ids: set[str] | None = None,
        source_policy: str,
        cross_row_comparison: dict[str, object] | None = None,
    ) -> None:
        noop_ids = intentional_noop_ids or set()
        case_definition_path = PACKAGE_DIR / case_definition_file
        if (
            not case_definition_path.is_file()
            or case_definition_path.is_symlink()
            or not case_definition_path.resolve().is_relative_to(PACKAGE_DIR.resolve())
        ):
            fail(f"{group_id}: missing or unsafe case definition: {case_definition_file}")
        case_definition_sha256 = sha256(case_definition_path)
        case_definition_value = json.loads(
            case_definition_path.read_text(encoding="utf-8")
        )
        case_definition_cases = case_definition_value.get("cases")
        if not isinstance(case_definition_cases, list):
            fail(f"{group_id}: case definition has no cases array")
        case_contract_by_id = {
            str(case["case_id"]): case
            for case in case_definition_cases
            if isinstance(case, dict) and isinstance(case.get("case_id"), str)
        }
        aex_member = PLUGIN_AEX_MEMBERS.get(plugin)
        if aex_member is None:
            fail(f"{group_id}: no AEX mapping for plugin {plugin}")
        aex_name = Path(aex_member).name
        aex_sha256 = AEX_SOURCES.get(aex_name)
        if aex_sha256 is None:
            fail(f"{group_id}: no AEX hash for {aex_member}")
        case_ids: list[str] = []
        row_ids: list[str] = []
        for case in cases:
            case_id = case.get("id")
            if not isinstance(case_id, str) or not case_id:
                fail(f"{group_id}: case without a string id")
            if case_id in case_ids:
                fail(f"{group_id}: duplicate case id: {case_id}")
            case_contract = case_contract_by_id.get(case_id)
            if case_contract is None:
                fail(f"{group_id}: case id absent from materialized definition: {case_id}")
            case_ids.append(case_id)
            source_member = source_for(case)  # type: ignore[operator]
            if source_member not in input_members:
                fail(f"{group_id}/{case_id}: unknown source member: {source_member}")
            source_dimensions = input_dimensions.get(source_member)
            if source_dimensions is None:
                fail(f"{group_id}/{case_id}: source dimensions are undeclared")
            for depth in depths:
                declared_depths = case_contract.get("depths")
                if isinstance(declared_depths, list) and depth not in declared_depths:
                    fail(f"{group_id}/{case_id}: depth {depth} absent from case contract")
                declared_source = case_contract.get("source")
                source_by_depth = case_contract.get("source_by_depth")
                if isinstance(source_by_depth, dict):
                    declared_source = source_by_depth.get(str(depth))
                if not isinstance(declared_source, dict):
                    fail(f"{group_id}/{case_id}: materialized source is missing")
                if (
                    declared_source.get("member") != source_member
                    or declared_source.get("sha256") != input_hashes[source_member]
                ):
                    fail(f"{group_id}/{case_id}: materialized source disagrees with inventory")
                row_id = f"{plugin}__{group_id}__{case_id}__{depth}bpc"
                row_id = (
                    row_id.lower()
                    .replace(" ", "_")
                    .replace("/", "_")
                    .replace("-", "_")
                )
                if any(row["row_id"] == row_id for row in rows):
                    fail(f"duplicate row id: {row_id}")
                intentional_noop = case_id in noop_ids
                if bool(case_contract.get("intentional_noop")) != intentional_noop:
                    fail(f"{group_id}/{case_id}: intentional-noop contract drift")
                row_ids.append(row_id)
                rows.append(
                    {
                        "row_id": row_id,
                        "plugin": plugin,
                        "group_id": group_id,
                        "case_id": case_id,
                        "depth": depth,
                        "source_member": source_member,
                        "source_sha256": input_hashes[source_member],
                        "aex_member": aex_member,
                        "aex_sha256": aex_sha256,
                        "comp": {
                            "width": source_dimensions[0],
                            "height": source_dimensions[1],
                            "pixel_aspect": 1.0,
                            "frame_rate": 24,
                            "frame": 24,
                            "time_seconds": 1.0,
                            "duration_seconds": 2.0,
                            "render_time_span_start_seconds": 1.0,
                            "render_time_span_duration_seconds": 1.0 / 24.0,
                            "resolution_factor": [1, 1],
                            "source_layer_scale": [100.0, 100.0],
                            "source_layer_centered": True,
                            "source_layer_index": 1,
                            "num_layers": 1,
                        },
                        "case_definition_file": case_definition_file,
                        "case_definition_sha256": case_definition_sha256,
                        "case_contract_sha256": canonical_json_sha256(case_contract),
                        "intentional_noop": intentional_noop,
                        "expected_raw_off_on_relation": (
                            "identical" if intentional_noop else "different"
                        ),
                    }
                )
        if noop_ids - set(case_ids):
            fail(f"{group_id}: unknown intentional-noop ids: {sorted(noop_ids - set(case_ids))}")
        group = {
            "plugin": plugin,
            "group_id": group_id,
            "depths": depths,
            "case_definition_file": case_definition_file,
            "case_definition_sha256": case_definition_sha256,
            "aex_member": aex_member,
            "aex_sha256": aex_sha256,
            "case_ids": case_ids,
            "case_count": len(case_ids),
            "row_count": len(row_ids),
            "row_ids": row_ids,
            "source_policy": source_policy,
        }
        if cross_row_comparison is not None:
            group["cross_row_comparison"] = cross_row_comparison
        groups.append(group)

    odd_even = lambda odd, even: (
        lambda case: odd if int(str(case["id"])[-2:]) % 2 else even
    )

    normalized_name = "olm_bitdepth_16bpc_normalized_exact_20260625.json"
    normalized_cases = load_request_cases(normalized_name)
    dg_canonical = [
        case for case in normalized_cases if case_effect_name(case) == "Distance Gradation"
    ]
    add_group(
        plugin="OLMDistanceGradation",
        group_id="canonical_29_integer_source",
        depths=[8, 16],
        cases=dg_canonical,
        case_definition_file="case_definitions/olmdistancegradation_materialized_33.json",
        source_for=lambda case: "inputs/distancegradation_nonopaque_rgba8.png",
        source_policy="all 29 8/16bpc cases use the bundled nonopaque RGBA8 source",
    )
    add_group(
        plugin="OLMDistanceGradation",
        group_id="canonical_29_float_source",
        depths=[32],
        cases=dg_canonical,
        case_definition_file="case_definitions/olmdistancegradation_materialized_33.json",
        source_for=lambda case: "inputs/distancegradation_float_source.exr",
        source_policy=(
            "all 29 32bpc cases use the same bundled FLOAT32 source with "
            "Preserve RGB and straight alpha"
        ),
    )
    dg_bg_name = "olmdistancegradation_16bpc_bg_compose_variants_20260626.json"
    dg_bg_cases = [
        case
        for case in load_request_cases(dg_bg_name)
        if str(case.get("id", "")).endswith("_bg_off_variant")
    ]
    add_group(
        plugin="OLMDistanceGradation",
        group_id="background_off_4",
        depths=[8, 16, 32],
        cases=dg_bg_cases,
        case_definition_file="case_definitions/olmdistancegradation_materialized_33.json",
        source_for=lambda case: "inputs/distancegradation_bg_off_rgba16.png",
        source_policy="all four background-off variants use the bundled RGBA16 fixture",
    )

    directional_final_name = "olm_final_random10_olm_directionalblur_20260629.json"
    add_group(
        plugin="OLMDirectionalBlur",
        group_id="final_random_10",
        depths=[8, 16, 32],
        cases=load_request_cases(directional_final_name),
        case_definition_file="case_definitions/olmdirectionalblur_materialized_18.json",
        source_for=odd_even(
            "inputs/final_random_float_grid.exr",
            "inputs/final_random_float_alternate.exr",
        ),
        source_policy="odd/even case ids use the two bundled FLOAT32 EXRs",
    )
    directional_context_name = "directionalblur_context_scale_20260606.json"
    directional_input_map = {
        "opaque_cell_edges": "inputs/opaque_cells_rgba8.png",
        "alpha_hard_edges": "inputs/hard_alpha_edges_rgba8.png",
        "alpha_ramp_rgb": "inputs/alpha_ramp_rgba8.png",
    }
    add_group(
        plugin="OLMDirectionalBlur",
        group_id="context_scale_8",
        depths=[8, 16, 32],
        cases=load_request_cases(directional_context_name),
        case_definition_file="case_definitions/olmdirectionalblur_materialized_18.json",
        source_for=lambda case: directional_input_map[str(case["input"])],
        source_policy="request input ids map exactly to the three bundled RGBA8 fixtures",
    )

    radial_size_name = "radialblur_inner_size_variation_20260606.json"
    radial_selected_ids = {
        "rb_inner_sv000_edge000",
        "rb_inner_sv050_edge000",
        "rb_inner_alpha_sv050_edge000",
        "rb_inner_alpha_sv050_edge025",
    }
    radial_selected_cases = [
        case
        for case in load_request_cases(radial_size_name)
        if str(case.get("id")) in radial_selected_ids
    ]
    if {str(case["id"]) for case in radial_selected_cases} != radial_selected_ids:
        fail("RadialBlur selected Inner/Size Variation cases drifted")
    radial_size_map = {
        "current_olm_cells": "inputs/opaque_cells_rgba8.png",
        "alpha_grid": "inputs/radial_alpha_grid_rgba8.png",
    }
    add_group(
        plugin="OLMRadialBlur",
        group_id="controlled_inner_size_variation_4",
        depths=[8, 16, 32],
        cases=radial_selected_cases,
        case_definition_file="case_definitions/olmradialblur_minimal_controlled_r4.json",
        source_for=lambda case: radial_size_map[str(case["input"])],
        source_policy=(
            "opaque cases use the exact historical opaque-cells hash; nonopaque "
            "cases use the alpha-grid fixture"
        ),
    )
    add_group(
        plugin="OLMRadialBlur",
        group_id="canonical_20260604_zoom_rotation_2",
        depths=[8, 16, 32],
        cases=[
            {"id": "olmradialblur__canonical_20260604_case_0009_zoom"},
            {"id": "olmradialblur__canonical_20260604_case_0010_tiny_rotation"},
        ],
        case_definition_file=(
            "case_definitions/olmradialblur_minimal_controlled_r4.json"
        ),
        source_for=lambda case: "inputs/shared_blur_colorkey_rgba8.png",
        source_policy=(
            "both explicitly generation-qualified canonical cases use the same "
            "hash-bound cells fixture; do not substitute 20260605 case numbers"
        ),
    )

    add_group(
        plugin="OLMKiraKira",
        group_id="controlled_ramps_off_10",
        depths=[8, 16, 32],
        cases=[{"id": case_id} for case_id in KIRAKIRA_CONTROLLED_CASE_IDS],
        case_definition_file="case_definitions/olmkirakira_controlled_ramps_off_matrix.json",
        source_for=lambda case: (
            "inputs/alpha_ramp_rgba8.png"
            if str(case["id"]) in KIRAKIRA_ALPHA_CASE_IDS
            else "inputs/opaque_cells_rgba8.png"
        ),
        intentional_noop_ids=KIRAKIRA_INTENTIONAL_NOOP_IDS,
        source_policy=(
            "the three Approximated Input/Fade cases use the alpha-ramp fixture; "
            "the other seven use opaque cells; all 25 mapped match-name writes "
            "are fully materialized and all five Use Ramp values are zero"
        ),
        cross_row_comparison={
            "definition_file": (
                "case_definitions/olmkirakira_controlled_ramps_off_matrix.json"
            ),
            "report": "cross_row/olmkirakira_controlled_matrix.json",
            "per_depth": True,
            "pair_count_per_depth": 7,
            "all_declared_differentials_must_be_nonzero": True,
        },
    )

    smoother_name = "olmsmoother_v1_bitdepth_16_32bpc_software_20260715.json"
    smoother_source_map = {
        "case_0001": "inputs/smoother_v1_case0001_rgba8.png",
        "case_0002": "inputs/smoother_v1_case0002_rgba8.png",
        "case_0003": "inputs/smoother_v1_case0003_rgba8.png",
    }
    add_group(
        plugin="OLMSmoother v1",
        group_id="canonical_3",
        depths=[8, 16, 32],
        cases=load_request_cases(smoother_name),
        case_definition_file="case_definitions/olmsmoother_v1_materialized_13.json",
        source_for=lambda case: smoother_source_map[str(case["id"])],
        source_policy="each canonical case uses its exact bundled RGBA8 fixture",
    )
    smoother_final_name = "olm_final_random10_olm_smoother_20260629.json"
    add_group(
        plugin="OLMSmoother v1",
        group_id="final_random_10",
        depths=[32],
        cases=load_request_cases(smoother_final_name),
        case_definition_file="case_definitions/olmsmoother_v1_materialized_13.json",
        source_for=odd_even(
            "inputs/smoother_v1_float_odd.exr",
            "inputs/smoother_v1_float_even.exr",
        ),
        source_policy=(
            "odd/even ids use the two bundled Preserve-RGB Mac control EXRs; "
            "the old Windows before-effect files and their old no-op labels are rejected"
        ),
    )

    colorkeep_lane = next(lane for lane in LANES if lane["plugin"] == "ColorKeep")
    colorkeep_cases = [
        {"id": case["case_id"], "fixture": case["fixture"]}
        for case in colorkeep_lane["cases"]  # type: ignore[index]
    ]
    add_group(
        plugin="ColorKeep",
        group_id="discovery_3",
        depths=[8, 16, 32],
        cases=colorkeep_cases,
        case_definition_file="case_definitions/colorkeep_controlled_discovery_3.json",
        source_for=lambda case: str(case["fixture"]),
        intentional_noop_ids={"colorkeep_two_color_identity"},
        source_policy="each case binds the explicit fixture declared in the ColorKeep lane",
    )

    lane_counts: dict[str, int] = {}
    for row in rows:
        plugin = str(row["plugin"])
        lane_counts[plugin] = lane_counts.get(plugin, 0) + 1
    expected_lane_counts = RETURN_CONTRACT["row_contract"]["expected_lane_rows"]
    if lane_counts != expected_lane_counts:
        fail(f"row inventory lane mismatch: actual={lane_counts} expected={expected_lane_counts}")
    if len(rows) != RETURN_CONTRACT["row_contract"]["expected_total_rows"]:
        fail(f"row inventory total mismatch: {len(rows)}")
    return {
        "schema_version": 1,
        "campaign_id": CAMPAIGN_ID,
        "claim_boundary": (
            "This is the exact outbound row inventory. Windows must reproduce "
            "these row_ids exactly once in BATCH_MANIFEST and RETURN_STATUS."
        ),
        "row_count": len(rows),
        "lane_counts": lane_counts,
        "groups": groups,
        "rows": rows,
    }


def build_execution_rows(row_inventory: dict[str, object]) -> dict[str, object]:
    definition_cache: dict[str, dict[str, object]] = {}
    case_cache: dict[tuple[str, str], dict[str, object]] = {}
    execution_rows: list[dict[str, object]] = []
    rows = row_inventory.get("rows")
    if not isinstance(rows, list):
        fail("row inventory has no rows array")
    for row in rows:
        if not isinstance(row, dict):
            fail("row inventory contains a non-object row")
        definition_member = str(row["case_definition_file"])
        definition = definition_cache.get(definition_member)
        if definition is None:
            definition_path = PACKAGE_DIR / definition_member
            definition = json.loads(definition_path.read_text(encoding="utf-8"))
            definition_cache[definition_member] = definition
            cases = definition.get("cases")
            if not isinstance(cases, list):
                fail(f"execution definition has no cases: {definition_member}")
            for case in cases:
                if not isinstance(case, dict) or not isinstance(
                    case.get("case_id"), str
                ):
                    fail(f"execution definition has an invalid case: {definition_member}")
                case_cache[(definition_member, str(case["case_id"]))] = case
        case_contract = case_cache.get((definition_member, str(row["case_id"])))
        if case_contract is None:
            fail(f"execution case is missing: {row['row_id']}")
        surface = definition.get("surface")
        if surface is None:
            surface = definition.get("surface_contract")
        if not isinstance(surface, dict):
            fail(f"execution surface is missing: {row['row_id']}")
        writes = case_contract.get("writes")
        if writes is None:
            writes = case_contract.get("parameter_writes")
        if not isinstance(writes, list):
            fail(f"execution writes are missing: {row['row_id']}")
        surface_rows = {
            item.get("match_name"): item
            for item in surface.get("exact_rows", [])
            if isinstance(item, dict) and isinstance(item.get("match_name"), str)
        }
        parameter_actions: list[dict[str, object]] = []
        for write in writes:
            if not isinstance(write, dict):
                fail(f"execution parameter action is not an object: {row['row_id']}")
            action = dict(write)
            if action.get("write") is False:
                action["action"] = "verify_fresh_default"
                action["write"] = False
                if (
                    "expected_fresh_default" not in action
                    or action.get("value") != action["expected_fresh_default"]
                ):
                    fail(f"verify-default action is incomplete: {row['row_id']}")
            else:
                action["action"] = "set"
                action["write"] = True
                if "value" not in action:
                    fail(f"set action has no value: {row['row_id']}")
            property_type = action.get("property_type")
            value = action.get("value")
            surface_row = surface_rows.get(action.get("match_name"), {})
            default_value = surface_row.get("default")
            if property_type in (6415, 6418):
                action["value_type"] = (
                    "point" if property_type == 6415 else "color"
                )
                action["comparison_mode"] = "float32_u32_vector"
            elif property_type == 6421:
                action["value_type"] = "layer_index"
                action["comparison_mode"] = "exact_integer"
            elif isinstance(value, float) or isinstance(default_value, float):
                action["value_type"] = "scalar_float"
                action["comparison_mode"] = "float32_u32_scalar"
            else:
                action["value_type"] = "integer_or_popup"
                action["comparison_mode"] = "exact_integer"
            if str(action["comparison_mode"]).startswith("float32_u32_"):
                canonical_value, raw_words = float32_value_and_u32(action["value"])
                action["value"] = canonical_value
                action["value_raw_f32_u32"] = raw_words
                if action["action"] == "verify_fresh_default":
                    action["expected_fresh_default"] = canonical_value
            parameter_actions.append(action)
        execution_row: dict[str, object] = {
            **row,
            "effect": {
                "display_name": definition.get("effect_display_name"),
                "match_name": definition.get("effect_match_name"),
            },
            "parameter_surface": surface,
            "parameter_writes": parameter_actions,
            "parameter_action_semantics": {
                "set": (
                    "Resolve exactly one recursive leaf by exact match_name, set "
                    "value, then read back before and after render."
                ),
                "verify_fresh_default": (
                    "Do not call setValue. Before any render, require the fresh "
                    "effect value to equal expected_fresh_default, then read back "
                    "the same value after render."
                ),
            },
            "standard_options": COMMON_STANDARD_OPTIONS,
            "project_contract": {
                "ae_version": "26.3x87",
                "renderer": "SOFTWARE",
                "renderer_raw": 1816,
                "bits_per_channel": row["depth"],
                "working_space_normalized": None,
                "working_space_raw_accepted": [None, ""],
                "linear_blending": False,
                "blend_colors_using_1_0_gamma": False,
                "comp": row["comp"],
                "input_interpretation": {
                    "method": "hash_bound_aep_template_footage_replace",
                    "replace_method": "FootageItem.replace(File)",
                    "preserve_rgb": True,
                    "alpha_mode": "straight",
                    "premultiplied": False,
                    "template_member": "inputs/preserve_rgb_template.aep",
                    "template_sha256": (
                        "51fd5403b0a43825f0f6d189c49154ad756f4c565498f733c1fb725377583679"
                    ),
                    "footage_item_name": "OLM_COLOR_PROBE_INPUT",
                    "comp_item_name": "OLM_COLOR_PROBE_COMP",
                    "comp_layer_index": 1,
                    "expected_num_layers": 1,
                    "source_identity_gate": (
                        "comp.layer(1).source.id == footage_item.id after replace"
                    ),
                    "effect_parade_must_be_empty_before_add": True,
                },
                "primary_output": {
                    "format": "OpenEXR",
                    "storage": "scanline",
                    "compression": "none",
                    "physical_channels": ["A", "B", "G", "R"],
                    "sample_type": "FLOAT32",
                    "channel_type": 2,
                },
            },
            "fresh_identity_contract": {
                "fresh_project": True,
                "fresh_effect": True,
                "fresh_nonce": True,
                "fresh_aerender_process": True,
                "render_queue_items": ["no_effect", "effect_on"],
            },
        }
        execution_row["execution_row_sha256"] = canonical_json_sha256(execution_row)
        execution_rows.append(execution_row)
    if len(execution_rows) != EXPECTED_TOTAL_ROWS:
        fail(f"execution row total drift: {len(execution_rows)}")
    return {
        "schema_version": 1,
        "campaign_id": CAMPAIGN_ID,
        "row_count": len(execution_rows),
        "claim_boundary": (
            "This is the fully resolved immutable execution contract. "
            "BATCH_MANIFEST.rows must be exact ordered deep-equal copies."
        ),
        "rows": execution_rows,
    }


def build_case_definition_overrides() -> dict[str, object]:
    input_hashes = {
        f"inputs/{name}": digest for name, _, digest, _ in INPUT_SOURCES
    }

    def source_record(member: str) -> dict[str, str]:
        digest = input_hashes.get(member)
        if digest is None:
            fail(f"case definition references an unknown source member: {member}")
        return {"member": member, "sha256": digest}

    dg_canonical_path = verified_source(
        "refs/reference_requests/olm_bitdepth_16bpc_normalized_exact_20260625.json",
        "ce6163fa71619139ab2164fa3e8ce681c1b9b739960e42fe276b04a8e7fa9da3",
    )
    dg_canonical_request = json.loads(dg_canonical_path.read_text(encoding="utf-8"))
    dg_display_names = [
        "Invert",
        "In/Out",
        "Inside Threshold",
        "Outside Threshold",
        "Render Mode",
        "Use Background Color",
        "Gradation Color",
        "BG Color ",
        "Interpolation Mode",
        "Power",
        "Blur Mode",
        "Blur Size",
    ]
    dg_defaults: list[object] = [
        0,
        1,
        128,
        128,
        1,
        0,
        [1.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 0.0, 1.0],
        2,
        1.0,
        1,
        0,
    ]
    dg_surface = [
        {
            "property_index": index,
            "match_name": f"OLM Distance Gradation-{index:04d}",
            "display_name": dg_display_names[index - 1],
            "property_type": 6418 if index in (7, 8) else 6417,
            "default": dg_defaults[index - 1],
            "enabled": True,
            "active": True,
            "write_resolution": "match_name",
        }
        for index in range(1, 13)
    ]
    dg_expected_match_names = [row["match_name"] for row in dg_surface]
    dg_cases: list[dict[str, object]] = []
    for historical_case in dg_canonical_request["cases"]:
        effect = historical_case.get("effect")
        if not isinstance(effect, dict) or effect.get("name") != "Distance Gradation":
            continue
        params_full = historical_case.get("params_full")
        if not isinstance(params_full, list) or len(params_full) != 14:
            fail(f"DistanceGradation canonical case lacks 14 params: {historical_case.get('id')}")
        plugin_rows = params_full[:12]
        if [row.get("match_name") for row in plugin_rows] != dg_expected_match_names:
            fail(f"DistanceGradation match-name drift: {historical_case.get('id')}")
        if [row.get("name") for row in plugin_rows] != dg_display_names:
            fail(f"DistanceGradation display-name drift: {historical_case.get('id')}")
        if params_full[12].get("match_name") != "ADBE Effect Mask Opacity":
            fail("DistanceGradation opacity row drift")
        if params_full[13].get("match_name") != "ADBE Force CPU GPU":
            fail("DistanceGradation GPU row drift")
        dg_cases.append(
            {
                "case_id": historical_case["id"],
                "intentional_noop": False,
                "source_by_depth": {
                    "8": source_record("inputs/distancegradation_nonopaque_rgba8.png"),
                    "16": source_record("inputs/distancegradation_nonopaque_rgba8.png"),
                    "32": source_record("inputs/distancegradation_float_source.exr"),
                },
                "writes": [
                    {
                        "match_name": row["match_name"],
                        "property_type": 6418
                        if row["match_name"]
                        in {
                            "OLM Distance Gradation-0007",
                            "OLM Distance Gradation-0008",
                        }
                        else 6417,
                        "value": row["value"],
                    }
                    for row in plugin_rows
                ],
            }
        )
    if len(dg_cases) != 29:
        fail(f"DistanceGradation canonical case count drift: {len(dg_cases)}")
    dg_bg_vectors: dict[str, list[object]] = {
        "olmdistancegradation_case_0020_bg_off_variant": [
            0,
            1,
            78,
            204,
            1,
            0,
            [0.1098041459918, 0.0, 0.93333333730698, 1.0],
            [1.0, 0.0, 0.0, 1.0],
            1,
            1.0,
            1,
            0,
        ],
        "olmdistancegradation_case_0021_bg_off_variant": [
            0,
            3,
            78,
            402,
            1,
            0,
            [0.1098041459918, 0.0, 0.93333333730698, 1.0],
            [1.0, 0.0, 0.0, 1.0],
            1,
            1.0,
            1,
            0,
        ],
        "olmdistancegradation_case_0022_bg_off_variant": [
            0,
            3,
            36,
            11,
            1,
            0,
            [0.1098041459918, 0.0, 0.93333333730698, 1.0],
            [1.0, 0.0, 0.0, 1.0],
            1,
            1.0,
            1,
            0,
        ],
        "olmdistancegradation_case_0023_bg_off_variant": [
            0,
            3,
            36,
            0,
            1,
            0,
            [0.1098041459918, 0.0, 0.93333333730698, 1.0],
            [1.0, 0.0, 0.0, 1.0],
            1,
            1.0,
            1,
            0,
        ],
    }
    for case_id, values in dg_bg_vectors.items():
        dg_cases.append(
            {
                "case_id": case_id,
                "intentional_noop": False,
                "source_by_depth": {
                    str(depth): source_record(
                        "inputs/distancegradation_bg_off_rgba16.png"
                    )
                    for depth in (8, 16, 32)
                },
                "writes": [
                    {
                        "match_name": dg_expected_match_names[index],
                        "property_type": 6418 if index in (6, 7) else 6417,
                        "value": value,
                    }
                    for index, value in enumerate(values)
                ],
            }
        )
    dg_override = {
        "schema_version": 1,
        "plugin": "OLMDistanceGradation",
        "effect_display_name": "Distance Gradation",
        "effect_match_name": "OLM Distance Gradation",
        "aex_member": "aex/DistanceGradation.aex",
        "aex_sha256": AEX_SOURCES["DistanceGradation.aex"],
        "depths": [8, 16, 32],
        "surface": {
            "plugin_only_leaf_count": 12,
            "exact_rows": dg_surface,
            "write_resolution": "exact match_name only",
        },
        "standard_options": [
            {
                "scope": "effect_compositing_option",
                "match_name": "ADBE Effect Mask Opacity",
                "property_type": 6417,
                "value": 100,
            },
            {
                "scope": "effect_compositing_option",
                "match_name": "ADBE Force CPU GPU",
                "property_type": 6417,
                "value": 1,
            },
        ],
        "cases": dg_cases,
        "historical_seed_members": [
            "requests/olm_bitdepth_16bpc_normalized_exact_20260625.json",
            "requests/olmdistancegradation_16bpc_bg_compose_variants_20260626.json",
        ],
        "historical_seed_sha256": {
            "requests/olm_bitdepth_16bpc_normalized_exact_20260625.json": sha256(
                dg_canonical_path
            ),
            "requests/olmdistancegradation_16bpc_bg_compose_variants_20260626.json": (
                "9d2454d9c6fdd6fc82ed9d71166e55b27ccd8b9132cee2aad75c71fe6e20d2df"
            ),
        },
        "rejected_historical_instructions": [
            "reversed background-request effect identity",
            "BG Color without its exact trailing space",
            "historical render_sets, depth declarations, input IDs, and variant matrices",
            "all historical 32bpc captures whose Inside Threshold readback collapsed to 1",
        ],
        "claim_boundary": "materialized case contract only; Windows AE raw references are required",
    }

    directional_writable = [
        (1, "Angle", 0, 6417),
        (2, "Brightness Gain", 1.0, 6417),
        (3, "Size Variation", 0, 6417),
        (5, "Blur Strength", 0, 6417),
        (6, "Alpha Fade", 0, 6417),
        (7, "Sharp Tail", 0, 6417),
        (10, "Blur Strength", 0, 6417),
        (11, "Alpha Fade", 0, 6417),
        (12, "Sharp Tail", 0, 6417),
        (15, "Noise Variation", 0, 6417),
        (16, "Noise Type", 1, 6417),
        (17, "Noise Layer", 0, 6421),
        (18, "Seed", 1, 6417),
        (19, "Offset", 0, 6417),
        (20, "Thickness", 10, 6417),
    ]
    directional_no_value = [
        (4, "Front Blur Parameters"),
        (8, "Sharp Tail"),
        (9, "Back Blur Parameters"),
        (13, "Sharp Tail"),
        (14, "Noise Parameters"),
        (21, "Thickness"),
    ]
    directional_surface = []
    for index, display_name, default, property_type in directional_writable:
        directional_surface.append(
            {
                "property_index": index,
                "match_name": f"OLM Directional Blur-{index:04d}",
                "display_name": display_name,
                "property_type": property_type,
                "default": default,
                "enabled": True,
                "active": True,
                "verify": True,
                "write": index != 17,
                "write_policy": (
                    "fresh-effect default gate; do not write without a proven None-layer setter"
                    if index == 17
                    else "exact match_name"
                ),
            }
        )
    for index, display_name in directional_no_value:
        directional_surface.append(
            {
                "property_index": index,
                "match_name": f"OLM Directional Blur-{index:04d}",
                "display_name": display_name,
                "property_type": 6412,
                "enabled": True,
                "active": True,
                "verify": True,
                "write": False,
            }
        )
    directional_surface.sort(key=lambda row: int(row["property_index"]))
    directional_vectors: dict[str, list[object]] = {
        "db_existing_case_0001_software_pair": [
            0, 1.0, 92, 1690, 0, 45, 0, 0, 0, 0, 1, 0, 1, 0, 10
        ],
        "db_existing_case_0005_software_pair": [
            -99, 1.0, 31, 190, 0, 20, 0, 0, 0, 0, 1, 0, 1, 0, 10
        ],
        "db_angle0_no_tail_no_size": [
            0, 1.0, 0, 240, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 10
        ],
        "db_angle0_strength_sweep_small": [
            0, 1.0, 0, 48, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 10
        ],
        "db_angle0_alpha_fade_hard_edges": [
            0, 1.0, 0, 240, 96, 0, 0, 0, 0, 0, 1, 0, 1, 0, 10
        ],
        "db_diagonal_alpha_ramp": [
            -45, 1.0, 0, 240, 96, 0, 0, 0, 0, 0, 1, 0, 1, 0, 10
        ],
        "db_size_variation_component": [
            0, 1.0, 100, 240, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 10
        ],
        "db_sharp_tail_component": [
            0, 1.0, 0, 240, 0, 75, 0, 0, 0, 0, 1, 0, 1, 0, 10
        ],
        "final_random10_olm_directionalblur_01": [
            179, 1.1928, 78, 519, 19, 37, 180, 56, 42, 8, 1, 0, 121, 27, 75
        ],
        "final_random10_olm_directionalblur_02": [
            7, 4.127, 48, 1372, 64, 25, 1972, 6, 54, 45, 3, 0, 901, 11, 28
        ],
        "final_random10_olm_directionalblur_03": [
            -166, 7.0612, 18, 2226, 9, 12, 3764, 56, 67, 82, 2, 0, 682, 46, 79
        ],
        "final_random10_olm_directionalblur_04": [
            23, 9.9954, 88, 3080, 54, 99, 1557, 6, 79, 18, 1, 0, 463, 30, 32
        ],
        "final_random10_olm_directionalblur_05": [
            -150, 2.9296, 58, 3934, 99, 87, 3349, 56, 91, 55, 1, 0, 244, 14, 83
        ],
        "final_random10_olm_directionalblur_06": [
            39, 5.8637, 28, 787, 44, 74, 1141, 7, 4, 92, 3, 0, 25, 49, 36
        ],
        "final_random10_olm_directionalblur_07": [
            -134, 8.7979, 98, 1641, 90, 61, 2933, 57, 16, 29, 2, 0, 805, 33, 87
        ],
        "final_random10_olm_directionalblur_08": [
            55, 1.7321, 67, 2495, 35, 49, 726, 7, 29, 66, 1, 0, 586, 17, 40
        ],
        "final_random10_olm_directionalblur_09": [
            -117, 4.6663, 37, 3349, 80, 36, 2518, 57, 41, 3, 1, 0, 366, 1, 91
        ],
        "final_random10_olm_directionalblur_10": [
            71, 7.6005, 7, 203, 25, 24, 310, 7, 53, 40, 3, 0, 147, 36, 44
        ],
    }
    directional_context_sources = {
        "db_existing_case_0001_software_pair": "inputs/opaque_cells_rgba8.png",
        "db_existing_case_0005_software_pair": "inputs/opaque_cells_rgba8.png",
        "db_angle0_no_tail_no_size": "inputs/opaque_cells_rgba8.png",
        "db_angle0_strength_sweep_small": "inputs/opaque_cells_rgba8.png",
        "db_angle0_alpha_fade_hard_edges": "inputs/hard_alpha_edges_rgba8.png",
        "db_diagonal_alpha_ramp": "inputs/alpha_ramp_rgba8.png",
        "db_size_variation_component": "inputs/hard_alpha_edges_rgba8.png",
        "db_sharp_tail_component": "inputs/hard_alpha_edges_rgba8.png",
    }
    directional_cases = []
    writable_match_names = [
        f"OLM Directional Blur-{index:04d}"
        for index, _, _, _ in directional_writable
    ]
    for case_id, values in directional_vectors.items():
        if len(values) != len(directional_writable):
            fail(f"DirectionalBlur vector length drift: {case_id}")
        if case_id.startswith("final_random10_"):
            suffix = int(case_id[-2:])
            member = (
                "inputs/final_random_float_grid.exr"
                if suffix % 2
                else "inputs/final_random_float_alternate.exr"
            )
        else:
            member = directional_context_sources[case_id]
        writes = []
        for (index, _, default, property_type), match_name, value in zip(
            directional_writable, writable_match_names, values, strict=True
        ):
            writes.append(
                {
                    "match_name": match_name,
                    "property_type": property_type,
                    "value": value,
                    "write": index != 17,
                    "expected_fresh_default": default if index == 17 else None,
                }
            )
        directional_cases.append(
            {
                "case_id": case_id,
                "source": source_record(member),
                "intentional_noop": False,
                "writes": writes,
            }
        )
    directional_override = {
        "schema_version": 1,
        "plugin": "OLMDirectionalBlur",
        "effect_display_name": "OLM DirectionalBlur",
        "effect_match_name": "OLM Directional Blur",
        "aex_member": "aex/OLMDirectionalBlur.aex",
        "aex_sha256": AEX_SOURCES["OLMDirectionalBlur.aex"],
        "depths": [8, 16, 32],
        "surface": {
            "plugin_only_leaf_count": 21,
            "exact_rows": directional_surface,
            "write_resolution": "exact match_name only",
            "duplicate_display_names_are_not_write_keys": True,
        },
        "standard_options": [
            {
                "scope": "effect_compositing_option",
                "match_name": "ADBE Effect Mask Opacity",
                "property_type": 6417,
                "value": 100,
            },
            {
                "scope": "effect_compositing_option",
                "match_name": "ADBE Force CPU GPU",
                "property_type": 6417,
                "value": 1,
            },
        ],
        "cases": directional_cases,
        "historical_seed_members": [
            "requests/olm_final_random10_olm_directionalblur_20260629.json",
            "requests/directionalblur_context_scale_20260606.json",
        ],
        "historical_seed_sha256": {
            "requests/olm_final_random10_olm_directionalblur_20260629.json": (
                "8ed4268cde397d36df48e6e4f1388b51e242bf3bc1773804a7d6cc8cd3c0823a"
            ),
            "requests/directionalblur_context_scale_20260606.json": (
                "21e98440401d52456e7859aa5fe3a5e95241e1d9e6f368fd96d189c4d9111310"
            ),
        },
        "rejected_historical_instructions": [
            "index-only writes",
            "Front/Back display-name aliases",
            "historical 30fps variant",
            "historical input IDs and depth declarations",
        ],
        "claim_boundary": "materialized case contract only; Windows AE raw references are required",
    }

    smoother_v1_canonical_path = verified_source(
        "refs/reference_requests/olmsmoother_v1_bitdepth_16_32bpc_software_20260715.json",
        "f2250e80ed22cb83403da379a99f63815865cb9cb244f0a2ef95c9093cb52860",
    )
    smoother_v1_final_path = verified_source(
        "refs/reference_requests/olm_final_random10_olm_smoother_20260629.json",
        "7dc4c2ac2e111713a746d5c5142137a2f968bfe3952d7620099ccb77b1540d33",
    )
    smoother_v1_canonical = json.loads(
        smoother_v1_canonical_path.read_text(encoding="utf-8")
    )
    smoother_v1_final = json.loads(
        smoother_v1_final_path.read_text(encoding="utf-8")
    )
    smoother_v1_surface = [
        {
            "property_index": 1,
            "match_name": "OLM Smoother-0001",
            "display_name": "Use Color Key",
            "property_type": 6417,
            "default": 0,
            "enabled": True,
            "active": True,
        },
        {
            "property_index": 2,
            "match_name": "OLM Smoother-0002",
            "display_name": "Color Key",
            "property_type": 6418,
            "default": [1.0, 1.0, 1.0, 1.0],
            "enabled": True,
            "active": True,
        },
        {
            "property_index": 3,
            "match_name": "OLM Smoother-0003",
            "display_name": "Do Smooth Range",
            "property_type": 6417,
            "default": 6,
            "enabled": True,
            "active": True,
        },
    ]
    smoother_v1_source_by_case = {
        "case_0001": "inputs/smoother_v1_case0001_rgba8.png",
        "case_0002": "inputs/smoother_v1_case0002_rgba8.png",
        "case_0003": "inputs/smoother_v1_case0003_rgba8.png",
    }
    smoother_v1_cases = []
    for case in smoother_v1_canonical["cases"]:
        case_id = str(case["id"])
        params = case["effect"]["params"]
        if [row["match_name"] for row in params] != [
            row["match_name"] for row in smoother_v1_surface
        ]:
            fail(f"Smoother v1 canonical surface drift: {case_id}")
        smoother_v1_cases.append(
            {
                "case_id": case_id,
                "depths": [8, 16, 32],
                "source": source_record(smoother_v1_source_by_case[case_id]),
                "intentional_noop": False,
                "writes": [
                    {
                        "match_name": row["match_name"],
                        "property_type": smoother_v1_surface[index]["property_type"],
                        "value": row["value"],
                        "float_values_canonicalized_to_f32": True,
                    }
                    for index, row in enumerate(params)
                ],
            }
        )
    for case in smoother_v1_final["cases"]:
        case_id = str(case["id"])
        params = case["params"]
        suffix = int(case_id[-2:])
        smoother_v1_cases.append(
            {
                "case_id": case_id,
                "depths": [32],
                "source": source_record(
                    "inputs/smoother_v1_float_odd.exr"
                    if suffix % 2
                    else "inputs/smoother_v1_float_even.exr"
                ),
                "intentional_noop": False,
                "writes": [
                    {
                        "match_name": "OLM Smoother-0001",
                        "property_type": 6417,
                        "value": params["__index_1"],
                        "float_values_canonicalized_to_f32": True,
                    },
                    {
                        "match_name": "OLM Smoother-0002",
                        "property_type": 6418,
                        "value": params["__index_2"],
                        "float_values_canonicalized_to_f32": True,
                    },
                    {
                        "match_name": "OLM Smoother-0003",
                        "property_type": 6417,
                        "value": params["__index_3"],
                        "float_values_canonicalized_to_f32": True,
                    },
                ],
            }
        )
    if len(smoother_v1_cases) != 13:
        fail(f"Smoother v1 materialized case count drift: {len(smoother_v1_cases)}")
    smoother_v1_override = {
        "schema_version": 1,
        "plugin": "OLMSmoother v1",
        "effect_display_name": "OLM Smoother",
        "effect_match_name": "OLM Smoother",
        "aex_member": "aex/OLMSmoother.aex",
        "aex_sha256": AEX_SOURCES["OLMSmoother.aex"],
        "surface": {
            "plugin_only_leaf_count": 3,
            "exact_rows": smoother_v1_surface,
            "write_resolution": "exact match_name only",
        },
        "standard_options": [
            {
                "scope": "effect_compositing_option",
                "match_name": "ADBE Effect Mask Opacity",
                "property_type": 6417,
                "value": 100,
            },
            {
                "scope": "effect_compositing_option",
                "match_name": "ADBE Force CPU GPU",
                "property_type": 6417,
                "value": 1,
            },
        ],
        "cases": smoother_v1_cases,
        "historical_seed_sha256": {
            "requests/olmsmoother_v1_bitdepth_16_32bpc_software_20260715.json": (
                sha256(smoother_v1_canonical_path)
            ),
            "requests/olm_final_random10_olm_smoother_20260629.json": (
                sha256(smoother_v1_final_path)
            ),
        },
        "rejected_historical_semantics": [
            "final-random property-index addressing",
            "old Windows control sources",
            "old no-op labels for final-random cases 05 and 07; the newly bound Preserve-RGB sources are positive-effect rows",
        ],
        "claim_boundary": "materialized case contract only; Windows AE raw references are required",
    }

    radial_manifest_path = verified_source(
        "refs/win_references/20260604_olm/OLMRadialBlur/reference_manifest.json",
        "7ec542fad64cc210474c6309c3e48c9f12bd0885f54d31943da873d94024b565",
    )
    radial_manifest = json.loads(radial_manifest_path.read_text(encoding="utf-8"))
    radial_case_0009 = next(
        (case for case in radial_manifest["cases"] if case.get("id") == "case_0009"),
        None,
    )
    radial_case_0010 = next(
        (case for case in radial_manifest["cases"] if case.get("id") == "case_0010"),
        None,
    )
    if radial_case_0009 is None or radial_case_0010 is None:
        fail("canonical 20260604 OLMRadialBlur cases 0009/0010 are missing")
    radial_size_manifest_path = verified_source(
        "refs/win_references/olm_reference_return_windows_recapture_20260615/"
        "OLMRadialBlur_sizevar/reference_manifest.json",
        "fa7670dd8c1fdc6be3654846c7c0e2e5f1e09991043f477adef2f92997aab54d",
    )
    radial_size_manifest = json.loads(
        radial_size_manifest_path.read_text(encoding="utf-8")
    )
    radial_selected_ids = [
        "rb_inner_sv000_edge000",
        "rb_inner_sv050_edge000",
        "rb_inner_alpha_sv050_edge000",
        "rb_inner_alpha_sv050_edge025",
    ]
    radial_size_cases = {
        case["id"]: case
        for case in radial_size_manifest["cases"]
        if case.get("id") in radial_selected_ids
    }
    if set(radial_size_cases) != set(radial_selected_ids):
        fail("RadialBlur controlled size-variation cases are missing")
    radial_surface_source = radial_size_cases["rb_inner_sv000_edge000"]["effects"][0][
        "params"
    ]
    radial_plugin_surface_rows = [
        row
        for row in radial_surface_source
        if str(row.get("match_name", "")).startswith("OLM RadialBlur-")
    ]
    if len(radial_plugin_surface_rows) != 30:
        fail(f"RadialBlur plugin surface count drift: {len(radial_plugin_surface_rows)}")
    radial_property_types = {
        str(row["match_name"]): int(row["property_value_type"])
        for row in radial_plugin_surface_rows
    }
    radial_no_value_names = {
        match_name
        for match_name, property_type in radial_property_types.items()
        if property_type == 6412
    }
    radial_writable_names = {
        match_name
        for match_name, property_type in radial_property_types.items()
        if property_type != 6412
    }
    if len(radial_writable_names) != 22 or len(radial_no_value_names) != 8:
        fail("RadialBlur writable/NO_VALUE surface cardinality drift")

    def radial_case_writes(case: dict[str, object]) -> list[dict[str, object]]:
        effects = case.get("effects")
        if not isinstance(effects, list) or len(effects) != 1:
            fail(f"RadialBlur case effect cardinality drift: {case.get('id')}")
        params = effects[0].get("params")  # type: ignore[union-attr]
        if not isinstance(params, list):
            fail(f"RadialBlur case params missing: {case.get('id')}")
        values = {
            str(row["match_name"]): row.get("value")
            for row in params
            if str(row.get("match_name", "")) in radial_writable_names
        }
        if set(values) != radial_writable_names:
            fail(f"RadialBlur case writable map drift: {case.get('id')}")
        return [
            {
                "match_name": match_name,
                "property_type": radial_property_types[match_name],
                "value": values[match_name],
                "write": match_name != "OLM RadialBlur-0021",
                "expected_fresh_default": (
                    0 if match_name == "OLM RadialBlur-0021" else None
                ),
            }
            for match_name in sorted(values)
        ]

    radial_case_records = [
        {
            "case_id": "olmradialblur__canonical_20260604_case_0009_zoom",
            "source_case_id": "case_0009",
            "generation": "20260604",
            "coverage": ["canonical_zoom"],
            "source": source_record("inputs/shared_blur_colorkey_rgba8.png"),
            "intentional_noop": False,
            "expected_raw_off_on_relation": "different",
            "writes": radial_case_writes(radial_case_0009),
        },
        {
            "case_id": "olmradialblur__canonical_20260604_case_0010_tiny_rotation",
            "source_case_id": "case_0010",
            "generation": "20260604",
            "coverage": ["canonical_rotation", "tiny_rotation"],
            "source": source_record("inputs/shared_blur_colorkey_rgba8.png"),
            "intentional_noop": False,
            "expected_raw_off_on_relation": "different",
            "writes": radial_case_writes(radial_case_0010),
        },
    ]
    radial_size_sources = {
        "rb_inner_sv000_edge000": "inputs/opaque_cells_rgba8.png",
        "rb_inner_sv050_edge000": "inputs/opaque_cells_rgba8.png",
        "rb_inner_alpha_sv050_edge000": "inputs/radial_alpha_grid_rgba8.png",
        "rb_inner_alpha_sv050_edge025": "inputs/radial_alpha_grid_rgba8.png",
    }
    radial_coverage = {
        "rb_inner_sv000_edge000": [
            "rotation_inner",
            "size_variation_baseline",
        ],
        "rb_inner_sv050_edge000": ["rotation_inner", "size_variation_50"],
        "rb_inner_alpha_sv050_edge000": [
            "rotation_inner",
            "size_variation_50",
            "nonopaque_alpha",
        ],
        "rb_inner_alpha_sv050_edge025": [
            "complex_rotation_inner",
            "size_variation_50",
            "nonopaque_alpha",
            "outer_and_inner_edge_fade_controls",
        ],
    }
    for case_id in radial_selected_ids:
        radial_case_records.append(
            {
                "case_id": case_id,
                "coverage": radial_coverage[case_id],
                "source": source_record(radial_size_sources[case_id]),
                "intentional_noop": False,
                "expected_raw_off_on_relation": "different",
                "writes": radial_case_writes(radial_size_cases[case_id]),
            }
        )
    radial_override = {
        "schema_version": 2,
        "lane_id": "olmradialblur_minimal_controlled_r4",
        "plugin": "OLMRadialBlur",
        "effect_display_name": "OLM RadialBlur",
        "effect_match_name": "OLM RadialBlur",
        "aex_member": "aex/OLMRadialBlur.aex",
        "aex_sha256": AEX_SOURCES["OLMRadialBlur.aex"],
        "depths": [8, 16, 32],
        "surface": {
            "plugin_only_leaf_count": 30,
            "value_bearing_count": 22,
            "set_action_count": 21,
            "verify_fresh_default_action_count": 1,
            "no_value_count": 8,
            "write_resolution": "recursive exact match_name only",
            "exact_rows": [
                {
                    "property_index": int(row["property_index"]),
                    "match_name": str(row["match_name"]),
                    "display_name": str(row.get("name", "")),
                    "property_type": int(row["property_value_type"]),
                    "enabled": bool(row["enabled"]),
                    "active": bool(row["active"]),
                    "verify": True,
                    "write": str(row["match_name"]) in radial_writable_names
                    and str(row["match_name"]) != "OLM RadialBlur-0021",
                }
                for row in radial_plugin_surface_rows
            ],
            "host_compositing_properties_are_separate": [
                "ADBE Effect Mask Opacity",
                "ADBE Force CPU GPU",
            ],
        },
        "cases": radial_case_records,
        "pair_invariants": [
            {
                "pair_id": "canonical_zoom_rotation",
                "case_ids": [
                    "olmradialblur__canonical_20260604_case_0009_zoom",
                    "olmradialblur__canonical_20260604_case_0010_tiny_rotation",
                ],
                "declared_differences": {
                    "OLM RadialBlur-0001": [1, 2],
                    "OLM RadialBlur-0004": [1717, 4],
                },
                "effect_on_relation": "different",
            },
            {
                "pair_id": "opaque_inner_size_variation",
                "case_ids": [
                    "rb_inner_sv000_edge000",
                    "rb_inner_sv050_edge000",
                ],
                "declared_differences": {
                    "OLM RadialBlur-0017": [0, 50],
                },
                "historical_png_relation": "identical",
                "raw_float32_pair_relation": "record_only_not_a_gate",
            },
            {
                "pair_id": "alpha_inner_edge_fade_complex",
                "case_ids": [
                    "rb_inner_alpha_sv050_edge000",
                    "rb_inner_alpha_sv050_edge025",
                ],
                "declared_differences": {
                    "OLM RadialBlur-0005": [0, 25],
                    "OLM RadialBlur-0009": [0, 25],
                },
                "effect_on_relation": "different",
            },
        ],
        "historical_manifest_sha256": {
            "canonical_20260604": sha256(radial_manifest_path),
            "size_variation_20260615": sha256(radial_size_manifest_path),
        },
        "reject_substitution": (
            "Do not substitute same-numbered 20260605_extra cases or the ambiguous "
            "20260706 return; do not map current_olm_cells to the different "
            "shared_blur_colorkey fixture."
        ),
        "claim_boundary": (
            "materialized case definitions and differential requirements only; "
            "Windows AE raw references and independent Mac comparison remain required"
        ),
    }

    kirakira_seed_path = verified_source(
        "refs/reference_requests/kirakira_single_ray_20260606.json",
        "382156137d17c3ed8eb6a7e670c01a4576b1672d0b55498d3bc2edd782cbb932",
    )
    kirakira_surface_path = verified_source(
        "refs/conformance/olmkirakira_parameter_surface_contract_20260717.json",
        "8805dc0894ec5d603945f1c70e2d5270e18c855b456f291a0bd7b9510ff07a40",
    )
    kirakira_surface_source = json.loads(
        kirakira_surface_path.read_text(encoding="utf-8")
    )
    kirakira_exact_rows = [
        {
            "property_index": int(record["windows_property_index"]),
            "match_name": str(record["windows_match_name"]),
            "display_name": str(record["windows_name"]),
            "property_type": int(record["windows_property_value_type"]),
            "enabled": True,
            "active": True,
            "verify": True,
            "write": bool(record["settable"]),
        }
        for record in kirakira_surface_source[
            "windows_to_mac_match_name_status_table"
        ]
        if str(record["windows_match_name"]).startswith("OLM OLM Kira Kira-")
    ]
    if (
        len(kirakira_exact_rows) != 40
        or [row["property_index"] for row in kirakira_exact_rows]
        != list(range(1, 41))
        or len({row["match_name"] for row in kirakira_exact_rows}) != 40
        or any(
            type(row.get(field)) is not bool
            for row in kirakira_exact_rows
            for field in ("enabled", "active")
        )
    ):
        fail("KiraKira exact surface mapping drift")
    color_match_names = {
        "OLM OLM Kira Kira-0013",
        "OLM OLM Kira Kira-0014",
        "OLM OLM Kira Kira-0015",
        "OLM OLM Kira Kira-0016",
        "OLM OLM Kira Kira-0028",
    }
    ray_values: dict[str, object] = {
        "OLM OLM Kira Kira-0008": 2,
        "OLM OLM Kira Kira-0009": 2,
        "OLM OLM Kira Kira-0017": 1,
        "OLM OLM Kira Kira-0010": 0,
        "OLM OLM Kira Kira-0002": 1,
        "OLM OLM Kira Kira-0011": 100,
        "OLM OLM Kira Kira-0027": 0,
        "OLM OLM Kira Kira-0007": 100,
        "OLM OLM Kira Kira-0012": 100,
        "OLM OLM Kira Kira-0003": 50,
        "OLM OLM Kira Kira-0013": [1.0, 1.0, 1.0, 1.0],
        "OLM OLM Kira Kira-0018": 0,
        "OLM OLM Kira Kira-0004": 0,
        "OLM OLM Kira Kira-0014": [1.0, 1.0, 1.0, 1.0],
        "OLM OLM Kira Kira-0020": 0,
        "OLM OLM Kira Kira-0005": 0,
        "OLM OLM Kira Kira-0015": [1.0, 1.0, 1.0, 1.0],
        "OLM OLM Kira Kira-0022": 0,
        "OLM OLM Kira Kira-0026": 0,
        "OLM OLM Kira Kira-0028": [1.0, 1.0, 1.0, 1.0],
        "OLM OLM Kira Kira-0035": 0,
        "OLM OLM Kira Kira-0006": 0,
        "OLM OLM Kira Kira-0016": [1.0, 1.0, 1.0, 1.0],
        "OLM OLM Kira Kira-0024": 0,
        "OLM OLM Kira Kira-0001": 0,
    }
    if len(ray_values) != 25:
        fail("KiraKira controlled base map must contain exactly 25 match names")

    def materialized_kirakira_values(
        base: dict[str, object], overrides: dict[str, object]
    ) -> list[dict[str, object]]:
        unknown = set(overrides) - set(base)
        if unknown:
            fail(f"KiraKira override contains unknown match names: {sorted(unknown)}")
        values = dict(base)
        values.update(overrides)
        return [
            {
                "match_name": match_name,
                "property_type": 6418 if match_name in color_match_names else 6417,
                "value": values[match_name],
            }
            for match_name in sorted(values)
        ]

    hi_r0_orange_values = dict(ray_values)
    hi_r0_orange_values.update(
        {
            "OLM OLM Kira Kira-0003": 0,
            "OLM OLM Kira Kira-0009": 3,
            "OLM OLM Kira Kira-0016": [1.0, 0.25, 0.0625, 1.0],
        }
    )
    opaque_source = {
        "member": "inputs/opaque_cells_rgba8.png",
        "sha256": "1ec1c0fa672865b43f7869eec196e0442ab77ce3e4d4711a6cb2e6f6e6844021",
    }
    alpha_source = {
        "member": "inputs/alpha_ramp_rgba8.png",
        "sha256": "13da843a8282dda1e26491c4dd9e9a9b9fd34eea80b5380f13897fac664d14d5",
    }
    kirakira_case_specs = [
        (
            KIRAKIRA_CONTROLLED_CASE_IDS[0],
            opaque_source,
            ray_values,
            {"OLM OLM Kira Kira-0009": 1},
            False,
        ),
        (KIRAKIRA_CONTROLLED_CASE_IDS[1], opaque_source, ray_values, {}, False),
        (
            KIRAKIRA_CONTROLLED_CASE_IDS[2],
            opaque_source,
            ray_values,
            {"OLM OLM Kira Kira-0017": 2},
            False,
        ),
        (KIRAKIRA_CONTROLLED_CASE_IDS[3], alpha_source, ray_values, {}, False),
        (
            KIRAKIRA_CONTROLLED_CASE_IDS[4],
            alpha_source,
            ray_values,
            {"OLM OLM Kira Kira-0010": 1},
            False,
        ),
        (
            KIRAKIRA_CONTROLLED_CASE_IDS[5],
            alpha_source,
            ray_values,
            {"OLM OLM Kira Kira-0027": 1},
            False,
        ),
        (
            KIRAKIRA_CONTROLLED_CASE_IDS[6],
            opaque_source,
            hi_r0_orange_values,
            {},
            True,
        ),
        (
            KIRAKIRA_CONTROLLED_CASE_IDS[7],
            opaque_source,
            hi_r0_orange_values,
            {
                "OLM OLM Kira Kira-0006": 5,
                "OLM OLM Kira Kira-0016": [1.0, 1.0, 1.0, 1.0],
            },
            False,
        ),
        (
            KIRAKIRA_CONTROLLED_CASE_IDS[8],
            opaque_source,
            hi_r0_orange_values,
            {"OLM OLM Kira Kira-0006": 5},
            False,
        ),
        (
            KIRAKIRA_CONTROLLED_CASE_IDS[9],
            opaque_source,
            hi_r0_orange_values,
            {
                "OLM OLM Kira Kira-0006": 5,
                "OLM OLM Kira Kira-0009": 4,
            },
            False,
        ),
    ]
    kirakira_cases = [
        {
            "case_id": case_id,
            "source": source,
            "intentional_noop": intentional_noop,
            "writes": materialized_kirakira_values(base, overrides),
        }
        for case_id, source, base, overrides, intentional_noop in kirakira_case_specs
    ]
    ramp_toggle_match_names = [
        "OLM OLM Kira Kira-0018",
        "OLM OLM Kira Kira-0020",
        "OLM OLM Kira Kira-0022",
        "OLM OLM Kira Kira-0024",
        "OLM OLM Kira Kira-0035",
    ]
    for case in kirakira_cases:
        values = {row["match_name"]: row["value"] for row in case["writes"]}
        if any(values[name] != 0 for name in ramp_toggle_match_names):
            fail(f"KiraKira controlled case enables a ramp: {case['case_id']}")
    kirakira_pairs = [
        {
            "pair_id": "blur_mode_1_vs_2",
            "left_case_id": KIRAKIRA_CONTROLLED_CASE_IDS[0],
            "right_case_id": KIRAKIRA_CONTROLLED_CASE_IDS[1],
            "only_different_match_name": "OLM OLM Kira Kira-0009",
            "left_value": 1,
            "right_value": 2,
            "effect_on_relation": "different",
        },
        {
            "pair_id": "merge_mode_1_vs_2",
            "left_case_id": KIRAKIRA_CONTROLLED_CASE_IDS[1],
            "right_case_id": KIRAKIRA_CONTROLLED_CASE_IDS[2],
            "only_different_match_name": "OLM OLM Kira Kira-0017",
            "left_value": 1,
            "right_value": 2,
            "effect_on_relation": "different",
        },
        {
            "pair_id": "approximated_input_off_vs_on",
            "left_case_id": KIRAKIRA_CONTROLLED_CASE_IDS[3],
            "right_case_id": KIRAKIRA_CONTROLLED_CASE_IDS[4],
            "only_different_match_name": "OLM OLM Kira Kira-0010",
            "left_value": 0,
            "right_value": 1,
            "effect_on_relation": "different",
        },
        {
            "pair_id": "fade_off_vs_on",
            "left_case_id": KIRAKIRA_CONTROLLED_CASE_IDS[3],
            "right_case_id": KIRAKIRA_CONTROLLED_CASE_IDS[5],
            "only_different_match_name": "OLM OLM Kira Kira-0027",
            "left_value": 0,
            "right_value": 1,
            "effect_on_relation": "different",
        },
        {
            "pair_id": "highlight_radius_0_vs_5",
            "left_case_id": KIRAKIRA_CONTROLLED_CASE_IDS[6],
            "right_case_id": KIRAKIRA_CONTROLLED_CASE_IDS[8],
            "only_different_match_name": "OLM OLM Kira Kira-0006",
            "left_value": 0,
            "right_value": 5,
            "effect_on_relation": "different",
        },
        {
            "pair_id": "highlight_color_white_vs_orange",
            "left_case_id": KIRAKIRA_CONTROLLED_CASE_IDS[7],
            "right_case_id": KIRAKIRA_CONTROLLED_CASE_IDS[8],
            "only_different_match_name": "OLM OLM Kira Kira-0016",
            "left_value": [1.0, 1.0, 1.0, 1.0],
            "right_value": [1.0, 0.25, 0.0625, 1.0],
            "effect_on_rgb_relation": "different",
        },
        {
            "pair_id": "blur_mode_3_vs_4",
            "left_case_id": KIRAKIRA_CONTROLLED_CASE_IDS[8],
            "right_case_id": KIRAKIRA_CONTROLLED_CASE_IDS[9],
            "only_different_match_name": "OLM OLM Kira Kira-0009",
            "left_value": 3,
            "right_value": 4,
            "effect_on_relation": "different",
        },
    ]
    kirakira_override = {
        "schema_version": 2,
        "plugin": "OLMKiraKira",
        "effect_display_name": "OLM Kira Kira",
        "effect_match_name": "OLM OLM Kira Kira",
        "aex_member": "aex/OLMKiraKira.aex",
        "aex_sha256": "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7",
        "depths": [8, 16, 32],
        "comp": {
            "width": 1920,
            "height": 1080,
            "pixel_aspect": 1.0,
            "resolution_factor": [1, 1],
            "frame_rate": 24,
            "frame": 24,
            "time_seconds": 1.0,
        },
        "surface_contract": {
            "write_resolution": "exact match_name only; property indices and display-name aliases are forbidden",
            "plugin_only_leaf_count": 40,
            "exact_rows": kirakira_exact_rows,
            "expected_writable_match_names": sorted(ray_values),
            "expected_writable_count": 25,
            "expected_property_type_codes": {
                "color": 6418,
                "all_other_writes": 6417,
            },
            "ramp_toggle_match_names_must_read_zero": ramp_toggle_match_names,
            "forbidden_label_match_names": [
                "OLM OLM Kira Kira-0029",
                "OLM OLM Kira Kira-0031",
                "OLM OLM Kira Kira-0033",
                "OLM OLM Kira Kira-0037",
                "OLM OLM Kira Kira-0039",
            ],
            "forbidden_custom_ramp_payload_match_names": [
                "OLM OLM Kira Kira-0019",
                "OLM OLM Kira Kira-0021",
                "OLM OLM Kira Kira-0023",
                "OLM OLM Kira Kira-0025",
                "OLM OLM Kira Kira-0036",
            ],
            "forbidden_separator_match_names": [
                "OLM OLM Kira Kira-0030",
                "OLM OLM Kira Kira-0032",
                "OLM OLM Kira Kira-0034",
                "OLM OLM Kira Kira-0038",
                "OLM OLM Kira Kira-0040",
            ],
            "fail_if": [
                "an expected writable match name is missing or duplicated",
                "a write or readback uses a property index or display-name alias",
                "a forbidden row is written or inferred",
                "any expected value or property type differs before or after render",
                "any Use Ramp value is nonzero",
            ],
        },
        "historical_seed_member": "requests/kirakira_single_ray_20260606.json",
        "historical_seed_sha256": sha256(kirakira_seed_path),
        "mapping_support_member": (
            "support_evidence/olmkirakira_parameter_surface_contract_20260717.json"
        ),
        "mapping_support_sha256": (
            "8805dc0894ec5d603945f1c70e2d5270e18c855b456f291a0bd7b9510ff07a40"
        ),
        "cases": kirakira_cases,
        "pair_invariants": kirakira_pairs,
        "cross_row_report": "cross_row/olmkirakira_controlled_matrix.json",
        "deferred": {
            "final_random_use_ramp_states": (
                "Do not capture or promote until the custom-ramp payload has an "
                "exact serialization/readback contract."
            )
        },
        "claim_boundary": (
            "case definitions and Windows differential requirements only; "
            "independent Mac raw off/on comparison is still required for AE exactness"
        ),
    }
    colorkeep_lane = next(lane for lane in LANES if lane["plugin"] == "ColorKeep")
    input_hashes = {
        f"inputs/{name}": digest for name, _, digest, _ in INPUT_SOURCES
    }
    colorkeep_cases = []
    for case in colorkeep_lane["cases"]:  # type: ignore[index]
        fixture = str(case["fixture"])
        if fixture not in input_hashes:
            fail(f"ColorKeep case has an unknown fixture: {fixture}")
        materialized_writes = []
        for write in case["parameter_writes"]:
            property_index = int(write["property_index"])
            materialized_write = dict(write)
            if "value_rgba" in materialized_write:
                if "value" in materialized_write:
                    fail("ColorKeep write contains both value and value_rgba")
                materialized_write["value"] = materialized_write.pop("value_rgba")
            materialized_write["match_name"] = (
                f"OLM Color Keep-{property_index:04d}"
            )
            materialized_write["property_type"] = (
                6417 if property_index == 1 else 6418
            )
            materialized_write["write_resolution"] = (
                "exact property_index + exact match_name + exact display_name"
            )
            materialized_writes.append(materialized_write)
        colorkeep_cases.append(
            {
                "case_id": case["case_id"],
                "source": {
                    "member": fixture,
                    "sha256": input_hashes[fixture],
                },
                "intentional_noop": bool(case["intentional_noop"]),
                "parameter_writes": materialized_writes,
                "purpose": case["purpose"],
            }
        )
    colorkeep_surface = [
        {
            "property_index": 1,
            "match_name": "OLM Color Keep-0001",
            "display_name": "Enabled Color Num",
            "property_type": 6417,
            "default": 1,
            "enabled": True,
            "active": True,
        }
    ]
    colorkeep_surface.extend(
        {
            "property_index": index,
            "match_name": f"OLM Color Keep-{index:04d}",
            "display_name": "Color",
            "property_type": 6418,
            "default": [0.0, 0.0, 0.0, 1.0],
            "enabled": True,
            "active": True,
        }
        for index in range(2, 102)
    )
    colorkeep_override = {
        "schema_version": 1,
        "plugin": "ColorKeep",
        "effect_display_name": "Color Keep",
        "effect_match_name": "OLM Color Keep",
        "aex_member": "aex/ColorKeep.aex",
        "aex_sha256": AEX_SOURCES["ColorKeep.aex"],
        "depths": [8, 16, 32],
        "surface_contract": {
            "plugin_only_leaf_count": 101,
            "num_params_including_input": 102,
            "exact_rows": colorkeep_surface,
            "binary_and_aexcompat_summary": colorkeep_lane[
                "expected_setup_from_binary_and_aexcompat"
            ],
        },
        "surface_gate": (
            "Capture all 101 plugin-only leaves before writes. Apply a case only "
            "after property indices 1/2/3, display names, types, untouched defaults, "
            "and the full leaf count match exactly; otherwise fail the row without guessing."
        ),
        "cases": colorkeep_cases,
        "claim_boundary": (
            "The setup is binary/AEXCompat-grounded intermediate evidence. "
            "Windows and Mac AE raw off/on comparisons remain required."
        ),
    }
    return {
        "colorkeep_controlled_discovery_3.json": colorkeep_override,
        "olmdistancegradation_materialized_33.json": dg_override,
        "olmdirectionalblur_materialized_18.json": directional_override,
        "olmsmoother_v1_materialized_13.json": smoother_v1_override,
        "olmradialblur_minimal_controlled_r4.json": radial_override,
        "olmkirakira_controlled_ramps_off_matrix.json": kirakira_override,
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

    support_index: list[dict[str, object]] = []
    for source, digest, plugin, scope in SUPPORT_SOURCES:
        name = Path(source).name
        record = copy_verified(source, digest, PACKAGE_DIR / "support_evidence" / name)
        record["plugin"] = plugin
        record["scope"] = scope
        support_index.append(record)

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
    write_text(PACKAGE_DIR / "REFERENCE_GAP_MATRIX.md", REFERENCE_GAP_MATRIX)
    write_text(PACKAGE_DIR / "RETURN_FORMAT.md", RETURN_FORMAT)
    write_text(PACKAGE_DIR / "VERIFY_REQUEST.ps1", VERIFY_REQUEST_PS1)
    tool_index: list[dict[str, object]] = []
    for source, digest, member, purpose in TOOL_SOURCES:
        record = copy_verified(source, digest, PACKAGE_DIR / member)
        record["purpose"] = purpose
        tool_index.append(record)
    write_json(
        PACKAGE_DIR / "TOOL_INDEX.json",
        {
            "schema_version": 1,
            "campaign_id": CAMPAIGN_ID,
            "files": tool_index,
        },
    )
    case_definition_overrides = build_case_definition_overrides()
    for name, value in sorted(case_definition_overrides.items()):
        write_json(PACKAGE_DIR / "case_definitions" / name, value)
    row_inventory = build_row_inventory()
    execution_rows = build_execution_rows(row_inventory)
    write_json(PACKAGE_DIR / "ROW_INVENTORY.json", row_inventory)
    write_json(PACKAGE_DIR / "EXECUTION_ROWS.json", execution_rows)
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
        PACKAGE_DIR / "SUPPORT_INDEX.json",
        {
            "schema_version": 1,
            "claim_boundary": "intermediate mapping/IR evidence only; never AE exact",
            "files": support_index,
        },
    )
    write_json(
        PACKAGE_DIR / "AEX_INDEX.json",
        {
            "schema_version": 1,
            "files": aex_index,
        },
    )
    return_schemas = build_return_schemas()
    for name, schema in sorted(return_schemas.items()):
        write_json(PACKAGE_DIR / "schemas" / name, schema)
    write_json(
        PACKAGE_DIR / "schemas" / "SCHEMA_INDEX.json",
        {
            "schema_version": 1,
            "campaign_id": CAMPAIGN_ID,
            "files": sorted(return_schemas),
            "schemas_are_normative": True,
            "validation": (
                "The listed schemas are normative. tools/VERIFY_RETURN.py performs "
                "manual equivalent enforcement of their constraints, plus exact "
                "request binding, row bijection, checksums, EXR decoding, and "
                "cross-row predicates; it does not dynamically execute jsonschema."
            ),
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

    verifier_environment = os.environ.copy()
    verifier_environment["PYTHONDONTWRITEBYTECODE"] = "1"
    self_test = subprocess.run(
        [
            sys.executable,
            str(PACKAGE_DIR / "tools" / "VERIFY_RETURN.py"),
            "--request-root",
            str(PACKAGE_DIR),
            "--self-test-request",
        ],
        cwd=PACKAGE_DIR,
        env=verifier_environment,
        capture_output=True,
        text=True,
        check=False,
    )
    if self_test.returncode != 0:
        fail(
            "bundled request self-test failed:\n"
            f"stdout:\n{self_test.stdout}\n"
            f"stderr:\n{self_test.stderr}"
        )

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
                "support_evidence": len(support_index),
                "tools": len(tool_index),
                "rows": row_inventory["row_count"],
                "rows_estimate": sum(int(lane["rows_estimate"]) for lane in LANES),
                "request_self_test": "PASS",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
