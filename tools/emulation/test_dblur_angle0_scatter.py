#!/usr/bin/env python3
"""OLMDirectionalBlur angle-0 front-scatter emulation witness.

Drives FUN_180001830 (front table builder, leaf) and FUN_1800013e0 (leftward
front scatter) directly under Unicorn to fact-check the angle-0 (494,169)
R=164->0 miss. Read-only wrt project sources; writes only under tools/emulation.

All findings printed with FACT/OBSERVED labels. No tuning, no PNG matching.
"""
from __future__ import annotations

import math
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
AEX_PATH = REPO_ROOT / "plugins_2025" / "OLMDirectionalBlur.aex"

FUN_TABLE = 0x180001830
FUN_SCATTER = 0x1800013e0

# constants confirmed from data section (see report)
DAT_b1e0 = 1e-05     # f64 add
DAT_b1ec = 3.0       # f32 divisor
DAT_b1e8 = 1.0       # f32 (fVar17 base -> 1.0/param_11)

report = []
def log(s=""):
    print(s)
    report.append(s)


def py_front_table(length):
    """Python reference for FUN_180001830."""
    d = (length / DAT_b1ec) ** 2
    d = d + d + DAT_b1e0
    return [math.exp(-(i * i) / d) for i in range(length)]


def check_table(loader):
    log("## ABI / leaf health: FUN_180001830 (front table builder)")
    ok_all = True
    for length in (4, 8, 16, 32):
        tbl_addr = loader.bump_alloc(length * 4)
        loader.write_f32_array(tbl_addr, [-999.0] * length)
        loader.call_function(FUN_TABLE, int_args=[tbl_addr, length])
        got = loader.read_f32_array(tbl_addr, length)
        ref = py_front_table(length)
        maxdiff = max(abs(a - b) for a, b in zip(got, ref))
        ok = maxdiff < 1e-6
        ok_all &= ok
        log(f"  len={length:3d} maxdiff={maxdiff:.3e} {'PASS' if ok else 'FAIL'}"
            f"  head={['%.5f'%v for v in got[:4]]}")
    log(f"  => table builder ABI health: {'PASS' if ok_all else 'FAIL'}")
    log("")
    return ok_all


def run_scatter(loader, *, src_x, row, width, front_strength, param_11,
                alpha_valid_src=1.0, src_rgb=(1.0, 0.0, 0.0), table_len=None):
    """Drive FUN_1800013e0 once. Returns per-column (B_rgba, denom) dicts.

    Layout: A/B are RGBA (4 f32/pixel) indexed by pixel = row*width + col.
            denom, alpha_or_valid are 1 f32/pixel.
    param_9 (front_strength) is read as int; effective span = int(fs*param_11).
    table index = int(offset * (1.0/param_11)); table needs >= that many entries.
    """
    n_pix = width  # single row is enough (row*width offset applied)
    base_pix = row * width
    total_pix = base_pix + width

    A = loader.bump_alloc(total_pix * 4 * 4)
    B = loader.bump_alloc(total_pix * 4 * 4)
    denom = loader.bump_alloc(total_pix * 4)
    av = loader.bump_alloc(total_pix * 4)

    loader.write_f32_array(A, [0.0] * total_pix * 4)
    loader.write_f32_array(B, [0.0] * total_pix * 4)
    loader.write_f32_array(denom, [0.0] * total_pix)
    loader.write_f32_array(av, [0.0] * total_pix)

    # place source column
    p = base_pix + src_x
    loader.write_f32_array(A + p * 16, [src_rgb[0], src_rgb[1], src_rgb[2], 1.0])
    loader.write_f32_array(av + p * 4, [alpha_valid_src])

    # front table sized generously
    span = int(front_strength * param_11)
    if table_len is None:
        inv = (1.0 / param_11) if param_11 > 0 else 1.0
        table_len = max(4, int(span * inv) + 4, front_strength + 4)
    tbl = loader.bump_alloc(table_len * 4)
    loader.write_f32_array(tbl, [-999.0] * table_len)
    loader.call_function(FUN_TABLE, int_args=[tbl, table_len])

    # param_11 is arg index 10 (11th) -> stack slot; pass raw float bits as int.
    p11_bits = struct.unpack("<I", struct.pack("<f", param_11))[0]
    int_args = [src_x, base_pix, 1, A, B, denom, av, tbl,
                front_strength, width, p11_bits]
    loader.call_function(FUN_SCATTER, int_args=int_args)

    out = {}
    for col in range(width):
        pp = base_pix + col
        rgba = loader.read_f32_array(B + pp * 16, 4)
        dn = loader.read_f32_array(denom + pp * 4, 1)[0]
        if any(abs(v) > 1e-12 for v in rgba) or abs(dn) > 1e-12:
            out[col] = (rgba, dn)
    return {"span": span, "table_len": table_len, "nonzero": out}


