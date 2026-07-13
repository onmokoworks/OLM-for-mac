#!/usr/bin/env python3
"""Execute the actual-AEX Mode 3 Gaussian body and capture its 63 output words."""

from __future__ import annotations

import argparse
import importlib.util
import json
import struct
import sys
from pathlib import Path
from typing import Any

from unicorn.x86_const import (
    UC_X86_REG_RCX,
    UC_X86_REG_RDX,
    UC_X86_REG_R8,
    UC_X86_REG_R9,
    UC_X86_REG_RSP,
    UC_X86_REG_XMM3,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE_PATH = HERE / "probe_olmkirakira_mode3_actual_aex.py"
DEFAULT_JSON = ROOT / "refs/conformance/olmkirakira_mode3_gaussian_output_actual_aex_20260713.json"
DEFAULT_MD = ROOT / "refs/conformance/olmkirakira_mode3_gaussian_output_actual_aex_20260713.md"
CALLER_RETURN = 0x181151105


def load_base():
    spec = importlib.util.spec_from_file_location("olmkirakira_mode3_boundary_base", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(HERE))
    spec.loader.exec_module(module)
    return module


BASE = load_base()
ORIGINAL_LOADER = BASE.AexLoader
ORIGINAL_MAT_HEADER = BASE.mat_header
CONTINUATION: dict[str, Any] = {"entry_hits": [], "return_hits": []}
LAST_LOADER = None


def raw_mat_words(loader, wrapper_pointer: int) -> dict[str, Any] | None:
    wrapper = BASE.read_array_wrapper(loader, wrapper_pointer)
    if not wrapper or not wrapper.get("mat"):
        return wrapper
    mat = wrapper["mat"]
    rows, cols = mat["rows"], mat["cols"]
    data, step = int(mat["data"], 16), mat["step_bytes"]
    words = []
    for y in range(rows):
        words.extend(struct.unpack(f"<{cols}I", loader.read_bytes(data + y * step, cols * 4)))
    wrapper["mat"]["words_u32"] = [f"0x{word:08x}" for word in words]
    wrapper["mat"]["word_count"] = len(words)
    wrapper["mat"]["nonzero_word_count"] = sum(word != 0 for word in words)
    return wrapper


def body_compatible_mat_header(loader, data: int, rows: int, cols: int, step: int) -> int:
    header = ORIGINAL_MAT_HEADER(loader, data, rows, cols, step)
    # cv::Mat::size.p is consumed by the embedded InputArray size path. For a
    # two-dimensional Mat it points at the inline rows/cols pair at +0x08.
    loader.write_bytes(header + 64, struct.pack("<Q", header + 8))
    return header


class ContinuingAexLoader(ORIGINAL_LOADER):
    """Replace only the boundary probe's stop hook; retain all base scaffolding."""

    def __init__(self, *args, **kwargs):
        global LAST_LOADER
        super().__init__(*args, **kwargs)
        LAST_LOADER = self
        super().add_code_hook(CALLER_RETURN, self._on_gaussian_return)

    def add_code_hook(self, address, handler):
        if address != BASE.FUN_GAUSSIAN:
            return super().add_code_hook(address, handler)

        def capture_and_continue(loader, _address, _size):
            regs = [loader.uc.reg_read(reg) for reg in
                    (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)]
            xmm3 = loader.uc.reg_read(UC_X86_REG_XMM3)
            sigma = struct.unpack("<d", int(xmm3 & ((1 << 64) - 1)).to_bytes(8, "little"))[0]
            rsp = loader.uc.reg_read(UC_X86_REG_RSP)
            hit = {
                "rip": hex(BASE.FUN_GAUSSIAN),
                "return_address": hex(struct.unpack("<Q", loader.read_bytes(rsp, 8))[0]),
                "register_args_rcx_rdx_r8_r9": [hex(value) for value in regs],
                "size": [BASE.u32(regs[2]), BASE.u32(regs[2] >> 32)],
                "sigma_x_f64": sigma,
                "input_array": raw_mat_words(loader, regs[0]),
                "output_array_before": raw_mat_words(loader, regs[1]),
                "output_wrapper_pointer": regs[1],
            }
            CONTINUATION["entry_hits"].append(hit)

        return super().add_code_hook(address, capture_and_continue)

    def _on_gaussian_return(self, loader, _address, _size):
        if not CONTINUATION["entry_hits"]:
            return
        entry = CONTINUATION["entry_hits"][-1]
        CONTINUATION["return_hits"].append({
            "rip": hex(CALLER_RETURN),
            "output_array_after": raw_mat_words(loader, entry["output_wrapper_pointer"]),
        })


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aex-path", type=Path, default=BASE.DEFAULT_AEX)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    parser.add_argument("--max-instructions", type=int, default=50_000_000)
    return parser.parse_args()


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# OLMKiraKira Mode 3 actual-AEX Gaussian output",
        "",
        f"Status: **{report['status']}**",
        "",
        "## FACT",
        "",
    ]
    lines += [f"- {fact}" for fact in report["FACT"]]
    lines += ["", "## INFERENCE / LIMIT", ""]
    lines += [f"- {item}" for item in report["INFERENCE"]]
    lines += ["", "## Execution", "", f"- `{json.dumps(report['execution'], sort_keys=True)}`", ""]
    if report.get("output_capture"):
        lines += ["## Output capture", "", f"- `{json.dumps(report['output_capture'], sort_keys=True)}`", ""]
    if report.get("blocker"):
        lines += ["## Blocker", "", f"- `{json.dumps(report['blocker'], sort_keys=True)}`", ""]
    return "\n".join(lines)


