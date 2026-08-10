#!/usr/bin/env python3
"""Capture actual-AEX Mode-3 Length-50 complete chains at canonical angles."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import struct
import sys
from pathlib import Path
from typing import Any

from unicorn.x86_const import UC_X86_REG_R14, UC_X86_REG_RCX


ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "tools/emulation"
OUTPUT_BASE = HERE / "probe_olmkirakira_mode3_gaussian_output_actual_aex_20260713.py"
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
REPORT = ROOT / "refs/conformance/olmkirakira_mode3_default50_canonical_actual_aex_20260810.json"
WARP = 0x181297AC0
FORWARD_AFTER = 0x181150946
CASES = ((9, 7, 0), (9, 9, 45), (9, 9, -45), (9, 9, 90))


def load_output_base():
    spec = importlib.util.spec_from_file_location("kira_mode3_output_base", OUTPUT_BASE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Gaussian output probe")
    sys.path.insert(0, str(HERE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def raw_mat_words(base: Any, loader: Any, header: int) -> dict[str, Any]:
    mat = base.read_mat(loader, header)
    if not mat:
        raise RuntimeError(f"cannot decode Mat {header:#x}")
    rows, cols = mat["rows"], mat["cols"]
    data, step = int(mat["data"], 16), mat["step_bytes"]
    words: list[str] = []
    for y in range(rows):
        words.extend(f"0x{word:08x}" for word in
                     struct.unpack(f"<{cols}I", loader.read_bytes(data + y * step, cols * 4)))
    return {"rows": rows, "cols": cols, "step_bytes": step, "words_u32": words}


def raw_wrapper_words(base: Any, loader: Any, wrapper: int) -> dict[str, Any]:
    value = base.read_array_wrapper(loader, wrapper)
    if not value or not value.get("mat"):
        raise RuntimeError(f"cannot decode wrapper {wrapper:#x}")
    return raw_mat_words(base, loader, int(value["mat"]["header"], 16))


def run_case(output: Any, width: int, height: int, angle: int) -> dict[str, Any]:
    base = output.BASE
    base.mat_header = output.body_compatible_mat_header
    observed: dict[str, Any] = {"warp_sources": []}

    class Loader(output.ContinuingAexLoader):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.add_code_hook(WARP, lambda loader, _address, _size:
                               observed["warp_sources"].append(raw_wrapper_words(
                                   base, loader, loader.uc.reg_read(UC_X86_REG_RCX))))
            self.add_code_hook(FORWARD_AFTER, lambda loader, _address, _size:
                               observed.__setitem__("forward", raw_mat_words(
                                   base, loader, loader.uc.reg_read(UC_X86_REG_R14))))

        def call_function(self, address, *args, **kwargs):
            if address != base.FUN_HELPER:
                return super().call_function(address, *args, **kwargs)
            helper_args = list(kwargs["int_args"])
            helper_args[5] = angle
            helper_args[6] = 50
            helper_args[7] = 3
            kwargs["int_args"] = helper_args
            result = super().call_function(address, *args, **kwargs)
            observed["final"] = raw_mat_words(base, self, helper_args[3])
            return result

    output.CONTINUATION["entry_hits"].clear()
    output.CONTINUATION["return_hits"].clear()
    base.AexLoader = Loader
    args = type("Args", (), {
        "aex_path": AEX, "width": width, "height": height,
        "length": 50, "sigma": 0.0, "max_instructions": 80_000_000,
    })()
    report = base.run(args)
    returned = output.CONTINUATION["return_hits"][-1] if output.CONTINUATION["return_hits"] else None
    if report.get("error") is not None or len(observed["warp_sources"]) != 2 or not returned:
        raise RuntimeError({"report": report, "observed": observed, "returned": returned})
    gaussian = returned["output_array_after"]
    gaussian_words = gaussian["mat"]["words_u32"]
    return {
        "width": width, "height": height, "length": 50, "angle_degrees": angle,
        "source": observed["warp_sources"][0],
        "forward": observed["forward"],
        "gaussian": {"rows": height, "cols": width, "step_bytes": width * 4,
                     "words_u32": gaussian_words},
        "final": observed["final"],
        "gaussian_entry_hits": len(output.CONTINUATION["entry_hits"]),
        "gaussian_return_hits": len(output.CONTINUATION["return_hits"]),
        "warp_call_count": len(observed["warp_sources"]),
        "crt_initializer_callbacks": len(report["manual_crt_initializers_diagnostic"]["callbacks"]),
    }


def main() -> int:
    os.environ["OLM_KK_PROCESS_ATTACH_DIAGNOSTIC"] = "1"
    os.environ["OLM_KK_MANUAL_CRT_INITIALIZERS_DIAGNOSTIC"] = "1"
    output = load_output_base()
    cases = [run_case(output, width, height, angle) for width, height, angle in CASES]
    report = {
        "schema": "olmkirakira.mode3-default50-canonical-actual-aex/1",
        "status": "captured",
        "aex_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
        "entry": "FUN_181150790",
        "cases": cases,
        "boundary": "Hostless checked-in Windows AEX with process attach and 50 CRT initializer callbacks; no native-AE claim.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "cases": len(cases)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
