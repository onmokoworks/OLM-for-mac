#!/usr/bin/env python3
"""Bounded Mac-only actual-AEX proof for Mode4 Highlight writeback/normalization."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "tools/emulation"
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
DECOMP = ROOT / "decomp/OLMKiraKira.aex.c.txt"
ASM = ROOT / "disasm/OLMKiraKira.aex.asm.txt"
OUT_JSON = ROOT / "refs/conformance/olmkirakira_mode4_highlight_writeback_20260718.json"
OUT_MD = ROOT / "refs/conformance/olmkirakira_mode4_highlight_writeback_20260718.md"
TAIL = 0x181150F3D
HELPER = 0x181150790


def load_base():
    spec = importlib.util.spec_from_file_location("mode4_writeback_base_20260718", HERE / "audit_olmkirakira_mode4_edge_passes_20260718.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load bounded actual-AEX harness")
    sys.path.insert(0, str(HERE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.load_base()


def f32(value: int) -> float:
    return struct.unpack("<f", (value & 0xFFFFFFFF).to_bytes(4, "little"))[0]


def sanitize_paths(value: object) -> object:
    """Keep generated evidence portable without changing numeric witness data."""
    if isinstance(value, dict):
        return {key: sanitize_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_paths(item) for item in value]
    if isinstance(value, str):
        try:
            path = Path(value)
            if path.is_absolute() and path.is_relative_to(ROOT):
                return str(path.relative_to(ROOT))
        except (OSError, ValueError):
            pass
    return value


def main() -> int:
    base = load_base()
    tail_hits: list[dict[str, object]] = []
    writeback: dict[str, object] = {}

    class WitnessLoader(base.AexLoader):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            from unicorn.x86_const import UC_X86_REG_R12, UC_X86_REG_R14, UC_X86_REG_R15, UC_X86_REG_XMM9

            def named_tail(loader, address, _size):
                tail_hits.append({
                    "rip": hex(address),
                    "r12_mat": base.read_mat(loader, loader.uc.reg_read(UC_X86_REG_R12)),
                    "r14_mat": base.read_mat(loader, loader.uc.reg_read(UC_X86_REG_R14)),
                    "r15d": loader.uc.reg_read(UC_X86_REG_R15) & 0xFFFFFFFF,
                    "xmm9_f32": f32(loader.uc.reg_read(UC_X86_REG_XMM9)),
                })

            self.add_code_hook(TAIL, named_tail)

        def call_function(self, address, *args, **kwargs):
            int_args = list(kwargs.get("int_args", []))
            if address == HELPER:
                int_args[7] = 4
                kwargs["int_args"] = int_args
            result = super().call_function(address, *args, **kwargs)
            if address == HELPER:
                dst = base.read_mat(self, int_args[3])
                writeback["destination"] = dst
                writeback["changed"] = bool(dst and dst.get("values_f32") and any(dst["values_f32"][0]))
            return result

    original = base.AexLoader
    base.AexLoader = WitnessLoader
    args = type("Args", (), {"aex_path": AEX, "width": 9, "height": 7, "length": 5, "sigma": 0.0, "max_instructions": 20_000_000})()
    try:
        execution = base.run(args)
    finally:
        base.AexLoader = original

    decomp = DECOMP.read_text(encoding="utf-8")
    asm = ASM.read_text(encoding="utf-8")
    mode4 = decomp[decomp.index("// === FUN_18114f4a0"):decomp.index("// === FUN_18114fd90")]
    normalize = decomp[decomp.index("// === FUN_18114fd90"):decomp.index("// === FUN_18114ffd0")]
    mode4_branch = mode4[mode4.index("uVar14 = CONCAT44(iVar6,iVar6)"):]
    static_decomp = {
        "mode4_three_blur_calls": mode4_branch.count("FUN_181280bc0(") == 3,
        "mode4_gain_square_then_square": "fVar13 = *pfVar8 * *pfVar8" in mode4 and "*pfVar8 = fVar13 * fVar13" in mode4,
        "five_layer_combination": "lVar11 = 5" in normalize and "plVar6 = plVar6 + 1" in normalize,
        "alpha_union": "param_7[3] + fVar12" in normalize and "param_7[3] * fVar12" in normalize,
        "rgb_normalization": "fVar1 / fVar12" in normalize and "*param_7 = fVar12 * *param_7" in normalize,
    }
    static_asm = {
        "mode4_gain_writeback": "18115121a  IMUL ESI,ESI" in asm and "181151229  JMP 0x181150f3d" in asm,
        "shared_tail": "181150f3d  NEG R15D" in asm,
        "mode4_three_blur_calls": asm.count("181280bc0") >= 3,
        "normalization_function": "; === FUN_18114fd90 @ 18114fd90 ===" in asm,
    }
    checks = {
        "actual_aex_mode4_tail": len(tail_hits) == 1 and tail_hits[0]["rip"] == hex(TAIL),
        "actual_aex_mode4_output_writeback": bool(writeback.get("changed")),
        "actual_mode_selector_overridden_only_in_harness": execution.get("input", {}).get("blur_mode") == 3,
        "static_decomp": all(static_decomp.values()),
        "static_asm": all(static_asm.values()),
        "no_production_edit": True,
    }
    status = "PASS_MODE4_BOUNDED_WRITEBACK_NORMALIZATION" if all(checks.values()) else "BLOCKED_MODE4_BOUNDED_WRITEBACK_NORMALIZATION"
    report = {
        "schema": 1,
        "kind": "olmkirakira_mode4_highlight_writeback_normalization",
        "date": "2026-07-18",
        "status": status,
        "ae_exact_claim": False,
        "production_edit": False,
        "binary": {"path": str(AEX.relative_to(ROOT)), "sha256": hashlib.sha256(AEX.read_bytes()).hexdigest()},
        "question": "What final Mode4 Highlight normalization/combination or scalar output writeback is bounded across decomp, asm, and actual AEX?",
        "answer": {
            "actual_aex": "The Mac-only Unicorn witness reaches the shared tail after the Mode4 recurrence and leaves a changed CV_32FC1 destination buffer; this bounds scalar-buffer output writeback.",
            "static": "The caller normalizes RGB by accumulated alpha and combines five layers with source-over alpha union; Mode4 also squares the scalar gain twice after its three blur calls.",
            "limit": "The actual-AEX witness does not execute the full AE-host caller, color parameter binding, or final PF pixel store, so AE-exact output is not claimed.",
        },
        "checks": checks,
        "static": {"decomp": static_decomp, "asm": static_asm},
        "actual_aex": {"helper": hex(HELPER), "tail": hex(TAIL), "execution": execution, "tail_hits": tail_hits, "writeback": writeback},
        "limits": [
            "Mac-only Unicorn execution of the checked-in Windows PE; no Windows or AE-host claim.",
            "Mode selector 4 is changed only in the harness; input reports blur_mode 3 as requested by the base probe.",
            "Static caller normalization/combination is not an actual full-caller witness and does not prove final PF pixel encoding.",
            "No production source or AEX bytes were patched.",
        ],
    }
    report = sanitize_paths(report)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(f"""# OLMKiraKira Mode4 Highlight writeback and normalization (2026-07-18)

Status: **{status}**
AE exact: **false**
Production edit: **none**

## Bounded result

The Mac-only actual-AEX witness reaches the shared Mode4 tail at `0x181150f3d`
after the recurrence and produces a changed `CV_32FC1` destination buffer.
That proves scalar-buffer output writeback for this bounded synthetic witness.

Static decomp/asm also bounds the caller-side semantics: Mode4 makes three
`FUN_181280bc0` passes, squares the scalar gain twice, and the shared five-layer
combiner normalizes RGB by accumulated alpha and uses source-over alpha union.

## Limits

This does not prove the full AE-host caller, Highlight Color parameter binding,
final PF pixel encoding, Windows behavior, or AE-exact equivalence. No
production source or AEX bytes were changed.

Verification: `python3 tools/emulation/audit_olmkirakira_mode4_highlight_writeback_20260718.py`
""", encoding="utf-8")
    print(json.dumps({"status": status, "checks": checks, "json": str(OUT_JSON), "md": str(OUT_MD)}, sort_keys=True))
    return 0 if status.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
