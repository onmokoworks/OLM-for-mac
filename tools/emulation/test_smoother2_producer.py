"""
test_smoother2_producer.py -- local Unicorn emulation of the OLMSmoother2
legacy producer path for the 0004 and 0012 witnesses.

Binary: aex/OLMSmoother2AE/Plugins/64/2025/OLMSmoother2.aex (ImageBase 0x180000000).

Scope / goal (per the SMOOTHER2 producer-emu task):

  * Hand-build a "SmootherPolygon" working struct in guest memory (synthetic
    source-world RGBA float plane + u8 class-plane) and drive the confirmed
    producer functions directly, reading back the branch outcomes:
      - 0004: FUN_180013140 (NW-triangle emitter) + its two scanners
        FUN_18000dbd0 (right scan) and FUN_18000d6a0 (down scan).
      - 0012: FUN_18000e170 (bitsum c-value) + FUN_18000f270 (suppress/append
        wrapper) + FUN_18000e3a0 (weight compute + append).
  * Leaf sanity first: FUN_180013630 (the pure weight kernel) against an
    independent Python re-implementation of its own decomp, to confirm ABI.

STRUCT LAYOUT (re-derived directly from the decomp read this run, NOT from the
task's prose memory note; where they differ the decomp wins):

  param_1 is a longlong* to the working struct. Byte offsets:
    +0x00 (param_1[0])   source-world float RGBA base   (append copies 16B here)
    +0x10 (param_1[2])   source-world row stride (BYTES) (append: param_1[2])
    +0x18 (param_1[3])   class-plane base (u8, 4 bytes/pixel: [b0,b1,b2,b3])
    +0x20 (param_1[4])   two int32: low=width, high(+0x24)=height
    +0x28 (param_1[5])   class-plane row stride (BYTES)
    +0x30 (param_1[6])   cur_x  (int32)
    +0x34                cur_y  (int32)
    +0x38 (param_1[7])   smoothness_n (float)   [used by 0004 FUN_1800104d0 weights]
    +0x3c                base_weight (float)    [used by e3a0/f270 scale]
    +0x40                vertex array, stride 0x14 (16B RGBA copy + 4B weight @ +0x10)
    +0x130 (param_1[0x26]) vertex count (append cap 12)

  Scanner param_2 is a 3-qword local snapshot {param_1[3], param_1[4],
  param_1[5]} so inside the scanner: *param_2=class base, param_2[1]=param_1[4]
  (low int = width via (int)param_2[1]; +0xc high int = height),
  (int)param_2[2]=class stride.

  Scanner/emit param_3 = (int*)(param_1+6): param_3[0]=cur_x, param_3[1]=cur_y.

  FUN_18000e170(param_1_base, desc): desc is int[6]; uses desc[0]=x, desc[1]=y.
    class-plane addressing base=+0x18, stride=+0x28. Returns bitsum:
      bit1 (val 1) = class[y*stride + x*4 + 0] != 0                (A(x,y))
      bit2 (val 2) = class[(y-1)*stride + x*4 + 0] != 0            (A(x,y-1))
      bit4 (val 4) = class[y*stride + x*4 - 3] != 0                (chan of (x-1))
    Early return 4 if desc[0]==0.

All new code confined to tools/emulation/. No source/notes/ledger edits, no commit.
"""

from __future__ import annotations

import struct
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
AEX_PATH = REPO_ROOT / "aex" / "OLMSmoother2AE" / "Plugins" / "64" / "2025" / "OLMSmoother2.aex"

# function addresses (0x180000000 base, confirmed by decomp headers this run)
FUN_180013140 = 0x180013140   # 0004 NW-triangle emitter
FUN_18000dbd0 = 0x18000dbd0   # right scanner
FUN_18000d6a0 = 0x18000d6a0   # down scanner
FUN_1800104d0 = 0x1800104d0   # append vertex
FUN_180013630 = 0x180013630   # weight kernel (leaf)
FUN_18000e170 = 0x18000e170   # 0012 bitsum
FUN_18000f270 = 0x18000f270   # 0012 suppress/append wrapper
FUN_18000e3a0 = 0x18000e3a0   # 0012 weight+append

# struct byte offsets
O_SRC_BASE = 0x00
O_SRC_STRIDE = 0x10
O_CLASS_BASE = 0x18
O_WH = 0x20            # low=width, +0x24 high=height
O_CLASS_STRIDE = 0x28
O_CUR_X = 0x30
O_CUR_Y = 0x34
O_SMOOTHNESS = 0x38
O_BASE_WEIGHT = 0x3c
O_VERTS = 0x40
O_VCOUNT = 0x130
VERT_STRIDE = 0x14

STRUCT_SIZE = 0x200   # comfortably past +0x130 + 12*0x14


def read_rdata_f32(loader: AexLoader, addr: int) -> float:
    return struct.unpack("<f", loader.read_bytes(addr, 4))[0]


