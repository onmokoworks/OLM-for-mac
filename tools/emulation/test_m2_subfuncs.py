"""
Milestone 2, parts 1-2: verify the two sub-functions that FUN_180004640
depends on, plus the libm import wiring, using the M1 "small input +
independent Python reference" strategy.

  - FUN_18000b680 (@ 0x18000b680): builds a Gaussian-like kernel array,
    out[i] = expf(-(i*i) / (2*(n*n)/9 + 1e-5)), for i in [0, n). With the
    default CPU-feature flag DAT_18002b180 == 1 the function takes its scalar
    `expf` fallback path (verified by reading the binary's .data), so it
    exercises the `expf` import we register here. Constants recovered from
    the mapped image: DAT_180021738 = 1/9 (0.11111f), DAT_180021740 = 1e-5,
    DAT_1800212d4 = 1.0f.

  - FUN_180001bb0 (@ 0x180001bb0): reads a center coordinate (cx, cy) stored
    in the big working buffer at byte offsets +0x3c938 / +0x3c93c, plus
    width/height ints, and writes two integer "corner distance" radii. No
    imports. Cross-checked against a pure-Python transliteration of the
    decomp (lines for FUN_180001bb0).

Run:  tools/emulation/.venv/bin/python tools/emulation/test_m2_subfuncs.py
"""

from __future__ import annotations

import math
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
AEX_PATH = REPO_ROOT / "aex" / "OLMRadialBlur" / "Plugins" / "64" / "2025" / "OLMRadialBlur.aex"

FUN_18000b680 = 0x18000B680
FUN_180001bb0 = 0x180001BB0

CX_OFFSET = 0x3C938
CY_OFFSET = 0x3C93C


def f32(x: float) -> float:
    """Round a Python float to float32 precision."""
    return struct.unpack("<f", struct.pack("<f", x))[0]


def ref_gaussian(n: int) -> list:
    """Independent re-implementation of FUN_18000b680's scalar path."""
    if n <= 0:
        return []
    v = f32(f32(f32(n) * f32(n)) * f32(0.111111119389534))  # n*n * (1/9), all f32
    v = f32((v + v) + 1e-05)  # (v+v) f32, +1e-5 in double, back to f32
    inv = f32(1.0 / v)
    out = []
    for i in range(n):
        arg = f32(f32(-(i * i)) * inv)
        out.append(f32(math.exp(arg)))
    return out


