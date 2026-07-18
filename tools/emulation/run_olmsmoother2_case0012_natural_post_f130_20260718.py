#!/usr/bin/env python3
"""Bounded natural actual-AEX run for Smoother2 case_0012.

The only translated host operation is PF8 premultiplication.  Key removal,
sRGB decode, class-plane generation, polygon dispatch, and cce0 execute from
the checked-in current Windows AEX under Unicorn.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

from PIL import Image
from unicorn.x86_const import UC_X86_REG_RBP, UC_X86_REG_RBX, UC_X86_REG_RCX, UC_X86_REG_RDX

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "emulation"))

from aex_loader import AexLoader  # noqa: E402
from test_olmsmoother2_case0012_classplane_natural_caller_20260717 import (  # noqa: E402
    FUN_ADA0,
    SerialVcomp,
    install_descriptors,
)
from test_smoother2_fullchain_diff import FCCE0  # noqa: E402
from test_smoother2_producer import AEX_PATH, SmootherStruct  # noqa: E402

CASE_ID = "legacy_case_0012_gamma5_red_blue_current_aex"
EXPECTED_AEX_SHA256 = "7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7"
WINDOWS_ROOT = ROOT / (
    "refs/win_references/olm_reference_return_windows_smoother2_legacy_full_current_aex_recapture_20260621/"
    "OLMSmootherv2"
)
SOURCE = WINDOWS_ROOT / "input\\current_olm_cells.png"
WINDOWS_BEFORE = WINDOWS_ROOT / (
    "smoother2_legacy_full_current_aex_recapture_20260621__software__fr24__"
    "legacy_case_0012_gamma5_red_blue_current_aex_before_effects.png"
)
PARAMS = ROOT / (
    "refs/reports/olmsmoother2_current_aex_residual_audit_latest/run/candidate/_params/"
    "smoother2_legacy_full_current_aex_recapture_20260621__software__fr24__"
    "legacy_case_0012_gamma5_red_blue_current_aex.json"
)

CROP_ORIGIN = (84, 833)
CROP_SIZE = 16
HOST_TARGET = (92, 841)
LOCAL_TARGET = (HOST_TARGET[0] - CROP_ORIGIN[0], HOST_TARGET[1] - CROP_ORIGIN[1])
EXPECTED_HOST_DESCRIPTOR = [92, 841, 1, 92, 842, 2]
EXPECTED_LOCAL_DESCRIPTOR = [8, 8, 1, 8, 9, 2]

FUN_KEY_REMOVE = 0x180002A70
FUN_SRGB_DECODE = 0x180002BA0
FUN_FEF0 = 0x18000FEF0
POST_F130_PRE_BOOST = 0x18000FF99
POST_F130_POST_BOOST = 0x18000FFD2
CCE0_AFTER_C280 = 0x18000CD5F


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("FAIL CLOSED: " + message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f32_u32(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def pf8_premultiply(value: int, alpha: int) -> int:
    return (value * alpha + 127) // 255


def read_case_parameters() -> dict[str, Any]:
    data = json.loads(PARAMS.read_text(encoding="utf-8"))
    require(data["case_id"] == CASE_ID, "parameter case id drift")
    rows = data["params"]["effects"][0]["params"]
    values: dict[str, Any] = {}
    gamma_colors = []
    for row in rows:
        name = row["name"]
        if name == "Gamma Color":
            gamma_colors.append(row["value"])
        elif name not in {"Effect Opacity", "GPU Rendering"}:
            values[name] = row["value"]
    values["Gamma Colors"] = gamma_colors
    require(values["Enable Color Key"] == 1 and values["Invert Color Key"] == 0, "key mode drift")
    require(values["Color Key"] == [1, 1, 1, 1], "key color drift")
    require(values["Smoothness"] == 100 and values["Extra Smooth"] == 40, "scale parameters drift")
    require(values["Smooth Range"] == 88 and values["Smoother Version"] == 2, "classifier parameters drift")
    require(values["Gamma Correction"] == 2 and values["Number of Gamma Colors"] == 5, "gamma mode drift")
    require(len(gamma_colors) == 5, "gamma color list drift")
    return values


def alloc_i32(loader: AexLoader, value: int) -> int:
    address = loader.bump_alloc(4, align=4)
    loader.write_bytes(address, struct.pack("<i", value))
    return address


def source_pixel(loader: AexLoader, smoother: SmootherStruct, x: int, y: int) -> list[float]:
    address = smoother.src_base + y * smoother.src_stride + x * 16
    return list(struct.unpack("<4f", loader.read_bytes(address, 16)))


def class_pixel(loader: AexLoader, smoother: SmootherStruct, x: int, y: int) -> list[int]:
    address = smoother.class_base + y * smoother.class_stride + x * 4
    return list(loader.read_bytes(address, 4))


def snapshot_builder(loader: AexLoader, base: int) -> dict[str, Any]:
    count = struct.unpack("<Q", loader.read_bytes(base + 0x130, 8))[0]
    require(count <= 12, f"builder polygon count out of range: {count}")
    vertices = []
    for index in range(count):
        address = base + 0x40 + index * 0x14
        rgba = list(struct.unpack("<4f", loader.read_bytes(address, 16)))
        weight = struct.unpack("<f", loader.read_bytes(address + 16, 4))[0]
        vertices.append({
            "rgba": rgba,
            "rgba_u32": [f32_u32(value) for value in rgba],
            "weight": weight,
            "weight_u32": f32_u32(weight),
        })
    return {"count": count, "vertices": vertices}


def snapshot_compact(loader: AexLoader, base: int) -> dict[str, Any]:
    count = struct.unpack("<Q", loader.read_bytes(base + 0xF0, 8))[0]
    require(count <= 12, f"compact polygon count out of range: {count}")
    vertices = []
    for index in range(count):
        address = base + index * 0x14
        rgba = list(struct.unpack("<4f", loader.read_bytes(address, 16)))
        weight = struct.unpack("<f", loader.read_bytes(address + 16, 4))[0]
        vertices.append({
            "rgba": rgba,
            "rgba_u32": [f32_u32(value) for value in rgba],
            "weight": weight,
            "weight_u32": f32_u32(weight),
        })
    return {"count": count, "vertices": vertices}


def translate_descriptor(descriptor: list[int]) -> list[int]:
    translated = descriptor.copy()
    translated[0] += CROP_ORIGIN[0]
    translated[1] += CROP_ORIGIN[1]
    translated[3] += CROP_ORIGIN[0]
    translated[4] += CROP_ORIGIN[1]
    return translated


def build_host_adapted_source(loader: AexLoader, smoother: SmootherStruct) -> dict[str, Any]:
    with Image.open(SOURCE) as image:
        image = image.convert("RGBA")
        for local_y in range(CROP_SIZE):
            for local_x in range(CROP_SIZE):
                host_x = CROP_ORIGIN[0] + local_x
                host_y = CROP_ORIGIN[1] + local_y
                red, green, blue, alpha = image.getpixel((host_x, host_y))
                premultiplied = (
                    pf8_premultiply(red, alpha),
                    pf8_premultiply(green, alpha),
                    pf8_premultiply(blue, alpha),
                )
                smoother.set_src_pixel(
                    local_x,
                    local_y,
                    (
                        premultiplied[0] / 255.0,
                        premultiplied[1] / 255.0,
                        premultiplied[2] / 255.0,
                        alpha / 255.0,
                    ),
                )
        raw_witness = list(image.getpixel((92, 840)))

    with Image.open(WINDOWS_BEFORE) as image:
        before_witness = list(image.convert("RGBA").getpixel((92, 840)))
    require(raw_witness == [174, 174, 174, 174], f"raw PF8 witness drift: {raw_witness}")
    require(before_witness == [119, 119, 119, 174], f"Windows before-effects witness drift: {before_witness}")
    require(pf8_premultiply(174, 174) == 119, "PF8 nearest-code adapter drift")
    return {"raw_witness": raw_witness, "windows_before_effects_witness": before_witness}


def run() -> dict[str, Any]:
    require(sha256(AEX_PATH) == EXPECTED_AEX_SHA256, "current AEX hash drift")
    params = read_case_parameters()
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=False)
    loader.register_libm_impls(max_threads=1)
    smoother = SmootherStruct(loader, CROP_SIZE, CROP_SIZE)
    host_adapter = build_host_adapted_source(loader, smoother)
    vcomp = SerialVcomp(loader)

    width = alloc_i32(loader, CROP_SIZE)
    left = alloc_i32(loader, 0)
    height = alloc_i32(loader, CROP_SIZE)
    top = alloc_i32(loader, 0)
    source_descriptor = loader.bump_alloc(24, align=16)
    loader.write_bytes(
        source_descriptor,
        struct.pack("<QiiQ", smoother.src_base, CROP_SIZE, CROP_SIZE, smoother.src_stride),
    )
    key = loader.bump_alloc(16, align=16)
    loader.write_bytes(key, struct.pack("<4f", *params["Color Key"]))
    key_result = loader.call_function(
        FUN_KEY_REMOVE,
        int_args=[width, left, height, top, source_descriptor, key],
        max_instructions=5_000_000,
    )
    gamma_context = loader.bump_alloc(8, align=8)
    loader.write_bytes(gamma_context, b"\x00" * 8)
    gamma_result = loader.call_function(
        FUN_SRGB_DECODE,
        int_args=[width, left, height, top, source_descriptor, gamma_context],
        max_instructions=10_000_000,
    )
    post_setup_previous = source_pixel(loader, smoother, LOCAL_TARGET[0], LOCAL_TARGET[1] - 1)
    post_setup_center = source_pixel(loader, smoother, *LOCAL_TARGET)

    source_plane, class_plane, rectangle, class_config = install_descriptors(
        loader, smoother, int(params["Smooth Range"])
    )
    class_result = loader.call_function(
        FUN_ADA0,
        int_args=[source_plane, class_plane, rectangle, class_config],
        max_instructions=20_000_000,
    )

    class_witness = {
        "previous": class_pixel(loader, smoother, LOCAL_TARGET[0], LOCAL_TARGET[1] - 1),
        "center": class_pixel(loader, smoother, *LOCAL_TARGET),
    }
    require(class_witness["previous"] == [255, 0, 0, 0], "previous class witness differs")
    require(class_witness["center"] == [255, 255, 0, 255], "center class witness differs")

    events: dict[str, Any] = {}

    def at_fef0(_loader: AexLoader, _address: int, _size: int) -> None:
        descriptor_pointer = loader.uc.reg_read(UC_X86_REG_RDX)
        descriptor = list(struct.unpack("<6i", loader.read_bytes(descriptor_pointer, 24)))
        require("descriptor" not in events, "multiple fef0 descriptor events")
        events["descriptor"] = {
            "local": descriptor,
            "host_translated": translate_descriptor(descriptor),
            "key": (descriptor[2] - 1) + descriptor[5] * 10,
        }

    def at_post_f130(_loader: AexLoader, _address: int, _size: int) -> None:
        require("post_f130_pre_boost" not in events, "multiple post-f130 events")
        events["post_f130_pre_boost"] = snapshot_builder(loader, loader.uc.reg_read(UC_X86_REG_RBX))

    def at_post_boost(_loader: AexLoader, _address: int, _size: int) -> None:
        require("post_f130_post_boost" not in events, "multiple post-boost events")
        events["post_f130_post_boost"] = snapshot_builder(loader, loader.uc.reg_read(UC_X86_REG_RBX))

    def at_c280_return(_loader: AexLoader, _address: int, _size: int) -> None:
        require("cce0_input" not in events, "multiple cce0-input events")
        rbp = loader.uc.reg_read(UC_X86_REG_RBP)
        events["cce0_input"] = snapshot_compact(loader, rbp - 0x60)

    loader.add_code_hook(FUN_FEF0, at_fef0)
    loader.add_code_hook(POST_F130_PRE_BOOST, at_post_f130)
    loader.add_code_hook(POST_F130_POST_BOOST, at_post_boost)
    loader.add_code_hook(CCE0_AFTER_C280, at_c280_return)

    output = loader.bump_alloc(16, align=16)
    loader.write_bytes(output, b"\x00" * 16)
    cce0_source = loader.bump_alloc(24, align=16)
    cce0_class = loader.bump_alloc(24, align=16)
    packed_size = struct.pack("<ii", CROP_SIZE, CROP_SIZE)
    loader.write_bytes(cce0_source, struct.pack("<Q", smoother.src_base) + packed_size + struct.pack("<Q", smoother.src_stride))
    loader.write_bytes(cce0_class, struct.pack("<Q", smoother.class_base) + packed_size + struct.pack("<Q", smoother.class_stride))
    xy = loader.bump_alloc(8, align=8)
    loader.write_bytes(xy, struct.pack("<ii", *LOCAL_TARGET))
    render_config = loader.bump_alloc(0x80, align=16)
    loader.write_bytes(render_config, b"\x00" * 0x80)
    colors = loader.bump_alloc(5 * 16, align=16)
    loader.write_bytes(colors, b"".join(struct.pack("<4f", *color) for color in params["Gamma Colors"]))
    loader.write_bytes(render_config, struct.pack("<i", int(params["Smoother Version"])))
    loader.write_bytes(render_config + 0x20, struct.pack("<ii", int(params["Smoothness"]), int(params["Extra Smooth"])))
    loader.write_bytes(render_config + 0x28, struct.pack("<f", float(params["Gamma Value"])))
    loader.write_bytes(render_config + 0x30, struct.pack("<Q", int(params["Number of Gamma Colors"])))
    loader.write_bytes(render_config + 0x38, struct.pack("<Q", colors))
    loader.write_bytes(render_config + 0x40, b"\x03")
    cce0_result = loader.call_function(
        FCCE0,
        int_args=[output, cce0_source, cce0_class, xy, render_config, 0],
        max_instructions=20_000_000,
    )

    require(events["descriptor"]["local"] == EXPECTED_LOCAL_DESCRIPTOR, "local descriptor differs")
    require(events["descriptor"]["host_translated"] == EXPECTED_HOST_DESCRIPTOR, "host descriptor differs")
    require(events["descriptor"]["key"] == 20, "dispatch key differs")
    require(events["post_f130_pre_boost"]["count"] == 2, "post-f130 polygon count differs")
    require(events["post_f130_post_boost"]["count"] == 2, "post-boost polygon count differs")
    require(events["cce0_input"] == events["post_f130_post_boost"], "cce0 input differs from completed builder polygon")

    output_rgba = list(struct.unpack("<4f", loader.read_bytes(output, 16)))
    windows_retained_previous = 0.18447503447532654
    previous_ulp_delta = abs(f32_u32(post_setup_previous[0]) - f32_u32(windows_retained_previous))
    return {
        "schema": 1,
        "verdict": "PASS_BOUNDED_NATURAL_ACTUAL_AEX_POST_F130_AND_CCE0_INPUT",
        "scope": "Mac-local Unicorn actual-AEX run on a 16x16 case_0012 crop; PF8 host premultiply is translated, downstream stages execute from the AEX",
        "binary": {"path": str(AEX_PATH.relative_to(ROOT)), "sha256": EXPECTED_AEX_SHA256},
        "fixtures": {
            "source": str(SOURCE.relative_to(ROOT)),
            "source_sha256": sha256(SOURCE),
            "windows_before_effects": str(WINDOWS_BEFORE.relative_to(ROOT)),
            "windows_before_effects_sha256": sha256(WINDOWS_BEFORE),
            "params": str(PARAMS.relative_to(ROOT)),
            "params_sha256": sha256(PARAMS),
        },
        "crop": {"host_origin": list(CROP_ORIGIN), "size": [CROP_SIZE, CROP_SIZE], "host_target": list(HOST_TARGET), "local_target": list(LOCAL_TARGET)},
        "host_adapter": {**host_adapter, "pf8_rule": "(channel * alpha + 127) // 255"},
        "natural_chain": [
            "PF8 host adapter",
            hex(FUN_KEY_REMOVE),
            hex(FUN_SRGB_DECODE),
            hex(FUN_ADA0),
            "VCOMP140!_vcomp_fork",
            "0x18000ac00",
            "0x18000ae10",
            hex(FCCE0),
            "0x18000c280",
            hex(FUN_FEF0),
            "0x18000f270",
            "0x18000f130",
        ],
        "execution": {
            "key_remove_instructions": key_result["instructions"],
            "srgb_decode_instructions": gamma_result["instructions"],
            "class_plane_instructions": class_result["instructions"],
            "cce0_instructions": cce0_result["instructions"],
            "vcomp_static_schedules": vcomp.static_events,
            "vcomp_forks": vcomp.fork_events,
            "classifier_entries": vcomp.classifier_entries,
        },
        "post_setup": {
            "previous_rgba": post_setup_previous,
            "previous_rgba_u32": [f32_u32(value) for value in post_setup_previous],
            "center_rgba": post_setup_center,
            "windows_retained_previous_red": windows_retained_previous,
            "mac_libm_vs_windows_retained_red_ulp_delta": previous_ulp_delta,
        },
        "class_witness": class_witness,
        "events": events,
        "cce0_output": {"rgba": output_rgba, "rgba_u32": [f32_u32(value) for value in output_rgba]},
        "fact": [
            "The accepted host descriptor is reproduced after coordinate translation.",
            "The actual AEX reaches f130 and yields a two-vertex polygon in the natural cce0->c280 dispatch.",
            "The completed builder polygon is byte-identical to the compact polygon consumed by cce0.",
        ],
        "limitations": [
            "The PF8 AE host premultiply operation is translated with the independently audited nearest-code byte rule.",
            "AexLoader implements the imported Windows pow with the Mac Python/libm oracle; the retained Windows setup red differs by the recorded ULP count.",
            "This is a bounded crop, not a full-frame AE render and not an AE-exact claim.",
        ],
        "claims_not_made": ["No Mac plug-in source change", "No Windows package change", "No AE exactness or final writer exactness claim"],
    }


def render_markdown(report: dict[str, Any]) -> str:
    event = report["events"]
    return "\n".join([
        "# OLMSmoother2 case0012 natural post-f130 boundary - 2026-07-18",
        "",
        f"- Verdict: `{report['verdict']}`",
        "- Scope: bounded Mac-local Unicorn execution of the checked-in current Windows AEX.",
        "",
        "## FACT",
        "",
        f"- Host-translated descriptor: `{event['descriptor']['host_translated']}`; dispatch key `{event['descriptor']['key']}`.",
        f"- Post-f130 polygon count: `{event['post_f130_pre_boost']['count']}`.",
        f"- Post-boost polygon count: `{event['post_f130_post_boost']['count']}`.",
        "- The post-boost builder polygon and compact cce0 input are bitwise equal, including float32 words.",
        f"- cce0 output float4: `{report['cce0_output']['rgba']}`.",
        "",
        "## Natural Chain",
        "",
        "`" + " -> ".join(report["natural_chain"]) + "`",
        "",
        "The PF8 host boundary is adapted with `(channel * alpha + 127) // 255`. Key removal, sRGB decode, class-plane generation, c280 dispatch, f270/f130, and cce0 execute from the actual AEX.",
        "",
        "## Boundary",
        "",
        f"- The imported Windows `pow` is currently implemented by Mac libm. At the retained `(92,840)` sample, its red float differs from the Windows retained value by `{report['post_setup']['mac_libm_vs_windows_retained_red_ulp_delta']}` float32 ULPs.",
        "- Therefore this closes local execution reachability and polygon ownership, not Windows/AE byte exactness.",
        "",
        "## Reproduction",
        "",
        "```sh",
        "python3 tools/emulation/run_olmsmoother2_case0012_natural_post_f130_20260718.py",
        "```",
        "",
        "## Claims Not Made",
        "",
        *[f"- {item}." for item in report["claims_not_made"]],
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, default=ROOT / "refs/conformance/olmsmoother2_case0012_natural_post_f130_20260718.json")
    parser.add_argument("--output-md", type=Path, default=ROOT / "refs/conformance/olmsmoother2_case0012_natural_post_f130_20260718.md")
    args = parser.parse_args()
    report = run()
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(report["verdict"])
    print(f"descriptor={report['events']['descriptor']['host_translated']}")
    print(f"post_f130_count={report['events']['post_f130_pre_boost']['count']}")
    print(f"cce0_input_count={report['events']['cce0_input']['count']}")
    print(f"pow_boundary_ulp={report['post_setup']['mac_libm_vs_windows_retained_red_ulp_delta']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