class SmootherStruct:
    """Hand-built working struct + synthetic worlds in guest memory."""

    def __init__(self, loader: AexLoader, width: int, height: int):
        self.loader = loader
        self.width = width
        self.height = height
        self.src_stride = width * 16      # RGBA float32 = 16 bytes/pixel
        self.class_stride = width * 4     # 4 bytes/pixel class plane

        self.src_base = loader.bump_alloc(self.src_stride * height, align=64)
        loader.write_bytes(self.src_base, b"\x00" * (self.src_stride * height))
        self.class_base = loader.bump_alloc(self.class_stride * height, align=64)
        loader.write_bytes(self.class_base, b"\x00" * (self.class_stride * height))

        self.base = loader.bump_alloc(STRUCT_SIZE, align=64)
        loader.write_bytes(self.base, b"\x00" * STRUCT_SIZE)
        self._w(O_SRC_BASE, struct.pack("<Q", self.src_base))
        self._w(O_SRC_STRIDE, struct.pack("<Q", self.src_stride))
        self._w(O_CLASS_BASE, struct.pack("<Q", self.class_base))
        self._w(O_WH, struct.pack("<ii", width, height))
        self._w(O_CLASS_STRIDE, struct.pack("<Q", self.class_stride))
        self._w(O_VCOUNT, struct.pack("<Q", 0))

    def _w(self, off: int, data: bytes) -> None:
        self.loader.write_bytes(self.base + off, data)

    # -- world / class setters --
    def set_src_pixel(self, x: int, y: int, rgba) -> None:
        off = self.src_base + y * self.src_stride + x * 16
        self.loader.write_bytes(off, struct.pack("<4f", *rgba))

    def set_class_pixel(self, x: int, y: int, b0: int, b1: int = 0, b2: int = 0, b3: int = 0) -> None:
        off = self.class_base + y * self.class_stride + x * 4
        self.loader.write_bytes(off, bytes([b0 & 0xFF, b1 & 0xFF, b2 & 0xFF, b3 & 0xFF]))

    def set_cur(self, x: int, y: int) -> None:
        self._w(O_CUR_X, struct.pack("<i", x))
        self._w(O_CUR_Y, struct.pack("<i", y))

    def set_smoothness(self, v: float) -> None:
        self._w(O_SMOOTHNESS, struct.pack("<f", v))

    def set_base_weight(self, v: float) -> None:
        self._w(O_BASE_WEIGHT, struct.pack("<f", v))

    def vcount(self) -> int:
        return struct.unpack("<Q", self.loader.read_bytes(self.base + O_VCOUNT, 8))[0]

    def set_vcount(self, n: int) -> None:
        self._w(O_VCOUNT, struct.pack("<Q", n))

    def vertices(self):
        out = []
        for i in range(self.vcount()):
            off = self.base + O_VERTS + i * VERT_STRIDE
            rgba = struct.unpack("<4f", self.loader.read_bytes(off, 16))
            weight = struct.unpack("<f", self.loader.read_bytes(off + 0x10, 4))[0]
            out.append({"rgba": rgba, "weight": weight})
        return out


# ---------------------------------------------------------------------------
# Leaf check: FUN_180013630 weight kernel vs independent Python re-impl
# ---------------------------------------------------------------------------

def py_weight_kernel(p1: float, p2: int, p3: float, one: float, half: float) -> float:
    # mirrors decomp 12755-12769; DAT_1800226a0 == one (1.0), DAT_180022694 == half (0.5)
    if (p1 != 0.0) and (float(p2) < p1) and (p3 != 0.0):
        f1 = float(p2)
        f2 = (one - f1 / p1) * p3 + (f1 / p1) * 0.0
        if p1 < f1 + one:
            return (p1 - f1) * f2 * half
        f1b = (f1 + one) / p1
        return ((one - f1b) * p3 + f1b * 0.0 + f2) * half
    return 0.0


def call_weight(loader: AexLoader, p1: float, p2: int, p3: float) -> float:
    # float FUN_180013630(float p1, int p2, float p3):
    #   XMM0=p1 (arg0), RDX low=p2 (arg1 int), XMM2=p3 (arg2)
    res = loader.call_function(
        FUN_180013630,
        int_args=[0, p2, 0],
        float_args={0: (p1, "f"), 2: (p3, "f")},
        max_instructions=200_000,
    )
    return res["xmm0_f32"]