def main():
    loader = AexLoader(str(AEX_PATH), verbose=False)
    loader.register_libm_impls(max_threads=1)

    log("# OLMDirectionalBlur angle-0 front-scatter emulation report")
    log(f"# aex: {AEX_PATH}")
    log(f"# constants: DAT_b1e0={DAT_b1e0}(add) DAT_b1ec={DAT_b1ec}(div) "
        f"DAT_b1e8={DAT_b1e8}(1/p11 base)")
    log("")

    table_ok = check_table(loader)

    log("## FUN_1800013e0 scatter behaviour (span / membership / direction)")
    log("Layout confirmed from decomp: A/B = RGBA(4 f32) at pixel (row*W+col);"
        " denom/alpha_or_valid = 1 f32/pixel. param_3=1 => leftward scatter,"
        " iVar11=-1. offset 0 (source col) never written.")
    log("")

    W = 800
    ROW = 169
    SRC = 500  # a source column to the RIGHT of dst 494

    # --- direction + offset-0 test ---
    r = run_scatter(loader, src_x=SRC, row=ROW, width=W,
                    front_strength=32, param_11=1.0)
    cols = sorted(r["nonzero"].keys())
    log(f"### Direction test: src_x={SRC} fs=32 p11=1.0 -> span={r['span']}")
    log(f"  written cols: min={min(cols)} max={max(cols)} count={len(cols)}")
    log(f"  src col {SRC} in written set? {SRC in r['nonzero']} (expect False)")
    log(f"  all written < src? {all(c < SRC for c in cols)} (expect True=leftward)")
    reaches_494 = 494 in r["nonzero"]
    log(f"  reaches dst 494? {reaches_494}"
        f"  (src-494={SRC-494} vs span={r['span']})")
    if 494 in r["nonzero"]:
        log(f"  B[494]={r['nonzero'][494]}")
    log("")

    # --- CANDIDATE 1: span-reach / membership at dst=494 ---
    log("## Candidate 1 (span reach / membership): does a src col >494 reach 494?")
    log("Sweep: fixed src_x, fs=32, vary param_11 to change effective span/reach.")
    log("Reach condition (FACT from decomp): dst = src - offset, "
        "1<=offset<span=int(fs*p11). So min dst reached = src-(span-1). "
        "494 reached iff src-(span-1) <= 494 <= src-1.")
    for src_x in (495, 500, 520, 540):
        for p11 in (0.5, 1.0, 1.5, 2.0):
            r = run_scatter(loader, src_x=src_x, row=ROW, width=W,
                            front_strength=32, param_11=p11)
            got494 = 494 in r["nonzero"]
            b494 = r["nonzero"].get(494, (None, None))[0]
            min_dst = min(r["nonzero"].keys()) if r["nonzero"] else None
            pred_min = src_x - (r["span"] - 1) if r["span"] > 1 else None
            log(f"  src={src_x} p11={p11:.1f} span={r['span']:3d} "
                f"min_dst_written={min_dst} pred={pred_min} "
                f"reach494={got494}"
                + (f" R@494={b494[0]:.4f}" if got494 else ""))
    log("")

    # --- CANDIDATE 2: param_11 degeneracy (span collapse) ---
    log("## Candidate 2 (param_11 degeneracy): span=int(fs*p11) collapses to <=1")
    log("FACT from decomp: body gated by (0<param_9) at outer and (1<param_9)"
        " for the write loops. param_9 = int(front_strength*param_11).")
    for fs in (4, 16, 32, 64):
        for p11 in (0.0, 0.01, 0.03, 0.06, 0.1, 0.25):
            r = run_scatter(loader, src_x=SRC, row=ROW, width=W,
                            front_strength=fs, param_11=p11)
            span = r["span"]
            nz = len(r["nonzero"])
            skipped = (nz == 0)
            note = ""
            if span <= 0:
                note = "SKIP(outer 0<param_9 false)"
            elif span <= 1:
                note = "SKIP(inner 1<param_9 false)"
            log(f"  fs={fs:3d} p11={p11:.2f} span={span:3d} nonzero_cols={nz}"
                f"  {'body-skipped' if skipped else 'body-ran'} {note}")
    log("")

    # --- membership: source col with zero alpha_or_valid contributes nothing ---
    log("## Valid-alpha side channel (alpha_or_valid weights each source col)")
    log("FACT: contribution fVar16 = alpha_or_valid[src]*table[...]; if the "
        "source col's alpha_or_valid==0, it scatters nothing.")
    for av_src in (0.0, 0.5, 1.0):
        r = run_scatter(loader, src_x=SRC, row=ROW, width=W,
                        front_strength=32, param_11=1.0, alpha_valid_src=av_src)
        nz = len(r["nonzero"])
        b = r["nonzero"].get(494, (None, None))
        log(f"  alpha_or_valid[src]={av_src:.1f} -> nonzero_cols={nz}"
            + (f" R@494={b[0][0]:.4f} denom@494={b[1]:.4f}" if 494 in r["nonzero"] else " (494 not reached/zero)"))
    log("")

    out_path = Path(__file__).parent / "_scatter_run_output.txt"
    out_path.write_text("\n".join(report))
    print(f"\n[written {out_path}]")


if __name__ == "__main__":
    main()
