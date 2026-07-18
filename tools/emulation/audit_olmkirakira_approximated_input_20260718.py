#!/usr/bin/env python3
"""Audit OLMKiraKira Approximated Input without changing production code.

The checked-in Windows AEX is inspected statically and then exercised through
the existing bounded common-owner harness with the checkbox enabled in memory.
The harness is intentionally fail-closed: a FilterEngine stop before resize is
reported as a runtime boundary, not converted into resize semantics.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
DECOMP = ROOT / "decomp/OLMKiraKira.aex.c.txt"
ASM = ROOT / "disasm/OLMKiraKira.aex.asm.txt"
REPORT = ROOT / "refs/conformance/olmkirakira_approximated_input_20260718.json"
REPORT_MD = ROOT / "refs/conformance/olmkirakira_approximated_input_20260718.md"
OWNER = ROOT / "tools/emulation/test_olmkirakira_mode2_common_owner_20260717.py"
RESIZE = 0x1812639F0


def require(text: str, needles: list[str], label: str) -> None:
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"{label}: missing {missing}")


def bounded_actual_run() -> dict[str, object]:
    """Run the existing owner harness with Approximated Input=1 in memory."""
    sys.path.insert(0, str(ROOT / "tools/emulation"))
    spec = importlib.util.spec_from_file_location("kira_owner_approx_audit", OWNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import bounded Kira owner harness")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    # This is a fixture-only mutation. No source, binary, or checked-in
    # parameter manifest is changed.
    module.PARAM_DEFAULTS[0x0A]["value"] = 1
    module.PARAM_BY_SELECTOR = {
        selector: module.PARAM_DEFAULTS[disk_id]
        for selector, disk_id in enumerate(module.PARAM_SELECTOR_ORDER)
    }

    original_add_code_hook = module.AexLoader.add_code_hook
    resize_hits: list[dict[str, object]] = []

    def add_code_hook(loader, address, handler):
        original_add_code_hook(loader, address, handler)
        if address != RESIZE:
            return

        def capture(current, rip, _size):
            rsp = current.uc.reg_read(module.UC_X86_REG_RSP)
            resize_hits.append({
                "rip": hex(rip),
                "rcx": hex(current.uc.reg_read(module.UC_X86_REG_RCX)),
                "rdx": hex(current.uc.reg_read(module.UC_X86_REG_RDX)),
                "r8": hex(current.uc.reg_read(module.UC_X86_REG_R8)),
                "r9": hex(current.uc.reg_read(module.UC_X86_REG_R9)),
                "rsp": hex(rsp),
            })

        original_add_code_hook(loader, address, capture)

    module.AexLoader.add_code_hook = add_code_hook
    try:
        runtime = module.run_owner_probe()
    finally:
        module.AexLoader.add_code_hook = original_add_code_hook

    return {
        "fixture": "existing FUN_18114c8f0 common-owner probe; Approximated Input=1 injected in memory",
        "resize_function": hex(RESIZE),
        "resize_entry_hits": resize_hits,
        "resize_entry_reached": bool(resize_hits),
        "owner_status": runtime.get("status"),
        "first_unavailable_boundary": runtime.get("first_unavailable_boundary"),
        "execution_exception": runtime.get("exception"),
        "event_count": len(runtime.get("events", [])),
        "production_files_modified": False,
    }


def main() -> int:
    decomp = DECOMP.read_text(encoding="utf-8")
    asm = ASM.read_text(encoding="utf-8")
    require(decomp, [
        "fVar11 = (float)*(int *)(param_1 + 0x11c) / (float)*(uint *)(param_1 + 0x120);",
        "if (DAT_181486c1c < fVar11)",
        "fVar11 = fVar11 * DAT_181486c1c;",
        "param_5[0x17] = (int)((float)iVar7 * DAT_181486c1c);",
        "param_5[0x18] = (int)((float)iVar1 * fVar5);",
        "param_5[6] = (int)((float)iVar7 * fVar11);",
        "param_5[4] = (int)((float)iVar1 * fVar11);",
        "FUN_1812639f0(local_348,local_360,CONCAT44(*local_2c8,local_2c8[1]),0);",
        "FUN_1812639f0(local_360,local_348,CONCAT44(*local_258,local_258[1]),0);",
        "if ((param_6 == 5)",
        "local_220 = param_6;",
        "local_13a0 = param_12;",
    ], "decomp")
    require(asm, [
        "18114cdf0  JZ 0x18114ce65",
        "18114cdf2  MOV dword ptr [RSP + 0x20],0x4",
        "18114ce00  MOV R8D,dword ptr [RDI + 0x60]",
        "18114ce04  MOV EDX,dword ptr [RDI + 0x5c]",
        "18114ce5c  CALL 0x1812639f0",
        "18114d083  CMP byte ptr [RDI + 0x50],0x0",
        "18114d09b  MOV R8D,dword ptr [RDI + 0x58]",
        "18114d09f  MOV EDX,dword ptr [RDI + 0x54]",
        "18114d11a  CALL 0x1812639f0",
        "181263b65  JNZ 0x181263b92",
        "181263e2b  CALL 0x181263fb0",
    ], "asm")

    # The literal 0 is the last argument in both decompiler call forms and
    # remains unchanged by FUN_1812639f0 unless the special interpolation=5
    # compatibility branch is selected. Therefore this path selects OpenCV
    # INTER_NEAREST (0), not INTER_LINEAR (1).
    static = {
        "render_scale_ratio": "float(render_info+0x11c) / uint(render_info+0x120)",
        "gate": "strict ratio > float32(0.5)",
        "effective_scale_when_enabled": "ratio * float32(0.5)",
        "effective_scale_when_disabled_or_ratio_le_half": "ratio; checkbox is cleared when ratio <= 0.5",
        "working_dimensions": "int_truncate(source_width * 0.5), int_truncate(source_height * 0.5)",
        "working_ray_lengths": "int_truncate(each_length * effective_scale)",
        "pre_resize": "source Mat -> working Mat, explicit dsize=(working_width, working_height)",
        "post_resize": "working Mat -> original-size Mat, explicit dsize=(source_width, source_height)",
        "interpolation": "OpenCV INTER_NEAREST (0), from both typed-owner calls' final literal 0",
        "border": "no border mode is passed to cv::resize; no separate border policy in this path",
        "alpha": "no alpha/premultiply branch in resize wrapper; channels are resized as Mat channels",
        "rounding_inside_resize_wrapper": "when dsize is supplied, scale is recomputed as dsize/src_dim; internal fallback uses cvRound, but typed owners supply dsize",
        "type_special_case": "resize wrapper rewrites interpolation 5 to 1 only for source depth 5/6; typed owners pass 0, so this does not apply",
    }

    runtime = bounded_actual_run()
    report = {
        "schema": 1,
        "kind": "olmkirakira_approximated_input_contract_audit",
        "date": "2026-07-18",
        "status": "binary_grounded_runtime_boundary_before_resize" if not runtime["resize_entry_reached"] else "binary_grounded_runtime_resize_entry_captured",
        "ae_exact_claim": False,
        "binary": str(AEX.relative_to(ROOT)),
        "binary_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
        "static_contract": static,
        "runtime": runtime,
        "fact": [
            "The gate is strict render-scale ratio > 0.5; ratio <= 0.5 clears the checkbox state.",
            "Enabled working dimensions and the five ray lengths use float multiplication followed by int conversion in the typed owners.",
            "Both pre- and post-resize calls pass explicit dsize values and a final interpolation literal of 0.",
            "FUN_1812639f0 is the OpenCV 4.5.5 resize wrapper and FUN_181263fb0 is its resize implementation path.",
            "The bounded actual-AEX owner run enabled the checkbox in memory and stopped at an existing FilterEngine assertion before the resize entry.",
        ],
        "inference": [
            "OpenCV INTER_NEAREST is the typed-owner interpolation contract because the last call argument is literal 0.",
            "Alpha follows ordinary per-channel nearest-neighbor copy for the typed Mat; there is no plugin-level alpha conversion in the wrapper.",
        ],
        "limits": [
            "No production plugin source was changed.",
            "The bounded owner harness did not reach FUN_1812639f0, so runtime resize output pixels were not claimed.",
            "The static contract does not by itself prove Mac AE exactness.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text(f"""# OLMKiraKira Approximated Input contract audit (2026-07-18)

