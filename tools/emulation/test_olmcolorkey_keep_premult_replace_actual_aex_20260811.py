#!/usr/bin/env python3
"""Actual-AEX Color Keep x Premultiplied x Replace public toggle matrix."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
import probe_olmcolorkey_pf16_full_worker_20260805 as actual_probe  # noqa: E402
import test_olmcolorkey_mac_smartrender_adapter_20260717 as mac_adapter  # noqa: E402

WIDTH, HEIGHT, PADDING = 11, 7, 8
FORMATS = {"PF8": 4, "PF16": 8, "PF32": 16}
TOGGLES = tuple((keep, premult, replace) for keep in (False, True)
                for premult in (False, True) for replace in (False, True))
REPLACEMENTS = ((0.90, 0.15, 0.10), (0.10, 0.35, 0.95))
REPORT = ROOT / "refs/conformance/olmcolorkey_keep_premult_replace_actual_aex_20260811.json"
MD = REPORT.with_suffix(".md")

CURRENT = TOGGLES[0]
_original_parameter_record = actual_probe.parameter_record


def role_at(x: int, y: int) -> str:
    roles = {
        (1, 1): "opaque_black", (8, 1): "opaque_green",
        (2, 3): "half_black", (7, 3): "half_green",
        (1, 5): "hidden_red", (5, 5): "hidden_green",
        (9, 5): "rejected_green",
    }
    return roles.get((x, y), "background")


def values(role: str, depth: str):
    alpha, red, green, blue = {
        "opaque_black": (1.0, 0.0, 0.0, 0.0),
        "opaque_green": (1.0, 0.0, 1.0, 0.0),
        "half_black": (0.5, 0.0, 0.0, 0.0),
        "half_green": (0.5, 0.0, 1.0, 0.0),
        "hidden_red": (0.0, 1.0, 0.0, 0.0),
        "hidden_green": (0.0, 0.0, 1.0, 0.0),
        "rejected_green": (1.0, 0.0, 0.75, 0.0),
        "background": (0.625, 0.25, 0.375, 0.50),
    }[role]
    if depth == "PF32":
        return (alpha, red, green, blue)
    maximum = 32768 if depth == "PF16" else 255
    return tuple(int(round(v * maximum)) for v in (alpha, red, green, blue))


def fixture(enabled_key: bool = False, key_shape: str = "single") -> tuple[bytes, int]:
    depth = actual_probe.PIXEL_FORMAT
    pb = FORMATS[depth]
    rb = WIDTH * pb + PADDING
    raw = bytearray([0xA5] * (rb * HEIGHT))
    fmt = "<4f" if depth == "PF32" else "<4H" if depth == "PF16" else "<4B"
    for y in range(HEIGHT):
        for x in range(WIDTH):
            struct.pack_into(fmt, raw, y * rb + x * pb, *values(role_at(x, y), depth))
    return bytes(raw), rb


def parameter_record(enabled_key: bool = False, edge_blur: float = 0.0,
                     edge_blur_direction: int = 2, key_count: int = 1,
                     edge_blur_distance_type: int = 2) -> bytes:
    keep, premult, replace = CURRENT
    payload = bytearray(_original_parameter_record(True, 0.0, 2, 2, 2))
    payload[0x24] = int(keep)
    payload[0x25] = int(premult)
    payload[0x4D] = int(replace)
    for i, rgb in enumerate(REPLACEMENTS):
        payload[0x53D + i] = int(replace)
        struct.pack_into("<3f", payload, 0x208 + i * 0x10, *rgb)
    return bytes(payload)


CUSTOM_MAIN = r'''
int main(){g_color_suite=g_color_suite_instance;g_ansi_suite=g_ansi_suite_instance;
constexpr int W=11,H=7,P=8;
for(int keep:{0,1})for(int premult:{0,1})for(int replace:{0,1})for(int depth:{8,16,32}){
 int ps=depth==8?4:depth==16?8:16,rb=W*ps+P;std::vector<std::uint8_t>inb(rb*H,0xA5),outb(rb*H,0xCC);
 auto role=[](int x,int y){if(x==1&&y==1)return 1;if(x==8&&y==1)return 2;if(x==2&&y==3)return 3;if(x==7&&y==3)return 4;if(x==1&&y==5)return 5;if(x==5&&y==5)return 6;if(x==9&&y==5)return 7;return 0;};
 for(int y=0;y<H;y++)for(int x=0;x<W;x++){int r=role(x,y);float a=r==1||r==2||r==7?1:r==3||r==4?.5f:r==5||r==6?0:.625f;float red=r==5?1:r?0:.25f;float green=r==2||r==4||r==6?1:r==7?.75f:r?0:.375f;float blue=r?0:.5f;auto*q=inb.data()+y*rb+x*ps;
  if(depth==8)*reinterpret_cast<PF_Pixel8*>(q)={(A_u_char)std::lround(a*255),(A_u_char)std::lround(red*255),(A_u_char)std::lround(green*255),(A_u_char)std::lround(blue*255)};
  else if(depth==16)*reinterpret_cast<PF_Pixel16*>(q)={(A_u_short)std::lround(a*32768),(A_u_short)std::lround(red*32768),(A_u_short)std::lround(green*32768),(A_u_short)std::lround(blue*32768)};
  else *reinterpret_cast<PF_PixelFloat*>(q)={a,red,green,blue};}
 PF_EffectWorld in{inb.data(),rb,W,H,(A_short)depth,{0,0,W,H},0},out{outb.data(),rb,W,H,(A_short)depth,{0,0,W,H},0};OLMColorKeyInfo info{};
 info.color_keep=keep;info.premultiplied=premult;info.number_of_colors=2;info.use_color[0]=info.use_color[1]=true;info.colors[0]={1,0,0,0};info.colors[1]={1,0,1,0};
 info.enable_replace=replace;info.use_replace_color[0]=info.use_replace_color[1]=replace;info.replace_colors[0]={1,.90f,.15f,.10f};info.replace_colors[1]={1,.10f,.35f,.95f};
 if(RenderWorld(&in,&out,info,(short)depth))return depth;std::fwrite(outb.data(),1,outb.size(),stdout);}
return 0;}
'''


def production() -> bytes:
    with tempfile.TemporaryDirectory(prefix="olmck_toggle_matrix_") as raw:
        directory = Path(raw)
        mac_adapter.compile_probe(directory)
        source = directory / "olmcolorkey_mac_smartrender_adapter_probe.cpp"
        source.write_text(source.read_text().replace("int main(){", "int legacy_main(){", 1) + CUSTOM_MAIN)
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True).stdout.strip()
        executable = directory / "toggle_matrix"
        build = subprocess.run(
            ["clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math",
             "-ffp-contract=off", "-isysroot", sdk, "-I", str(directory), str(source),
             "-framework", "Cocoa", "-o", str(executable)], cwd=ROOT,
            capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(build.stderr)
        run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True)
        if run.returncode:
            raise RuntimeError(run.stderr.decode(errors="replace"))
        return run.stdout


def main() -> int:
    global CURRENT
    actual_probe.WIDTH, actual_probe.HEIGHT = WIDTH, HEIGHT
    actual_probe.fixture, actual_probe.parameter_record = fixture, parameter_record
    actual = {}
    for toggles in TOGGLES:
        CURRENT = toggles
        for pixel_format in FORMATS:
            actual_probe.PIXEL_FORMAT = pixel_format
            actual[(*toggles, pixel_format)] = actual_probe.execute_case(
                actual_probe.AEX, True, 0.0, "single", 2, 2, 2)
    candidate = production()
    offset, rows, outputs, passed = 0, [], {}, True
    for keep, premult, replace in TOGGLES:
        for pixel_format, pixel_bytes in FORMATS.items():
            rowbytes = WIDTH * pixel_bytes + PADDING
            size = rowbytes * HEIGHT
            production_raw = candidate[offset:offset + size]
            offset += size
            case = actual[(keep, premult, replace, pixel_format)]
            actual_raw = b"".join(bytes.fromhex(row) + b"\xCC" * PADDING
                                  for row in case["captures"]["output_active_rows_hex"])
            exact = actual_raw == production_raw
            native = case["execution"]["hits"]["smart_worker"] == 1 and case["execution"]["hits"]["parameter_materialize"] == 1
            # The shared probe's legacy single-pixel gate is intentionally not
            # applicable to this seven-role fixture; native dispatch ownership
            # and raw output equality are asserted here instead.
            passed &= exact and native
            outputs[(keep, premult, replace, pixel_format)] = actual_raw
            rows.append({"color_keep": keep, "premultiplied": premult, "replace": replace,
                         "pixel_format": pixel_format, "status": "exact" if exact else "mismatch",
                         "bytes": size, "native_full_worker_path": native,
                         "shared_probe_status": case["status"],
                         "actual_sha256": hashlib.sha256(actual_raw).hexdigest(),
                         "production_sha256": hashlib.sha256(production_raw).hexdigest()})
    interactions = []
    for pixel_format in FORMATS:
        for keep in (False, True):
            for replace in (False, True):
                changed = outputs[(keep, False, replace, pixel_format)] != outputs[(keep, True, replace, pixel_format)]
                interactions.append({"pixel_format": pixel_format, "assertion": "premultiplied_changes_classifier", "color_keep": keep, "replace": replace, "passed": changed})
                passed &= changed
        for premult in (False, True):
            invisible = outputs[(False, premult, False, pixel_format)] == outputs[(False, premult, True, pixel_format)]
            visible = outputs[(True, premult, False, pixel_format)] != outputs[(True, premult, True, pixel_format)]
            interactions.extend([
                {"pixel_format": pixel_format, "assertion": "replace_invisible_when_color_keep_off", "premultiplied": premult, "passed": invisible},
                {"pixel_format": pixel_format, "assertion": "replace_visible_when_color_keep_on", "premultiplied": premult, "passed": visible},
            ])
            passed &= invisible and visible
    passed &= offset == len(candidate)
    report = {
        "schema_version": 1, "status": "exact" if passed else "mismatch",
        "fixture": {"dimensions": [WIDTH, HEIGHT], "row_padding_bytes": PADDING,
                    "keys": ["black", "green"],
                    "roles": ["opaque accepted keys", "fractional-alpha keys", "alpha-zero hidden red/green RGB", "rejected near-green", "fractional-alpha asymmetric background"]},
        "matrix": {"color_keep": [False, True], "premultiplied": [False, True],
                   "replace": [False, True], "pixel_formats": list(FORMATS)},
        "actual_aex_sha256": actual_probe.AEX_SHA256,
        "comparison": "actual AEX full worker versus production RenderWorld; full typed ARGB active bytes and every padding byte",
        "cases": rows,
        "interaction_assertions": interactions,
        "toggle_ownership": {
            "premultiplied": "input interpretation before classifier; RGB is multiplied by alpha only for comparison, while rejected writeback remains alpha-only and preserves hidden RGB",
            "color_keep": "inverts the classifier mask at writeback and gates replacement visibility",
            "replace": "changes RGB for accepted keyed pixels only when Color Keep is enabled; alpha classification is unchanged",
        },
        "claim_boundary": "Exact only for the declared 11x7 two-key padded fixture, Color Keep off/on, Premultiplied off/on, Replace off/on, and PF8/PF16/PF32 through the actual AEX full worker. Threshold, Edge, other key colors/counts, geometry, and native AE-host parameter materialization are not claimed.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    MD.write_text(
        "# OLMColorKey Color Keep × Premultiplied × Replace\n\n"
        f"Status: **{report['status']}**\n\n"
        "The 11x7 asymmetric two-key fixture covers accepted/rejected colors, fractional alpha, "
        "alpha-zero hidden RGB, and padded rows. All 24 public-toggle/depth cells compare the "
        "actual Windows AEX full worker against production output byte-for-byte.\n\n"
        "Toggle ownership: Premultiplied changes classifier input interpretation and rejected-pixel "
        "writeback; Color Keep inverts mask writeback and admits Replace; Replace changes accepted-key "
        "RGB without changing classification.\n\n"
        f"Boundary: {report['claim_boundary']}\n"
    )
    print(("PASS" if passed else "FAIL") +
          f"_OLMCOLORKEY_KEEP_PREMULT_REPLACE_ACTUAL_AEX_20260811 cases={len(rows)} bytes={offset}")
    return 0 if passed else 3


if __name__ == "__main__":
    raise SystemExit(main())
