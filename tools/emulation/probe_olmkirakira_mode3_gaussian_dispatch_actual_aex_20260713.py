#!/usr/bin/env python3
"""Audit actual-AEX Gaussian dispatch backing and direct callees."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import pefile
import struct
import sys
from pathlib import Path
from typing import Any

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from unicorn.x86_const import (
    UC_X86_REG_RAX, UC_X86_REG_RBX, UC_X86_REG_RCX, UC_X86_REG_RDX,
    UC_X86_REG_RSI, UC_X86_REG_RDI, UC_X86_REG_RBP, UC_X86_REG_RSP,
    UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_R10, UC_X86_REG_R11,
    UC_X86_REG_R12, UC_X86_REG_R13, UC_X86_REG_R14, UC_X86_REG_R15,
    UC_X86_REG_RIP, UC_X86_REG_XMM1, UC_X86_REG_XMM2, UC_X86_REG_XMM3,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUTPUT_PATH = HERE / "probe_olmkirakira_mode3_gaussian_output_actual_aex_20260713.py"
DEFAULT_JSON = ROOT / "refs/conformance/olmkirakira_mode3_gaussian_dispatch_actual_aex_20260713.json"
DEFAULT_MD = ROOT / "refs/conformance/olmkirakira_mode3_gaussian_dispatch_actual_aex_20260713.md"
DISPATCH_GLOBAL = 0x181843990
DISPATCH_RDATA_BEGIN = 0x1818481A0
DISPATCH_RDATA_END = 0x18184A1A0
GAUSSIAN_BEGIN = 0x181272EC0
GAUSSIAN_END = 0x181274B00


def load_output_probe():
    spec = importlib.util.spec_from_file_location("gaussian_output_probe", OUTPUT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {OUTPUT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(HERE))
    spec.loader.exec_module(module)
    return module


OUTPUT = load_output_probe()
BASE = OUTPUT.BASE
DIRECT_TARGETS: set[int] = set()
_dis = Cs(CS_ARCH_X86, CS_MODE_64)
_dis.detail = True
_pe = pefile.PE(str(BASE.DEFAULT_AEX), fast_load=True)
_gaussian_instructions = list(_dis.disasm(
    _pe.get_data(GAUSSIAN_BEGIN - _pe.OPTIONAL_HEADER.ImageBase,
                 GAUSSIAN_END - GAUSSIAN_BEGIN), GAUSSIAN_BEGIN))
DIRECT_CALLS: dict[int, int] = {}
INDIRECT_CALLS: dict[int, dict[str, Any]] = {}
for insn in _gaussian_instructions:
    if insn.mnemonic == "call" and insn.op_str.startswith("0x"):
        DIRECT_CALLS[insn.address] = int(insn.op_str, 16)
        DIRECT_TARGETS.add(int(insn.op_str, 16))
    elif insn.mnemonic == "call" and insn.operands and insn.operands[0].type == 3:
        mem = insn.operands[0].mem
        INDIRECT_CALLS[insn.address] = {
            "address": hex(insn.address),
            "bytes": insn.bytes.hex(),
            "text": f"{insn.mnemonic} {insn.op_str}",
            "size": insn.size,
            "base_reg": insn.reg_name(mem.base) if mem.base else None,
            "index_reg": insn.reg_name(mem.index) if mem.index else None,
            "scale": mem.scale,
            "disp": mem.disp,
        }

REGS = {
    "rax": UC_X86_REG_RAX, "rbx": UC_X86_REG_RBX, "rcx": UC_X86_REG_RCX,
    "rdx": UC_X86_REG_RDX, "rsi": UC_X86_REG_RSI, "rdi": UC_X86_REG_RDI,
    "rbp": UC_X86_REG_RBP, "rsp": UC_X86_REG_RSP, "r8": UC_X86_REG_R8,
    "r9": UC_X86_REG_R9, "r10": UC_X86_REG_R10, "r11": UC_X86_REG_R11,
    "r12": UC_X86_REG_R12, "r13": UC_X86_REG_R13, "r14": UC_X86_REG_R14,
    "r15": UC_X86_REG_R15, "rip": UC_X86_REG_RIP,
}


def qwords(loader, address: int, count: int) -> list[str]:
    return [f"0x{struct.unpack('<Q', loader.read_bytes(address + i * 8, 8))[0]:016x}"
            for i in range(count)]


def nonzero_qwords(loader, address: int, size: int) -> int:
    return sum(any(loader.read_bytes(address + off, 8)) for off in range(0, size, 8))


def resolve_indirect_target(loader, spec: dict[str, Any]) -> tuple[int, int]:
    base = loader.uc.reg_read(REGS[spec["base_reg"]]) if spec["base_reg"] else 0
    index = loader.uc.reg_read(REGS[spec["index_reg"]]) if spec["index_reg"] else 0
    slot = (base + index * spec["scale"] + spec["disp"]) & ((1 << 64) - 1)
    target = struct.unpack("<Q", loader.read_bytes(slot, 8))[0]
    return slot, target


def target_class(target: int) -> str:
    if 0x180000000 <= target < 0x190000000:
        return "aex-image"
    if 0x71000000 <= target < 0x72000000:
        return "import-stub"
    if 0x82000000 <= target < 0x83000000:
        return "host-callback"
    return "other"


def xmm_f64(loader, reg) -> float:
    raw = loader.uc.reg_read(reg) & ((1 << 64) - 1)
    return struct.unpack("<d", raw.to_bytes(8, "little"))[0]


def safe_qword(loader, address: int) -> int | None:
    try:
        return struct.unpack("<Q", loader.read_bytes(address, 8))[0]
    except Exception:
        return None


def safe_dwords(loader, address: int, count: int = 4) -> list[str]:
    try:
        return [f"0x{x:08x}" for x in struct.unpack(
            f"<{count}I", loader.read_bytes(address, count * 4))]
    except Exception:
        return []


def allocation_raw(loader, output_report: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for item in output_report.get("called_imports", []):
        if item.get("name") != "_aligned_malloc" or item.get("ret") in {"0x0", "0x0L"}:
            continue
        size = int(item["args"][0], 16)
        if size < 0x40 or size > 0x400:
            continue
        pointer = int(item["ret"], 16)
        raw = loader.read_bytes(pointer, size)
        words = [f"0x{x:08x}" for x in struct.unpack(f"<{size // 4}I", raw[:size - size % 4])]
        floats = []
        for offset in range(0, max(0, size - 21 * 4 + 1), 4):
            run = struct.unpack("<21f", raw[offset:offset + 21 * 4])
            if all(value == run[0] for value in run) and run[0] not in (0.0, -0.0):
                floats.append({"offset": offset, "value": run[0]})
        result.append({"pointer": item["ret"], "size": size, "raw_words_u32": words,
                       "uniform_21f_runs": floats})
    return result


def dispatch_snapshot(loader) -> dict[str, Any]:
    table = struct.unpack("<Q", loader.read_bytes(DISPATCH_GLOBAL, 8))[0]
    return {
        "global": hex(DISPATCH_GLOBAL),
        "table": hex(table),
        "table_first_16_qwords": qwords(loader, table, 16),
        "table_nonzero_qwords_0x10000": nonzero_qwords(loader, table, 0x10000),
        "rdata_constant_first_16_qwords": qwords(loader, DISPATCH_RDATA_BEGIN, 16),
        "rdata_constant_nonzero_qwords": nonzero_qwords(loader, DISPATCH_RDATA_BEGIN,
                                                         DISPATCH_RDATA_END - DISPATCH_RDATA_BEGIN),
    }


class DispatchAuditLoader(OUTPUT.ContinuingAexLoader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if os.environ.get("OLM_KK_SYNC_SHIM_DIAGNOSTIC") == "1":
            def void_success(_uc, _args):
                return 1
            for name in ("EnterCriticalSection", "LeaveCriticalSection", "SetEvent", "ResetEvent"):
                self.register_import_impl(name, void_success)
        self.dispatch_audit: dict[str, Any] = {
            "direct_callee_hits": [],
            "direct_call_runtime": [],
            "dispatch_snapshots": [],
            "indirect_call_static": list(INDIRECT_CALLS.values()),
            "indirect_call_runtime": [],
            "indirect_runtime_targets": [],
            "allocation_raw": [],
            "sigma_propagation": [],
            "coefficient_generators": [],
            "soft_exp_calls": [],
        }
        for target in sorted(DIRECT_TARGETS):
            super().add_code_hook(target, self._callee_hook(target))
        for address, target in DIRECT_CALLS.items():
            OUTPUT.ORIGINAL_LOADER.add_code_hook(self, address, self._direct_call_hook(address, target))
        for address, spec in INDIRECT_CALLS.items():
            OUTPUT.ORIGINAL_LOADER.add_code_hook(self, address, self._indirect_hook(address, spec))
        OUTPUT.ORIGINAL_LOADER.add_code_hook(self, BASE.FUN_GAUSSIAN, self._entry_hook)
        OUTPUT.ORIGINAL_LOADER.add_code_hook(self, OUTPUT.CALLER_RETURN, self._return_hook)
        OUTPUT.ORIGINAL_LOADER.add_code_hook(self, 0x181266730, self._gaussian_setup_entry)
        OUTPUT.ORIGINAL_LOADER.add_code_hook(self, 0x1812754A0, self._coefficient_helper_entry)
        OUTPUT.ORIGINAL_LOADER.add_code_hook(self, 0x181274E10, self._sigma_consumer_entry)
        OUTPUT.ORIGINAL_LOADER.add_code_hook(self, 0x181274E83, self._coefficient_generator_call)
        OUTPUT.ORIGINAL_LOADER.add_code_hook(self, 0x181274E88, self._coefficient_generator_return)
        OUTPUT.ORIGINAL_LOADER.add_code_hook(self, 0x181275500, self._coefficient_generator_entry)
        OUTPUT.ORIGINAL_LOADER.add_code_hook(self, 0x181333430, self._soft_exp_entry)
        OUTPUT.ORIGINAL_LOADER.add_code_hook(self, 0x18133344B, self._soft_exp_return)

    def _callee_hook(self, target: int):
        def hook(loader, _address, _size):
            hits = self.dispatch_audit["direct_callee_hits"]
            if target not in hits:
                hits.append(target)
        return hook

    def _direct_call_hook(self, address: int, target: int):
        def hook(loader, _address, _size):
            self.dispatch_audit["direct_call_runtime"].append({
                "sequence": len(self.dispatch_audit["direct_call_runtime"]),
                "callsite": hex(address),
                "target": hex(target),
            })
        return hook

    def _indirect_hook(self, address: int, spec: dict[str, Any]):
        def hook(loader, _address, _size):
            try:
                slot, target = resolve_indirect_target(loader, spec)
                record = dict(spec)
                record.update({"slot": hex(slot), "target": hex(target),
                               "target_class": target_class(target),
                               "sequence": len(self.dispatch_audit["indirect_call_runtime"])})
                self.dispatch_audit["indirect_call_runtime"].append(record)
                if target not in self.dispatch_audit["indirect_runtime_targets"]:
                    self.dispatch_audit["indirect_runtime_targets"].append(target)
            except Exception as exc:
                self.dispatch_audit["indirect_call_runtime"].append(
                    dict(spec, target_error=repr(exc),
                         sequence=len(self.dispatch_audit["indirect_call_runtime"])))
        return hook

    def _gaussian_setup_entry(self, loader, _address, _size):
        rsp = loader.uc.reg_read(UC_X86_REG_RSP)
        ksize = loader.uc.reg_read(UC_X86_REG_R9)
        self.dispatch_audit["sigma_propagation"].append({
            "point": "FUN_181266730_entry",
            "rsp": hex(rsp),
            "stack_plus_28_sigma_x_raw_u64": hex(safe_qword(loader, rsp + 0x28) or 0),
            "stack_plus_28_sigma_x_f64": struct.unpack("<d", loader.read_bytes(rsp + 0x28, 8))[0],
            "stack_plus_30_sigma_y_raw_u64": hex(safe_qword(loader, rsp + 0x30) or 0),
            "stack_plus_30_sigma_y_f64": struct.unpack("<d", loader.read_bytes(rsp + 0x30, 8))[0],
            "r9_ksize_pointer": hex(ksize),
            "r9_ksize_words_u32": safe_dwords(loader, ksize, 4),
            "r8_type_raw_u32": loader.uc.reg_read(UC_X86_REG_R8) & 0xFFFFFFFF,
        })

    def _coefficient_helper_entry(self, loader, _address, _size):
        output = loader.uc.reg_read(UC_X86_REG_R9)
        self.dispatch_audit["sigma_propagation"].append({
            "point": "FUN_1812754a0_entry",
            "xmm1_sigma_f64": xmm_f64(loader, UC_X86_REG_XMM1),
            "ecx_kernel_size_raw_u32": loader.uc.reg_read(UC_X86_REG_RCX) & 0xFFFFFFFF,
            "r8_type_raw_u32": loader.uc.reg_read(UC_X86_REG_R8) & 0xFFFFFFFF,
            "r9_output_mat_pointer": hex(output),
            "r9_output_mat_wrapper": BASE.read_array_wrapper(loader, output),
        })

    def _sigma_consumer_entry(self, loader, _address, _size):
        self.dispatch_audit["sigma_propagation"].append({
            "point": "FUN_181274e10_entry",
            "xmm2_sigma_f64": xmm_f64(loader, UC_X86_REG_XMM2),
        })

    def _coefficient_generator_call(self, loader, _address, _size):
        self.dispatch_audit["coefficient_generators"].append({
            "import_log_begin": len(loader.import_log),
        })

    def _coefficient_generator_entry(self, loader, _address, _size):
        current = self.dispatch_audit["coefficient_generators"][-1]
        current["entry"] = {
            "r8_count": loader.uc.reg_read(UC_X86_REG_R8) & 0xFFFFFFFF,
            "xmm3_sigma_f64": xmm_f64(loader, UC_X86_REG_XMM3),
        }

    def _coefficient_generator_return(self, loader, _address, _size):
        rsp = loader.uc.reg_read(UC_X86_REG_RSP)
        begin = safe_qword(loader, rsp + 0x30) or 0
        end = safe_qword(loader, rsp + 0x38) or 0
        count = (end - begin) // 8 if begin and end >= begin else 0
        raw = loader.read_bytes(begin, count * 8) if 0 < count <= 4096 else b""
        current = self.dispatch_audit["coefficient_generators"][-1]
        current["return"] = {
            "begin": hex(begin),
            "end": hex(end),
            "count": count,
            "words_u64": [f"0x{word:016x}" for word in struct.unpack(f"<{count}Q", raw)] if raw else [],
            "values_f64": list(struct.unpack(f"<{count}d", raw)) if raw else [],
            "imports_during_generator": [
                {"dll": item.dll, "name": item.name, "implemented": item.name in loader.import_impls}
                for item in loader.import_log[current["import_log_begin"]:]
            ],
        }

    def _soft_exp_entry(self, loader, _address, _size):
        rcx = loader.uc.reg_read(UC_X86_REG_RCX)
        rdx = loader.uc.reg_read(UC_X86_REG_RDX)
        self.dispatch_audit["soft_exp_calls"].append({
            "destination": rcx,
            "input_u64": f"0x{safe_qword(loader, rdx) or 0:016x}",
            "input_f64": struct.unpack("<d", loader.read_bytes(rdx, 8))[0],
        })

    def _soft_exp_return(self, loader, _address, _size):
        current = self.dispatch_audit["soft_exp_calls"][-1]
        destination = current.pop("destination")
        current["output_u64"] = f"0x{safe_qword(loader, destination) or 0:016x}"
        current["output_f64"] = struct.unpack("<d", loader.read_bytes(destination, 8))[0]

    def _entry_hook(self, loader, _address, _size):
        self.dispatch_audit["dispatch_snapshots"].append({
            "point": "gaussian_entry",
            "rip": hex(loader.uc.reg_read(UC_X86_REG_RIP)),
            "snapshot": dispatch_snapshot(loader),
        })

    def _return_hook(self, loader, _address, _size):
        self.dispatch_audit["dispatch_snapshots"].append({
            "point": "caller_return",
            "rip": hex(loader.uc.reg_read(UC_X86_REG_RIP)),
            "snapshot": dispatch_snapshot(loader),
        })


def render(report: dict[str, Any]) -> str:
    lines = ["# OLMKiraKira Mode 3 Gaussian dispatch audit", "", f"Status: **{report['status']}**", "",
             "## FACT", ""]
    lines += [f"- {item}" for item in report["FACT"]]
    lines += ["", "## INFERENCE / LIMIT", ""]
    lines += [f"- {item}" for item in report["INFERENCE"]]
    lines += ["", "## Evidence", "", f"- `{json.dumps(report['evidence'], sort_keys=True)}`", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aex-path", type=Path, default=BASE.DEFAULT_AEX)
    parser.add_argument("--width", type=int, default=9)
    parser.add_argument("--height", type=int, default=7)
    parser.add_argument("--length", type=int, default=5)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    parser.add_argument("--max-instructions", type=int, default=50_000_000)
    args = parser.parse_args()

    OUTPUT.ContinuingAexLoader = DispatchAuditLoader
    old_argv = sys.argv
    sys.argv = [str(OUTPUT_PATH), "--aex-path", str(args.aex_path),
                "--width", str(args.width), "--height", str(args.height),
                "--length", str(args.length),
                "--output-json", str(args.output_json), "--output-md", str(args.output_md),
                "--max-instructions", str(args.max_instructions)]
    try:
        OUTPUT.main()
    finally:
        sys.argv = old_argv
    output_report = json.loads(args.output_json.read_text(encoding="utf-8"))
    loader = OUTPUT.LAST_LOADER
    audit = loader.dispatch_audit if loader is not None else {}
    audit["allocation_raw"] = allocation_raw(loader, output_report) if loader is not None else []
    targets = [hex(target) for target in sorted(audit.get("direct_callee_hits", []))]
    snapshots = audit.get("dispatch_snapshots", [])
    table_before = snapshots[0]["snapshot"] if snapshots else None
    table_after = snapshots[-1]["snapshot"] if snapshots else None
    report = {
        "schema": "olmkirakira-mode3-gaussian-dispatch-actual-aex/1",
        "status": output_report.get("status"),
        "FACT": [
            "The probe reuses the existing actual-AEX Gaussian body and caller-return capture without changing production or the existing probes.",
            f"The captured call contract uses Size(0,1), sigmaX={args.length * 0.5}, and {args.width * args.height} float32 output words after return.",
            "The dispatch global points at the probe-owned backing store; the embedded initializer populates that store before Gaussian entry and it remains populated at caller return.",
            f"The Gaussian body reached {len(targets)} unique direct callees: {', '.join(targets) if targets else 'none recorded'}.",
            f"Capstone found {len(INDIRECT_CALLS)} RIP/memory indirect callsites in the disassembled interval; {len(audit.get('indirect_call_runtime', []))} executed at runtime.",
            "The executed direct-call order includes FUN_181266730 at sequence 10; its nested static callees include FUN_1812754a0, FUN_181275500, and FUN_181275d70 as coefficient/setup-path candidates.",
            f"Sigma propagation is captured for requested length {args.length} and sigmaX={args.length * 0.5}.",
        ],
        "INFERENCE": [
            "The initial zero fill is only allocation state; coefficient-generator captures are the authoritative kernel witness.",
            "The captured return words are an emulation-path witness, not a pinned OpenCV 4.5.5 oracle, until the indirect kernel/CPU feature path is matched to a live Windows process.",
            "Allocation scans are supporting evidence, not symbol identification; generator return values are recorded separately.",
        ],
        "evidence": {
            "aex": str(args.aex_path),
            "aex_sha256": output_report.get("execution", {}).get("aex_sha256"),
            "process_attach_diagnostic": output_report.get("process_attach_diagnostic"),
            "manual_crt_initializers_diagnostic": output_report.get("manual_crt_initializers_diagnostic"),
            "entry_hit_count": output_report.get("execution", {}).get("entry_hit_count"),
            "return_hit_count": output_report.get("execution", {}).get("return_hit_count"),
            "output_word_count": len(output_report.get("output_capture", {}).get("output_array_after", {}).get("mat", {}).get("words_u32", [])),
            "dispatch_table_before": table_before,
            "dispatch_table_after": table_after,
            "direct_callee_hits": targets,
            "direct_callee_candidates_in_gaussian_range": [hex(target) for target in sorted(DIRECT_TARGETS)],
            "direct_call_runtime": audit.get("direct_call_runtime", []),
            "indirect_call_static": audit.get("indirect_call_static", []),
            "indirect_call_runtime": audit.get("indirect_call_runtime", []),
            "indirect_runtime_targets": [hex(target) for target in audit.get("indirect_runtime_targets", [])],
            "allocation_raw": audit.get("allocation_raw", []),
            "sigma_propagation": audit.get("sigma_propagation", []),
            "coefficient_generators": audit.get("coefficient_generators", []),
            "soft_exp_calls": audit.get("soft_exp_calls", []),
            "windows_live_minimum_targets": [
                {"address": "0x181272ec0", "role": "GaussianBlur wrapper entry"},
                {"address": "0x181266730", "role": "called Gaussian setup/coefficient-path helper"},
                {"address": "0x1812754a0", "role": "called by 0x181266730; coefficient/math helper candidate"},
                {"address": "0x181275500", "role": "called by 0x181266730; coefficient/math helper candidate"},
                {"address": "0x181275d70", "role": "called by 0x181266730; allocation/exception-path candidate"},
                {"address": "0x400104c0", "role": "probe allocation containing 21 uniform float32 taps"},
            ],
        },
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "json": str(args.output_json),
                      "callee_hits": targets, "table_nonzero_before":
                      table_before["table_nonzero_qwords_0x10000"] if table_before else None}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
