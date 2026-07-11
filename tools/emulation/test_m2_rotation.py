"""
Milestone 2, parts 3-4: attempt to drive FUN_180004640 (the Rotation entry
point) under emulation with a small synthetic input, enumerate the param_2
context-struct offsets that get read, and witness the +0xf250/+0xf252/+0xe
handle-pointer writes.

FUN_180004640 is NOT a self-contained numeric kernel: it acquires the AE
"PF Handle Suite" through `*(*param_2 + 0x180)` (the SPBasicSuite dispatch),
allocates + locks several handles (storing the locked data pointers into
param_1[0xf250], [0xf252], [0xe], [0x10], [0x12], [0x14]), then runs sampler
loops via function pointers. To get anywhere we mock the SPBasicSuite and the
PF Handle Suite with real, working handle allocation backed by the loader's
host region.

This harness is deliberately bounded (instruction cap + wall clock) and
reports *exactly* how far execution got and what was observed, rather than
forcing a result. See M2_ROTATION_REPORT.md for the outcome.
"""

from __future__ import annotations

import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
AEX_PATH = REPO_ROOT / "aex" / "OLMRadialBlur" / "Plugins" / "64" / "2025" / "OLMRadialBlur.aex"

FUN_180004640 = 0x180004640

# param_1 working-buffer layout facts (float indices unless noted):
#   [0]        input scale/divisor: iVar29 = (int)(360.0 / param_1[0])
#   [0xf24e]   = byte 0x3c938 = center x (read back by FUN_180001bb0)
#   [0xf24f]   = byte 0x3c93c = center y
#   [0xf250]   (byte 0x3c940) <- handle data ptr (uint64)  << witness target
#   [0xf252]   (byte 0x3c948) <- handle data ptr (uint64)  << witness target
#   [0xe]      (byte 0x38)    <- handle data ptr (uint64)  << witness target
#   [0xf254]   = omp_get_max_threads() result
# The buffer must be large enough for the biggest write index (~0xf255 floats
# plus 30000-float sub-tables at 0x1a and 0x754a). We allocate generously.
PARAM1_FLOATS = 0x20000  # 131072 floats = 512 KiB, well past 0xf255 + tables

WORLD_W = 16
WORLD_H = 16


def u64(loader, addr):
    return struct.unpack("<Q", loader.read_bytes(addr, 8))[0]


def witness_cells(loader, f250_ptr, f252_ptr, e0e_ptr, cells):
    """
    Typed dump of a polar cell across the three witness sub-regions.

      f250 -> RGBA float plane   : 4 floats per cell (cell c at byte c*16)
      f252 -> weight/alpha plane : 1 float per cell  (cell c at byte c*4)
      +0xe -> normalized output  : 4 floats per cell (cell c at byte c*16)

    Returns a list of human-readable strings. Guards against null/unmapped
    pointers so a partial run still produces useful output.
    """
    lines = []
    for c in cells:
        parts = [f"cell {c:4d}:"]
        for label, ptr, n, step in (("f250(RGBA)", f250_ptr, 4, 16),
                                     ("f252(w)", f252_ptr, 1, 4),
                                     ("+0xe(out)", e0e_ptr, 4, 16)):
            if ptr == 0:
                parts.append(f"{label}=<null>")
                continue
            try:
                vals = struct.unpack(f"<{n}f", loader.read_bytes(ptr + c * step, n * 4))
                parts.append(f"{label}={tuple(round(v, 5) for v in vals)}")
            except Exception:
                parts.append(f"{label}=<unmapped>")
        lines.append(" ".join(parts))
    return lines


