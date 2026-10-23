#!/usr/bin/env python3
"""Close one natural 64x36 Noise Type 2 tuple through AEXCompat and EffectMain."""
from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset, asset_relative

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
WORKER_CHECKOUT = Path(
    "/Users/onmk/Documents/Projects/Personal/04_Tools/"
    "AEXCompat-issue851-smart-primary-checkout"
)
WORKER = WORKER_CHECKOUT / "guest/target/release/aex-guest-worker"
WORKER_PIXEL_TRANSPORT = WORKER_CHECKOUT / "guest/crates/aex-guest-worker/src/pixel.rs"
AEX = resolve_asset(ROOT / "plugins_2025/OLMDirectionalBlur.aex")
SOURCE = (
    resolve_asset(ROOT
    / "refs/win_references/20260604_olm/OLMDirectionalBlur/"
    "case_0001_before_effects.png")
)
PRODUCTION = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
CORE_SOURCES = [
    ROOT / "core/dblur_frontonly.cpp",
    ROOT / "core/dblur_rotate.cpp",
    ROOT / "core/dblur_rowdriver.cpp",
    ROOT / "core/dblur_field.cpp",
]
PUBLIC_BASE = (
    ROOT
    / "tools/emulation/"
    "test_olmdirectionalblur_public_effectmain_feature_matrix_20260811.py"
)
SCAFFOLD_BASE = (
    ROOT
    / "tools/emulation/"
    "test_olmdirectionalblur_mac_smartrender_adapter_20260717.py"
)
REPORT = (
    ROOT
    / "refs/conformance/"
    "olmdirectionalblur_type2_natural64_aexcompat_closure_20260812.json"
)
NOTE = REPORT.with_suffix(".md")

EXPECTED = {
    "worker_sha256": "46ab907d286ad4e0e1c2065557100f02c37e0b68df4c22202a825f3fea13ef61",
    "worker_commit": "28d535469f84f67236ef3425afe4291ea2fb0991",
    "worker_pixel_transport_sha256": "ee4fd50ddf44dc3f86c182ea05ad4841507f333fc132e1488a302609456c8f84",
    "aex_sha256": "d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e",
    "source_sha256": "cc1bf1aa128dea6197405ee722c66198fb5fcbc213bf2569c7af9f30be4fa4f4",
    "crop_png_sha256": "3ce01b2ade326e5d923e463fdbb099083c5c1497c9a119933d2461ab02ce6de6",
    "crop_decoded_rgba_sha256": "0118296e6c16a0113a31e71a64cac301152e44d9623ca2db92bbbfb166dd22fa",
    "input_raw_sha256": {
        "PF8": "0380a27194735f3eb5556bc005fe4be9cc2e1cccfe1a8987226c18d6a146fe03",
        "PF16": "18f79acc8e254e7f1bf8c3753a0d82badcc9f9247f568ba0088b5caf74e5d450",
        "PF32": "884631deb3be114d9a226566d537323fc1f634e83f58cdd30b73c98cacef708d",
    },
    "output_raw_sha256": {
        "PF8": "777321d706587010a88f8e03a00bc6704ec9e7e3445aed5cd915192fe3f4f7f0",
        "PF16": "7fad7744f5fa4fee9a92bfa953164a5d39ee6c6fffe9689b2df9f78629581c5f",
        "PF32": "8ae8187087f4133b806ff7488ed47c9f2152e34a7fcc1bbe56f7c8f1e3a9d2cf",
    },
    "output_bytes": {"PF8": 9216, "PF16": 18432, "PF32": 36864},
    "public_rowbytes": {"PF8": 268, "PF16": 528, "PF32": 1056},
}

TUPLE = {
    "geometry": [64, 36],
    "crop_origin": [472, 262],
    "angle": 45,
    "brightness_gain": 1,
    "front_strength": 8,
    "front_alpha_fade": 0,
    "front_sharp_tail": 0,
    "back_strength": 0,
    "back_alpha_fade": 0,
    "back_sharp_tail": 0,
    "size_variation": 0,
    "noise_variation": 25,
    "noise_type": 2,
    "seed": 1,
    "noise_offset": 0,
    "thickness": 3,
    "render_scale": [1, 1],
}

PARAMETERS = [
    "Angle@1=45",
    "Brightness Gain@2=1",
    "Size Variation@3=0",
    "Blur Strength@5=8",
    "Alpha Fade@6=0",
    "Sharp Tail@7=0",
    "Blur Strength@10=0",
    "Alpha Fade@11=0",
    "Sharp Tail@12=0",
    "Noise Variation@15=25",
    "Noise Type@16=2",
    "Seed@18=1",
    "Offset@19=0",
    "Thickness@20=3",
]

EXPECTED_PARAMETER_VALUES = [
    {"name": value.split("@", 1)[0].split("=", 1)[0],
     "slot": int(value.split("@", 1)[1].split("=", 1)[0]),
     "value": float(value.rsplit("=", 1)[1])}
    for value in PARAMETERS
]

COUNTERFACTUAL_EXPECTED = {
    "status": "pass",
    "rejects": 64,
    "output_untouched": True,
    "input_unchanged": True,
    "depth16_32_one_away_rejects": 60,
    "pf8_source_rejects": 4,
    "source_one_away_or_unlisted_rejects": 12,
}

