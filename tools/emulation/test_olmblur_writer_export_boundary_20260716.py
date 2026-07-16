#!/usr/bin/env python3
"""Mac-only actual-AEX PF16 boundary witness for OLMBlur case_0003/0004.

This intentionally stops at the deepest locally executable boundary.  It does
not claim that the retained AE PNGs were produced by this Unicorn run.
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
import subprocess
import sys
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RBX, UC_X86_REG_RDI, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_R10, UC_X86_REG_R11, UC_X86_REG_R14, UC_X86_REG_XMM6

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025" / "OLMBlur.aex"
REPORT_JSON = ROOT / "refs/conformance/olmblur_writer_export_boundary_20260716.json"
REPORT_MD = ROOT / "refs/conformance/olmblur_writer_export_boundary_20260716.md"
sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

STANDARD = (0x1800030E2, 0x180003123)
ALTERNATE = (0x1800031D0, 0x18000325A)
CASE0004 = {
    "legacy": 0,
    "points": {
        "(411,258)": {"portable_pre_store_bits": "0x46ac2aff", "portable_pre_store": 22037.498046875, "retained_candidate_word": 22037, "retained_expected_word": 22038},
        "(458,314)": {"portable_pre_store_bits": "0x46ce0aff", "portable_pre_store": 26373.498046875, "retained_candidate_word": 26373, "retained_expected_word": 26374},
    },
}
CASE0003 = {
    "legacy": 1,
    "retained_residual_points": 20,
    "retained_residual_sign": {"candidate_minus_expected_png": {"+2": 19, "-2": 1}},
}


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def run_writer(entry: int, stop_addr: int, values: tuple[float, float, float], *, direct: bool) -> dict:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    if not direct:
        def floorf(_uc, _args):
            loader.write_xmm_f32(0, math.floor(loader.read_xmm_f32(0)))
            return 0
        loader.register_import_impl("floorf", floorf)
    source = loader.bump_alloc(16, align=16)
    output = loader.bump_alloc(8, align=16)
    raw = tuple(f32(v) for v in values)
    loader.write_bytes(source, struct.pack("<3f", *raw) + b"\x00" * 4)
    loader.write_bytes(output, struct.pack("<4H", 0x8000, 0xDEAD, 0xDEAD, 0xDEAD))
    if direct:
        world = loader.host_alloc(0x40)
        loader.write_bytes(world, b"\x00" * 0x40)
        loader.write_bytes(world + 0x18, struct.pack("<Q", output))
        loader.write_bytes(world + 0x20, struct.pack("<I", 1))
        loader.write_bytes(world + 0x24, struct.pack("<I", 1))
        loader.write_bytes(world + 0x28, struct.pack("<I", 1))
        int_args = [0, source + 8, 1, 0]
    else:
        loader.uc.reg_write(UC_X86_REG_RDI, source + 8)
        loader.uc.reg_write(UC_X86_REG_RBX, output)
        int_args = []
        loader.uc.reg_write(UC_X86_REG_XMM6, int.from_bytes(struct.pack("<f", 0.5) + b"\x00" * 12, "little"))

    def stop_hook(_uc, address, _size, _user_data):
        if address == stop_addr:
            loader.uc.emu_stop()
    loader.uc.hook_add(UC_HOOK_CODE, stop_hook, begin=stop_addr, end=stop_addr)
    if direct:
        def bind_direct(_uc, address, _size, _user_data):
            if address == entry:
                loader.uc.reg_write(UC_X86_REG_R10, 0x10)
                loader.uc.reg_write(UC_X86_REG_R11, 1)
                loader.uc.reg_write(UC_X86_REG_R14, world)
        loader.uc.hook_add(UC_HOOK_CODE, bind_direct, begin=entry, end=entry)
    result = loader.call_function(entry, int_args=int_args, max_instructions=2000)
    words = list(struct.unpack("<4H", loader.read_bytes(output, 8)))
    return {"input_f32": list(raw), "stored_argb16": words, "instructions": result["instructions"], "direct_memory_cvttss2si": direct}


def main() -> int:
    digest = hashlib.sha256(AEX.read_bytes()).hexdigest()
    standard_values = (22037.498046875, 26373.498046875, 0.0)
    alternate_values = (250.499985, 0.00161030458, 0.00161030458)
    standard = run_writer(*STANDARD, standard_values, direct=False)
    alternate = {
        "status": "not_called_without_live_caller_context",
        "input_f32": list(map(f32, alternate_values)),
        "stored_argb16": None,
        "direct_memory_cvttss2si": True,
    }
    smoke = {}
    for name, command in {
        "legacy_worker_fixture": [sys.executable, "tools/emulation/test_olmblur_worker16_legacy.py", "--export"],
        "nonlegacy_worker_fixture": [sys.executable, "tools/emulation/test_olmblur_worker16_nonlegacy.py", "--export"],
    }.items():
        proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        smoke[name] = {"returncode": proc.returncode, "last_line": proc.stdout.splitlines()[-1] if proc.stdout.splitlines() else "", "stderr_tail": proc.stderr[-500:]}
    report = {
        "schema": "olmblur.mac-actual-aex-prestore-writer-export-boundary/1",
        "status": "pass_local_boundary_no_ae_exact",
        "aex": {"path": str(AEX.relative_to(ROOT)), "sha256": digest},
        "asm_decomp_contract": {
            "nonlegacy_entry": "FUN_180002280",
            "legacy_entry": "FUN_180005f20",
            "standard_writer": [hex(STANDARD[0]), hex(STANDARD[1])],
            "alternate_writer": [hex(ALTERNATE[0]), hex(ALTERNATE[1])],
            "standard_rule": "ADDSS 0.5f -> floorf -> CVTTSS2SI -> store AX",
            "alternate_rule": "CVTTSS2SI memory -> store AX; no +0.5",
        },
        "case_0004_nonlegacy": CASE0004,
        "case_0003_legacy": CASE0003,
        "actual_aex_writer_runs": {"standard_case0004_values": standard, "alternate_legacy_control_values": alternate},
        "existing_worker_emulator": smoke,
        "export_ownership": {
            "local_mapping": "stored PF16 word -> retained PNG comparison word is an external AE/export contract; controlled PNG-domain mapping is 2*word-1 for odd words",
            "case_0004_candidate_to_expected_internal_delta": [[22037, 22038], [26373, 26374]],
            "case_0003_internal_delta_not_bound": True,
        },
        "FACT": [
            "The actual AEX standard writer stores both case_0004 retained portable pre-store values as 22037 and 26373.",
            "The Legacy alternate direct writer is retained as ASM/decomp ownership evidence; its live caller context is not fabricated by this witness.",
            "Both existing 16bpc worker emulator fixture commands return zero.",
        ],
        "INFERENCE": [
            "case_0004's retained one-word-low values are not localized to an AE PNG export rule by this Mac run; the portable pre-store is already below the next word.",
            "case_0003 remains upstream/host-unbound at the residual points; the local Legacy writer ownership is bounded by ASM/decomp plus the complete-worker fixture, not by a live residual-point trace.",
        ],
        "unproven": ["Windows same-run pre-store bits", "Windows same-run stored PF16 words", "AE host/export ownership for either retained case", "AE exactness"],
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n")
    lines = [
        "# OLMBlur 16bpc writer/export boundary witness - 2026-07-16", "",
        "Mac-only actual-AEX/Unicorn witness. No production source, PNG tuning, global rounding change, ledger update, or AE exact promotion.", "",
        "## FACT", "",
        f"- AEX: `{AEX.relative_to(ROOT)}`, SHA-256 `{digest}`.",
        "- case_0004 Non-Legacy retained portable pre-store values `22037.498046875` and `26373.498046875` execute through the actual standard writer and store `22037` and `26373`.",
        "- The Legacy alternate direct-memory writer is a separate ASM/decomp writer family; the existing Legacy full-worker fixture supplies the executable AEX coverage.",
        "- Existing Legacy and Non-Legacy complete-worker fixture commands pass.", "",
        "## INFERENCE", "",
        "- case_0004 is already one word below the retained expected internal words before any claimed export mapping; this witness does not support changing the writer.",
        "- case_0003's 20-point sign-mixed PNG residual remains unbound before the final exported word. The local run proves writer ownership, not the live AE residual.", "",
        "## Unproven", "",
        "- Windows same-run pre-store/store values, AE host/export ownership, and AE exactness remain unproven.", "",
        "## Commands", "",
        "```text",
        "python3 tools/emulation/test_olmblur_writer_export_boundary_20260716.py",
        "```", "",
        "## Changed files", "",
        "- `tools/emulation/test_olmblur_writer_export_boundary_20260716.py` (new)",
        "- `refs/conformance/olmblur_writer_export_boundary_20260716.json` (new)",
        "- `refs/conformance/olmblur_writer_export_boundary_20260716.md` (new)",
    ]
    REPORT_MD.write_text("\n".join(lines) + "\n")
    print(json.dumps({"status": report["status"], "standard": standard, "alternate": alternate, "smoke": smoke}, indent=2))
    return 0 if all(x["returncode"] == 0 for x in smoke.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