def run_leaf_check() -> dict:
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    half = read_rdata_f32(loader, 0x180022694)   # DAT_180022694
    one = read_rdata_f32(loader, 0x1800226a0)    # DAT_1800226a0
    dd8 = read_rdata_f32(loader, 0x180022dd8)
    dd4 = read_rdata_f32(loader, 0x180022dd4)
    de8 = read_rdata_f32(loader, 0x180022de8)
    ddc = read_rdata_f32(loader, 0x180022ddc)

    cases = [
        (10.0, 3, 1.0),
        (5.0, 2, 0.5),
        (0.0, 1, 1.0),     # p1==0 -> 0
        (4.0, 5, 1.0),     # p2>=p1 -> 0
        (8.0, 1, 0.0),     # p3==0 -> 0
        (6.0, 6, 0.8),     # p1 < f1+1 boundary region
    ]
    rows = []
    for p1, p2, p3 in cases:
        got = call_weight(loader, p1, p2, p3)
        exp = py_weight_kernel(p1, p2, p3, one, half)
        rows.append({
            "p1": p1, "p2": p2, "p3": p3,
            "got": got, "expected": exp,
            "match": abs(got - exp) <= 1e-6 or (got == exp),
        })
    return {
        "constants": {
            "DAT_180022694(half)": half, "DAT_1800226a0(one)": one,
            "DAT_180022dd8": dd8, "DAT_180022dd4": dd4,
            "DAT_180022de8": de8, "DAT_180022ddc": ddc,
        },
        "rows": rows,
        "all_match": all(r["match"] for r in rows),
    }


# ---------------------------------------------------------------------------
# 0004: FUN_180013140 + scanners
# ---------------------------------------------------------------------------

def call_scanner(loader: AexLoader, fn: int, ss: SmootherStruct, cur_x: int, cur_y: int):
    """
    Drive FUN_18000dbd0 / FUN_18000d6a0 individually.
    param_1 = out int[3] {x, y, code}; param_2 = snapshot {classbase,wh,stride};
    param_3 = int[2] {cur_x, cur_y}.
    Returns (out_x, out_y, code).
    """
    out = loader.bump_alloc(16, align=16)
    loader.write_bytes(out, b"\x00" * 16)
    snap = loader.bump_alloc(24, align=16)
    loader.write_bytes(snap + 0, struct.pack("<Q", ss.class_base))
    loader.write_bytes(snap + 8, struct.pack("<ii", ss.width, ss.height))
    loader.write_bytes(snap + 16, struct.pack("<Q", ss.class_stride))
    p3 = loader.bump_alloc(8, align=16)
    loader.write_bytes(p3, struct.pack("<ii", cur_x, cur_y))
    loader.call_function(fn, int_args=[out, snap, p3], max_instructions=500_000)
    x, y, code = struct.unpack("<iii", loader.read_bytes(out, 12))
    return x, y, code


def run_0004(scenario_name: str, setup) -> dict:
    """
    setup(ss) configures the class-plane / cur before driving FUN_180013140.
    We record: guard pass/fail, iVar6 (from right scanner), iVar5 (from down
    scanner) exactly as FUN_180013140 computes them, vcount, vertices.
    """
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    half = read_rdata_f32(loader, 0x180022694)
    one = read_rdata_f32(loader, 0x1800226a0)
    width, height = 16, 16
    ss = SmootherStruct(loader, width, height)
    ss.set_smoothness(2.0)      # smoothness_n at +0x38 (float)
    ss.set_base_weight(1.0)     # +0x3c
    setup(ss)
    cur_x = struct.unpack("<i", loader.read_bytes(ss.base + O_CUR_X, 4))[0]
    cur_y = struct.unpack("<i", loader.read_bytes(ss.base + O_CUR_Y, 4))[0]

    # entry guard exactly as decomp 12585: cur_y != height-1 && cur_x != 0
    entry_guard = (cur_y != (height - 1)) and (cur_x != 0)

    # replicate iVar6/iVar5 by driving scanners the same way FUN_180013140 does
    rx, ry, rcode = call_scanner(loader, FUN_18000dbd0, ss, cur_x, cur_y)
    iVar6 = (rx - cur_x) + 1          # decomp: (*piVar4 - iVar3) + 1
    dx, dy, dcode = call_scanner(loader, FUN_18000d6a0, ss, cur_x, cur_y)
    iVar5 = (dy - cur_y) + 1          # decomp: (piVar4[1] - iVar2) + 1

    # emit guard (decomp 12596-12599)
    class_prev = None
    if entry_guard:
        # class[(int)param_1[5]*cur_y + cur_x*4 - 1 + param_1[3]]
        off = ss.class_base + ss.class_stride * cur_y + cur_x * 4 - 1
        class_prev = loader.read_bytes(off, 1)[0]
    emit_guard = None
    if entry_guard:
        emit_guard = ((iVar6 < 4) or (iVar5 < 4)) and (
            ((iVar6 < 2 or iVar5 < 2)) or (class_prev == 0)
        )

    ss.set_vcount(0)
    loader.call_function(FUN_180013140, int_args=[ss.base], max_instructions=2_000_000)
    verts = ss.vertices()

    return {
        "scenario": scenario_name,
        "cur": (cur_x, cur_y),
        "entry_guard": entry_guard,
        "right_scan": {"out": (rx, ry), "code": rcode, "iVar6": iVar6},
        "down_scan": {"out": (dx, dy), "code": dcode, "iVar5": iVar5},
        "class_prev_byte": class_prev,
        "emit_guard": emit_guard,
        "vcount": ss.vcount(),
        "vertices": verts,
        "half": half, "one": one,
    }