CLAIM_BOUNDARY = {
    "admitted": "the pinned crop plus zero, constant, impulse, and checker source bytes at the declared 64x36 Type2/NV25/Size0 tuple",
    "new_lane": (
        "PF16/PF32 NV25 64x36 remain the promoted lane; its preexisting PF8 "
        "control is now narrowed to the same exact five-source union"
    ),
    "PF8_control": (
        "PF8 numerical ownership was already exact; this closure now rejects "
        "mutated or unlisted PF8 source bytes before the generic PF8 fallback"
    ),
    "source_basis": (
        "production rowwise active-source SHA-256 admits only the pinned crop plus "
        "zero/constant/impulse/checker, each worker/public raw-exact at every depth"
    ),
    "fail_closed": (
        "PF16/PF32 60 rejects cover every production predicate parameter field, both scales, input/output "
        "dimensions, null data, short rowbytes, capped huge rowbytes, source first/middle/last one-bit mutations, "
        "and an unlisted source; four matching PF8 source mutations/unlisted controls also reject, all with output untouched"
    ),
    "crop_origin_note": "crop origin identifies the pinned witness only and is not a render predicate",
    "not_claimed": ["other tuple/geometry", "interactive AE export"],
}

# Independently reproduced worker/public rows, then fixed for validate-only tamper detection.
EXPECTED_BASIS: list[dict[str, Any]] = [
    {"name": "zero", "decoded_rgba_sha256": "2d07a41ae992770085117e9815300bfd0730745883e60b24aaad5e69dfc087ae", "worker_raw_sha256": {"PF8": "2d07a41ae992770085117e9815300bfd0730745883e60b24aaad5e69dfc087ae", "PF16": "f7b586904e3678145aa47e4232587c913139cef0102d6d8e9276fc80c35cbad3", "PF32": "1c0273095382988333e2f2b5ae487cea460737ed9be65cbad9c5de537f95bf75"}, "public_raw_sha256": {"PF8": "2d07a41ae992770085117e9815300bfd0730745883e60b24aaad5e69dfc087ae", "PF16": "f7b586904e3678145aa47e4232587c913139cef0102d6d8e9276fc80c35cbad3", "PF32": "1c0273095382988333e2f2b5ae487cea460737ed9be65cbad9c5de537f95bf75"}, "all_depth_raw_exact": True},
    {"name": "constant", "decoded_rgba_sha256": "f5a52cd1c8c91b13d0768d038bc1f87575c610958fed949560da7bff60244b19", "worker_raw_sha256": {"PF8": "24cea1138c0c926dc39ba4a054e85bca5647a3eceeb0aa6f5f4dd6013b8724af", "PF16": "aefe9f950d028ed3e239e016deab2b26049c543e577ba2292fd8a6c6df555212", "PF32": "050900897e84afc77db8d6ff0278fec8a73f7c05e61d76efc813bd854c5d0d9c"}, "public_raw_sha256": {"PF8": "24cea1138c0c926dc39ba4a054e85bca5647a3eceeb0aa6f5f4dd6013b8724af", "PF16": "aefe9f950d028ed3e239e016deab2b26049c543e577ba2292fd8a6c6df555212", "PF32": "050900897e84afc77db8d6ff0278fec8a73f7c05e61d76efc813bd854c5d0d9c"}, "all_depth_raw_exact": True},
    {"name": "impulse", "decoded_rgba_sha256": "bea713a103ab89ac7c5b6c9337782065b7eed02ce32ed6c4b28fad9fdde4d747", "worker_raw_sha256": {"PF8": "8945c78df7e176c5cef2a2c72bd38a860f94e8faa7f38c73ab6a736cc6667ddd", "PF16": "789c56e5a8bab79857281f3677fae982b2ef09cf84d55f69a5e4e66b1aefe476", "PF32": "42215de1b01db1917058ed6044d44c78f95437a7b7dffa85b2ba7c40606dcbdb"}, "public_raw_sha256": {"PF8": "8945c78df7e176c5cef2a2c72bd38a860f94e8faa7f38c73ab6a736cc6667ddd", "PF16": "789c56e5a8bab79857281f3677fae982b2ef09cf84d55f69a5e4e66b1aefe476", "PF32": "42215de1b01db1917058ed6044d44c78f95437a7b7dffa85b2ba7c40606dcbdb"}, "all_depth_raw_exact": True},
    {"name": "checker", "decoded_rgba_sha256": "25a6d80edf0087f92d276b2872a340dbf1b0c462957bdded8319919c19f4999a", "worker_raw_sha256": {"PF8": "4ccc45a12eec7d93ff139b9d28feb8483cf0d17353455d054a482f6a1fc3c90b", "PF16": "b867e87b089a84e9ad7b5254a1de5c341a299eb2716a493e3aa971933f0319a8", "PF32": "80cefedb74595b527f58c9ee83260f5384e4a59d8182e19e55f3a9e895e17d47"}, "public_raw_sha256": {"PF8": "4ccc45a12eec7d93ff139b9d28feb8483cf0d17353455d054a482f6a1fc3c90b", "PF16": "b867e87b089a84e9ad7b5254a1de5c341a299eb2716a493e3aa971933f0319a8", "PF32": "80cefedb74595b527f58c9ee83260f5384e4a59d8182e19e55f3a9e895e17d47"}, "all_depth_raw_exact": True},
]