def ref_bb0(cx: float, cy: float, w: int, h: int):
    """Independent re-implementation of FUN_180001bb0."""
    # x axis
    fx = cx
    fw = float(w)
    dx_perp = 0.0
    if 0.0 <= fx:
        if fx < fw:
            dx_perp = 0.0
            if fx <= float(w // 2):
                fx = fw - fx
        else:
            dx_perp = fx - fw
    else:
        dx_perp = -fx  # xor sign bit == negate
        fx = fw - fx

    # y axis
    fy = cy
    fh = float(h)
    dy_perp = 0.0
    reached_lab = False
    if 0.0 <= fy:
        if fh <= fy:
            dy_perp = fy - fh
            reached_lab = True
        elif float(h // 2) < fy:
            reached_lab = True
    else:
        dy_perp = -fy
    if not reached_lab:
        fy = fh - fy

    r1 = int(math.sqrt(dy_perp * dy_perp + dx_perp * dx_perp))
    r2 = int(math.sqrt(fy * fy + fx * fx))
    return r1, r2


def check_gaussian(loader: AexLoader, report: list) -> bool:
    print("\n=== M2 Check A: FUN_18000b680 (Gaussian kernel builder, expf path) ===")
    n = 8
    buf = loader.bump_alloc((n + 4) * 4, align=16)
    loader.write_bytes(buf, b"\xAA" * ((n + 4) * 4))

    result = loader.call_function(FUN_18000b680, int_args=[buf, n])
    got = loader.read_f32_array(buf, n)
    expected = ref_gaussian(n)

    max_abs = max(abs(g - e) for g, e in zip(got, expected))
    ok = max_abs <= 1e-6
    imports = sorted({l.name for l in loader.import_log})

    print(f"  n = {n}, buffer = 0x{buf:x}")
    print(f"  expected = {[round(v, 6) for v in expected]}")
    print(f"  got      = {[round(v, 6) for v in got]}")
    print(f"  max abs diff = {max_abs:.3e}")
    print(f"  imports called = {imports}")
    print(f"  instructions = {result['instructions']}")
    print(f"  RESULT: {'PASS' if ok else 'FAIL'}")

    report.append("## M2 Check A: FUN_18000b680 (Gaussian kernel builder)\n")
    report.append(f"- n = {n}, scalar `expf` path (DAT_18002b180 == 1)")
    report.append(f"- Expected (independent Python ref): `{[round(v, 6) for v in expected]}`")
    report.append(f"- Got (emulator): `{[round(v, 6) for v in got]}`")
    report.append(f"- Max abs diff: {max_abs:.3e}")
    report.append(f"- Imports exercised: {imports}")
    report.append(f"- Instructions: {result['instructions']}")
    report.append(f"- **Result: {'PASS' if ok else 'FAIL'}**\n")
    return ok


def check_bb0(loader: AexLoader, report: list) -> bool:
    print("\n=== M2 Check B: FUN_180001bb0 (corner-distance radii) ===")
    buf = loader.bump_alloc(CY_OFFSET + 0x100, align=16)
    out_r1 = loader.bump_alloc(4)
    out_r2 = loader.bump_alloc(4)

    cases = [
        (10.0, 20.0, 100, 50),   # center inside, near left/top
        (90.0, 5.0, 100, 50),    # right-ish, top
        (-8.0, 60.0, 100, 50),   # outside left, below bottom
        (50.0, 25.0, 100, 50),   # dead center
    ]

    all_ok = True
    rows = []
    for (cx, cy, w, h) in cases:
        loader.write_bytes(buf + CX_OFFSET, struct.pack("<f", cx))
        loader.write_bytes(buf + CY_OFFSET, struct.pack("<f", cy))
        loader.write_bytes(out_r1, b"\x00\x00\x00\x00")
        loader.write_bytes(out_r2, b"\x00\x00\x00\x00")
        loader.call_function(FUN_180001bb0, int_args=[buf, w, h, out_r1, out_r2])
        g1 = struct.unpack("<i", loader.read_bytes(out_r1, 4))[0]
        g2 = struct.unpack("<i", loader.read_bytes(out_r2, 4))[0]
        e1, e2 = ref_bb0(cx, cy, w, h)
        ok = (g1, g2) == (e1, e2)
        all_ok = all_ok and ok
        rows.append((cx, cy, w, h, (e1, e2), (g1, g2), ok))
        print(f"  cx={cx:6}, cy={cy:6}, w={w}, h={h}: expected={(e1,e2)}, got={(g1,g2)}  {'OK' if ok else 'MISMATCH'}")

    print(f"  RESULT: {'PASS' if all_ok else 'FAIL'}")
    report.append("## M2 Check B: FUN_180001bb0 (corner-distance radii)\n")
    report.append("| cx | cy | w | h | expected (r1,r2) | got | ok |")
    report.append("|----|----|---|---|------------------|-----|----|")
    for (cx, cy, w, h, e, g, ok) in rows:
        report.append(f"| {cx} | {cy} | {w} | {h} | {e} | {g} | {'yes' if ok else 'NO'} |")
    report.append(f"\n- **Result: {'PASS' if all_ok else 'FAIL'}**\n")
    return all_ok


def main() -> int:
    if not AEX_PATH.exists():
        print(f"ERROR: .aex not found at {AEX_PATH}")
        return 1

    report = ["# Milestone 2 sub-function verification\n",
              f"- Binary: `{AEX_PATH.relative_to(REPO_ROOT)}`\n"]

    loader = AexLoader(str(AEX_PATH), verbose=False)
    loader.register_libm_impls(max_threads=1)

    ok_a = check_gaussian(loader, report)
    ok_b = check_bb0(loader, report)

    overall = ok_a and ok_b
    report.append("## Overall\n")
    report.append(f"- Check A (FUN_18000b680): {'PASS' if ok_a else 'FAIL'}")
    report.append(f"- Check B (FUN_180001bb0): {'PASS' if ok_b else 'FAIL'}")
    report.append(f"- **M2 sub-function verification: {'PASS' if overall else 'FAIL'}**")

    out = Path(__file__).parent / "M2_SUBFUNCS_REPORT.md"
    out.write_text("\n".join(report) + "\n")
    print(f"\nWrote {out}")
    print(f"\n=== OVERALL: {'PASS' if overall else 'FAIL'} ===")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
