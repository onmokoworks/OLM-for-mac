#!/usr/bin/env python3
"""Capture complete actual-AEX Mode-4 scalar chains at canonical ray angles."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path
from typing import Any

from unicorn.x86_const import UC_X86_REG_R14, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9


ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "tools/emulation"
BASE_PATH = HERE / "probe_olmkirakira_mode3_actual_aex.py"
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
WARP = 0x181297AC0
FORWARD_AFTER = 0x181150946
CASES = ((9, 7, 0), (9, 9, 45), (9, 9, -45), (9, 9, 90))


def load_base():
    spec = importlib.util.spec_from_file_location("kira_mode4_canonical_base", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load actual-AEX base")
    sys.path.insert(0, str(HERE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def raw_words(base: Any, loader: Any, wrapper: int) -> dict[str, Any]:
    value = base.read_array_wrapper(loader, wrapper)
    if not value or not value.get("mat"):
        raise RuntimeError(f"cannot decode wrapper {wrapper:#x}")
    mat = value["mat"]
    rows, cols = mat["rows"], mat["cols"]
    data, step = int(mat["data"], 16), mat["step_bytes"]
    words: list[str] = []
    for y in range(rows):
        row = struct.unpack(f"<{cols}I", loader.read_bytes(data + y * step, cols * 4))
        words.extend(f"0x{word:08x}" for word in row)
    return {"rows": rows, "cols": cols, "step_bytes": step, "words_u32": words}


def raw_mat_words(base: Any, loader: Any, header: int) -> dict[str, Any]:
    mat = base.read_mat(loader, header)
    if not mat:
        raise RuntimeError(f"cannot decode Mat {header:#x}")
    rows, cols = mat["rows"], mat["cols"]
    data, step = int(mat["data"], 16), mat["step_bytes"]
    words: list[str] = []
    for y in range(rows):
        row = struct.unpack(f"<{cols}I", loader.read_bytes(data + y * step, cols * 4))
        words.extend(f"0x{word:08x}" for word in row)
    return {"rows": rows, "cols": cols, "step_bytes": step, "words_u32": words}


def run_case(base: Any, width: int, height: int, angle: int) -> dict[str, Any]:
    observed: dict[str, Any] = {"warp_entries": []}

    class Loader(base.AexLoader):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            def capture_warp(loader, _address, _size):
                wrappers = [loader.uc.reg_read(reg) for reg in
                            (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8)]
                observed["warp_entries"].append({
                    "source": raw_words(base, loader, wrappers[0]),
                    "transform": base.read_array_wrapper(loader, wrappers[2]),
                    "dsize_packed": hex(loader.uc.reg_read(UC_X86_REG_R9)),
                })
            self.add_code_hook(WARP, capture_warp)
            self.add_code_hook(FORWARD_AFTER, lambda loader, _address, _size:
                               observed.__setitem__("forward", raw_mat_words(
                                   base, loader, loader.uc.reg_read(UC_X86_REG_R14))))

        def call_function(self, address, *args, **kwargs):
            if address != base.FUN_HELPER:
                return super().call_function(address, *args, **kwargs)
            helper_args = list(kwargs["int_args"])
            helper_args[5] = angle
            helper_args[6] = 5
            helper_args[7] = 4
            kwargs["int_args"] = helper_args
            result = super().call_function(address, *args, **kwargs)
            observed["final"] = raw_mat_words(base, self, helper_args[3])
            return result

    original = base.AexLoader
    base.AexLoader = Loader
    args = type("Args", (), {
        "aex_path": AEX, "width": width, "height": height,
        "length": 5, "sigma": 0.0, "max_instructions": 30_000_000,
    })()
    try:
        execution = base.run(args)
    finally:
        base.AexLoader = original
    if execution.get("error") is not None or len(observed["warp_entries"]) != 2:
        raise RuntimeError({"execution": execution, "observed": observed})
    first, second = observed["warp_entries"]
    return {
        "width": width, "height": height, "radius": 5, "angle_degrees": angle,
        "execution_status": execution["status"],
        "source": first["source"],
        "forward": observed["forward"],
        "recurrence": second["source"],
        "final": observed["final"],
        "warp_call_count": 2,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path,
                        default=ROOT / "refs/conformance/olmkirakira_mode4_canonical_angles_actual_aex_20260810.json")
    args = parser.parse_args()
    base = load_base()
    cases = [run_case(base, width, height, angle) for width, height, angle in CASES]
    report = {
        "schema": "olmkirakira.mode4-canonical-angles-actual-aex/1",
        "status": "captured",
        "aex_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
        "entry": "FUN_181150790",
        "cases": cases,
        "boundary": "Hostless execution of the checked-in Windows AEX; no native-AE claim.",
    }
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "cases": len(cases)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
