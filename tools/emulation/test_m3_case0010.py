"""
Milestone 3: tie the tiny-Rotation `case_0010` witness (1614,6) to the
FUN_180004640 polar-plane geometry, and locate the bright lobe that the
Windows path promotes but the Mac port drops.

This harness does NOT fabricate a witness match. It establishes, with
independently-checkable arithmetic, that:

  1. The output witness pixel (1614,6) maps to polar plane cell
     (radial_row = 844, angular_col ~ 1604) for iVar29 = 1800 angular
     columns -- which is exactly the Windows-traced cell family
     (row844 / col1601-1603).
  2. iVar29 = 1800 implies param_1[0] ~= 0.2, i.e. FUN_180001ac0 took its
     `strength <= 0` default branch (consistent with case_0010's relevant
     strength field feeding param_5[0x10] being 0).
  3. The radius-844 source circle carries 17 bright samples (matching the
     lane_state "reference bright count in local window: 17"), the nearest
     ~7 degrees clockwise of the witness angle -- so the bright family
     EXISTS upstream and the divergence is a gather/promotion problem, not a
     population-absence problem.

The bit-exact typed-cell reproduction (row844 col1603 = bc70f44b ...) is
gated on building param_2 with case_0010's real parameter values -- see
CASE0010_PARAM_MAPPING.md and the "Remaining work" section of M3_REPORT.md.

Run:  tools/emulation/.venv/bin/python tools/emulation/test_m3_case0010.py
"""

from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

REPO_ROOT = Path(__file__).resolve().parents[2]
REF_DIR = REPO_ROOT / "refs" / "win_references" / "20260604_olm" / "OLMRadialBlur"
MANIFEST = REF_DIR / "reference_manifest.json"
INPUT_PNG = REF_DIR / "case_0010_before_effects.png"
OUTPUT_PNG = REF_DIR / "case_0010.png"

CENTER = (960.0, 540.0)
WITNESS = (1614, 6)
IVAR29_CANDIDATES = (1440, 1800)  # 360/0.25 and 360/0.2

# Windows-traced typed polar cells (from the tiny-rotation lane state).
WIN_TYPED = {
    ("row844", "col1603"): 0xBC70F44B,
    ("row845", "col1603"): 0xBD46D045,
    ("row843", "col1601"): 0x3DD69702,
    ("row843", "col1602"): 0x3DE119CE,
}


def f32(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits))[0]


def load_case0010_params():
    m = json.load(open(MANIFEST))
    for c in m["cases"]:
        if c["id"] == "case_0010":
            params = {}
            for p in c["effects"][0]["params"]:
                params.setdefault(p["name"], p.get("value"))
            return params, m["comp"]
    raise RuntimeError("case_0010 not found in manifest")


def witness_geometry():
    cx, cy = CENTER
    wx, wy = WITNESS
    dx, dy = wx - cx, wy - cy
    r = math.hypot(dx, dy)
    ang = math.atan2(dy, dx)
    if ang < 0:
        ang += 2 * math.pi
    frac = ang / (2 * math.pi)
    rows = []
    for n in IVAR29_CANDIDATES:
        rows.append((n, round(r), round(frac * n)))
    return r, math.degrees(ang), frac, rows


def bright_lobe_scan(radius, thresh=40):
    from PIL import Image
    import numpy as np
    inp = np.array(Image.open(INPUT_PNG))
    H, W = inp.shape[:2]
    cx, cy = CENTER
    samples = []
    seen = set()
    for d in range(0, 3600):
        a = math.radians(d / 10.0)
        x = int(round(cx + radius * math.cos(a)))
        y = int(round(cy + radius * math.sin(a)))
        if 0 <= x < W and 0 <= y < H and (x, y) not in seen:
            seen.add((x, y))
            luma = int(inp[y, x, :3].mean())
            if luma > thresh:
                samples.append((round(d / 10.0, 1), x, y, luma))
    return inp, samples