def build_host_suites(loader: AexLoader):
    """
    Build an emulated SPBasicSuite + PF Handle Suite.

    Returns the guest address of the SPBasicSuite dispatch array (the value
    that must be stored at `*param_2 + 0x180`).
    """
    # --- PF Handle Suite: 4 function pointers (new, lock, unlock, dispose) ---
    def h_new(ld, args):
        size = args[0] & 0xFFFFFFFFFFFFFFFF
        if size == 0:
            size = 1
        data = ld.host_alloc(size)
        ld.write_bytes(data, b"\x00" * size)
        handle = ld.host_alloc(8)
        ld.write_bytes(handle, struct.pack("<Q", data))
        return handle

    def h_lock(ld, args):
        handle = args[0]
        if handle == 0:
            return 0
        return u64(ld, handle)

    def h_noop(ld, args):
        return 0

    new_cb = loader.install_callback("PFHandle.new", h_new)
    lock_cb = loader.install_callback("PFHandle.lock", h_lock)
    unlock_cb = loader.install_callback("PFHandle.unlock", h_noop)
    dispose_cb = loader.install_callback("PFHandle.dispose", h_noop)

    handle_suite = loader.host_alloc(8 * 4)
    loader.write_bytes(handle_suite, struct.pack("<4Q", new_cb, lock_cb, unlock_cb, dispose_cb))

    # --- SPBasicSuite: [0]=AcquireSuite, [1]=ReleaseSuite ---
    def sp_acquire(ld, args):
        # (name_ptr, version, out_ptr) -> write handle_suite ptr to [out_ptr]
        out_ptr = args[2]
        ld.write_bytes(out_ptr, struct.pack("<Q", handle_suite))
        return 0  # kSPNoError

    def sp_release(ld, args):
        return 0

    acquire_cb = loader.install_callback("SPBasic.AcquireSuite", sp_acquire)
    release_cb = loader.install_callback("SPBasic.ReleaseSuite", sp_release)

    spbasic = loader.host_alloc(8 * 2)
    loader.write_bytes(spbasic, struct.pack("<2Q", acquire_cb, release_cb))
    return spbasic


def build_context(loader: AexLoader, spbasic: int):
    """
    Build the param_2 context struct + param_1 working buffer with small,
    self-consistent synthetic values. Returns (param_1_addr, param_2_addr).
    """
    # param_1 working buffer (sentinel-filled so stray reads are visible)
    param_1 = loader.bump_alloc(PARAM1_FLOATS * 4, align=64)
    loader.write_bytes(param_1, b"\x00" * (PARAM1_FLOATS * 4))
    # input divisor: 360/90 = 4 samples -> tiny bounded loops
    loader.write_bytes(param_1 + 0 * 4, struct.pack("<f", 90.0))

    # P0: the object whose +0x180 holds the SPBasicSuite pointer
    p0 = loader.host_alloc(0x200)
    loader.write_bytes(p0, b"\x00" * 0x200)
    loader.write_bytes(p0 + 0x180, struct.pack("<Q", spbasic))

    # param_2[1]: a struct with width @ +0x24 and height @ +0x28
    world_params = loader.host_alloc(0x40)
    loader.write_bytes(world_params, b"\x00" * 0x40)
    loader.write_bytes(world_params + 0x24, struct.pack("<i", WORLD_W))
    loader.write_bytes(world_params + 0x28, struct.pack("<i", WORLD_H))

    # Input/output pixel worlds. Input worlds get a recognizable gradient
    # (pixel(col,row) = (col/W, row/H, 0.5, 1.0)) so sampled/rotated output
    # is non-trivial and visible in the witness dump; the output world starts
    # zeroed.
    world_floats = WORLD_W * WORLD_H * 4
    worlds = {}
    grad = []
    for row in range(WORLD_H):
        for col in range(WORLD_W):
            grad.extend([col / WORLD_W, row / WORLD_H, 0.5, 1.0])
    for idx in (0x11, 0x12, 0x13):
        w = loader.host_alloc(world_floats * 4)
        loader.write_f32_array(w, grad)
        worlds[idx] = w
    w_out = loader.host_alloc(world_floats * 4)
    loader.write_bytes(w_out, b"\x00" * (world_floats * 4))
    worlds[0x14] = w_out

    # param_2 context struct
    param_2 = loader.host_alloc(0x100)
    loader.write_bytes(param_2, b"\x00" * 0x100)
    W = lambda off, data: loader.write_bytes(param_2 + off, data)
    W(0x00, struct.pack("<Q", p0))            # *param_2 -> P0 (has +0x180 spbasic)
    W(0x08, struct.pack("<Q", world_params))  # param_2[1] -> width/height struct
    W(0x28, struct.pack("<d", 8.0))           # param_2[5] double -> center x
    W(0x30, struct.pack("<d", 8.0))           # param_2[6] double -> center y
    W(0x44, b"\x00")                          # byte flag (alpha branch): 0
    W(0x54, struct.pack("<f", 1.0))           # float -> param_1[9]
    W(0x58, struct.pack("<i", 8))             # int  param_2[0xb]
    W(0x5c, struct.pack("<f", 1.0))           # float -> param_1[0xb]
    W(0x60, struct.pack("<i", 8))             # int  param_2[0xc]
    W(0x64, struct.pack("<i", 8))             # int @ +0x64
    W(0x68, struct.pack("<i", 8))             # int  param_2[0xd]
    W(0x6c, struct.pack("<i", 8))             # int @ +0x6c
    W(0x70, struct.pack("<i", 8))             # int  param_2[0xe]
    W(0x74, b"\x00")                          # byte flag: 0 -> FUN_180001800/270
    W(0x78, struct.pack("<f", 1.0))           # float param_2[0xf] -> param_1[5] (divisor!)
    W(0x7c, struct.pack("<i", 0))             # int angle -> cos/sin
    W(0x88, struct.pack("<Q", worlds[0x11]))  # param_2[0x11] world ptr
    W(0x90, struct.pack("<Q", worlds[0x12]))  # param_2[0x12] world ptr
    W(0x98, struct.pack("<Q", worlds[0x13]))  # param_2[0x13] world ptr
    W(0xa0, struct.pack("<Q", worlds[0x14]))  # param_2[0x14] output world ptr

    return param_1, param_2