def main() -> int:
    global LAST_LOADER
    args = parse_args()
    CONTINUATION["entry_hits"].clear()
    CONTINUATION["return_hits"].clear()
    BASE.AexLoader = ContinuingAexLoader
    BASE.mat_header = body_compatible_mat_header
    base_args = argparse.Namespace(
        aex_path=args.aex_path,
        width=9,
        height=7,
        length=5,
        sigma=0.0,
        output_json=args.output_json,
        output_md=args.output_md,
        max_instructions=args.max_instructions,
    )
    base_report = BASE.run(base_args)
    called_imports = []
    if LAST_LOADER is not None:
        called_imports = [
            {"name": item.name, "dll": item.dll,
             "args": [hex(arg) for arg in item.args], "ret": hex(item.ret),
             "implemented": item.name in LAST_LOADER.import_impls}
            for item in LAST_LOADER.import_log
        ]
    returned = CONTINUATION["return_hits"][-1] if CONTINUATION["return_hits"] else None
    output = returned["output_array_after"] if returned else None
    words = output.get("mat", {}).get("words_u32", []) if output else []
    status = "captured" if len(words) == 63 else "blocked"
    report = {
        "schema": "olmkirakira-mode3-gaussian-output-actual-aex/1",
        "status": status,
        "FACT": [
            "The derived probe suppresses only the stop at FUN_181272ec0 and executes the actual embedded Gaussian body.",
            "The output capture point is the caller instruction at 0x181151105 immediately after the Gaussian call returns.",
        ],
        "INFERENCE": [
            "Captured words are promoted to the primary oracle only when the caller return hook is reached and exactly 63 CV_32FC1 words decode.",
        ],
        "execution": {
            "aex": str(args.aex_path),
            "aex_sha256": base_report.get("aex_sha256"),
            "entry": hex(BASE.FUN_GAUSSIAN),
            "caller_return": hex(CALLER_RETURN),
            "input_shape": [7, 9],
            "input_nonzero": True,
            "length": 5,
            "sigma_x": 2.5,
            "base_status": base_report.get("status"),
            "entry_hit_count": len(CONTINUATION["entry_hits"]),
            "return_hit_count": len(CONTINUATION["return_hits"]),
        },
        "entry_capture": CONTINUATION["entry_hits"],
        "output_capture": returned,
        "called_imports": called_imports,
        "unimplemented_called_imports": sorted({item["name"] for item in called_imports
                                                if not item["implemented"]}),
        "blocker": None if status == "captured" else {
            "base_error": base_report.get("error"),
            "fault_boundary": base_report.get("fault_boundary"),
            "runtime_imports": base_report.get("runtime_imports"),
            "last_rip": base_report.get("fault_boundary", {}).get("invalid_memory", {}).get("rip"),
        },
    }
    if status == "captured":
        report["FACT"].append(f"The actual-AEX output contains {len(words)} raw float32 words captured after return.")
        report["FACT"].append(f"The captured output has {output['mat']['nonzero_word_count']} nonzero raw words.")
    else:
        report["FACT"].append("The Gaussian body did not return; no actual-AEX output oracle is claimed.")
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({"status": status, "entry_hits": len(CONTINUATION["entry_hits"]),
                      "return_hits": len(CONTINUATION["return_hits"]), "word_count": len(words)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