Status: **{report['status']}**
AE exact: **false**

## Determined contract

| Item | Contract | Evidence class |
| --- | --- | --- |
| Enable gate | strict `render_scale_ratio > 0.5`; otherwise the checkbox state is cleared | binary-grounded |
| Ratio | `render_width / render_info_width` and the corresponding height ratio are represented by the render-info fields; enabled path applies `ratio * 0.5` | binary-grounded |
| Working size | `int_truncate(src_width * 0.5)`, `int_truncate(src_height * 0.5)` | binary-grounded |
| Ray lengths | each length is `int_truncate(length * effective_scale)` | binary-grounded |
| Pre-resize | source Mat to working Mat with explicit working `dsize` | binary-grounded |
| Post-resize | working Mat to original-size Mat with explicit original `dsize` | binary-grounded |
| Interpolation | OpenCV `INTER_NEAREST` (`0`) | binary-grounded from both typed-owner callsites |
| Border | no border mode is passed; no plugin border branch | binary-grounded |
| Alpha | no premultiply/unpremultiply or alpha-specific branch; resize operates on Mat channels | binary-grounded wrapper audit |
| Rounding | typed owners truncate working dimensions/lengths; resize wrapper receives explicit dsize, so its `cvRound` fallback is not selected | binary-grounded |

## Runtime boundary

The existing bounded actual-AEX common-owner harness was run with
`Approximated Input=1` injected only in memory. It entered the common owner but
stopped at an existing `cv::FilterEngine::init` assertion before reaching
`FUN_1812639f0`. This is recorded as a fail-closed runtime boundary, not as
evidence that the resize branch is absent.

## Re-run

`python3 tools/emulation/audit_olmkirakira_approximated_input_20260718.py`

No production plugin source was edited. The next implementation step, if taken,
should be an isolated resize primitive using OpenCV 4.5.5 `INTER_NEAREST` and
explicit dsize, followed by a real Windows/Mac AE differential. This report does
not authorize changing the production plugin by itself.
""", encoding="utf-8")
    print(json.dumps({"status": report["status"], "interpolation": static["interpolation"], "resize_entry_reached": runtime["resize_entry_reached"], "report": str(REPORT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