# ---------------------------------------------------------------------------
# 0012: FUN_18000e170 bitsum + FUN_18000f270 / FUN_18000e3a0 append
# ---------------------------------------------------------------------------

def call_e170(loader: AexLoader, ss: SmootherStruct, desc) -> int:
    """char FUN_18000e170(longlong base, int* desc); desc = int[6]."""
    d = loader.bump_alloc(24, align=16)
    loader.write_bytes(d, struct.pack("<6i", *desc))
    res = loader.call_function(FUN_18000e170, int_args=[ss.base, d], max_instructions=100_000)
    return res["rax"] & 0xFF


def call_f270(loader: AexLoader, ss: SmootherStruct, desc, param3: float):
    """longlong FUN_18000f270(longlong* base, int* desc, float param3)."""
    d = loader.bump_alloc(24, align=16)
    loader.write_bytes(d, struct.pack("<6i", *desc))
    ss.set_vcount(0)
    res = loader.call_function(
        FUN_18000f270,
        int_args=[ss.base, d, 0],
        float_args={2: (param3, "f")},
        max_instructions=500_000,
    )
    return res["rax"] & 0xFF, ss.vcount(), ss.vertices()


def call_e3a0(loader: AexLoader, ss: SmootherStruct, desc, param3: float, param4: float):
    """ulonglong FUN_18000e3a0(longlong* base, int* desc, float p3, float p4)."""
    d = loader.bump_alloc(24, align=16)
    loader.write_bytes(d, struct.pack("<6i", *desc))
    ss.set_vcount(0)
    res = loader.call_function(
        FUN_18000e3a0,
        int_args=[ss.base, d, 0, 0],
        float_args={2: (param3, "f"), 3: (param4, "f")},
        max_instructions=500_000,
    )
    return res["rax"] & 0xFF, ss.vcount(), ss.vertices()


def run_0012() -> dict:
    """
    Witness (91,841). Recorded local descriptor (producer_path_diff JSON):
      cardinal6 desc = "91,841,1,91,843,5", key=50
      e170: a_center=0 (A(x,y)==0), a_prev=1 (A(x,y-1)!=0), r_left=0 -> c=2
      f270: c=2, p3=1, extra_n=0.4, count_before=0
      e3a0: weight=0.35632184, trap=1.74,0,0.5, scale_m=0.58, scale_h=1
      append: src (91,840) -> dst (91,841), rgba ~0.991.., weight 0.35632184
    We reconstruct a class-plane that yields exactly c=2 (A(x,y-1) set, A(x,y)
    clear, (x-1) channel clear), set cur/base_weight per the record, then read
    the real e170/f270/e3a0 outcomes from the binary.
    """
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    half = read_rdata_f32(loader, 0x180022694)
    one = read_rdata_f32(loader, 0x1800226a0)
    dd8 = read_rdata_f32(loader, 0x180022dd8)

    # Use a small world; place witness at local coords (5,6) so y-1 exists and
    # x-1 exists. Absolute 91/841 doesn't fit a 16x16 world; the producer math
    # is translation-invariant in class addressing (only relative neighbours
    # and desc arithmetic matter), and desc y-differences are what feed e3a0.
    width, height = 16, 16
    ss = SmootherStruct(loader, width, height)
    x, y = 5, 6
    ss.set_cur(x, y)
    # base_weight (+0x3c) controls e3a0 scale param p3 = weight*dd8 + half.
    # Record shows scale computation; set base_weight so we can read the real
    # weight the binary produces (we do NOT force a target; just drive it).
    ss.set_base_weight(0.4)      # matches recorded "extra_n"/scale_m family region
    ss.set_smoothness(2.0)

    # class-plane to force c=2: A(x,y-1)=bit2 set, A(x,y)=bit1 clear,
    # (x-1) channel (bit4, offset x*4-3 == (x-1)*4+1) clear.
    # e170 reads byte0 of each pixel for bit1/bit2, and offset x*4-3 for bit4.
    ss.set_class_pixel(x, y - 1, b0=1)     # A(x,y-1) -> bit2
    # ensure A(x,y)==0 and (x-1,*) channel byte1==0 (already zero)

    desc = [x, y, 1, x, y + 2, 5]   # mirrors record shape "91,841,1,91,843,5"

    c_val = call_e170(loader, ss, desc)

    # f270 scale param exactly as decomp 9539-9541: base_weight*dd8 + half
    scale = struct.unpack("<f", loader.read_bytes(ss.base + O_BASE_WEIGHT, 4))[0] * dd8 + half
    f270_ret, f270_count, f270_verts = call_f270(loader, ss, desc, 1.0)

    # e3a0 driven directly with p3=scale, p4=1.0 (the record's param4 family)
    e3a0_ret, e3a0_count, e3a0_verts = call_e3a0(loader, ss, desc, scale, 1.0)

    # source pixel that append copies (e3a0 dst = desc[0], desc[1]-1)
    ss.set_src_pixel(desc[0], desc[1] - 1, (0.99106717, 0.99106717, 0.99106717, 0.99607843))
    e3a0_ret2, e3a0_count2, e3a0_verts2 = call_e3a0(loader, ss, desc, scale, 1.0)

    return {
        "constants": {"half": half, "one": one, "dd8": dd8},
        "desc": desc,
        "e170_c": c_val,
        "f270_scale_input": scale,
        "f270": {"ret": f270_ret, "count": f270_count, "verts": f270_verts},
        "e3a0_zero_src": {"ret": e3a0_ret, "count": e3a0_count, "verts": e3a0_verts},
        "e3a0_with_src": {"ret": e3a0_ret2, "count": e3a0_count2, "verts": e3a0_verts2},
    }