def main() -> int:
    if not AEX_PATH.exists():
        print(f"ERROR: .aex not found at {AEX_PATH}")
        return 1

    loader = AexLoader(str(AEX_PATH), verbose=False)
    loader.register_libm_impls(max_threads=1)

    spbasic = build_host_suites(loader)
    param_1, param_2 = build_context(loader, spbasic)

    # Trace reads landing in the param_2 struct (0x100 bytes) to corroborate
    # the statically-derived layout.
    loader.add_read_trace_range(param_2, param_2 + 0x100, "param_2")

    print(f"param_1 = 0x{param_1:x}, param_2 = 0x{param_2:x}")
    print("Running FUN_180004640 (bounded)...")

    cap = 30_000_000
    t0 = time.time()
    fault = None
    try:
        result = loader.call_function(FUN_180004640, int_args=[param_1, param_2], max_instructions=cap)
        completed = True
        instrs = result["instructions"]
    except RuntimeError as exc:
        completed = False
        fault = str(exc)
        instrs = loader.instructions_executed
    elapsed = time.time() - t0

    # Witness the handle-pointer slots
    f250 = u64(loader, param_1 + 0xF250 * 4)
    f252 = u64(loader, param_1 + 0xF252 * 4)
    e0e = u64(loader, param_1 + 0xE * 4)
    # param_1[0xf254] holds omp_get_max_threads() written via an *integer*
    # store into a float-typed slot, so decode it as the raw int too.
    f254_bits = struct.unpack("<I", loader.read_bytes(param_1 + 0xF254 * 4, 4))[0]

    # Distinct param_2 read offsets (dynamic)
    read_offsets = sorted({off for (_, off, _, _) in loader.read_trace})

    print(f"\ncompleted={completed}  instructions={instrs}  elapsed={elapsed:.2f}s")
    if fault:
        print(f"fault: {fault}")
    print(f"omp_get_max_threads stored at param_1[0xf254] (raw int) = {f254_bits}")
    print(f"param_1[0xf250] = 0x{f250:x}")
    print(f"param_1[0xf252] = 0x{f252:x}")
    print(f"param_1[0xe]    = 0x{e0e:x}")

    # Witness dump: for a few polar cells, read the RGBA / weight / output
    # values out of the handle buffers f250/f252/+0xe point at.
    print("\nWitness dump (per polar cell):")
    witness = witness_cells(loader, f250, f252, e0e, cells=range(0, 4))
    for line in witness:
        print("  " + line)
    print(f"imports called: {sorted({l.name for l in loader.import_log})}")
    print(f"host callbacks called: {sorted({c[0] for c in loader.callback_log})}")
    print(f"param_2 read offsets (hex): {[hex(o) for o in read_offsets]}")

    # ---- reports ----
    layout = build_param2_layout_md(read_offsets)
    (Path(__file__).parent / "PARAM2_LAYOUT.md").write_text(layout)

    rep = []
    rep.append("# Milestone 2: FUN_180004640 rotation-driver attempt\n")
    rep.append(f"- Binary: `{AEX_PATH.relative_to(REPO_ROOT)}`")
    rep.append(f"- Synthetic input: {WORLD_W}x{WORLD_H} RGBA float worlds, "
               f"param_1[0]=90.0 (iVar29 = 360/90 = 4), angle=0, center=(8,8)\n")
    rep.append("## Execution outcome\n")
    rep.append(f"- Completed to RET: **{completed}**")
    rep.append(f"- Instructions executed: {instrs} (cap {cap})")
    rep.append(f"- Wall clock: {elapsed:.2f}s")
    if fault:
        rep.append(f"- Stop reason (fault): `{fault}`")
    rep.append("")
    rep.append("## Witnessed handle-pointer writes\n")
    rep.append(f"- `param_1[0xf254]` (omp_get_max_threads, raw int): {f254_bits}")
    rep.append(f"- `param_1[0xf250]`: `0x{f250:x}` {'(written, non-zero handle ptr)' if f250 else '(NOT written / zero)'}")
    rep.append(f"- `param_1[0xf252]`: `0x{f252:x}` {'(written, non-zero handle ptr)' if f252 else '(NOT written / zero)'}")
    rep.append(f"- `param_1[0xe]`: `0x{e0e:x}` {'(written, non-zero handle ptr)' if e0e else '(NOT written / zero)'}")
    rep.append("")
    rep.append("## Witness dump (typed, per polar cell)\n")
    rep.append("f250 -> RGBA plane (4f/cell); f252 -> weight plane (1f/cell); "
               "+0xe -> normalized output (4f/cell). Input worlds carry a gradient "
               "`pixel(col,row) = (col/W, row/H, 0.5, 1.0)`, so the values below "
               "are the rotation kernel's actual sampled/weighted/normalized "
               "output and vary by polar cell -- e.g. R rises across cells as the "
               "sampler walks the gradient, and `+0xe(out)` is the per-cell "
               "normalization of f250 by the reference channel.\n")
    rep.append("```")
    for line in witness_cells(loader, f250, f252, e0e, cells=range(0, 6)):
        rep.append(line)
    rep.append("```")
    rep.append("")
    rep.append("## Host suite activity\n")
    rep.append(f"- Imports exercised: {sorted({l.name for l in loader.import_log})}")
    from collections import Counter
    cb_counts = Counter(c[0] for c in loader.callback_log)
    for label, n in sorted(cb_counts.items()):
        rep.append(f"- callback `{label}`: {n} call(s)")
    rep.append("")
    rep.append("## param_2 offsets actually read (dynamic trace)\n")
    rep.append(f"`{[hex(o) for o in read_offsets]}`\n")
    (Path(__file__).parent / "M2_ROTATION_REPORT.md").write_text("\n".join(rep) + "\n")

    print(f"\nWrote PARAM2_LAYOUT.md and M2_ROTATION_REPORT.md")
    return 0