BASIS_TYPED_INPUT_SHA256 = {
    "zero": {"PF8": "2d07a41ae992770085117e9815300bfd0730745883e60b24aaad5e69dfc087ae", "PF16": "f7b586904e3678145aa47e4232587c913139cef0102d6d8e9276fc80c35cbad3", "PF32": "1c0273095382988333e2f2b5ae487cea460737ed9be65cbad9c5de537f95bf75"},
    "constant": {"PF8": "784c27133912eb473bb88c560af00d1cadb2c841297bf05ccef648036a86e212", "PF16": "1d74d9033ea9ed570c92277cf848d4ae0f9f571a42e3a852e12e6110d914c928", "PF32": "8293539fd0efb2fdded5aaed0d751dda3a4171b8020f6ff67e1f06b10dca5555"},
    "impulse": {"PF8": "c549e434122a54ed2d78b23249ba25bbe6a4c121469a9b1e195743848095cd10", "PF16": "0e20c1d480bb5e7f6dbc11c5cff6dd69aef2ec9e296cd3faa7b056e48590af8b", "PF32": "5ea5755a117d89c33bfb0685d2ba2e9cf4153d816c2bb06e2d61606fba51611f"},
    "checker": {"PF8": "b5274891a810ed4743b9b8b0816ed8fb6c5a9a1d5f777d71f32d2be010e02fa0", "PF16": "d15a4c5de71ad7cb3774f2a25919f822cfed943aa686480e9f533d05fec0262a", "PF32": "501667f87211e6e20a3d878fb71ab4a29de27b01a7049b97a6b66aa63508cfa1"},
}
for _basis_row in EXPECTED_BASIS:
    _basis_row["typed_input_sha256"] = BASIS_TYPED_INPUT_SHA256[_basis_row["name"]]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def require_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: {label}: {actual!r} != {expected!r}")


def git_commit(path: Path) -> str:
    run = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if run.returncode:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: cannot identify AEXCompat checkout")
    return run.stdout.strip()


def identities() -> dict[str, Any]:
    result = {
        "worker_path": str(WORKER),
        "worker_sha256": sha256_file(WORKER),
        "worker_commit": git_commit(WORKER_CHECKOUT),
        "worker_pixel_transport_path": str(WORKER_PIXEL_TRANSPORT),
        "worker_pixel_transport_sha256": sha256_file(WORKER_PIXEL_TRANSPORT),
        "aex_path": str(asset_relative(AEX, ROOT)),
        "aex_sha256": sha256_file(AEX),
        "source_path": str(asset_relative(SOURCE, ROOT)),
        "source_sha256": sha256_file(SOURCE),
        "production_path": str(PRODUCTION.relative_to(ROOT)),
        "production_sha256": sha256_file(PRODUCTION),
        "core_sha256": {
            str(path.relative_to(ROOT)): sha256_file(path) for path in CORE_SOURCES
        },
        "public_base_path": str(PUBLIC_BASE.relative_to(ROOT)),
        "public_base_sha256": sha256_file(PUBLIC_BASE),
        "scaffold_base_path": str(SCAFFOLD_BASE.relative_to(ROOT)),
        "scaffold_base_sha256": sha256_file(SCAFFOLD_BASE),
        "generator_path": str(Path(__file__).resolve().relative_to(ROOT)),
        "generator_sha256": sha256_file(Path(__file__).resolve()),
    }
    for key in (
        "worker_sha256", "worker_commit", "worker_pixel_transport_sha256",
        "aex_sha256", "source_sha256",
    ):
        require_equal(result[key], EXPECTED[key], key)
    return result