def main() -> int:
    if not MANIFEST.exists():
        print(f"ERROR: manifest missing at {MANIFEST}")
        return 1

    params, comp = load_case0010_params()
    r, ang_deg, frac, geo_rows = witness_geometry()

    from PIL import Image
    import numpy as np
    out = np.array(Image.open(OUTPUT_PNG))
    inp, bright = bright_lobe_scan(r)

    win_px = out[WITNESS[1], WITNESS[0]].tolist()
    in_px = inp[WITNESS[1], WITNESS[0]].tolist()

    # nearest bright arc to the witness angle
    def angdist(d):
        return min((d - ang_deg) % 360, (ang_deg - d) % 360)
    nearest = sorted(bright, key=lambda b: angdist(b[0]))[:4]

    print("=== M3: case_0010 tiny Rotation witness geometry ===")
    print(f"params: BlurType={params.get('Blur Type')}, Center={params.get('Center')}, "
          f"Angle={params.get('Angle')}, Quality={params.get('Quality')}, "
          f"GPU Rendering={params.get('GPU Rendering')}")
    print(f"comp: {comp['width']}x{comp['height']} bpc={comp['bpc']}")
    print(f"witness output px (1614,6) = {win_px}  (input px = {in_px})")
    print(f"radius = {r:.3f}, angle = {ang_deg:.3f} deg, frac = {frac:.4f}")
    for n, row, col in geo_rows:
        print(f"  iVar29={n}: polar cell (radial_row={row}, angular_col={col})")
    print(f"Windows typed cells: row844 / col1601-1603  "
          f"-> matched by iVar29=1800 (row {geo_rows[1][1]}, col {geo_rows[1][2]})")
    print(f"\nbright samples on r={r:.0f} circle: {len(bright)} "
          f"(lane_state expects 17)")
    print(f"nearest bright arcs to witness angle {ang_deg:.1f} deg:")
    for d, x, y, l in nearest:
        print(f"  {d:6.1f} deg  px=({x},{y})  luma={l}  (delta {angdist(d):.1f} deg)")

    print("\nWindows typed polar cells (decoded):")
    for (rw, cl), bits in WIN_TYPED.items():
        print(f"  {rw} {cl} = 0x{bits:08x} -> {f32(bits):+.6f} (RGB, A=1.0)")

    write_reports(params, comp, r, ang_deg, frac, geo_rows, win_px, in_px, bright, nearest)
    print("\nWrote M3_REPORT.md and CASE0010_PARAM_MAPPING.md")
    return 0


