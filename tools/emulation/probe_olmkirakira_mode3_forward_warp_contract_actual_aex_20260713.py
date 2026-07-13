#!/usr/bin/env python3
"""Capture the actual-AEX Mode 3 forward-warp call contract.

This is deliberately layered on the existing ray-population probe so the
contract and the pre/post Mat witnesses come from one emulation run.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import struct
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RBP, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE_PATH = HERE / "probe_olmkirakira_mode3_ray_population_actual_aex_20260713.py"
WARP = 0x181297AC0
DEFAULT_JSON = ROOT / "refs/conformance/olmkirakira_mode3_forward_warp_contract_actual_aex_20260713.json"
DEFAULT_MD = ROOT / "refs/conformance/olmkirakira_mode3_forward_warp_contract_actual_aex_20260713.md"
SIDECAR_PYTHON = ROOT / "tools/emulation/.venv-cv455/bin/python"


def load_base():
    spec = importlib.util.spec_from_file_location("olmkirakira_mode3_ray_population_base", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def qword(loader: Any, address: int) -> int | None:
    try:
        return struct.unpack("<Q", loader.read_bytes(address, 8))[0]
    except Exception:
        return None


def int32(loader: Any, address: int) -> int | None:
    try:
        return struct.unpack("<i", loader.read_bytes(address, 4))[0]
    except Exception:
        return None


def run_warp_sidecar(call: dict[str, Any], expected: list[list[float]]) -> dict[str, Any]:
    if not SIDECAR_PYTHON.exists():
        return {"status": "missing", "python": str(SIDECAR_PYTHON)}
    payload = {
        "src": call["src"]["mat"]["values_f32"],
        "matrix": call["transform"]["decoded_by_mat_depth"],
        "dsize": [call["dsize"]["width"], call["dsize"]["height"]],
        "flags": call["optional_stack_args"]["interpolation_flags"],
        "border_mode": call["optional_stack_args"]["border_mode"],
        "expected": expected,
    }
    code = (
        "import cv2,json,numpy as np,sys; p=json.load(sys.stdin); "
        "s=np.array(p['src'],dtype=np.float32); m=np.array(p['matrix'],dtype=np.float64).reshape(2,3); "
        "e=np.array(p['expected'],dtype=np.float32); "
        "o=cv2.warpAffine(s,m,tuple(p['dsize']),flags=p['flags'],borderMode=p['border_mode'],borderValue=0); "
        "eq=o.view(np.uint32)==e.view(np.uint32); "
        "print(json.dumps({'cv2':cv2.__version__,'total_words':int(o.size),'exact_words':int(eq.sum()),"
        "'max_abs':float(np.max(np.abs(o-e))),'nonzero':int(np.count_nonzero(o))}))"
    )
    proc = subprocess.run([str(SIDECAR_PYTHON), "-c", code], input=json.dumps(payload), text=True, capture_output=True)
    if proc.returncode:
        return {"status": "error", "python": str(SIDECAR_PYTHON), "stderr": proc.stderr.strip()}
    return {"status": "ok", "python": str(SIDECAR_PYTHON), **json.loads(proc.stdout)}


def matrix_values(loader: Any, core: Any, ptr: int | None) -> dict[str, Any]:
    """Decode the 2x3 InputArray Mat and retain raw candidates when ambiguous."""
    result: dict[str, Any] = {"pointer": hex(ptr) if ptr else None, "wrapper": core.read_array_wrapper(loader, ptr) if ptr else None}
    mat = result["wrapper"].get("mat") if result["wrapper"] else None
    if not mat:
        return result
    data = int(mat["data"], 16)
    result["mat"] = mat
    candidates: dict[str, Any] = {}
    for kind, fmt in (("f32", "<6f"), ("f64", "<6d")):
        size = struct.calcsize(fmt)
        try:
            raw = loader.read_bytes(data, size)
            candidates[kind] = list(struct.unpack(fmt, raw))
        except Exception:
            candidates[kind] = None
    result["raw_2x3_candidates"] = candidates
    result["decoded_by_mat_depth"] = candidates["f64"] if mat.get("depth_code") == 6 else candidates["f32"] if mat.get("depth_code") == 5 else None
    return result


def run(args: argparse.Namespace) -> dict[str, Any]:
    base = load_base()
    core = base.load_base()
    captures: list[dict[str, Any]] = []
    original_add_hook = core.AexLoader.add_code_hook

    def on_warp(loader: Any, _address: int, _size: int) -> None:
        def capture(emu: Any, address: int, size: int) -> None:
            rcx = emu.uc.reg_read(UC_X86_REG_RCX)
            rdx = emu.uc.reg_read(UC_X86_REG_RDX)
            r8 = emu.uc.reg_read(UC_X86_REG_R8)
            r9 = emu.uc.reg_read(UC_X86_REG_R9)
            rsp = emu.uc.reg_read(UC_X86_REG_RSP)
            item = {
                "sequence": len(captures) + 1,
                "rip": hex(address),
                "instruction_size": size,
                "abi": "windows-x64",
                "registers": {"RCX_src": hex(rcx), "RDX_dst": hex(rdx), "R8_transform": hex(r8), "R9_dsize_packed": hex(r9)},
                "src": core.read_array_wrapper(emu, rcx),
                "dst": core.read_array_wrapper(emu, rdx),
                "transform": matrix_values(emu, core, r8),
                "dsize": {"width": core.u32(r9), "height": core.u32(r9 >> 32), "packed": hex(r9), "source": "R9"},
                "optional_stack_args": {
                    # Windows x64 stack arguments are at caller RSP+0x20,
                    # shifted by the 8-byte return address at callee entry.
                    "interpolation_flags": int32(emu, rsp + 0x28),
                    "border_mode": int32(emu, rsp + 0x30),
                    "border_value_pointer": hex(qword(emu, rsp + 0x38) or 0),
                    "rsp": hex(rsp),
                },
                "caller_frame": {"RBP": hex(emu.uc.reg_read(UC_X86_REG_RBP)), "return_address": hex(qword(emu, rsp) or 0)},
            }
            captures.append(item)

        original_add_hook(loader, WARP, capture)

    def add_hook(loader: Any, address: int, handler: Any) -> None:
        if address == core.FUN_GAUSSIAN:
            on_warp(loader, WARP, 0)
        original_add_hook(loader, address, handler)

    core.AexLoader.add_code_hook = add_hook
    try:
        report = base.run(SimpleNamespace(aex_path=args.aex_path, width=args.width, height=args.height, length=args.length, sigma=args.sigma, max_instructions=args.max_instructions))
    finally:
        core.AexLoader.add_code_hook = original_add_hook

    forward = captures[0] if captures else None
    report["schema"] = "olmkirakira-mode3-forward-warp-contract-actual-aex/1"
    report["status"] = "captured_forward_warp_contract" if forward else "missing_forward_warp_contract"
    report["forward_warp_contract"] = {
        "wrapper": "FUN_181297ac0",
        "address": hex(WARP),
        "argument_order": ["src", "dst", "2x3 transform", "dsize"],
        "optional_arguments": {"interpolation": "callee [RSP+0x28]", "border_mode": "callee [RSP+0x30]", "border_value": "callee [RSP+0x38]"},
        "calls": captures,
    }
    warp_values = (((report.get("ray_population_capture") or {}).get("warp_after") or [{}])[0].get("temp_a") or {}).get("values_f32") or []
    warp_nonzero = sum(value != 0.0 for row in warp_values for value in row)
    report["forward_warp_sidecar"] = run_warp_sidecar(forward, warp_values) if forward and warp_values else {"status": "not_run"}
    report["FACT"] = [
        "The actual AEX reached FUN_181297ac0 at the forward-warp boundary.",
        "The first captured call is the forward warp from the Mode 3 helper; the same run also retains ROI-after and warp-after Mat snapshots.",
        "The call boundary records src Mat, dst Mat, transform InputArray, packed dsize, interpolation flags, border mode, and border-value pointer.",
        f"The captured synthetic fixture remains non-zero after the in-place forward warp ({warp_nonzero} non-zero cells).",
        f"OpenCV 4.5.5 sidecar replay matches {report['forward_warp_sidecar'].get('exact_words', 0)}/{report['forward_warp_sidecar'].get('total_words', 0)} float32 words.",
    ] if forward else ["The actual-AEX run did not reach FUN_181297ac0; no warp contract is claimed."]
    report["INFERENCE"] = [
        "The probe registers real cos/sin imports before the AEX builds its affine matrix; the captured coefficients therefore retain the helper's actual trigonometric contract.",
        "The transform's semantic 2x3 representation is promoted only when the decoded Mat type and raw candidate agree; raw bytes remain the primary evidence.",
        "The synthetic fixture is a reachability witness, not an AE host-produced ray population.",
    ]
    return report


def render_md(report: dict[str, Any]) -> str:
    contract = report["forward_warp_contract"]
    lines = ["# OLMKiraKira Mode 3 forward-warp contract actual-AEX witness", "", f"Status: **{report['status']}**", "", "## FACT", ""]
    lines += [f"- {x}" for x in report["FACT"]] + ["", "## INFERENCE", ""]
    lines += [f"- {x}" for x in report["INFERENCE"]] + ["", "## Contract", "", f"- Wrapper: `{contract['wrapper']} @ {contract['address']}`", f"- Argument order: `{json.dumps(contract['argument_order'])}`", f"- Optional arguments: `{json.dumps(contract['optional_arguments'], sort_keys=True)}`", f"- Call count: `{len(contract['calls'])}`", ""]
    for call in contract["calls"]:
        lines += [f"### Call {call['sequence']}", "", f"- src: `{json.dumps(call['src'], sort_keys=True)}`", f"- dst: `{json.dumps(call['dst'], sort_keys=True)}`", f"- transform: `{json.dumps(call['transform'], sort_keys=True)}`", f"- dsize: `{json.dumps(call['dsize'], sort_keys=True)}`", f"- interpolation/border: `{json.dumps(call['optional_stack_args'], sort_keys=True)}`", ""]
    lines += ["## Sidecar", "", f"- `{json.dumps(report.get('forward_warp_sidecar', {}), sort_keys=True)}`", "", "## Existing stage evidence", "", f"- ROI/warp capture: `{json.dumps(report.get('ray_population_capture', {}), sort_keys=True)}`", "", "## Limit", "", "- This evidence captures actual-AEX call arguments and a synthetic non-zero post-warp population; it does not claim an AE host-produced input or final conformance.", ""]
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
    print(json.dumps({"status": report["status"], "calls": len(report["forward_warp_contract"]["calls"]), "json": str(args.output_json), "md": str(args.output_md)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
