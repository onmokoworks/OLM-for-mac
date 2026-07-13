#!/usr/bin/env python3
"""Capture a non-zero Mode 3 pre-Gaussian ray population from the AEX.

The existing Mode 3 probe proves the Gaussian call shape, but its temporary
ray Mat is zero at that boundary.  This witness keeps the AEX code running and
records the ROI-copy and forward-warp boundaries inside FUN_181150790 using a
small deterministic non-zero source fixture.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import struct
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from unicorn.x86_const import UC_X86_REG_RBP, UC_X86_REG_R12, UC_X86_REG_R14

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE_PATH = HERE / "probe_olmkirakira_mode3_actual_aex.py"
FUN_HELPER = 0x181150790
ROI_AFTER_COPY = 0x181150898
WARP_AFTER = 0x181150946
DEFAULT_JSON = ROOT / "refs/conformance/olmkirakira_mode3_ray_population_actual_aex_20260713.json"
DEFAULT_MD = ROOT / "refs/conformance/olmkirakira_mode3_ray_population_actual_aex_20260713.md"


def load_base():
    spec = importlib.util.spec_from_file_location("olmkirakira_mode3_actual_aex_base", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ints(loader: Any, address: int) -> list[int]:
    return list(struct.unpack("<4i", loader.read_bytes(address, 16)))


def matrix_snapshot(base: Any, loader: Any, mat: int) -> dict[str, Any] | None:
    return base.read_mat(loader, mat)


def run(args: argparse.Namespace) -> dict[str, Any]:
    base = load_base()
    captures: dict[str, Any] = {"roi_after_copy": [], "warp_after": []}
    original_add_hook = base.AexLoader.add_code_hook

    def install_boundary_hooks(loader: Any) -> None:
        def capture(label: str, include_roi: bool = False):
            def handler(emu: Any, _address: int, _size: int) -> None:
                rbp = emu.uc.reg_read(UC_X86_REG_RBP)
                r12 = emu.uc.reg_read(UC_X86_REG_R12)
                r14 = emu.uc.reg_read(UC_X86_REG_R14)
                item: dict[str, Any] = {
                    "rip": hex(_address),
                    "temp_a_register": "R14",
                    "temp_a_header": hex(r14),
                    "temp_a": matrix_snapshot(base, emu, r14),
                    "temp_b_register": "R12",
                    "temp_b_header": hex(r12),
                    "temp_b": matrix_snapshot(base, emu, r12),
                }
                if include_roi:
                    item["roi_xywh_from_fun_locals"] = ints(emu, rbp - 0x80)
                    item["roi_local_address"] = hex(rbp - 0x80)
                captures[label].append(item)
            return handler

        original_add_hook(loader, ROI_AFTER_COPY, capture("roi_after_copy", include_roi=True))
        original_add_hook(loader, WARP_AFTER, capture("warp_after"))

    def add_hook(loader: Any, address: int, handler: Any) -> None:
        # Install before the base target hook: its handler stops Unicorn.
        if address == base.FUN_GAUSSIAN:
            install_boundary_hooks(loader)
        original_add_hook(loader, address, handler)

    base.AexLoader.add_code_hook = add_hook
    try:
        report = base.run(SimpleNamespace(
            aex_path=args.aex_path,
            width=args.width,
            height=args.height,
            length=args.length,
            sigma=args.sigma,
            max_instructions=args.max_instructions,
        ))
    finally:
        base.AexLoader.add_code_hook = original_add_hook

    report["schema"] = "olmkirakira-mode3-ray-population-actual-aex/1"
    report["status"] = "captured_nonzero_pre_gaussian" if captures["warp_after"] else report["status"]
    report["ray_population_capture"] = captures
    report["producer_contract"] = {
        "function": "FUN_181150790",
        "roi_after_copy": hex(ROI_AFTER_COPY),
        "forward_warp_after": hex(WARP_AFTER),
        "gaussian_target": hex(base.FUN_GAUSSIAN),
        "temp_a": "R14 / param_3 / Gaussian InputArray",
        "temp_b": "R12 / stack param_5 / Gaussian OutputArray",
        "roi_local": "[RBP-0x80] = x,y,width,height after FUN_18115cfb0",
    }
    report["synthetic_fixture"] = {
        "kind": "nonzero_source_mat_fixture",
        "purpose": "provide a deterministic source population to the actual AEX ROI and warp stages",
        "values": "f32(row,col) = ((row*width + col) mod 17) / 17",
        "coordinates": "zero-based (x=col, y=row)",
    }
    nonzero = []
    for stage in ("roi_after_copy", "warp_after"):
        for item in captures[stage]:
            values = (item.get("temp_a") or {}).get("values_f32") or []
            for y, row in enumerate(values):
                for x, value in enumerate(row):
                    if value != 0.0:
                        nonzero.append({"stage": stage, "x": x, "y": y, "f32": value})
    report["nonzero_coordinates"] = nonzero
    return report


def render_md(report: dict[str, Any]) -> str:
    lines = [f"# OLMKiraKira Mode 3 ray population actual-AEX witness", "", f"Status: **{report['status']}**", "", "## FACT", ""]
    facts = [
        "The witness executes FUN_181150790 in the actual 2025 AEX and captures its Mode 3 Gaussian call.",
        f"The ROI copy boundary is captured after 0x{ROI_AFTER_COPY:x}; the forward warp boundary is captured after 0x{WARP_AFTER:x}.",
        "At the Gaussian boundary, R14/param_3 is the InputArray and R12/stack param_5 is the OutputArray.",
        "Each boundary record contains the Mat header, dimensions, step, raw f32 values, and zero-based coordinates.",
    ]
    lines += [f"- {fact}" for fact in facts] + ["", "## SYNTHETIC FIXTURE", "", f"- `{json.dumps(report['synthetic_fixture'], sort_keys=True)}`", "", "## PRODUCER / WARP / ROI", ""]
    lines += [f"- `{json.dumps(report['producer_contract'], sort_keys=True)}`", "", f"- Non-zero coordinate count: `{len(report['nonzero_coordinates'])}`", f"- First non-zero coordinates: `{json.dumps(report['nonzero_coordinates'][:12], sort_keys=True)}`", ""]
    lines += ["## CAPTURES", "", f"- ROI after copy: `{json.dumps(report['ray_population_capture']['roi_after_copy'], sort_keys=True)}`", f"- Forward warp after: `{json.dumps(report['ray_population_capture']['warp_after'], sort_keys=True)}`", ""]
    lines += ["## LIMIT", "", "- The non-zero source is a deterministic synthetic fixture; it is not claimed to be an AE host-produced ray.", "- This witness establishes actual-AEX producer-stage placement and raw pre-Gaussian population behavior, not final rendered conformance.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aex-path", type=Path, default=ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex")
    parser.add_argument("--width", type=int, default=9)
    parser.add_argument("--height", type=int, default=7)
    parser.add_argument("--length", type=int, default=5)
    parser.add_argument("--sigma", type=float, default=0.0)
    parser.add_argument("--max-instructions", type=int, default=20_000_000)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()
    report = run(args)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "nonzero": len(report["nonzero_coordinates"]), "json": str(args.output_json), "md": str(args.output_md)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