def run_0012_bitsum_sweep() -> dict:
    """
    Enumerate the three e170 input bits around the 0012 witness:
      - center byte0 -> bit 1
      - prev-row byte0 -> bit 2
      - left pixel byte1 -> bit 4

    The Mac witness is c=2 and appends. Windows output is transparent, so this
    sweep identifies the exact local class-plane byte condition that would move
    the binary into the suppressing c=4 lane.
    """
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    half = read_rdata_f32(loader, 0x180022694)
    dd8 = read_rdata_f32(loader, 0x180022dd8)

    rows = []
    width, height = 16, 16
    x, y = 5, 6
    desc = [x, y, 1, x, y + 2, 5]
    scale = 0.4 * dd8 + half
    for center in (0, 1):
        for prev in (0, 1):
            for left_b1 in (0, 1):
                ss = SmootherStruct(loader, width, height)
                ss.set_cur(x, y)
                ss.set_base_weight(0.4)
                ss.set_smoothness(2.0)
                ss.set_src_pixel(desc[0], desc[1] - 1, (0.99106717, 0.99106717, 0.99106717, 0.99607843))
                if center:
                    ss.set_class_pixel(x, y, b0=1)
                if prev:
                    ss.set_class_pixel(x, y - 1, b0=1)
                if left_b1:
                    ss.set_class_pixel(x - 1, y, b0=0, b1=1)
                c_val = call_e170(loader, ss, desc)
                f270_ret, f270_count, f270_verts = call_f270(loader, ss, desc, 1.0)
                e3a0_ret, e3a0_count, e3a0_verts = call_e3a0(loader, ss, desc, scale, 1.0)
                rows.append({
                    "center_b0": center,
                    "prev_b0": prev,
                    "left_b1": left_b1,
                    "e170_c": c_val,
                    "f270_ret": f270_ret,
                    "f270_count": f270_count,
                    "f270_first_weight": f270_verts[0]["weight"] if f270_verts else None,
                    "e3a0_ret": e3a0_ret,
                    "e3a0_count": e3a0_count,
                    "e3a0_first_weight": e3a0_verts[0]["weight"] if e3a0_verts else None,
                })
    return {
        "desc": desc,
        "scale": scale,
        "rows": rows,
        "suppressing_rows": [row for row in rows if row["e170_c"] == 4 or row["f270_count"] == 0],
    }


def run_0004_scanner_sweep() -> dict:
    """
    Sweep synthetic right/down scanner spans plus class_prev for FUN_180013140.

    right_span:
      number of class-plane pixels to the right of cur with byte1=1 that keep
      FUN_18000dbd0 advancing.
    down_span:
      number of class-plane pixels below cur with byte0=1 that keep
      FUN_18000d6a0 advancing.
    class_prev_b3:
      byte3 at (cur_x-1, cur_y); this is the exact byte FUN_180013140 consults
      in its second emit-guard clause.
    """
    rows = []
    spans = [0, 1, 2, 3, 6]
    width, height = 16, 16
    cur_x, cur_y = 8, 4
    for right_span in spans:
        for down_span in spans:
            for class_prev_b3 in (0, 1):
                def setup(ss: SmootherStruct,
                          right_span=right_span,
                          down_span=down_span,
                          class_prev_b3=class_prev_b3):
                    ss.set_cur(cur_x, cur_y)
                    for dx in range(1, right_span + 1):
                        ss.set_class_pixel(cur_x + dx, cur_y, b0=0, b1=1)
                    for dy in range(1, down_span + 1):
                        ss.set_class_pixel(cur_x, cur_y + dy, b0=1)
                    if class_prev_b3:
                        ss.set_class_pixel(cur_x - 1, cur_y, b0=0, b1=0, b2=0, b3=1)

                result = run_0004(
                    f"span-r{right_span}-d{down_span}-prev{class_prev_b3}",
                    setup,
                )
                rows.append({
                    "right_span": right_span,
                    "down_span": down_span,
                    "class_prev_b3": class_prev_b3,
                    "iVar6": result["right_scan"]["iVar6"],
                    "iVar5": result["down_scan"]["iVar5"],
                    "emit_guard": result["emit_guard"],
                    "vcount": result["vcount"],
                })
    no_emit = [row for row in rows if row["vcount"] == 0]
    emit = [row for row in rows if row["vcount"] != 0]
    return {
        "cur": [cur_x, cur_y],
        "rows": rows,
        "no_emit_rows": no_emit,
        "emit_rows": emit,
    }


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

