#!/usr/bin/env python3
"""Run the real case_0001 row 169 through FUN_1800038d0 under Unicorn.

This is a bounded diagnostic probe.  It records typed rowdriver/helper facts
only; it does not alter Mac sources, tune PNG output, or invent Windows data.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from pathlib import Path
from typing import Any

from PIL import Image
from unicorn.x86_const import UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_RSP

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AEX = ROOT / "plugins_2025" / "OLMDirectionalBlur.aex"
DEFAULT_SOURCE = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"
DEFAULT_JSON = ROOT / "refs/conformance/olmdirectionalblur_case0001_row169_typed_classifier_20260710.json"
DEFAULT_MD = ROOT / "refs/conformance/olmdirectionalblur_case0001_row169_typed_classifier_20260710.md"

ROW = 169
TARGETS = list(range(487, 495)) + [579]
FUN_ROWDRIVER = 0x1800038D0
FUN_FRONT_SCATTER = 0x1800013E0


def public_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return path.name


def f32(value: float) -> bytes:
    return struct.pack("<f", float(value))


def read_u64(loader: AexLoader, address: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(address, 8))[0]


def read_f32(loader: AexLoader, address: int) -> float:
    return struct.unpack("<f", loader.read_bytes(address, 4))[0]


def classify(*, source_x: int, valid: float, component: float, param_11: float,
             front_strength: int, strip_x: int, source_range: tuple[int, int]) -> str:
    span = int(front_strength * param_11)
    reach = 1 <= source_x - strip_x < span
    if valid <= 0.0:
        return "invalid-source"
    if component <= 0.0:
        return "component-invalid"
    if span <= 1:
        return "span<=1"
    if not (source_range[0] <= source_x <= source_range[1]):
        return "outside-valid-source-range"
    if not reach:
        return "not-reached-by-span"
    return "reachable"


def load_source(path: Path) -> tuple[int, int, list[float]]:
    image = Image.open(path).convert("RGBA")
    width, height = image.size
    pixels = list(image.getdata())
    values: list[float] = []
    for red, green, blue, alpha in pixels:
        values.extend((red / 255.0, green / 255.0, blue / 255.0, alpha / 255.0))
    return width, height, values


def build_component_map(loader: AexLoader, width: int, height: int, rgba: list[float]) -> tuple[int, float]:
    """Build the AEX component record shape from the real source alpha mask."""
    count = width * height
    visited = bytearray(count)
    records = [(0.0, 0.0, 0.0, 0.0)] * count
    max_area = 0.0
    for start in range(count):
        if visited[start] or rgba[start * 4 + 3] <= 0.0:
            visited[start] = 1
            continue
        stack = [start]
        component: list[int] = []
        min_y, max_y = height, -1
        while stack:
            pixel = stack.pop()
            if visited[pixel]:
                continue
            visited[pixel] = 1
            if rgba[pixel * 4 + 3] <= 0.0:
                continue
            component.append(pixel)
            x, y = pixel % width, pixel // width
            min_y, max_y = min(min_y, y), max(max_y, y)
            if x:
                stack.append(pixel - 1)
            if x + 1 < width:
                stack.append(pixel + 1)
            if y:
                stack.append(pixel - width)
            if y + 1 < height:
                stack.append(pixel + width)
        area = float(len(component))
        max_area = max(max_area, area)
        center_y = float((min_y + max_y) // 2)
        half_height = max(float(max_y) - center_y, 1.0)
        record = (area, float(min_y), center_y, half_height)
        for pixel in component:
            records[pixel] = record
    address = loader.bump_alloc(count * 16, align=16)
    loader.write_bytes(address, struct.pack(f"<{count * 4}f", *(v for row in records for v in row)))
    return address, max_area


def allocate_f32(loader: AexLoader, values: list[float]) -> int:
    address = loader.bump_alloc(len(values) * 4, align=16)
    loader.write_bytes(address, struct.pack(f"<{len(values)}f", *values))
    return address


def make_result(args: argparse.Namespace) -> dict[str, Any]:
    result: dict[str, Any] = {
        "kind": "olmdirectionalblur_case0001_row169_typed_classifier",
        "schema": 1,
        "status": "blocked",
        "platform": "Mac host / Unicorn x86-64 emulation",
        "case_id": "case_0001",
        "row_y": ROW,
        "strip_x": [487, 494],
        "targets": TARGETS,
        "source_path": public_path(args.source),
        "aex_path": public_path(args.aex),
        "function": "FUN_1800038d0",
        "blocked": {"reason": "not-run", "missing": [], "rip": None},
        "records": [],
    }
    try:
        width, height, rgba = load_source(args.source)
        if not (0 <= ROW < height and max(TARGETS) < width):
            raise ValueError(f"source dimensions {width}x{height} do not contain row {ROW} / strip {TARGETS}")
        loader = AexLoader(str(args.aex), verbose=False, fast=True)
        loader.register_libm_impls(max_threads=1)
        count = width * height
        A = allocate_f32(loader, rgba)
        B = allocate_f32(loader, [0.0] * (count * 4))
        denom = allocate_f32(loader, [0.0] * count)
        valid_arr = allocate_f32(loader, [v for i, v in enumerate(rgba) if i % 4 == 3])
        component_map, max_area = build_component_map(loader, width, height, rgba)
        front_strength = 1690
        table_len = max(front_strength + 4, 8)
        table = allocate_f32(loader, [1.0] * table_len)
        back_table = allocate_f32(loader, [1.0] * table_len)
        a_ptr = loader.bump_alloc(8, align=8)
        b_ptr = loader.bump_alloc(8, align=8)
        loader.write_bytes(a_ptr, struct.pack("<Q", A))
        loader.write_bytes(b_ptr, struct.pack("<Q", B))
        context = loader.bump_alloc(0x8200, align=16)
        loader.write_bytes(context, b"\x00" * 0x8200)
        for offset, value in ((0x20, 0), (0x30, 1.0), (0x38, max_area or 1.0),
                              (0x40, 1.0), (0x44, 1.0), (0x48, front_strength),
                              (0x4C, front_strength), (0x50, 0), (0x54, 0)):
            data = struct.pack("<I", value) if isinstance(value, int) else f32(value)
            loader.write_bytes(context + offset, data)
        for offset, value in ((0x58, table), (0x4068, back_table), (0x8080, denom),
                              (0x8088, valid_arr), (0x8118, component_map)):
            loader.write_bytes(context + offset, struct.pack("<Q", value))

        helper_calls: list[dict[str, Any]] = []
        def on_front_scatter(ld: AexLoader, address: int, size: int) -> None:
            rsp = ld.uc.reg_read(UC_X86_REG_RSP)
            source_x = ld.uc.reg_read(UC_X86_REG_RCX)
            row_base = ld.uc.reg_read(UC_X86_REG_RDX)
            direction = ld.uc.reg_read(UC_X86_REG_R8)
            if row_base == ROW * width and direction == 1:
                p11 = read_f32(ld, rsp + 0x58)
                strength = struct.unpack("<i", ld.read_bytes(rsp + 0x48, 4))[0]
                helper_calls.append({"source_x": source_x, "param_11": p11,
                                     "span": int(strength * p11),
                                     "destination_min": source_x - max(int(strength * p11) - 1, 0),
                                     "destination_max": source_x - 1})
        loader.add_code_hook(FUN_FRONT_SCATTER, on_front_scatter)
        loader.call_function(FUN_ROWDRIVER, int_args=[ROW, ROW + 1, a_ptr, b_ptr, width, 0, context], max_instructions=0)
        row_alpha_x = [x for x in range(width) if rgba[(ROW * width + x) * 4 + 3] > 0.0]
        source_range = (min(row_alpha_x), max(row_alpha_x)) if row_alpha_x else None
        for x in TARGETS:
            pixel = ROW * width + x
            comp = read_f32(loader, component_map + pixel * 16)
            valid = read_f32(loader, valid_arr + pixel * 4)
            p11 = math.pow(comp / (max_area or 1.0), 1.0) if comp > 0.0 else 0.0
            matching = [call for call in helper_calls if call["destination_min"] <= x <= call["destination_max"]]
            source_x = max((call["source_x"] for call in matching), default=None)
            span = max((call["span"] for call in matching), default=int(front_strength * p11))
            actual_call = max(matching, key=lambda call: call["source_x"]) if matching else None
            p11 = actual_call["param_11"] if actual_call else p11
            reach = source_x is not None and 1 <= source_x - x < span
            outside_range = source_x is None or source_range is None or not (source_range[0] <= source_x <= source_range[1])
            result["records"].append({
                "xy": [x, ROW], "valid": valid, "component": comp,
                "param_11": p11, "span": span, "source_x": source_x,
                "reach": reach,
                "valid_source_range": list(source_range) if source_range else None,
                "outside_valid_source_range": outside_range,
                "span_le_1": span <= 1,
                "classification": classify(source_x=source_x or 0, valid=valid,
                                             component=comp, param_11=p11,
                                             front_strength=front_strength, strip_x=x,
                                             source_range=source_range or (1, 0)),
            })
        result["status"] = "ok"
        result["blocked"] = None
        result["helper_call_count"] = len(helper_calls)
        result["source_dimensions"] = [width, height]
    except Exception as exc:  # blocked is a first-class, machine-readable result
        result["blocked"] = {"reason": type(exc).__name__, "message": str(exc),
                             "missing": ["typed rowdriver/helper fields"], "rip": None}
    return result


def render_md(result: dict[str, Any]) -> str:
    lines = ["# OLMDirectionalBlur case_0001 row169 typed classifier", "",
             f"- Status: `{result['status']}`", f"- Function: `{result['function']}`",
             f"- Platform: `{result['platform']}`", f"- Source: `{result['source_path']}`", ""]
    if result["status"] != "ok":
        lines += ["## Blocked", "", f"```json\n{json.dumps(result['blocked'], indent=2)}\n```", ""]
        return "\n".join(lines)
    lines += ["## Typed Strip Records", "", "| x | valid | component | param_11 | span | source_x | reach | outside_valid_source_range | span_le_1 | classification |", "| ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: | :---: | :--- |"]
    for row in result["records"]:
        lines.append("| {x} | {valid:.9g} | {component:.9g} | {param_11:.9g} | {span} | {source_x} | {reach} | {outside_valid_source_range} | {span_le_1} | `{classification}` |".format(x=row["xy"][0], **row))
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aex", type=Path, default=DEFAULT_AEX)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()
    result = make_result(args)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_md(result), encoding="utf-8")
    print(json.dumps({"status": result["status"], "output_json": str(args.output_json),
                      "output_md": str(args.output_md)}, sort_keys=True))
    return 0 if result["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
