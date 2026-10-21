#!/usr/bin/env python3
"""Bounded intermediate-Gamma/key-endpoint exported-owner closure."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMSmoother2AE/Plugins/64/2025/OLMSmoother2.aex"
SOURCE = ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"
HARNESS = ROOT / "tools/emulation/olmsmoother2_gamma18_keyendpoint_effectmain_harness_20260812.cpp"
REPORT = ROOT / "refs/conformance/olmsmoother2_gamma18_keyendpoint_exported_owner_closure_20260812.json"
DOC = REPORT.with_suffix(".md")
WORKER = Path(os.environ.get(
    "OLM_AEX_GUEST_WORKER",
    "/Users/onmk/Documents/Projects/Personal/04_Tools/"
    "AEXCompat-issue851-smart-primary-checkout/guest/target/release/aex-guest-worker",
))

EXPECTED = {
    "aex": "7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7",
    "worker": "46ab907d286ad4e0e1c2065557100f02c37e0b68df4c22202a825f3fea13ef61",
    "worker_commit": "28d535469f84f67236ef3425afe4291ea2fb0991",
    "source": "87e861e4a0c5678502d744ab9aaea00a5066b20536be0d1e01f0b98a8045bffd",
    "harness": "2c60d139f2e3ddcce52c77f67c5640358a54a2fd23bd09c624b5e97880d4e229",
    "base_rgba8": "3a61958d4ef386108a075ca5acdf294184b0d9d29c9c97bb61c3491726c5698c",
    "fixture_rgba8": "82199eb51f6455f4842efd1f6020469b04af53a4ba9f7b8df366cd84bf13c67f",
    "fixture_png": "4cbe4d7815b0b5c591fb4db4304633d11b32db2dbab22b5cb04b3ae4235ab13c",
}

RGB = [
    (202,187,230),(255,0,0),(65,1,1),(0,255,0),(206,55,161),
    (86,55,26),(43,73,217),(231,16,235),(116,106,230),(1,9,43),
    (91,38,34),(99,183,84),(230,125,149),(208,155,60),(168,21,161),
    (233,157,226),(8,57,119),(159,56,196),(232,156,109),(50,140,246),
    (229,135,20),(36,6,46),(176,107,229),(168,83,193),(235,7,162),
]
DEPTHS = {"PF8": ("argb8", 4, 5), "PF16": ("argb16", 8, 7),
          "PF32": ("argb32f", 16, 13)}
RAW_HASHES = {
    "v1_noninvert": {
        "PF8": "29f115036540706bb61962d3fa85bfef5dea5f08847ad2dfa19c368d82bcf2eb",
        "PF16": "ad57d85d46aee324ecc02636a2eaa14c10b0c01679d30817dd61d2086b9d1e69",
        "PF32": "363b5b2fc0d9a9e30e1a38136985b46cbc8927227c7d2dda8d518104f6782ea8",
    },
    "v1_invert": {
        "PF8": "ad3c4081df00896edb660aedf61f05a734686c55a468badbcd846431ed4948e2",
        "PF16": "a0276758e35a93d3f48bf5107eaf163c4308cd642d48c9a34bd479cc581781d8",
        "PF32": "bf00a302cfca39996b23cfa6b17dc86c3e04516353fa7e3374271a2cd0fe6ff6",
    },
    "v2_noninvert": {
        "PF8": "25db2380ab04d862e7fe14e6e319a206dfb83481946aa4392eca29eeb0aee90c",
        "PF16": "f79064a05e02aa36580c3323a7a7ec048272b07b14293ef4a7d356726ec2da3e",
        "PF32": "7a463e32ff665b8fb2e263e0fa9ea5177c67b62ea52f500729a5b2b586de78b2",
    },
    "v2_invert": {
        "PF8": "ad3c4081df00896edb660aedf61f05a734686c55a468badbcd846431ed4948e2",
        "PF16": "a0276758e35a93d3f48bf5107eaf163c4308cd642d48c9a34bd479cc581781d8",
        "PF32": "4b2a3f6b2739d2751c4c53028dabbeb828879964e9abdbccd63be83abecb2599",
    },
}
GAMMA_OBSERVABILITY_HASHES = {
    "1.0": {
        "PF8": "d11b8baa684132c72c833d1ba7bee8c905e9b54a7de362bd80ce046f9509649c",
        "PF16": "7786c667f1ddfdfc9fa7653e3d58b1a17ef65214847466056fe0eee781fd01ab",
        "PF32": "735596ca3461ec380eac33bc507c2b8f3c6d2f19a03d9ddf8b945947708145b0",
    },
    "1.8": RAW_HASHES["v2_noninvert"],
    "2.4": {
        "PF8": "ed31505731b5679a096deae1073e109c730a378b7fa0f1b8ed963da8353875b3",
        "PF16": "781310546342e5d8ad781e192dc8acecb065e4309df1c4016166d5479732adbd",
        "PF32": "77d87803b38a38f113a5507d56da04cdac80f9098bf31ec1121c85b1c5b99b81",
    },
}
KEY_DISABLED_OBSERVABILITY_HASHES = {
    "PF8": "ca56c65ec9209d52c956f40e51cb8f7c133a001eab1b141b95c04295917cce99",
    "PF16": "66127e3fbe12b1b39f25127550d006f69db7d8aabe9c571f8caf91fc6819dee7",
    "PF32": "c6239c135d38db34c1eed69a66855dff650961301df72da35feb5d413c06962b",
}
CELL_ORDER = [(f"v{version}_{'invert' if invert else 'noninvert'}", depth)
              for version in (1, 2) for invert in (False, True) for depth in DEPTHS]
CLAIM = (
    "Raw exact only for the fixed 5x5 opaque RGBA8 fixture (24 pixels retained from "
    "the prior compound fixture and pixel 0 replaced by the exact key endpoint), Color "
    "Key RGB=(202,187,230), Gamma Colors ordered [red,key], Gamma Value=1.8, "
    "Smoothness/Range/Extra Smooth=100, Version 1/2 x non-invert/invert x "
    "PF8/PF16/PF32. No arbitrary input, Gamma Value, key/palette, smoothing, geometry, "
    "AE-host, GPU, or installed-binary claim."
)
FAIL_CLOSE = [
    "any input pixel, key/palette endpoint, Gamma Value, smoothing value, version, polarity, geometry, or depth outside the declared twelve cells",
    "any unpinned AEX, AEXCompat worker/commit, production source, or public EffectMain harness identity",
    "native Windows, After Effects host/color-management, GPU, or installed-plugin execution",
]


def sha_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_current_identities() -> bool:
    try:
        return (sha_path(AEX) == EXPECTED["aex"] and WORKER.is_file() and
                sha_path(WORKER) == EXPECTED["worker"] and
                sha_path(SOURCE) == EXPECTED["source"] and
                sha_path(HARNESS) == EXPECTED["harness"])
    except OSError:
        return False


def owner_params(version: int, invert: bool, gamma: float = 1.8,
                 key_enabled: bool = True) -> list[str]:
    return [
        f"Enable Color Key={int(key_enabled)}", "Color Key=255,202,187,230",
        f"Invert Color Key={int(invert)}", "Smoothness=100",
        "Extra Smooth=100", "Smooth Range=100", f"Smoother Version={version}",
        "Gamma Correction=2", f"Gamma Value={gamma}", "Number of Gamma Colors=2",
        "Gamma Color@11=255,255,0,0", "Gamma Color@12=255,202,187,230",
    ]


def tight(raw: bytes, depth: str) -> bytes:
    _format, pixel_size, padding = DEPTHS[depth]
    rowbytes = 5 * pixel_size + padding
    return b"".join(raw[y * rowbytes:y * rowbytes + 5 * pixel_size]
                    for y in range(5))


def production_effectmain() -> tuple[list[dict[str, object]], dict[str, object]]:
    with tempfile.TemporaryDirectory(prefix="sm2_gamma18_effectmain_") as raw:
        executable = Path(raw) / "effectmain"
        build = subprocess.run([
            "clang++", "-std=c++17", "-O2", "-fno-fast-math", "-ffp-contract=off",
            "-I", str(ROOT / "cli/OLMSmoother2/shim"),
            "-I", str(ROOT / "mac/OLMSmoother2/Mac"), str(HARNESS),
            "-o", str(executable),
        ], cwd=ROOT, capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(build.stderr)
        run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True, text=True)
        if run.returncode:
            raise RuntimeError(run.stderr)
    cases: dict[tuple[str, str], bytes] = {}
    metadata: dict[tuple[str, str], list[int]] = {}
    for line in run.stdout.splitlines():
        fields = line.split()
        if fields[0] == "CASE" and len(fields) == 4:
            cases[(fields[2], fields[1])] = bytes.fromhex(fields[3])
        elif fields[0] == "META" and len(fields) == 12:
            metadata[(fields[2], fields[1])] = [int(value) for value in fields[3:]]
        else:
            raise AssertionError(f"unexpected harness output: {line}")
    if set(cases) != set(CELL_ORDER) or set(metadata) != set(CELL_ORDER):
        raise AssertionError("EffectMain cell coverage drift")
    rows = []
    for variant, depth in CELL_ORDER:
        raw_padded = cases[(variant, depth)]
        digest = hashlib.sha256(tight(raw_padded, depth)).hexdigest()
        expected = RAW_HASHES[variant][depth]
        if digest != expected:
            raise AssertionError(f"production raw mismatch {variant}/{depth}: {digest}")
        padding, pre, layer, output, checkouts, checkins, unchanged, in_pad, out_pad = metadata[(variant, depth)]
        if [padding, pre, layer, output, checkouts, checkins, unchanged, in_pad, out_pad] != [
                DEPTHS[depth][2], 1, 1, 1, 15, 15, 1, 1, 1]:
            raise AssertionError(f"production lifecycle mismatch {variant}/{depth}")
        rows.append({"variant": variant, "depth": depth,
                     "pixel_format": DEPTHS[depth][0],
                     "active_bytes": 25 * DEPTHS[depth][1],
                     "raw_sha256": digest, "status": "raw_exact"})
    gates = {
        "smart_pre_render_calls_per_cell": 1,
        "checkout_layer_pixels_calls_per_cell": 1,
        "checkout_output_calls_per_cell": 1,
        "parameter_checkouts_per_cell": 15,
        "parameter_checkins_per_cell": 15,
        "pre_render_rectangles_preserved": True,
        "complete_input_buffer_unchanged": True,
        "input_row_padding_preserved": True,
        "output_row_padding_preserved": True,
        "row_padding_bytes_by_depth": {depth: values[2] for depth, values in DEPTHS.items()},
    }
    return rows, gates


def parameter_readback_ok(actual: dict[str, object], version: int, invert: bool,
                          gamma: float = 1.8, key_enabled: bool = True) -> bool:
    values = actual.get("parameter_values")
    if not isinstance(values, list) or len(values) != 12:
        return False
    by_slot = {entry.get("slot"): entry for entry in values if isinstance(entry, dict)}
    return (
        by_slot.get(1, {}).get("value") == float(key_enabled) and
        by_slot.get(2, {}).get("color") == [255, 202, 187, 230] and
        by_slot.get(3, {}).get("value") == float(invert) and
        by_slot.get(4, {}).get("value") == 100.0 and
        by_slot.get(5, {}).get("value") == 100.0 and
        by_slot.get(6, {}).get("value") == 100.0 and
        by_slot.get(7, {}).get("value") == float(version) and
        by_slot.get(8, {}).get("value") == 2.0 and
        by_slot.get(9, {}).get("value") == gamma and
        by_slot.get(10, {}).get("value") == 2.0 and
        by_slot.get(11, {}).get("color") == [255, 255, 0, 0] and
        by_slot.get(12, {}).get("color") == [255, 202, 187, 230]
    )


def public_owner(directory: Path) -> tuple[
        list[dict[str, object]], str, dict[str, object], dict[str, object]]:
    input_png = directory / "input.png"
    image = Image.new("RGBA", (5, 5))
    image.putdata([(*rgb, 255) for rgb in RGB])
    image.save(input_png)
    rgba_sha = hashlib.sha256(bytes(channel for rgb in RGB for channel in (*rgb, 255))).hexdigest()
    if rgba_sha != EXPECTED["fixture_rgba8"] or sha_path(input_png) != EXPECTED["fixture_png"]:
        raise AssertionError("source fixture identity drift")
    rows = []
    for variant, depth in CELL_ORDER:
        version = int(variant[1])
        invert = variant.endswith("_invert") and not variant.endswith("_noninvert")
        pixel_format, pixel_size, _padding = DEPTHS[depth]
        result = subprocess.run([
            str(WORKER), "render-png", str(AEX), str(input_png),
            str(directory / f"{variant}-{depth}.png"), "--pixel-format", pixel_format,
            *owner_params(version, invert),
        ], cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr)
        actual = json.loads(result.stdout)
        expected = RAW_HASHES[variant][depth]
        exact = (
            actual.get("render_error") == 0 and actual.get("guards_intact") is True and
            actual.get("raw_pixel_bytes") == 25 * pixel_size and
            actual.get("raw_pixel_sha256") == expected and
            actual.get("render_mode") == "smart-cpu" and
            actual.get("gpu", {}).get("pre_render", {}).get("completed") is True and
            actual.get("gpu", {}).get("pre_render", {}).get("error") == 0 and
            actual.get("gpu", {}).get("render", {}).get("completed") is True and
            actual.get("gpu", {}).get("render", {}).get("error") == 0 and
            actual.get("unsupported_suite_calls") == [] and
            actual.get("dropped_unsupported_suite_calls") == 0 and
            parameter_readback_ok(actual, version, invert)
        )
        if not exact:
            raise AssertionError(f"exported owner mismatch {variant}/{depth}: {actual}")
        rows.append({"variant": variant, "depth": depth, "pixel_format": pixel_format,
                     "active_bytes": 25 * pixel_size, "raw_sha256": expected,
                     "render_mode": "smart-cpu", "guards_intact": True,
                     "smart_pre_render_completed": True, "smart_render_completed": True,
                     "unsupported_suite_calls": [], "status": "raw_exact"})
    observed: dict[str, dict[str, str]] = {}
    for gamma in (1.0, 2.4):
        label = str(gamma)
        observed[label] = {}
        for depth, (pixel_format, pixel_size, _padding) in DEPTHS.items():
            result = subprocess.run([
                str(WORKER), "render-png", str(AEX), str(input_png),
                str(directory / f"gamma-{label}-{depth}.png"),
                "--pixel-format", pixel_format, *owner_params(2, False, gamma),
            ], cwd=ROOT, capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError(result.stderr)
            actual = json.loads(result.stdout)
            expected = GAMMA_OBSERVABILITY_HASHES[label][depth]
            if not (
                actual.get("render_error") == 0 and actual.get("guards_intact") is True and
                actual.get("raw_pixel_bytes") == 25 * pixel_size and
                actual.get("raw_pixel_sha256") == expected and
                actual.get("render_mode") == "smart-cpu" and
                actual.get("gpu", {}).get("pre_render", {}).get("completed") is True and
                actual.get("gpu", {}).get("pre_render", {}).get("error") == 0 and
                actual.get("gpu", {}).get("render", {}).get("completed") is True and
                actual.get("gpu", {}).get("render", {}).get("error") == 0 and
                actual.get("unsupported_suite_calls") == [] and
                actual.get("dropped_unsupported_suite_calls") == 0 and
                parameter_readback_ok(actual, 2, False, gamma)
            ):
                raise AssertionError(f"Gamma observability mismatch {label}/{depth}: {actual}")
            observed[label][depth] = expected
    observed["1.8"] = dict(GAMMA_OBSERVABILITY_HASHES["1.8"])
    for depth in DEPTHS:
        if len({observed[label][depth] for label in ("1.0", "1.8", "2.4")}) != 3:
            raise AssertionError(f"Gamma 1.8 is not output-observable at {depth}")
    observability = {
        "diagnostic_scope": "actual exported Version 2 non-invert owner on the same fixture; Gamma endpoints are observation controls, not added exact-production cells",
        "raw_sha256_by_gamma_and_depth": observed,
        "gamma_1_8_distinct_from_1_0_and_2_4_all_depths": True,
    }
    key_disabled: dict[str, str] = {}
    for depth, (pixel_format, pixel_size, _padding) in DEPTHS.items():
        result = subprocess.run([
            str(WORKER), "render-png", str(AEX), str(input_png),
            str(directory / f"key-disabled-{depth}.png"), "--pixel-format", pixel_format,
            *owner_params(2, False, 1.8, False),
        ], cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr)
        actual = json.loads(result.stdout)
        expected = KEY_DISABLED_OBSERVABILITY_HASHES[depth]
        if not (
            actual.get("render_error") == 0 and actual.get("guards_intact") is True and
            actual.get("raw_pixel_bytes") == 25 * pixel_size and
            actual.get("raw_pixel_sha256") == expected and
            actual.get("render_mode") == "smart-cpu" and
            actual.get("gpu", {}).get("pre_render", {}).get("completed") is True and
            actual.get("gpu", {}).get("pre_render", {}).get("error") == 0 and
            actual.get("gpu", {}).get("render", {}).get("completed") is True and
            actual.get("gpu", {}).get("render", {}).get("error") == 0 and
            actual.get("unsupported_suite_calls") == [] and
            actual.get("dropped_unsupported_suite_calls") == 0 and
            parameter_readback_ok(actual, 2, False, 1.8, False)
        ):
            raise AssertionError(f"key endpoint observability mismatch {depth}: {actual}")
        if expected == RAW_HASHES["v2_noninvert"][depth]:
            raise AssertionError(f"exact key endpoint is not output-observable at {depth}")
        key_disabled[depth] = expected
    key_observability = {
        "diagnostic_scope": "same source and Version 2 non-invert Gamma 1.8 tuple; only Enable Color Key changes from 1 to 0",
        "key_enabled_raw_sha256_by_depth": dict(RAW_HASHES["v2_noninvert"]),
        "key_disabled_raw_sha256_by_depth": key_disabled,
        "exact_key_endpoint_action_distinct_all_depths": True,
    }
    return rows, sha_path(input_png), observability, key_observability


def expected_rows(public: bool) -> list[dict[str, object]]:
    rows = []
    for variant, depth in CELL_ORDER:
        pixel_format, pixel_size, _padding = DEPTHS[depth]
        row = {"variant": variant, "depth": depth, "pixel_format": pixel_format,
               "active_bytes": 25 * pixel_size,
               "raw_sha256": RAW_HASHES[variant][depth], "status": "raw_exact"}
        if public:
            row.update({"render_mode": "smart-cpu", "guards_intact": True,
                        "smart_pre_render_completed": True,
                        "smart_render_completed": True, "unsupported_suite_calls": []})
        rows.append(row)
    return rows


def validate_report(report: dict[str, object]) -> bool:
    try:
        expected_top_level = {
            "schema", "date", "status", "verdict", "claim_boundary", "identities",
            "fixture", "parameters", "actual_exported_smart_owner",
            "production_public_effectmain", "cross_checks",
            "intermediate_gamma_observability", "exact_key_endpoint_observability",
            "case_count", "exact_case_count", "production_code_changed", "fail_close",
        }
        expected_identities = {
            "aex_sha256": EXPECTED["aex"],
            "aexcompat_worker_sha256": EXPECTED["worker"],
            "aexcompat_commit": EXPECTED["worker_commit"],
            "production_source_sha256": EXPECTED["source"],
            "effectmain_harness_sha256": EXPECTED["harness"],
            "generator_sha256": sha_path(Path(__file__)),
        }
        expected_fixture = {
            "dimensions": [5, 5], "alpha_u8": 255, "rgb_u8": [list(x) for x in RGB],
            "derivation": "prior 25-pixel compound fixture with 24 pixels retained and pixel 0 changed from (1,1,1) to exact key endpoint (202,187,230)",
            "prior_fixture_rgba8_sha256": EXPECTED["base_rgba8"],
            "source_rgba8_sha256": EXPECTED["fixture_rgba8"],
            "input_png_sha256": EXPECTED["fixture_png"],
        }
        expected_parameters = {
            "color_key_rgb_u8": [202, 187, 230],
            "gamma_palette_rgb_u8": [[255, 0, 0], [202, 187, 230]],
            "gamma_value": 1.8, "gamma_mode": "Gamma Colors",
            "smoothness": 100, "smooth_range": 100, "extra_smooth": 100,
            "versions": [1, 2], "key_polarities": ["noninvert", "invert"],
            "depths": ["PF8", "PF16", "PF32"],
        }
        expected_gates = {
            "smart_pre_render_calls_per_cell": 1,
            "checkout_layer_pixels_calls_per_cell": 1,
            "checkout_output_calls_per_cell": 1,
            "parameter_checkouts_per_cell": 15,
            "parameter_checkins_per_cell": 15,
            "pre_render_rectangles_preserved": True,
            "complete_input_buffer_unchanged": True,
            "input_row_padding_preserved": True,
            "output_row_padding_preserved": True,
            "row_padding_bytes_by_depth": {"PF8": 5, "PF16": 7, "PF32": 13},
        }
        distinction = {
            "noninvert_version_outputs_distinct_all_depths": True,
            "key_polarities_distinct_each_version_all_depths": True,
            "invert_version_outputs": "PF8/PF16 equal on this bounded fixture; PF32 distinct",
            "endpoint_pixels_present": {"red": [1, 0], "key": [0, 0]},
        }
        observability = {
            "diagnostic_scope": "actual exported Version 2 non-invert owner on the same fixture; Gamma endpoints are observation controls, not added exact-production cells",
            "raw_sha256_by_gamma_and_depth": GAMMA_OBSERVABILITY_HASHES,
            "gamma_1_8_distinct_from_1_0_and_2_4_all_depths": True,
        }
        key_observability = {
            "diagnostic_scope": "same source and Version 2 non-invert Gamma 1.8 tuple; only Enable Color Key changes from 1 to 0",
            "key_enabled_raw_sha256_by_depth": RAW_HASHES["v2_noninvert"],
            "key_disabled_raw_sha256_by_depth": KEY_DISABLED_OBSERVABILITY_HASHES,
            "exact_key_endpoint_action_distinct_all_depths": True,
        }
        return (
            set(report) == expected_top_level and
            report.get("schema") == "olmsmoother2.gamma18-keyendpoint-owner-closure/1" and
            report.get("date") == "2026-08-12" and report.get("status") == "raw_exact" and
            report.get("verdict") == "PASS_12_INTERMEDIATE_GAMMA_KEY_ENDPOINT_EXPORTED_OWNER_TO_PUBLIC_EFFECTMAIN_RAW_EXACT" and
            report.get("claim_boundary") == CLAIM and report.get("identities") == expected_identities and
            report.get("fixture") == expected_fixture and report.get("parameters") == expected_parameters and
            report.get("actual_exported_smart_owner") == expected_rows(True) and
            report.get("production_public_effectmain", {}).get("rows") == expected_rows(False) and
            report.get("production_public_effectmain", {}).get("gates") == expected_gates and
            report.get("production_public_effectmain", {}).get("chain") == [
                "EffectMain SmartPreRender", "EffectMain SmartRender",
                "typed RenderBits output"] and
            report.get("cross_checks") == distinction and
            report.get("intermediate_gamma_observability") == observability and
            report.get("exact_key_endpoint_observability") == key_observability and
            report.get("fail_close") == FAIL_CLOSE and
            report.get("case_count") == 12 and report.get("exact_case_count") == 12 and
            report.get("production_code_changed") is False
        )
    except (AttributeError, KeyError, TypeError):
        return False


def main() -> int:
    if not validate_current_identities():
        raise RuntimeError("FAIL CLOSED: pinned AEX/worker/source/harness identity drift")
    production_rows, gates = production_effectmain()
    with tempfile.TemporaryDirectory(prefix="sm2_gamma18_owner_") as raw:
        public_rows, input_png_sha, gamma_observability, key_observability = public_owner(Path(raw))
    if public_rows != expected_rows(True) or production_rows != expected_rows(False):
        raise AssertionError("owner/production canonical row drift")
    for variant in ("v1_noninvert", "v2_noninvert"):
        if any(RAW_HASHES[variant][depth] == RAW_HASHES[variant.replace("noninvert", "invert")][depth]
               for depth in DEPTHS):
            raise AssertionError("key polarity is not observed at every depth")
    if any(RAW_HASHES["v1_noninvert"][depth] == RAW_HASHES["v2_noninvert"][depth]
           for depth in DEPTHS):
        raise AssertionError("intermediate Gamma/version path is not observed at every depth")

    identities = {
        "aex_sha256": sha_path(AEX), "aexcompat_worker_sha256": sha_path(WORKER),
        "aexcompat_commit": EXPECTED["worker_commit"],
        "production_source_sha256": sha_path(SOURCE),
        "effectmain_harness_sha256": sha_path(HARNESS),
        "generator_sha256": sha_path(Path(__file__)),
    }
    report = {
        "schema": "olmsmoother2.gamma18-keyendpoint-owner-closure/1",
        "date": "2026-08-12", "status": "raw_exact",
        "verdict": "PASS_12_INTERMEDIATE_GAMMA_KEY_ENDPOINT_EXPORTED_OWNER_TO_PUBLIC_EFFECTMAIN_RAW_EXACT",
        "claim_boundary": CLAIM, "identities": identities,
        "fixture": {
            "dimensions": [5, 5], "alpha_u8": 255, "rgb_u8": [list(x) for x in RGB],
            "derivation": "prior 25-pixel compound fixture with 24 pixels retained and pixel 0 changed from (1,1,1) to exact key endpoint (202,187,230)",
            "prior_fixture_rgba8_sha256": EXPECTED["base_rgba8"],
            "source_rgba8_sha256": EXPECTED["fixture_rgba8"],
            "input_png_sha256": input_png_sha,
        },
        "parameters": {
            "color_key_rgb_u8": [202, 187, 230],
            "gamma_palette_rgb_u8": [[255, 0, 0], [202, 187, 230]],
            "gamma_value": 1.8, "gamma_mode": "Gamma Colors",
            "smoothness": 100, "smooth_range": 100, "extra_smooth": 100,
            "versions": [1, 2], "key_polarities": ["noninvert", "invert"],
            "depths": ["PF8", "PF16", "PF32"],
        },
        "actual_exported_smart_owner": public_rows,
        "production_public_effectmain": {
            "chain": ["EffectMain SmartPreRender", "EffectMain SmartRender",
                      "typed RenderBits output"],
            "gates": gates, "rows": production_rows,
        },
        "cross_checks": {
            "noninvert_version_outputs_distinct_all_depths": True,
            "key_polarities_distinct_each_version_all_depths": True,
            "invert_version_outputs": "PF8/PF16 equal on this bounded fixture; PF32 distinct",
            "endpoint_pixels_present": {"red": [1, 0], "key": [0, 0]},
        },
        "intermediate_gamma_observability": gamma_observability,
        "exact_key_endpoint_observability": key_observability,
        "case_count": 12, "exact_case_count": 12,
        "production_code_changed": False, "fail_close": FAIL_CLOSE,
    }
    if not validate_report(report):
        raise AssertionError("generated report failed closed validation")
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    DOC.write_text(
        "# OLMSmoother2 Gamma 1.8 + key endpoint owner closure\n\n"
        "Verdict: `PASS_12_INTERMEDIATE_GAMMA_KEY_ENDPOINT_EXPORTED_OWNER_TO_PUBLIC_EFFECTMAIN_RAW_EXACT`\n\n"
        "The pinned unchanged Windows AEX exported Smart owner and production public "
        "`EffectMain` SmartPreRender → SmartRender path agree on all 12 raw outputs: "
        "Version 1/2 × non-invert/invert × PF8/PF16/PF32. The fixed opaque 5x5 source "
        "retains 24 pixels from the earlier compound fixture and replaces pixel 0 with "
        "the exact `(202,187,230)` key endpoint; pixel 1 is the red Gamma endpoint. "
        "Gamma Colors is ordered `[red,key]` at the intermediate Gamma Value `1.8`, "
        "with Smoothness/Range/Extra Smooth all `100`.\n\n"
        "As an observability control, the same actual Version 2 non-invert owner was also "
        "run at Gamma `1.0` and `2.4`; the `1.0`, `1.8`, and `2.4` raw hashes are pairwise "
        "distinct at every depth. Those endpoint controls are not added to the 12-cell "
        "actual-to-production claim.\n\n"
        "A second same-source control changes only `Enable Color Key` from on to off. "
        "Its raw hash differs from the key-enabled Gamma 1.8 output at PF8, PF16, and "
        "PF32, making the exact key endpoint action output-observable without expanding "
        "the 12-cell exact claim.\n\n"
        "The production public path additionally preserves complete input bytes, input/output "
        "row padding, pre-render rectangles, all parameter checkouts/checkins, and Smart "
        "lifecycle callbacks. No production code or installed plug-in was changed.\n\n"
        f"Boundary: {CLAIM}\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "raw_exact", "cells": 12, "report": str(REPORT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