def fmt_verts(verts):
    if not verts:
        return "[]"
    return "; ".join(
        f"rgba=({v['rgba'][0]:.6f},{v['rgba'][1]:.6f},{v['rgba'][2]:.6f},{v['rgba'][3]:.6f}) w={v['weight']:.8f}"
        for v in verts
    )


def main() -> int:
    L = []
    L.append("# SMOOTHER2_PRODUCER_EMU_REPORT")
    L.append("")
    L.append("Local Unicorn emulation of OLMSmoother2 legacy producer path")
    L.append("(`aex/OLMSmoother2AE/Plugins/64/2025/OLMSmoother2.aex`, ImageBase")
    L.append("0x180000000). Functions driven directly; binary executed, no")
    L.append("Windows round-trip. All facts below are read from the binary via")
    L.append("Unicorn unless explicitly marked INFERRED. No source/notes/ledger")
    L.append("files modified; no commit.")
    L.append("")

    # -- ABI / leaf --
    L.append("## ABI / leaf 健全性")
    leaf = run_leaf_check()
    c = leaf["constants"]
    L.append("- .rdata 重み定数（mapped image から直接読取）:")
    for k, v in c.items():
        L.append(f"  - `{k}` = {v!r}")
    L.append(f"- leaf 検証 FUN_180013630（weight kernel）vs 独立 Python 再実装: "
             f"{'PASS (全ケース一致)' if leaf['all_match'] else 'FAIL'}")
    for r in leaf["rows"]:
        L.append(f"  - p1={r['p1']}, p2={r['p2']}, p3={r['p3']}: got={r['got']:.8f} "
                 f"expected={r['expected']:.8f} match={r['match']}")
    L.append(f"- Win x64 ABI（XMM0/RDX/XMM2 引数, RET trampoline, __chkstk TEB）は "
             f"この一致で健全と確認{'された' if leaf['all_match'] else 'できなかった'}。")
    L.append("")

    # -- 0004 --
    L.append("## 0004 の分岐挙動（FUN_180013140 + scanners）")
    L.append("witness (1903,519) は Mac 側 count=0 / passthrough。ローカル 16x16 world")
    L.append("上で class-plane 状態を変えつつ、entry guard / emit guard / scanner 値")
    L.append("(iVar6=右scan, iVar5=下scan) / 頂点数・座標・重みを binary から読む。")
    L.append("")

    def s_empty(ss):
        # witness-like: class-plane empty around a non-edge, non-x0 cur
        ss.set_cur(8, 8)

    def s_isolated(ss):
        # single class pixel at cur, neighbours empty
        ss.set_cur(8, 8)
        ss.set_class_pixel(8, 8, b0=1)

    def s_left_block(ss):
        # left neighbour class byte0 set at (cur_x-1,cur_y) so class_prev != 0
        ss.set_cur(8, 8)
        ss.set_class_pixel(7, 8, b0=1)

    def s_edge_x0(ss):
        ss.set_cur(0, 8)   # cur_x==0 -> entry guard fails

    def s_edge_ybottom(ss):
        ss.set_cur(8, 15)  # cur_y==height-1 -> entry guard fails

    def s_dense(ss):
        # fill a NW block so scanners run far (large iVar5/iVar6)
        ss.set_cur(8, 8)
        for yy in range(4, 12):
            for xx in range(4, 12):
                ss.set_class_pixel(xx, yy, b0=1)

    def s_open_field(ss):
        # Document the all-zero default: down scanner (d6a0) breaks on
        # (*pcVar4=='\0') so iVar5 stays 1; right scanner similarly small.
        ss.set_cur(2, 2)

    def s_force_passthrough(ss):
        # Deliberately drive BOTH scanners far to fail the emit guard and
        # reach the count=0 passthrough branch.
        # down scanner d6a0 advances while: byte0(x,yy)!=0 AND byte1(x,yy)==0
        #   AND byte1(x-1,yy)==0  (pcVar4[-3] is (x-1) byte1). So set a column
        #   at x with byte0=1 for several rows below cur.
        # right scanner dbd0 advances while: byte1(xx,y)!=0 AND byte0(xx,y)==0
        #   AND byte1(xx,y-1)==0. So set a row at y with byte1=1 to the right.
        cx, cy = 8, 4
        ss.set_cur(cx, cy)
        for dy in range(1, 8):        # column below cur: byte0 set -> down walks
            ss.set_class_pixel(cx, cy + dy, b0=1)
        for dx in range(1, 8):        # row right of cur: byte1 set -> right walks
            ss.set_class_pixel(cx + dx, cy, b0=0, b1=1)
        # emit-guard second clause needs class_prev (byte at cur_x*4-1, i.e.
        # (cx-1) byte3) != 0 as well; set it so the whole guard fails.
        ss.set_class_pixel(cx - 1, cy, b0=0, b1=0, b2=0, b3=1)

    scenarios = [
        ("empty-around-cur(8,8)", s_empty),
        ("isolated-class@cur(8,8)", s_isolated),
        ("left-neighbour-set(7,8)", s_left_block),
        ("edge cur_x==0", s_edge_x0),
        ("edge cur_y==height-1", s_edge_ybottom),
        ("dense NW block", s_dense),
        ("open-field cur(2,2)", s_open_field),
        ("force-passthrough cur(8,4)", s_force_passthrough),
    ]
    r0004 = []
    for name, fn in scenarios:
        try:
            r = run_0004(name, fn)
        except Exception as exc:
            L.append(f"- **{name}**: 実行時エラー {exc!r}")
            continue
        r0004.append(r)
        L.append(f"- **{name}** cur={r['cur']}: entry_guard={r['entry_guard']}, "
                 f"iVar6(right)={r['right_scan']['iVar6']} (out={r['right_scan']['out']},"
                 f"code={r['right_scan']['code']}), iVar5(down)={r['down_scan']['iVar5']} "
                 f"(out={r['down_scan']['out']},code={r['down_scan']['code']}), "
                 f"class_prev_byte={r['class_prev_byte']}, emit_guard={r['emit_guard']}, "
                 f"**vcount={r['vcount']}**, verts={fmt_verts(r['vertices'])}")
    L.append("")

    # -- 0012 --
    L.append("## 0012 の分岐挙動（FUN_18000e170 / f270 / e3a0）")
    try:
        r12 = run_0012()
        L.append(f"- desc={r12['desc']}（record shape `91,841,1,91,843,5` を相対座標で再構成）")
        L.append(f"- **FUN_18000e170 bitsum c = {r12['e170_c']}**（record local: c=2）")
        L.append(f"- f270 scale 入力 = base_weight*DAT_180022dd8 + DAT_180022694 = {r12['f270_scale_input']:.8f}")
        f = r12["f270"]
        L.append(f"- **FUN_18000f270**: ret(append?)={f['ret']}, count={f['count']}, verts={fmt_verts(f['verts'])}")
        e0 = r12["e3a0_zero_src"]
        L.append(f"- FUN_18000e3a0 (src=0): ret={e0['ret']}, count={e0['count']}, "
                 f"**weight={e0['verts'][0]['weight']:.8f}** " if e0['verts'] else
                 f"- FUN_18000e3a0 (src=0): ret={e0['ret']}, count={e0['count']} (append 無し)")
        e1 = r12["e3a0_with_src"]
        if e1["verts"]:
            L.append(f"- FUN_18000e3a0 (src rgba=0.991): ret={e1['ret']}, count={e1['count']}, "
                     f"weight={e1['verts'][0]['weight']:.8f}, rgba={tuple(round(x,6) for x in e1['verts'][0]['rgba'])}")
        else:
            L.append(f"- FUN_18000e3a0 (src rgba=0.991): ret={e1['ret']}, count={e1['count']} (append 無し)")
    except Exception as exc:
        r12 = None
        import traceback
        L.append(f"- 0012 実行時エラー: {exc!r}")
        L.append("```")
        L.append(traceback.format_exc())
        L.append("```")
    L.append("")

    L.append("### 0012 e170 bitsum / append sweep")
    try:
        sweep12 = run_0012_bitsum_sweep()
        L.append(f"- desc={sweep12['desc']}, scale={sweep12['scale']:.8f}")
        L.append("| center_b0 | prev_b0 | left_b1 | e170 c | f270 count | e3a0 count |")
        L.append("| ---: | ---: | ---: | ---: | ---: | ---: |")
        for row in sweep12["rows"]:
            L.append(
                f"| {row['center_b0']} | {row['prev_b0']} | {row['left_b1']} | "
                f"{row['e170_c']} | {row['f270_count']} | {row['e3a0_count']} |"
            )
        suppressors = [
            f"(center={r['center_b0']},prev={r['prev_b0']},left_b1={r['left_b1']},c={r['e170_c']})"
            for r in sweep12["suppressing_rows"]
        ]
        L.append("- Suppressing / no-append local patterns: " + (", ".join(suppressors) if suppressors else "none"))
        L.append("- Reading: local Mac witness is `center=0, prev=1, left_b1=0 -> c=2 -> append`. "
                 "The only local e170/f270 no-append pattern in this three-byte sweep is "
                 "`center=0, prev=0, left_b1=1 -> c=4`. The `c=6` pattern still appends, so it is "
                 "not a suppression proof by itself. The next Windows proof should read the exact "
                 "three e170 bytes and the observed c value, not final writer bytes.")
    except Exception as exc:
        sweep12 = None
        import traceback
        L.append(f"- sweep 実行時エラー: {exc!r}")
        L.append("```")
        L.append(traceback.format_exc())
        L.append("```")
    L.append("")

    L.append("## 0004 scanner span sweep")
    try:
        sweep0004 = run_0004_scanner_sweep()
        L.append(f"- cur={tuple(sweep0004['cur'])}")
        L.append("| right_span | down_span | class_prev_b3 | iVar6 | iVar5 | emit_guard | vcount |")
        L.append("| ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
        for row in sweep0004["rows"]:
            L.append(
                f"| {row['right_span']} | {row['down_span']} | {row['class_prev_b3']} | "
                f"{row['iVar6']} | {row['iVar5']} | {row['emit_guard']} | {row['vcount']} |"
            )
        L.append(
            "- Reading: `FUN_180013140` no-emit happens in two local shapes: "
            "(1) both scanner spans reach >=4 (`iVar6>=4` and `iVar5>=4`), or "
            "(2) both spans reach >=2 while `class_prev_b3 != 0`. The earlier "
            "`force-passthrough` synthetic remains the stronger branch, with both "
            "spans long and `class_prev_b3=1`."
        )
        L.append(
            "- The earlier `left-neighbour-set(7,8)` scenario left `class_prev_byte=0` "
            "because the guard reads left-pixel byte3, not byte0. This sweep pins that "
            "byte-level requirement directly."
        )
    except Exception as exc:
        sweep0004 = None
        import traceback
        L.append(f"- 0004 scanner sweep 実行時エラー: {exc!r}")
        L.append("```")
        L.append(traceback.format_exc())
        L.append("```")
    L.append("")

    # -- divergence localisation --
    L.append("## Mac↔Windows 乖離の局在（取れた範囲）")
    L.append("- **0004 (1903,519)**: Windows writer は semitransparent gray "
             "`[103,103,103,113]` (raw 0xe8e8e871, float ~0.808/0.442)。Mac は "
             "count=0 passthrough で透明中心 `[1,1,1,0]`→`[0,0,0,0]`。上の scenario 群で "
             "「どの class-plane 状態で FUN_180013140 が頂点を append する／しないか」を "
             "binary で確定した（vcount 参照）。Windows 側の正解 class-plane 状態・"
             "cce0 出力 float は本 run では持たないため、Mac 分岐の fact 化までで停止。")
    L.append("- **0012 (91,841)**: Windows writer は透明 `0xffffff00`→`[0,0,0,0]`、Mac は "
             "cardinal6 append 生存 → cce0 blend で visible `[90,90,90,91]`。乖離は "
             "e170 の c 値（append 抑制の分岐点: c==4 で f270 が抑制）に局在する。"
             "本 run で Mac 側 e170 の実 c 値と f270/e3a0 の append 有無・weight を "
             "binary から確定した（上記）。Windows 側の実 c 値（class-plane 実状態）は "
             "本 run では未取得のため、そこが残差。")
    L.append("")

    L.append("## 残課題")
    L.append("- Windows 側の実 class-plane bytes / desc / cce0 出力 float は本 run に無い。"
             "上記は全て **Mac(=当該.aex) 側の分岐挙動の binary-grounding** であり、"
             "Windows 比較は writer-anchor（既確定）以外は未架橋。")
    L.append("- 0012 の完全 chain（FUN_1800125c0→FUN_180010760→c280 polygon builder→"
             "cce0 blend）は本 run では通していない（c280 polygon 構築の scaffold が別途必要）。"
             "producer の分岐点である e170/f270/e3a0 は直接駆動で確定済み。")
    L.append("- 0012 の座標は 16x16 world 上の相対座標 (5,6) で再構成（絶対 91/841 は"
             " world に収まらないが、class 近傍と desc 差分のみが producer 判定に効く）。"
             "これは INFERRED な座標移送であり、絶対座標依存の分岐が別に無いことは"
             " decomp 上は確認したが Windows 実データでは未確認。")

    report = "\n".join(L) + "\n"
    out_path = Path(__file__).parent / "SMOOTHER2_PRODUCER_EMU_REPORT.md"
    out_path.write_text(report)
    json_path = REPO_ROOT / "refs" / "conformance" / "olmsmoother2_producer_branch_sweep_20260708.json"
    md_path = REPO_ROOT / "refs" / "conformance" / "olmsmoother2_producer_branch_sweep_20260708.md"
    payload = {
        "kind": "olmsmoother2_producer_branch_sweep",
        "source": "tools/emulation/test_smoother2_producer.py",
        "aex": str(AEX_PATH.relative_to(REPO_ROOT)),
        "leaf": leaf,
        "case_0004": r0004,
        "case_0004_scanner_sweep": sweep0004,
        "case_0012": r12,
        "case_0012_bitsum_sweep": sweep12,
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(report, encoding="utf-8")
    print(report)
    print(f"wrote_json={json_path}")
    print(f"wrote_md={md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