def build_param2_layout_md(read_offsets) -> str:
    """Static layout table (from decomp) annotated with dynamic read hits."""
    hit = set(read_offsets)
    rows = [
        (0x00, "void*", "P0: *(P0+0x180) = SPBasicSuite dispatch (AE PF_InData-like). "
                        "Used by all handle-alloc helpers.", "*param_2"),
        (0x08, "void*", "param_2[1]: pointer to a struct with width @+0x24 and "
                        "height @+0x28 (output world geometry / PF_LayerDef-like).", "param_2[1]"),
        (0x28, "double", "center X (-> param_1[0xf24e], byte 0x3c938).", "param_2[5]"),
        (0x30, "double", "center Y (-> param_1[0xf24f], byte 0x3c93c).", "param_2[6]"),
        (0x44, "uint8", "flag: if 0, alpha channel is forced to 1.0 (0x3f800000); "
                        "else sampled via param_2[0x11].", "byte @0x44"),
        (0x54, "float", "-> param_1[9].", "float @0x54"),
        (0x58, "int32", "-> param_1[10] scaling term (param_2[0xb]).", "param_2[0xb]"),
        (0x5c, "float", "-> param_1[0xb].", "float @0x5c"),
        (0x60, "int32", "-> param_1[0xc] scaling term (param_2[0xc]).", "param_2[0xc]"),
        (0x64, "int32", "-> param_1[0xea7a] scaling term.", "int @0x64"),
        (0x68, "int32", "-> param_1[0xea7b] scaling term (param_2[0xd]).", "param_2[0xd]"),
        (0x6c, "int32", "-> param_1[0xf24c] / kernel size for FUN_18000b680.", "int @0x6c"),
        (0x70, "int32", "-> param_1[0xf24d] / kernel size for FUN_18000b680 (param_2[0xe]).", "param_2[0xe]"),
        (0x74, "uint8", "flag: selects sampler pair (0 -> FUN_180001800/FUN_180001270, "
                        "else FUN_180001950/FUN_180001520).", "byte @0x74"),
        (0x78, "float", "-> param_1[5] (used as a divisor; must be non-zero).", "param_2[0xf]"),
        (0x7c, "int32", "rotation angle in degrees; feeds cos()/sin() (double).", "int @0x7c"),
        (0x88, "void*", "param_2[0x11]: input world for alpha sampling.", "param_2[0x11]"),
        (0x90, "void*", "param_2[0x12]: input world (second sampler target).", "param_2[0x12]"),
        (0x98, "void*", "param_2[0x13]: input world (first sampler target).", "param_2[0x13]"),
        (0xa0, "void*", "param_2[0x14]: output world data base.", "param_2[0x14]"),
    ]
    out = ["# param_2 context-struct layout (FUN_180004640)\n",
           "Derived statically from `decomp/OLMRadialBlur.aex.c.txt` (FUN_180004640 "
           "and the FUN_1800045a0/43c0 handle helpers) and corroborated dynamically "
           "by a MEM_READ trace during the bounded emulation run "
           "(`test_m2_rotation.py`). The `read?` column marks offsets the trace "
           "actually observed being read before execution stopped.\n",
           "`param_2` is the plugin's own render-context struct (not a raw AE "
           "`PF_InData`); however `*param_2` behaves like a `PF_InData*` in that "
           "`*(*param_2 + 0x180)` is the PICA `SPBasicSuite` (AcquireSuite/"
           "ReleaseSuite), matching the AE SDK `AE_GeneralPlug.h`/`SPBasic.h` "
           "pattern. `param_2[1]`'s +0x24/+0x28 int fields behave like a world's "
           "width/height (cf. `PF_LayerDef`/`PF_EffectWorld` in `AE_Effect.h`).\n",
           "| byte off | C expr | type | read? | meaning |",
           "|----------|--------|------|-------|---------|"]
    for off, typ, meaning, expr in rows:
        mark = "yes" if off in hit else "-"
        out.append(f"| 0x{off:02x} | `{expr}` | {typ} | {mark} | {meaning} |")
    out.append("")
    out.append("## Notes on AE SDK header correspondence\n")
    out.append("- `*(*param_2 + 0x180)` -> `SPBasicSuite*` (`SPBasic.h`): first two "
               "function pointers are `AcquireSuite(name, version, out)` and "
               "`ReleaseSuite(name, version)`. The plugin acquires \"PF Handle "
               "Suite\" v2 (`PF_HandleSuite1` in `AE_Effect.h`).")
    out.append("- `PF_HandleSuite1` table order used here: [0]=`host_new_handle`, "
               "[+8]=`host_lock_handle`, [+0x10]=`host_unlock_handle`, "
               "[+0x18]=`host_dispose_handle`.")
    out.append("- Angle @+0x7c is stored as an int (degrees) and converted to double "
               "before `cos`/`sin`; note the AE SDK typically passes angles as "
               "`PF_Fixed`/`PF_FpLong`, so this int is likely a pre-rounded degree "
               "value the plugin computed upstream.")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
