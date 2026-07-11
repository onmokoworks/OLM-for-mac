"""Bounded Unicorn helper witness for OLMBlur 16bpc case_0006.

The 16bpc Non-Legacy complete worker is FUN_180002280; the Legacy worker is
FUN_180005f20. This witness calls the grounded Non-Legacy blur helpers
FUN_180001000 and FUN_180001980 directly. Their ABIs are the decompiler
signatures; stack arguments are marshalled by AexLoader.call_function.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
AEX_PATH = REPO_ROOT / "plugins_2025" / "OLMBlur.aex"
FUN_OLMBLUR_16BPC_ENTRY = 0x180002280
FUN_OLMBLUR_NONLEGACY_HORIZONTAL = 0x180001000
FUN_OLMBLUR_NONLEGACY_VERTICAL = 0x180001980


def alloc_f32(loader: AexLoader, values: list[float]) -> int:
    addr = loader.bump_alloc(4 * len(values), align=16)
    loader.write_bytes(addr, struct.pack("<%df" % len(values), *values))
    return addr


def alloc_u8(loader: AexLoader, values: list[int]) -> int:
    addr = loader.bump_alloc(len(values), align=16)
    loader.write_bytes(addr, bytes(values))
    return addr


def run_nonlegacy_helpers(loader: AexLoader) -> dict:
    # The actual non-Legacy call sites pass a 3-float RGB plane and a byte
    # active-mask. The values are lifted from synthetic 16bpc words so the
    # arithmetic is observable without pretending this is a PNG render.
    # The helper's flag cursor is offset by width*radius before its first
    # read (visible at FUN_180001000+0x80); leave the surrounding halo mapped.
    flags = alloc_u8(loader, [1] * 64)
    src = alloc_f32(loader, [100.0, 200.0, 300.0, 1000.0, 2000.0, 3000.0,
                             300.0, 600.0, 900.0])
    dst_h = alloc_f32(loader, [0.0] * 30)
    dst_v = alloc_f32(loader, [0.0] * 30)
    weights = alloc_f32(loader, [1.0, 2.0, 1.0])

    # FUN_180001000(p1,p2,p3,p4,uint width,uint height64,uint arg7,
    #                int arg8,int arg9). The call sites construct
    # param_6 with CONCAT44(..., height), so the low dword is height.
    h_result = loader.call_function(
        FUN_OLMBLUR_NONLEGACY_HORIZONTAL,
        int_args=[flags, src, dst_h, weights, 3, 1, 1, 0, 2],
        max_instructions=200_000,
    )
    # FUN_180001980(p1,p2,p3,p4,int width,int height,uint arg7,
    #                int arg8,int arg9), as used by the
    # non-Legacy call sites. This 3x1 case has one vertical row.
    # Two rows make the vertical accumulation observable instead of merely
    # copying one row through the boundary path.
    src_v = alloc_f32(loader, [100.0, 200.0, 300.0, 1000.0, 2000.0, 3000.0,
                               300.0, 600.0, 900.0, 3000.0, 6000.0, 9000.0,
                               500.0, 700.0, 900.0, 5000.0, 7000.0, 9000.0])
    flags_v = alloc_u8(loader, [1] * 64)
    v_result = loader.call_function(
        FUN_OLMBLUR_NONLEGACY_VERTICAL,
        int_args=[flags_v, src_v, dst_v, weights, 3, 3, 3, 2, 2],
        max_instructions=200_000,
    )
    def triplets(addr: int):
        values = struct.unpack("<30f", loader.read_bytes(addr, 120))
        return [list(values[i:i + 3]) for i in range(0, len(values), 3)]
    return {
        "functions": [hex(FUN_OLMBLUR_NONLEGACY_HORIZONTAL), hex(FUN_OLMBLUR_NONLEGACY_VERTICAL)],
        "abi_horizontal": "RCX,RDX,R8,R9 then [RSP+0x28..] = flags,src,dst,weights,width,height64,arg7,arg8,arg9",
        "abi_vertical": "RCX,RDX,R8,R9 then [RSP+0x28..] = flags,src,dst,weights,width,height,arg7,arg8,arg9",
        "input_16bpc_words": [100, 200, 300, 1000, 2000, 3000, 300, 600, 900],
        "input_float_lift": "identity word-to-float for helper isolation",
        "horizontal_output_rgb_triplets": triplets(dst_h),
        "vertical_output_rgb_triplets": triplets(dst_v),
        "horizontal_rax": hex(h_result["rax"]),
        "vertical_rax": hex(v_result["rax"]),
        "instructions": loader.instructions_executed,
    }


def main() -> int:
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    helper = run_nonlegacy_helpers(loader)
    print("FACT nonlegacy_helper_result", helper)
    print("FACT nonlegacy_helpers_are_import_free", not loader.import_log)
    print("FACT full_entry", hex(FUN_OLMBLUR_16BPC_ENTRY))
    print("FACT dg_host_pattern: DistanceGradation uses ctx+0x180 -> SPBasic vtable, AcquireSuite -> PF Handle vtable, new/lock/unlock/dispose callbacks.")
    print("INFERENCE full_entry_scope: the complete Non-Legacy entry is FUN_180002280; this helper witness does not claim case_0006 PNG/store equivalence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
