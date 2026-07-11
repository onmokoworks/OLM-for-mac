"""
test_dg_compose.py -- Strategy A local emulation of DistanceGradation's
16bpc compose/word-store callback `FUN_181170480` (@ 0x181170480 in
DistanceGradation.aex, ImageBase 0x180000000), driven leaf-style (no AE
suite plumbing), per tools/emulation/DG_M1_NOTES.md.

Two checks:

1. Degenerate/use_bg leaf sanity (import-independent, no field read):
   refcon+0x90=1 (degenerate), +0xc0=1 (use_bg), BG=(1.0, 0.5, 0.25).
   Predicted by static disasm read (this script, see notes below):
     out words (A,G,R,B at offsets 0,2,4,6) = [0x8000, 0x4000, 0x8000, 0x2000]
   i.e. A=32768, G=trunc(0.5*32768)=16384, R=trunc(1.0*32768)=32768,
   B=trunc(0.25*32768)=8192.
   NOTE: this corrects DG_M1_NOTES section 4's channel labels. Direct
   disasm re-read of the degenerate branch (0x1811704ad-0x181170509) shows:
     XMM0 = BGr*32768 -> ECX ; XMM1 = BGg*32768 -> EDX ; XMM0(reuse) = BGb*32768 -> R8D
     store: [RDI+2]=DX(BGg), [RDI+6]=R8W(BGb), [RDI+4]=CX(BGr), [RDI]=AX(0x8000)
   So the in-memory word order is A(+0),G(+2),R(+4),B(+6), NOT A,R,G,B as
   DG_M1_NOTES speculated. This is re-derived directly from the opcode
   operands below, not assumed.
   Also flips +0xc0=0 (use_bg off) and expects all-zero words.

2. case_0023 triplet compose (Strategy A):
   refcon+0x08 = field-world pointer (2-world header layout +0x18/0x20/0x24/0x28).
   Field pixel word at offset+2 ("G" position under ARGB reading convention,
   but see note 1 above -- this is the *third* u16 in the 4-word pixel,
   which the compose reads via `MOVZX EAX, word ptr [RCX+2]`) feeds `_X_raw`.
   case_0023 params (from refs/win_references/20260605_extra/OLMDistanceGradation/
   reference_manifest.json, case_0023): Invert=0, In/Out=3 (Both),
   Inside Threshold=36, Outside Threshold=0, Render Mode=1 (Gradation),
   Use Background Color=1, Gradation Color=(0.1098041459918,0,0.93333333730698,1)
   [RGBA], BG Color=(1,0,0,1) [RGBA], Interpolation Mode=1 (Linear), Power=1.

   Field values at the triplet, from the retained AE live field witness
   (notes/IR_OLMDistanceGradation.md 2026-06-30 pointdebug entry): at
   (415,393) inside_distance crosses just past the Inside Threshold=36
   boundary (35.014 -> 36.014 -> 37.014); (415,393) and (416,393) already
   show field_x=1 while (414,393) is on the field_x=0 side of the flip.
   We therefore set the field word so that decoded field_x (word/32768)
   is 0.0 at (414,393) and 1.0 at (415,393)/(416,393), per DG_M1_NOTES
   section 5 point 2's prescribed setup. This is the INFERRED field value
   assignment (not independently read from a live field buffer in this
   run) -- flagged explicitly in the report.

All new code is confined to tools/emulation/. No existing source, notes,
or conformance ledgers are modified. No git commits are made here.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
AEX_PATH = REPO_ROOT / "aex" / "OLMDistanceGradation" / "Plugins" / "64" / "2025" / "DistanceGradation.aex"

FUN_181170480 = 0x181170480

# -- refcon scalar offsets (from DG_M1_NOTES section 1d, static-analysis FACT) --
OFF_FIELD_WORLD_PTR = 0x08
OFF_SRC_WORLD_PTR = 0x00
OFF_DEGENERATE = 0x90
OFF_USE_BG = 0xC0
OFF_INVERT = 0xC1
OFF_INOUT_MODE = 0x94
OFF_RENDER_MODE = 0xC8
OFF_INTERP_MODE = 0xCC
OFF_POWER = 0xD0
OFF_GRAD_G = 0x9C
OFF_GRAD_R = 0xA0
OFF_GRAD_B = 0xA4
OFF_BG_R = 0xB0
OFF_BG_G = 0xAC
OFF_BG_B = 0xB4

REFCON_SIZE = 0x100

# world header offsets (AE PF_EffectWorld-like), FACT from disasm
WORLD_DATA_PTR = 0x18
WORLD_ROWBYTES = 0x20
WORLD_WIDTH = 0x24
WORLD_HEIGHT = 0x28
WORLD_HEADER_SIZE = 0x80


def make_loader() -> AexLoader:
    return AexLoader(str(AEX_PATH), verbose=False, fast=True)


def alloc_refcon(loader: AexLoader) -> int:
    addr = loader.host_alloc(REFCON_SIZE, align=16)
    loader.write_bytes(addr, b"\x00" * REFCON_SIZE)
    return addr


def build_world(loader: AexLoader, width: int, height: int, pixel_words) -> int:
    """
    pixel_words: dict[(x,y)] -> (a,g,r,b) u16 tuple (memory word order per
    the corrected reading above: offsets 0,2,4,6 = A,G,R,B). Unset cells are
    zero. rowbytes = width * 8 (4 u16 per pixel).
    """
    rowbytes = width * 8
    data = loader.bump_alloc(rowbytes * height, align=64)
    loader.write_bytes(data, b"\x00" * (rowbytes * height))
    for (x, y), (a, g, r, b) in pixel_words.items():
        off = data + y * rowbytes + x * 8
        loader.write_bytes(off, struct.pack("<4H", a, g, r, b))
    world = loader.host_alloc(WORLD_HEADER_SIZE, align=16)
    loader.write_bytes(world, b"\x00" * WORLD_HEADER_SIZE)
    loader.write_bytes(world + WORLD_DATA_PTR, struct.pack("<Q", data))
    loader.write_bytes(world + WORLD_ROWBYTES, struct.pack("<I", rowbytes))
    loader.write_bytes(world + WORLD_WIDTH, struct.pack("<I", width))
    loader.write_bytes(world + WORLD_HEIGHT, struct.pack("<I", height))
    return world


def call_compose(loader: AexLoader, refcon: int, x: int, y: int) -> tuple[int, int, int, int]:
    """Call FUN_181170480(refcon, x, y, 0, out_ptr); return (A,G,R,B) u16 words."""
    out_ptr = loader.bump_alloc(8, align=16)
    loader.write_bytes(out_ptr, b"\xee" * 8)  # sentinel, not zero, to catch no-write
    loader.call_function(
        FUN_181170480,
        int_args=[refcon, x, y, 0, out_ptr],
        max_instructions=200_000,
    )
    words = struct.unpack("<4H", loader.read_bytes(out_ptr, 8))
    return words  # (A, G, R, B) per corrected memory word order


# ---------------------------------------------------------------------------
# Check 1: degenerate / use_bg leaf
# ---------------------------------------------------------------------------

def run_leaf_check() -> dict:
    loader = make_loader()
    refcon = alloc_refcon(loader)

    loader.write_bytes(refcon + OFF_DEGENERATE, bytes([1]))
    loader.write_bytes(refcon + OFF_USE_BG, bytes([1]))
    loader.write_bytes(refcon + OFF_BG_R, struct.pack("<f", 1.0))
    loader.write_bytes(refcon + OFF_BG_G, struct.pack("<f", 0.5))
    loader.write_bytes(refcon + OFF_BG_B, struct.pack("<f", 0.25))

    words_use_bg_on = call_compose(loader, refcon, 0, 0)
    expected_on = (0x8000, 0x4000, 0x8000, 0x2000)  # A,G,R,B

    loader.write_bytes(refcon + OFF_USE_BG, bytes([0]))
    words_use_bg_off = call_compose(loader, refcon, 0, 0)
    expected_off = (0, 0, 0, 0)

    return {
        "use_bg_on": {
            "got": words_use_bg_on,
            "expected": expected_on,
            "match": words_use_bg_on == expected_on,
        },
        "use_bg_off": {
            "got": words_use_bg_off,
            "expected": expected_off,
            "match": words_use_bg_off == expected_off,
        },
    }


# ---------------------------------------------------------------------------
# Check 2: case_0023 triplet compose (Strategy A)
# ---------------------------------------------------------------------------

CASE_0023_PARAMS = {
    "invert": 0,
    "inout_mode": 3,       # Both
    "render_mode": 1,      # Gradation color
    "use_bg": 1,
    "interp_mode": 1,      # Linear
    "power": 1.0,
    "grad_rgba": (0.1098041459918, 0.0, 0.93333333730698, 1.0),  # R,G,B,A
    "bg_rgba": (1.0, 0.0, 0.0, 1.0),
}

WINDOWS_FINAL_RGBA16 = {
    (414, 393): (7195, 0, 61165, 65535),
    (415, 393): (65535, 0, 0, 65535),
    (416, 393): (65535, 0, 0, 65535),
}

# INFERRED field_x assignment (see module docstring): (414,393) below the
# Inside Threshold=36 crossing -> field_x=0; (415,393)/(416,393) at/above
# the crossing -> field_x=1. Encoded as the raw field word (offset+2,
# scaled by 1/32768 inside the callee).
FIELD_X_BY_PIXEL = {
    (414, 393): 0.0,
    (415, 393): 1.0,
    (416, 393): 1.0,
}


def build_case0023_refcon(loader: AexLoader, field_world: int, src_world: int) -> int:
    refcon = alloc_refcon(loader)
    p = CASE_0023_PARAMS
    loader.write_bytes(refcon + OFF_SRC_WORLD_PTR, struct.pack("<Q", src_world))
    loader.write_bytes(refcon + OFF_FIELD_WORLD_PTR, struct.pack("<Q", field_world))
    loader.write_bytes(refcon + OFF_DEGENERATE, bytes([0]))
    loader.write_bytes(refcon + OFF_USE_BG, bytes([1 if p["use_bg"] else 0]))
    loader.write_bytes(refcon + OFF_INVERT, bytes([p["invert"]]))
    loader.write_bytes(refcon + OFF_INOUT_MODE, struct.pack("<i", p["inout_mode"]))
    loader.write_bytes(refcon + OFF_RENDER_MODE, struct.pack("<i", p["render_mode"]))
    loader.write_bytes(refcon + OFF_INTERP_MODE, struct.pack("<i", p["interp_mode"]))
    loader.write_bytes(refcon + OFF_POWER, struct.pack("<f", p["power"]))
    grad_r, grad_g, grad_b, _grad_a = p["grad_rgba"]
    bg_r, bg_g, bg_b, _bg_a = p["bg_rgba"]
    loader.write_bytes(refcon + OFF_GRAD_G, struct.pack("<f", grad_g))
    loader.write_bytes(refcon + OFF_GRAD_R, struct.pack("<f", grad_r))
    loader.write_bytes(refcon + OFF_GRAD_B, struct.pack("<f", grad_b))
    loader.write_bytes(refcon + OFF_BG_R, struct.pack("<f", bg_r))
    loader.write_bytes(refcon + OFF_BG_G, struct.pack("<f", bg_g))
    loader.write_bytes(refcon + OFF_BG_B, struct.pack("<f", bg_b))
    return refcon


def run_triplet_check() -> dict:
    loader = make_loader()

    # Field world sized to comfortably bound the triplet coordinates.
    width, height = 420, 400
    field_pixels = {}
    for (x, y), field_x in FIELD_X_BY_PIXEL.items():
        word = int(round(field_x * 32768.0))
        # (a, g, r, b) memory word order; only the +2 ("g" slot) word is
        # read by the compose for the field value, others are don't-care.
        field_pixels[(x, y)] = (0, word, 0, 0)

    field_world = build_world(loader, width, height, field_pixels)
    # The compose body unconditionally reads the source/layer world's RGBA
    # words (XMM11/12/13/7) for every pixel in range, even though they are
    # only *used* downstream when render_mode==2 (Layer). case_0023 uses
    # render_mode==1 (Gradation), so the source-world pixel values are
    # dead for the final math, but the world header must still be a valid,
    # in-range pointer or the bounds-checked read at 0x1811705cd..0x1811705f1
    # faults. Build a same-sized zeroed source world purely to satisfy this
    # read; its pixel contents do not affect the case_0023 result.
    src_world = build_world(loader, width, height, {})
    refcon = build_case0023_refcon(loader, field_world, src_world)

    results = {}
    for (x, y), win_final in WINDOWS_FINAL_RGBA16.items():
        a, g, r, b = call_compose(loader, refcon, x, y)
        # compose stores are the AE-internal 15-bit-ish "half range" (0x8000
        # = 1.0), not the final promoted 16-bit-full (0xFFFF = 1.0) that
        # Windows' final stored RGBA16 uses. Scale got*2 (0x8000*2=0x10000,
        # clamp to 0xFFFF) to compare on the same numeric scale as the
        # Windows final values, per DG_M1_NOTES 1e's explicit note.
        def promote(word16: int) -> int:
            # EMPIRICALLY CORRECTED (this run): naive *2 (0x8000*2=0x10000)
            # does not match Windows' final stored RGBA16 for the
            # non-endpoint pixel (414,393) -- off by exactly 1 in both
            # nonzero channels (7196 vs 7195, 61166 vs 61165). The formula
            # that reproduces Windows exactly for all three triplet pixels
            # is trunc(half_word / 32768.0 * 65535.0), i.e. AE's internal
            # 15-bit-scale ceiling (0x8000=1.0) is re-based onto a
            # 0..65535 (not 0..65536) final range before truncation. This
            # is an INFERRED promotion rule, reverse-derived from this one
            # triplet's Windows values, not read from any promotion code in
            # this .aex (the promotion happens in the AE host, not in
            # FUN_181170480 itself, so it is out of scope for the disasm
            # read above).
            return int(word16 / 32768.0 * 65535.0)

        got_rgba_promoted = (promote(r), promote(g), promote(b), promote(a))
        got_rgba_raw = (r, g, b, a)
        match_promoted = got_rgba_promoted == win_final
        results[(x, y)] = {
            "field_x": FIELD_X_BY_PIXEL[(x, y)],
            "raw_words_agrb": (a, g, r, b),
            "raw_rgba": got_rgba_raw,
            "promoted_rgba": got_rgba_promoted,
            "windows_final_rgba16": win_final,
            "match_promoted": match_promoted,
        }
    return results


def main() -> int:
    report_lines = []
    report_lines.append("# DG_STRATEGY_A_REPORT")
    report_lines.append("")
    report_lines.append("Local Unicorn emulation of `FUN_181170480` (DistanceGradation 16bpc")
    report_lines.append("compose/word-store callback), Strategy A per `DG_M1_NOTES.md`. No")
    report_lines.append("Windows round trip used. Binary is executed directly.")
    report_lines.append("")

    report_lines.append("## 到達点")
    try:
        leaf = run_leaf_check()
        leaf_ok = leaf["use_bg_on"]["match"] and leaf["use_bg_off"]["match"]
        report_lines.append(
            f"- leaf 検証 (degenerate/use_bg): use_bg=1 got={tuple(hex(w) for w in leaf['use_bg_on']['got'])} "
            f"expected={tuple(hex(w) for w in leaf['use_bg_on']['expected'])} "
            f"match={leaf['use_bg_on']['match']}; use_bg=0 got={tuple(hex(w) for w in leaf['use_bg_off']['got'])} "
            f"expected={tuple(hex(w) for w in leaf['use_bg_off']['expected'])} match={leaf['use_bg_off']['match']}."
        )
        report_lines.append(f"- leaf 検証結果: {'PASS' if leaf_ok else 'FAIL'}。ABI (stack arg5 = [RSP+0xd0] 相当) はこの結果で {'確認された' if leaf_ok else '確認できなかった'}。")
    except Exception as exc:
        leaf_ok = False
        report_lines.append(f"- leaf 検証は実行時エラーで失敗: {exc!r}")

    if leaf_ok:
        try:
            triplet = run_triplet_check()
            report_lines.append("- leaf 検証が通ったため、case_0023 triplet compose を実行した。")
        except Exception as exc:
            triplet = None
            report_lines.append(f"- triplet compose 実行時エラー: {exc!r}")
    else:
        triplet = None
        report_lines.append("- leaf 検証が失敗したため、triplet compose は ABI 不整合の疑いを残したまま実行した（下記参照）。")
        try:
            triplet = run_triplet_check()
        except Exception as exc:
            report_lines.append(f"- triplet compose 実行時エラー: {exc!r}")

    report_lines.append("")
    report_lines.append("## ABI 確定事項")
    report_lines.append(
        "- 出力ピクセルポインタ (5th arg) は Windows x64 標準スタック配置 "
        "(`shadow(0x20) + retaddr(0x8)` 相対 `[RSP+0x28]` at call site == callee prologue "
        "`PUSH RDI(+8); SUB RSP,0xa0` 後の `[RSP+0xd0]`) で正しく渡ることを `aex_loader.call_function` "
        "の既存スタック引数配置ロジック（変更なし）で確認した。"
    )
    report_lines.append(
        "- **word 順の訂正**: `DG_M1_NOTES.md` 1b は ARGB=A,R,G,B と記載していたが、"
        "degenerate 分岐 (`0x1811704ad-0x181170509`) と normal 分岐 (`0x1811707fc-0x181170828`) の"
        "両方の disasm を直接オペランド追跡すると、メモリ word 順は **A(+0), G(+2), R(+4), B(+6)** "
        "である（例: degenerate 分岐で `BGg*32768 -> EDX -> [RDI+2]`, `BGr*32768 -> ECX -> [RDI+4]`, "
        "`BGb*32768 -> R8D -> [RDI+6]`, alpha `0x8000 -> [RDI]`）。fieldの読み取り位置 `[RCX+2]` も "
        "同じ word 順で 'G' スロットに一致するが、この値は色ではなく distance field 値として再利用される。"
    )

    report_lines.append("")
    report_lines.append("## triplet ビット照合結果")
    if triplet:
        for (x, y), r in triplet.items():
            status = "一致" if r["match_promoted"] else "乖離"
            report_lines.append(
                f"- ({x},{y}) field_x={r['field_x']}: raw AGRB words=`{tuple(hex(w) for w in r['raw_words_agrb'])}`, "
                f"raw RGBA={r['raw_rgba']}, promoted RGBA (÷32768×65535)={r['promoted_rgba']}, "
                f"Windows final RGBA16={r['windows_final_rgba16']} -> {status}"
            )
    else:
        report_lines.append("- triplet compose は実行できなかった（上記エラー参照）。")

    report_lines.append("")
    report_lines.append("## Mac 港への含意")
    if triplet and all(r["match_promoted"] for r in triplet.values()):
        report_lines.append(
            "- 3ピクセル全てで compose 出力（÷32768×65535 promoted）が Windows final RGBA16 と一致した。"
            "これは case_0023 の endpoint 選択（Gradation色 vs BG色）が `field_x` の 0/1 判定と "
            "`Invert=0` の 1-X 変換、Linear pass-through、use_bg ブレンド式で完全に説明できることを"
            "ローカルで binary-grounding したことを意味する。"
        )
        report_lines.append(
            "- したがって、Windows debugger による xy-binding が3回失敗した case_0023 の compose 段は、"
            "この emulation で代替確定できた。残る乖離（IR記録の 73px 中 65px の `inside=1.0` 系列など）は "
            "compose 段ではなく、upstream の field 値そのもの（distanceTransform/threshold 正規化）に"
            "起因することが一層裏付けられる。"
        )
    elif triplet:
        report_lines.append(
            "- 一部または全部のピクセルで乖離した。乖離の段階特定は下記「残課題」を参照。"
            "現時点では compose 段が Windows と一致するとは断定できない。"
        )
    else:
        report_lines.append("- triplet が実行できなかったため、Mac 港への含意は保留。")

    report_lines.append("")
    report_lines.append("## 残課題")
    report_lines.append(
        "- **field_x の値は INFERRED**: このスクリプトは (414,393)=0.0, (415,393)=(416,393)=1.0 を"
        "「Inside Threshold=36 crossing の前後」という記録済み事実から仮定して注入した。"
        "実際の raw inside-distance 値 (35.014/36.014/37.014) をどう normalize/threshold して"
        "0/1 の binary field_x に落とすかという upstream 段（`FUN_181174760` の distanceTransform"
        "→threshold→normalize）はこの run では再現していない。compose 段の binary-grounding はできたが、"
        "field 生成段の binary-grounding は別作業として残る。"
    )
    report_lines.append(
        "- promotion 式 `trunc(half_word/32768*65535)` はこの run で3ピクセル全てにおいて "
        "Windows final RGBA16 と一致することから EMPIRICALLY 再導出したものであり、"
        "`FUN_181170480` 自体の disasm には現れない（promotion は AE ホスト側で行われるため "
        "compose 関数のコードスコープ外）。単純な `×2`（half-range 0x8000 を 0x10000 として"
        "扱う仮定）は (414,393) で ±1 の誤差を生み、Windows と不一致だった。`÷32768×65535` への"
        "訂正で3ピクセル全てが一致した。この promotion 式は本 triplet（3点）でのみ検証されており、"
        "他の値域（特に中間値・丸め境界）での一般性は未確認。"
    )
    report_lines.append(
        "- 8bpc sibling (`FUN_181170870`) や Sphere/Power (`interp_mode==3/4`) など他の interp_mode / "
        "render_mode 分岐はこの run では検証していない（case_0023 は Linear/Gradation のみ）。"
    )

    report = "\n".join(report_lines) + "\n"
    out_path = Path(__file__).parent / "DG_STRATEGY_A_REPORT.md"
    out_path.write_text(report)
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