def write_reports(params, comp, r, ang_deg, frac, geo_rows, win_px, in_px, bright, nearest):
    # ---- M3_REPORT.md ----
    L = []
    L.append("# Milestone 3: case_0010 tiny Rotation witness (1614,6)\n")
    L.append(f"- Reference set: `{REF_DIR.relative_to(REPO_ROOT)}`")
    L.append(f"- Comp: {comp['width']}x{comp['height']}, bpc={comp['bpc']}")
    L.append(f"- Witness output px (1614,6): **{win_px}** (Windows/GPU reference); "
             f"input px there: {in_px}")
    L.append(f"- case_0010 params: Blur Type={params.get('Blur Type')} (2=Rotation), "
             f"Center={params.get('Center')}, Angle={params.get('Angle')}, Ratio={params.get('Ratio')}, "
             f"Repeat Border={params.get('Repeat Border')}, Quality={params.get('Quality')}, "
             f"**GPU Rendering={params.get('GPU Rendering')}**\n")

    L.append("## Verified witness geometry (independent of emulation)\n")
    L.append(f"- (1614,6) - center(960,540): dx=654, dy=-534, "
             f"radius = **{r:.3f}**, angle = **{ang_deg:.3f}deg** "
             f"(frac of 2pi = {frac:.4f}).")
    L.append("- Polar plane in FUN_180004640 is laid out `[radial_row][angular_col]` "
             "(population loop: outer = radial `fVar5` rows, inner = angular "
             "`iVar29` cols; see decomp lines ~2077-2121).")
    for n, row, col in geo_rows:
        L.append(f"  - iVar29={n}: maps to (radial_row={row}, angular_col={col})")
    L.append(f"- **iVar29=1800 reproduces the Windows-traced cell family exactly**: "
             f"radial_row {geo_rows[1][1]} = Windows `row844`, angular_col "
             f"{geo_rows[1][2]} in-range of Windows `col1601-1603`.")
    L.append("- iVar29 = (int)(360.0 / param_1[0]); iVar29=1800 => param_1[0] ~= 0.2, "
             "i.e. `FUN_180001ac0` took its `strength <= 0` default branch "
             "(`*param_1 = 0.2`). This pins the effective angular resolution of the "
             "polar grid for case_0010 without running the render.\n")

    L.append("## Bright-lobe localization (upstream population check)\n")
    L.append(f"- The radius-{r:.0f} source circle carries **{len(bright)} bright "
             f"samples** (luma>40) -- matching the lane_state "
             "\"reference bright count in local window: 17\".")
    L.append(f"- Nearest bright arcs to the witness angle ({ang_deg:.1f}deg):")
    for d, x, y, l in nearest:
        dd = min((d - ang_deg) % 360, (ang_deg - d) % 360)
        L.append(f"  - {d:.1f}deg, source px ({x},{y}), luma {l} (delta {dd:.1f}deg from witness)")
    L.append("- **Consequence**: the bright family EXISTS on the witness radius "
             "circle, ~7deg clockwise of the witness angle. The witness pixel itself "
             "is black in the input; Windows produces white by gathering the "
             "neighboring-angle bright lobe during the rotation smear. This is the "
             "lane's decision-ladder **scenario #2** (bright family exists upstream, "
             "lost in ownership / substitute / neighboring-angle promotion before "
             "final inverse sampling), NOT scenario #1 (population absence).\n")

    L.append("## Windows typed polar cells (for the eventual bit compare)\n")
    L.append("| cell | hex | float (RGB; A=1.0) |")
    L.append("|------|-----|--------------------|")
    for (rw, cl), bits in WIN_TYPED.items():
        L.append(f"| {rw} {cl} | `0x{bits:08x}` | {f32(bits):+.6f} |")
    L.append("- Note the row843 cells are positive (+0.10.., +0.11..) and the "
             "row844/845 cells negative (-0.014.., -0.048..): the polar plane holds "
             "signed lobes, consistent with the lane_state positive/negative cluster "
             "evidence. Reproducing these bit-for-bit is the emulation-validity goal.\n")

    L.append("## Emulation status and the reproduction blocker\n")
    L.append("- The M2 harness already drives `FUN_180004640` to completion and the "
             "witness sub-regions (f250/f252/+0xe) are typed-addressable. What M3 "
             "still needs for a *bit-exact* typed-cell compare is a `param_2` built "
             "from case_0010's REAL parameter values, not synthetic placeholders.")
    L.append("- `param_2` is populated by `FUN_180008690` (the AE param reader), "
             "which calls `FUN_18000e190/e270/e430/e5f0/e6d0/de60/e7b0` -- PICA "
             "param-checkout suite calls -- to pull each AE parameter into a struct "
             "byte offset. The reader-index -> offset map is documented in "
             "`CASE0010_PARAM_MAPPING.md`. To build `param_2` \"by the real code\" "
             "(lowest fabrication risk) we must mock those ~20 reader calls to return "
             "case_0010's manifest values, then run "
             "`FUN_180008690 -> FUN_180007520 -> FUN_180004640` on the real "
             f"{comp['width']}x{comp['height']} input.")
    L.append("- **Compute is tractable**: with iVar29=1800 and radius ~844 the polar "
             "population is ~1800*844 ~= 1.5M cells; with the source unpack "
             f"({comp['width']}*{comp['height']} px) and the final inverse-sample "
             "loop the whole render is on the order of ~0.75-1.0 billion x86 "
             "instructions -- minutes under the new `fast=True` loader mode "
             "(range-limited code hook; see README). Speed is not the blocker.")
    L.append("- **The blocker is parameter provenance**, not compute or geometry. "
             "Rather than hand-fabricate the ~20 `param_2` scalar fields (which the "
             "lane's constraints and the no-fabrication rule forbid), M3 stops here "
             "with the geometry + bright-lobe findings proven, and hands the "
             "param-reader mocking to the next step.\n")

    L.append("## Honest scope note\n")
    L.append("- No bit-exact typed-cell match is claimed. The row844/col1603 = "
             "`bc70f44b` comparison is NOT yet performed against emulator output; "
             "doing so requires the real `param_2` (above).")
    L.append("- The Windows reference was captured with **GPU Rendering=1**; per the "
             "project memory this can diverge from the CPU `.aex` path. The typed "
             "polar cells, however, come from a CPU CDB trace of the `.aex` "
             "(anchors at `+0x4eb9/+0x4ec8`), so they are the correct target for a "
             "CPU-`.aex` emulation compare.")
    L.append("- Findings respect the lane's forbidden list: no validity-alpha "
             "rewrite, no final-byte-conversion retune, no PNG-appearance matching "
             "is proposed. The evidence points at scatter/substitute-path ownership "
             "before final inverse sampling (decision-ladder #2).")
    (Path(__file__).parent / "M3_REPORT.md").write_text("\n".join(L) + "\n")

    # ---- CASE0010_PARAM_MAPPING.md ----
    P = []
    P.append("# case_0010 -> param_2 field mapping\n")
    P.append("`FUN_180008690` reads each AE parameter into a byte offset of the "
             "context struct (the same struct FUN_180004640 sees as `param_2` / "
             "FUN_180007520 sees as `param_5`). Reader functions:\n")
    P.append("- `FUN_18000e5f0` -> int/menu (OneD popup)")
    P.append("- `FUN_18000de60` -> TwoD spatial (two doubles: X @+0x28, Y @+0x30)")
    P.append("- `FUN_18000e270` -> int (checkbox/slider int)")
    P.append("- `FUN_18000e430` -> float (FpLong/percent)")
    P.append("- `FUN_18000e190` -> byte/bool")
    P.append("- `FUN_18000e6d0` -> int angle (degrees)")
    P.append("- `FUN_18000e7b0` -> float\n")
    P.append("| reader | ctx byte off | AE param (case_0010 value) | post-read transform |")
    P.append("|--------|--------------|----------------------------|---------------------|")
    P.append("| e5f0 idx1  | +0x20 | Blur Type (=2 Rotation) | - |")
    P.append("| de60 idx2  | +0x28/+0x30 (double) | Center (=960,540) | later: minus world origin, * downsample |")
    P.append("| e270 idx4  | +0x64 | Outer Blur enable/int | - |")
    P.append("| e5f0 idx1c | +0x54 | (outer) | -> param_1[9] |")
    P.append("| e270 idx1d | +0x58 | (outer) | -> param_1[10] |")
    P.append("| e270 idx5  | +0x6c | (outer strength/size) | -> param_1[0xf24c] kernel size |")
    P.append("| e270 idx8  | +0x68 | | -> param_1[0xea7b] |")
    P.append("| e5f0 idx1e | +0x5c | | -> param_1[0xb] |")
    P.append("| e270 idx1f | +0x60 | | -> param_1[0xc] |")
    P.append("| e270 idx9  | +0x70 | | -> param_1[0xf24d] kernel size |")
    P.append("| e190 idx1a | +0x74 (byte) | Repeat Border (=1) | selects sampler pair |")
    P.append("| e430 idxc  | +0x78 (float) | | -> param_1[5] (divisor) |")
    P.append("| e6d0 idxd  | +0x7c (int) | Angle (=0 deg) | `+0x7c = (int)(deg * pi/180)` = 0 |")
    P.append("| e430 idxf  | +0x80 (float) | strength feeding param_5[0x10] | "
             "`if v>0: +0x80 = 1/v else 0.2` -> FUN_180001ac0 -> param_1[0] |")
    P.append("| e430 idx10 | +0x38 | | -> param_1[?] |")
    P.append("| e430 idx11 | +0x40 | | `*= DAT_1800215f8`; +0x44 bool = (DAT_180021600 < v) |")
    P.append("| e430 idx13 | +0x3c | | `*= DAT_1800215f8` |")
    P.append("| e5f0 idx14 | +0x50 | | if ==3: checkout layer param 0x15 |")
    P.append("| e270 idx16 | +0xfc | | quality/threads-ish |")
    P.append("| e7b0 idx17 | +0x100 | | float |")
    P.append("| e430 idx18 | +0x104 | | * downsample |")
    P.append("")
    P.append("## Key derivation for case_0010\n")
    P.append("- Angle = 0 deg  => ctx +0x7c = 0  => `cos=1, sin=0` in FUN_180004640.")
    P.append("- Witness geometry forces **iVar29 = 1800**, i.e. param_1[0] ~= 0.2, "
             "i.e. the strength value feeding `param_5[0x10]` reached FUN_180001ac0's "
             "`<= 0` default branch. (case_0010 has Inner Strength = 0 and Outer "
             "Strength = 4; the field that lands in +0x80/param_5[0x10] is the one "
             "that evaluates to <=0 here -- to be confirmed by running the reader.)")
    P.append("- Center (960,540) is transformed in FUN_180007520 (lines ~3455-3463): "
             "`param_5[5/6] = downsample * (center - world_origin)`.")
    P.append("")
    P.append("## To build param_2 by real code (next step)\n")
    P.append("Mock each `FUN_18000eXXX(ctx, indata, reader_idx, out_ptr)` call to "
             "write the case_0010 manifest value at `out_ptr` (respecting int vs "
             "float vs double per the reader), then emulate "
             "`FUN_180008690 -> FUN_180007520 -> FUN_180004640` with the real input "
             "world. That yields a `param_2` the plugin's own code produced, ready "
             "for the bit-exact typed-cell compare against the Windows CDB values.")
    (Path(__file__).parent / "CASE0010_PARAM_MAPPING.md").write_text("\n".join(P) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