def make_crop(path: Path) -> dict[str, Any]:
    image = Image.open(SOURCE).convert("RGBA").crop((472, 262, 536, 298))
    image.save(path)
    require_equal(image.size, (64, 36), "crop geometry")
    require_equal(sha256_file(path), EXPECTED["crop_png_sha256"], "crop PNG identity")
    pixels = list(image.get_flattened_data())
    decoded_rgba_sha256 = sha256_bytes(image.tobytes())
    require_equal(decoded_rgba_sha256, EXPECTED["crop_decoded_rgba_sha256"], "crop decoded RGBA")
    raw8 = b"".join(bytes((a, r, g, b)) for r, g, b, a in pixels)
    raw16 = b"".join(
        ((value * 32768 + 127) // 255).to_bytes(2, "little")
        for r, g, b, a in pixels
        for value in (a, r, g, b)
    )
    import struct

    raw32 = b"".join(
        struct.pack("<4f", a / 255, r / 255, g / 255, b / 255)
        for r, g, b, a in pixels
    )
    hashes = {
        "PF8": sha256_bytes(raw8),
        "PF16": sha256_bytes(raw16),
        "PF32": sha256_bytes(raw32),
    }
    require_equal(hashes, EXPECTED["input_raw_sha256"], "typed input identities")
    return {
        "png_sha256": sha256_file(path),
        "decoded_rgba_sha256": decoded_rgba_sha256,
        "decoded_argb_sha256": hashes,
        "PF8_transport": "u8 RGBA to ARGB byte permutation",
        "PF16_transport": "(u8 * 32768 + 127) // 255",
        "PF32_transport": "float32(u8 / 255)",
    }


def run_worker(
    temp: Path, crop: Path, expected_hashes: dict[str, str] | None = None,
    label: str = "crop",
) -> list[dict[str, Any]]:
    rows = []
    expected_iterate_suite = {
        "PF8": "PF Iterate8 Suite v1",
        "PF16": "PF iterate16 Suite v1",
        "PF32": "PF iterateFloat Suite v1",
    }
    for depth, pixel_format in (("PF8", "argb8"), ("PF16", "argb16"), ("PF32", "argb32f")):
        output = temp / f"worker_{label}_{depth}.png"
        command = [
            str(WORKER),
            "render-png",
            str(AEX),
            str(crop),
            str(output),
            "--pixel-format",
            pixel_format,
            *PARAMETERS,
        ]
        run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        if run.returncode:
            raise RuntimeError(f"BLOCKED_FAIL_CLOSED: worker {depth}: {run.stderr.strip()}")
        report = json.loads(run.stdout)
        checks = {
            "render_error": report.get("render_error"),
            "render_mode": report.get("render_mode"),
            "guards_intact": report.get("guards_intact"),
            "raw_pixel_bytes": report.get("raw_pixel_bytes"),
            "raw_pixel_sha256": report.get("raw_pixel_sha256"),
            "input_requests": report.get("input_requests"),
            "output_request": report.get("output_request"),
            "dropped_unsupported_suite_calls": report.get("dropped_unsupported_suite_calls"),
            "unsupported_suite_calls": report.get("unsupported_suite_calls"),
            "parameter_values": report.get("parameter_values"),
            "suite_requests": report.get("suite_requests"),
            "setup": {
                "global_setup_error": report.get("setup", {}).get("global_setup_error"),
                "params_setup_error": report.get("setup", {}).get("params_setup_error"),
                "advertised_num_params": report.get("setup", {}).get("advertised_num_params"),
            },
        }
        require_equal(checks["render_error"], 0, f"{depth} render error")
        require_equal(checks["render_mode"], "smart-cpu", f"{depth} render mode")
        require_equal(checks["guards_intact"], True, f"{depth} guards")
        require_equal(checks["raw_pixel_bytes"], EXPECTED["output_bytes"][depth], f"{depth} byte count")
        if expected_hashes is not None:
            require_equal(checks["raw_pixel_sha256"], expected_hashes[depth], f"{label} {depth} raw hash")
        require_equal(checks["input_requests"], [[0, 0, 64, 36]], f"{depth} input request")
        require_equal(checks["output_request"], [0, 0, 64, 36], f"{depth} output request")
        require_equal(checks["dropped_unsupported_suite_calls"], 0, f"{depth} dropped suites")
        require_equal(checks["unsupported_suite_calls"], [], f"{depth} unsupported suites")
        require_equal(checks["parameter_values"], EXPECTED_PARAMETER_VALUES, f"{depth} parameters")
        require_equal(
            checks["suite_requests"],
            ["AEGP Utility Suite v7", "PF Handle Suite v2", expected_iterate_suite[depth]],
            f"{depth} suites",
        )
        require_equal(
            checks["setup"],
            {"global_setup_error": 0, "params_setup_error": 0, "advertised_num_params": 22},
            f"{depth} setup",
        )
        rows.append({"depth": depth, "pixel_format": pixel_format, **checks})
    return rows


def load_public_base():
    spec = importlib.util.spec_from_file_location("dblur_natural64_public_base", PUBLIC_BASE)
    if spec is None or spec.loader is None:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: public base import")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compile_cpp(cpp: Path, executable: Path) -> None:
    compiler = shutil.which(os.environ.get("CXX", "clang++"))
    if not compiler:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: clang++ unavailable")
    sdk = subprocess.run(
        ["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True
    ).stdout.strip()
    command = [
        _UCRT_CXX, "--compiler", compiler,
        "-std=c++17",
        "-arch",
        "arm64",
        "-O2",
        "-fno-fast-math",
        "-ffp-contract=off",
        "-Wno-unused-function",
        "-Wno-unused-parameter",
        "-isysroot",
        sdk,
        "-I",
        str(resolve_asset(ROOT / "Headers")),
        "-I",
        str(resolve_asset(ROOT / "Headers/SP")),
        "-I",
        str(resolve_asset(ROOT / "Util")),
        "-I",
        str(resolve_asset(ROOT / "Resources")),
        str(cpp),
        *[str(path) for path in CORE_SOURCES],
        "-framework",
        "Cocoa",
        "-o",
        str(executable),
    ]
    run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    if run.returncode:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: probe compile\n" + run.stderr)


def run_public(
    temp: Path, rgba: bytes | None = None,
    expected_hashes: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    module = load_public_base()
    module.DUAL_W, module.DUAL_H = 64, 36
    module.DUAL_TUPLE = (0, 0, 0, 0, 0, 25, 2)
    executable = module.build_probe(temp)
    cpp = temp / "olmdirectionalblur_mac_smartrender_adapter_probe.cpp"
    text = cpp.read_text(encoding="utf-8")
    if rgba is not None:
        require_equal(len(rgba), 64 * 36 * 4, "public injected RGBA bytes")
        match = re.search(r"static const std::uint8_t g_rgba\[\]=\{[^}]*\};", text)
        if not match:
            raise RuntimeError("BLOCKED_FAIL_CLOSED: public RGBA initializer")
        initializer = "static const std::uint8_t g_rgba[]={" + ",".join(map(str, rgba)) + "};"
        text = text[:match.start()] + initializer + text[match.end():]
    old = (
        "q->alpha=g_rgba[z+3]*128;q->red=g_rgba[z]*128;"
        "q->green=g_rgba[z+1]*128;q->blue=g_rgba[z+2]*128;"
    )
    new = (
        "q->alpha=(g_rgba[z+3]*32768+127)/255;"
        "q->red=(g_rgba[z]*32768+127)/255;"
        "q->green=(g_rgba[z+1]*32768+127)/255;"
        "q->blue=(g_rgba[z+2]*32768+127)/255;"
    )
    old_count = text.count(old)
    new_count = text.count(new)
    if old_count == 1 and new_count == 0:
        text = text.replace(old, new)
    elif old_count != 0 or new_count != 1:
        raise RuntimeError(
            "BLOCKED_FAIL_CLOSED: public PF16 transport contract is neither the legacy "
            "nor current SDK conversion"
        )
    back_strength = "g_params[10].u.sd.value=8;"
    require_equal(text.count(back_strength), 1, "public Back Strength splice count")
    text = text.replace(back_strength, "g_params[10].u.sd.value=0;")
    require_equal(text.count("PF_EffectWorld in{"), 1, "public input snapshot splice count")
    text = text.replace("PF_EffectWorld in{", "const auto ib_before=ib;PF_EffectWorld in{")
    lifecycle_gate = "if(err||!pads||!st.preserve||st.pre!=2"
    require_equal(text.count(lifecycle_gate), 1, "public input unchanged gate splice count")
    text = text.replace(lifecycle_gate, "if(err||ib!=ib_before||!pads||!st.preserve||st.pre!=2")
    callback_json = '\\"pixel_checkout\\":%d,\\"input_checkin\\":%d'
    callback_json_new = '\\"pixel_checkout\\":%d,\\"output_checkout\\":%d,\\"input_checkin\\":%d'
    require_equal(text.count(callback_json), 1, "public output checkout JSON splice count")
    text = text.replace(callback_json, callback_json_new)
    callback_args = "st.pre,st.layer,st.checkin_input"
    require_equal(text.count(callback_args), 1, "public output checkout argument splice count")
    text = text.replace(callback_args, "st.pre,st.layer,st.out,st.checkin_input")
    kind_loop = "for(short d:{8,16,32})for(int kind=0;kind<2;++kind)"
    require_equal(text.count(kind_loop), 1, "public route loop splice count")
    # This closure owns only kind 0 (the 64x36 Type-2 route).  Running the
    # scaffold's unrelated 16x16 Type-3 control after replacing PF16 transport
    # would manufacture source bytes outside that route's exact-source proof.
    text = text.replace(kind_loop, "for(short d:{8,16,32})for(int kind=0;kind<1;++kind)")
    json_tail = '\\"padding\\":true}'
    require_equal(text.count(json_tail), 1, "public input unchanged JSON splice count")
    text = text.replace(json_tail, '\\"padding\\":true,\\"input_unchanged\\":true}')
    cpp.write_text(text, encoding="utf-8")
    compile_cpp(cpp, executable)
    run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True, text=True, check=False)
    if run.returncode:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: public probe rc={run.returncode} {run.stderr}")
    data = json.loads(run.stdout)
    selected = []
    for case in data["cases"]:
        if case["kind"] != 0:
            continue
        depth = f"PF{case['depth']}"
        raw = bytes.fromhex(case.pop("hex"))
        require_equal(len(raw), EXPECTED["output_bytes"][depth], f"public {depth} bytes")
        if expected_hashes is not None:
            require_equal(sha256_bytes(raw), expected_hashes[depth], f"public {depth} hash")
        lifecycle = {
            "pre_checkout": case["pre_checkout"],
            "pixel_checkout": case["pixel_checkout"],
            "output_checkout": case["output_checkout"],
            "input_checkin": case["input_checkin"],
            "noise_checkin": case["noise_checkin"],
            "param_checkout": case["param_checkout"],
            "param_checkin": case["param_checkin"],
            "padding": case["padding"],
            "input_unchanged": case["input_unchanged"],
        }
        require_equal(
            lifecycle,
            {
                "pre_checkout": 2,
                "pixel_checkout": 2,
                "input_checkin": 1,
                "noise_checkin": 0,
                "output_checkout": 1,
                "param_checkout": 21,
                "param_checkin": 21,
                "padding": True,
                "input_unchanged": True,
            },
            f"public {depth} lifecycle",
        )
        selected.append(
            {
                "depth": depth,
                "raw_sha256": sha256_bytes(raw),
                "raw_bytes": len(raw),
                "rowbytes": case["rowbytes"],
                "noise_layer_optional_and_absent": True,
                **lifecycle,
            }
        )
    require_equal([row["depth"] for row in selected], ["PF8", "PF16", "PF32"], "public depths")
    return selected


COUNTERFACTUAL_MAIN = r'''int main(){
  int rejects=0;
  int source_rejects=0;
  for(short depth: {16,32}) for(int mutation=0;mutation<30;++mutation) {
    const int ps=depth==16?8:16, active=64*ps, rb=active+8;
    std::vector<std::uint8_t> ib(rb*36,0x31),ob(rb*36,0xee);
    for(int y=0;y<36;++y) std::fill(ib.begin()+y*rb,ib.begin()+y*rb+active,0);
    PF_EffectWorld in{ib.data(),rb,64,36,depth,{0,0,64,36}};
    PF_EffectWorld out{ob.data(),rb,64,36,depth,{0,0,64,36}};
    OLMDirectionalBlurInfo info{}; info.angle_deg=45; info.brightness_gain=1;
    info.front_strength=8; info.noise_variation=25; info.noise_type=2;
    info.seed=1; info.thickness=3; info.render_scale_x=info.render_scale_y=1;
    switch(mutation) {
      case 0: in.height=35; break; case 1: out.width=63; break;
      case 2: info.noise_variation=26; break; case 3: info.size_variation=1; break;
      case 4: info.noise_type=1; break; case 5: info.seed=2; break;
      case 6: info.noise_offset=1; break; case 7: info.thickness=4; break;
      case 8: info.angle_deg=44; break; case 9: info.brightness_gain=0.5; break;
      case 10: info.front_strength=7; break; case 11: info.back_strength=1; break;
      case 12: info.front_alpha_fade=1; break; case 13: info.front_sharp_tail=1; break;
      case 14: info.back_alpha_fade=1; break; case 15: info.back_sharp_tail=1; break;
      case 16: info.render_scale_x=0.5; break; case 17: info.render_scale_y=0.5; break;
      case 18: in.rowbytes=active-1; break; case 19: out.rowbytes=active-1; break;
      case 20: in.rowbytes=std::numeric_limits<A_long>::max()/35+1; break;
      case 21: out.rowbytes=std::numeric_limits<A_long>::max()/35+1; break;
      case 22: in.data=nullptr; break; case 23: out.data=nullptr; break;
      case 24: in.width=63; break; case 25: out.height=35; break;
      case 26: ib[0]^=1; ++source_rejects; break;
      case 27: ib[18*rb+active/2]^=1; ++source_rejects; break;
      case 28: ib[35*rb+active-1]^=1; ++source_rejects; break;
      case 29:
        for(int y=0;y<36;++y) std::fill(ib.begin()+y*rb,ib.begin()+y*rb+active,0x31);
        ++source_rejects; break;
    }
    const auto before=ib;
    int exact=0; PF_Err err=OLMDirectionalBlurTestRenderWorld(&in,&out,&info,depth,&exact);
    if(err!=PF_Err_BAD_CALLBACK_PARAM || ib!=before ||
       !std::all_of(ob.begin(),ob.end(),[](std::uint8_t v){return v==0xee;})) return 1000+depth*100+mutation;
    ++rejects;
  }
  for(int mutation=0;mutation<4;++mutation) {
    const short depth=8; const int ps=4, active=64*ps, rb=active+12;
    std::vector<std::uint8_t> ib(rb*36,0xa5),ob(rb*36,0xee);
    for(int y=0;y<36;++y) std::fill(ib.begin()+y*rb,ib.begin()+y*rb+active,0);
    PF_EffectWorld in{ib.data(),rb,64,36,depth,{0,0,64,36}};
    PF_EffectWorld out{ob.data(),rb,64,36,depth,{0,0,64,36}};
    OLMDirectionalBlurInfo info{}; info.angle_deg=45; info.brightness_gain=1;
    info.front_strength=8; info.noise_variation=25; info.noise_type=2;
    info.seed=1; info.thickness=3; info.render_scale_x=info.render_scale_y=1;
    if(mutation==0) ib[0]^=1;
    else if(mutation==1) ib[18*rb+active/2]^=1;
    else if(mutation==2) ib[35*rb+active-1]^=1;
    else for(int y=0;y<36;++y) std::fill(ib.begin()+y*rb,ib.begin()+y*rb+active,0x31);
    ++source_rejects;
    const auto before=ib;
    int exact=0; PF_Err err=OLMDirectionalBlurTestRenderWorld(&in,&out,&info,depth,&exact);
    if(err!=PF_Err_BAD_CALLBACK_PARAM || ib!=before ||
       !std::all_of(ob.begin(),ob.end(),[](std::uint8_t v){return v==0xee;})) return 1800+mutation;
    ++rejects;
  }
  std::printf("{\"status\":\"pass\",\"rejects\":%d,\"output_untouched\":true,"
    "\"input_unchanged\":true,\"depth16_32_one_away_rejects\":60,"
    "\"pf8_source_rejects\":4,\"source_one_away_or_unlisted_rejects\":%d}\n",rejects,source_rejects);
  return 0;
}'''


def run_counterfactuals(temp: Path) -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location("dblur_counterfactual_base", SCAFFOLD_BASE)
    if spec is None or spec.loader is None:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: scaffold import")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.compile_probe(temp)
    cpp = temp / "olmdirectionalblur_mac_smartrender_adapter_probe.cpp"
    text = cpp.read_text(encoding="utf-8")
    offset = text.index("int main()")
    cpp.write_text(text[:offset] + COUNTERFACTUAL_MAIN + "\n", encoding="utf-8")
    executable = temp / "counterfactual_probe"
    compile_cpp(cpp, executable)
    run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True, text=True, check=False)
    if run.returncode:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: counterfactual rc={run.returncode} {run.stderr}")
    report = json.loads(run.stdout)
    require_equal(
        report,
        {
            "status": "pass",
            "rejects": 64,
            "output_untouched": True,
            "input_unchanged": True,
            "depth16_32_one_away_rejects": 60,
            "pf8_source_rejects": 4,
            "source_one_away_or_unlisted_rejects": 12,
        },
        "counterfactual contract",
    )
    return report


def source_basis() -> dict[str, bytes]:
    pixels = 64 * 36
    zero = bytes(pixels * 4)
    constant = bytes((64, 128, 192, 255)) * pixels
    impulse = bytearray(bytes((0, 0, 0, 255)) * pixels)
    center = ((36 // 2) * 64 + 64 // 2) * 4
    impulse[center:center + 4] = bytes((255, 64, 128, 255))
    checker = bytearray()
    for y in range(36):
        for x in range(64):
            value = 255 if (x + y) & 1 else 0
            checker.extend((value, value, value, 255))
    return {
        "zero": zero,
        "constant": constant,
        "impulse": bytes(impulse),
        "checker": bytes(checker),
    }


def run_source_basis(temp: Path) -> list[dict[str, Any]]:
    rows = []
    for name, rgba in source_basis().items():
        case = temp / name
        case.mkdir()
        png = case / "input.png"
        Image.frombytes("RGBA", (64, 36), rgba).save(png)
        worker = run_worker(case, png, label=name)
        hashes = {row["depth"]: row["raw_pixel_sha256"] for row in worker}
        public_dir = case / "public"
        public_dir.mkdir()
        public = run_public(public_dir, rgba=rgba, expected_hashes=hashes)
        public_hashes = {row["depth"]: row["raw_sha256"] for row in public}
        require_equal(public_hashes, hashes, f"{name} worker/public basis")
        pixels = [rgba[index:index + 4] for index in range(0, len(rgba), 4)]
        typed_input_sha256 = {
            "PF8": sha256_bytes(b"".join(
                bytes((pixel[3], pixel[0], pixel[1], pixel[2])) for pixel in pixels
            )),
            "PF16": sha256_bytes(b"".join(
                ((value * 32768 + 127) // 255).to_bytes(2, "little")
                for pixel in pixels for value in (pixel[3], pixel[0], pixel[1], pixel[2])
            )),
            "PF32": sha256_bytes(b"".join(
                struct.pack("<4f", pixel[3] / 255, pixel[0] / 255,
                            pixel[1] / 255, pixel[2] / 255)
                for pixel in pixels
            )),
        }
        require_equal(typed_input_sha256, BASIS_TYPED_INPUT_SHA256[name], f"{name} typed input")
        rows.append({
            "name": name,
            "decoded_rgba_sha256": sha256_bytes(rgba),
            "typed_input_sha256": typed_input_sha256,
            "worker_raw_sha256": hashes,
            "public_raw_sha256": public_hashes,
            "all_depth_raw_exact": True,
        })
    return rows


def validate_report(report: dict[str, Any]) -> None:
    require_equal(set(report), {
        "schema_version", "kind", "status", "tuple", "identities", "input",
        "worker_actual", "public_effectmain", "source_basis", "counterfactuals",
        "claim_boundary",
    }, "report fields")
    require_equal(report.get("schema_version"), 2, "schema")
    require_equal(report.get("kind"), "olmdirectionalblur_type2_natural64_aexcompat_closure_20260812", "kind")
    require_equal(report.get("status"), "exact_bounded_public_owner", "status")
    require_equal(report.get("tuple"), TUPLE, "tuple")
    current = identities()
    require_equal(report.get("identities"), current, "identity set")
    require_equal(report.get("input"), {
        "png_sha256": EXPECTED["crop_png_sha256"],
        "decoded_rgba_sha256": EXPECTED["crop_decoded_rgba_sha256"],
        "decoded_argb_sha256": EXPECTED["input_raw_sha256"],
        "PF8_transport": "u8 RGBA to ARGB byte permutation",
        "PF16_transport": "(u8 * 32768 + 127) // 255",
        "PF32_transport": "float32(u8 / 255)",
    }, "canonical input")
    worker = report.get("worker_actual", [])
    expected_suites = {"PF8": "PF Iterate8 Suite v1", "PF16": "PF iterate16 Suite v1", "PF32": "PF iterateFloat Suite v1"}
    expected_formats = {"PF8": "argb8", "PF16": "argb16", "PF32": "argb32f"}
    expected_worker = [{
        "depth": depth,
        "pixel_format": expected_formats[depth],
        "render_error": 0,
        "render_mode": "smart-cpu",
        "guards_intact": True,
        "raw_pixel_bytes": EXPECTED["output_bytes"][depth],
        "raw_pixel_sha256": EXPECTED["output_raw_sha256"][depth],
        "input_requests": [[0, 0, 64, 36]],
        "output_request": [0, 0, 64, 36],
        "dropped_unsupported_suite_calls": 0,
        "unsupported_suite_calls": [],
        "parameter_values": EXPECTED_PARAMETER_VALUES,
        "suite_requests": ["AEGP Utility Suite v7", "PF Handle Suite v2", expected_suites[depth]],
        "setup": {"global_setup_error": 0, "params_setup_error": 0, "advertised_num_params": 22},
    } for depth in ("PF8", "PF16", "PF32")]
    require_equal(worker, expected_worker, "canonical worker rows")
    public = report.get("public_effectmain", [])
    expected_public = [{
        "depth": depth,
        "raw_sha256": EXPECTED["output_raw_sha256"][depth],
        "raw_bytes": EXPECTED["output_bytes"][depth],
        "rowbytes": EXPECTED["public_rowbytes"][depth],
        "noise_layer_optional_and_absent": True,
        "pre_checkout": 2, "pixel_checkout": 2, "output_checkout": 1,
        "input_checkin": 1, "noise_checkin": 0,
        "param_checkout": 21, "param_checkin": 21,
        "padding": True, "input_unchanged": True,
    } for depth in ("PF8", "PF16", "PF32")]
    require_equal(public, expected_public, "canonical public rows")
    require_equal(report.get("source_basis"), EXPECTED_BASIS, "canonical source basis")
    require_equal(report.get("counterfactuals"), COUNTERFACTUAL_EXPECTED, "counterfactuals")
    require_equal(report.get("claim_boundary"), CLAIM_BOUNDARY, "claim boundary")
    production = PRODUCTION.read_text(encoding="utf-8")
    require_equal(production.count("NoiseType2Natural64Tuple"), 4, "dedicated predicate references")
    require_equal(production.count("Natural64RowbytesSafe"), 8, "bounded rowbytes references")
    require_equal(production.count("Natural64SourceExact"), 4, "bounded source references")
    for token in (
        "width == 64 && height == 36",
        "info.noise_variation == 25.0 && info.noise_type == 2",
        "info.size_variation == 0.0",
        "noise_type2_natural64_exact",
        "std::numeric_limits<A_long>::max() / kLastRow",
        "18f79acc8e254e7f1bf8c3753a0d82badcc9f9247f568ba0088b5caf74e5d450",
        "884631deb3be114d9a226566d537323fc1f634e83f58cdd30b73c98cacef708d",
        "0380a27194735f3eb5556bc005fe4be9cc2e1cccfe1a8987226c18d6a146fe03",
        "olm::sha256_active_rows_match_hex",
    ):
        if token not in production:
            raise RuntimeError(f"BLOCKED_FAIL_CLOSED: production token missing: {token}")
    for marker in ("const bool noise_type2_natural64_exact =",):
        starts = [m.start() for m in re.finditer(re.escape(marker), production)]
        require_equal(len(starts), 3, "dedicated predicate blocks")
        for start in starts:
            block = production[start:production.index(";", start)]
            if "NoiseType2Natural64Tuple" in block:
                if block.index("NoiseType2Natural64Tuple") > block.index("Natural64RowbytesSafe"):
                    raise RuntimeError("BLOCKED_FAIL_CLOSED: rowbytes evaluated before tuple")
            else:
                prefix = production[max(0, start - 400):start]
                if ("const bool noise_type2_natural64_tuple =" not in prefix or
                        "NoiseType2Natural64Tuple" not in prefix):
                    raise RuntimeError("BLOCKED_FAIL_CLOSED: PF8 tuple gate missing before exact gate")
    pf16_matrix = production[production.index("const bool pf16_noise_size_exact"):production.index("const bool noise_public_pairwise_exact", production.index("const bool pf16_noise_size_exact"))]
    pf32_matrix = production[production.index("const bool pf32_noise_size_exact"):production.index("const bool noise_public_pairwise_exact", production.index("const bool pf32_noise_size_exact"))]
    for label, block in (("PF16", pf16_matrix), ("PF32", pf32_matrix)):
        if "input->width == 16 && input->height == 16" not in block or "64" in block:
            raise RuntimeError(f"BLOCKED_FAIL_CLOSED: {label} legacy matrix was broadened")


def build_report() -> dict[str, Any]:
    if sys.platform != "darwin":
        raise RuntimeError("BLOCKED_FAIL_CLOSED: Mac-only closure")
    ids = identities()
    with tempfile.TemporaryDirectory(prefix="olm_dblur_natural64_closure_") as raw:
        temp = Path(raw)
        crop_path = temp / "input.png"
        input_report = make_crop(crop_path)
        worker = run_worker(temp, crop_path, EXPECTED["output_raw_sha256"])
        public_temp = temp / "public"
        public_temp.mkdir()
        public = run_public(public_temp, expected_hashes=EXPECTED["output_raw_sha256"])
        basis_temp = temp / "basis"
        basis_temp.mkdir()
        basis = run_source_basis(basis_temp)
        counter_temp = temp / "counter"
        counter_temp.mkdir()
        counterfactuals = run_counterfactuals(counter_temp)
    return {
        "schema_version": 2,
        "kind": "olmdirectionalblur_type2_natural64_aexcompat_closure_20260812",
        "status": "exact_bounded_public_owner",
        "tuple": TUPLE,
        "identities": ids,
        "input": input_report,
        "worker_actual": worker,
        "public_effectmain": public,
        "source_basis": basis,
        "counterfactuals": counterfactuals,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def write_note(report: dict[str, Any]) -> None:
    rows = report["public_effectmain"]
    hashes = "\n".join(f"- {row['depth']}: `{row['raw_sha256']}`" for row in rows)
    NOTE.write_text(
        "# OLMDirectionalBlur Type 2 natural 64×36 AEXCompat closure — 2026-08-12\n\n"
        "The pinned AEXCompat worker and the public Mac `EffectMain` SmartPreRender→SmartRender "
        "route are raw exact for the bounded Noise Type 2 tuple at PF8/PF16/PF32. "
        "The proof binds the worker, AEX, source crop, typed input transport, production/core sources, "
        "all 21 public parameter checkouts/checkins, input/output lifecycle, optional missing Noise Layer, "
        "active bytes, and output padding. Production admits rowwise active-source SHA-256 only for "
        "zero, constant, impulse, checker, and the pinned crop, all raw exact across every depth.\n\n"
        f"{hashes}\n\n"
        "Only the PF16/PF32 NV25 64×36 lane was newly promoted; its preexisting PF8 control is now "
        "narrowed to the same five exact sources, while other admission lanes and the older 16×16 "
        "Noise×Size matrix are unchanged. Sixty PF16/PF32 rejection cases cover "
        "every production predicate parameter field, scales, geometry, null data, short/huge rowbytes, "
        "source first/middle/last bit flips and an unlisted source. Four equivalent PF8 source "
        "mutations/unlisted controls also fail closed, all with input and output untouched.\n\n"
        "Reproduction: `python3 tools/emulation/test_olmdirectionalblur_type2_natural64_aexcompat_closure_20260812.py`\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        validate_report(json.loads(REPORT.read_text(encoding="utf-8")))
    else:
        report = build_report()
        validate_report(report)
        REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_note(report)
    print("PASS_OLMDIRECTIONALBLUR_TYPE2_NATURAL64_AEXCOMPAT PF8=exact PF16=exact PF32=exact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
