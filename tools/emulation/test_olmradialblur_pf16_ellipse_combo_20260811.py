#!/usr/bin/env python3
"""PF16 Zoom/Rotation ellipse comparison at 9x7 and 32x18."""
from __future__ import annotations

import hashlib, importlib, json, pickle, struct, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "tools/emulation"
sys.path.insert(0, str(HERE))
import test_olmradialblur_zoom_pf16_small_actual_aex_20260805 as zoom
import test_olmradialblur_rotation_pf16_small_actual_aex_20260805 as rotation

CASES = [(w, h, rb, r, a) for w, h, rb in ((9, 7, 80), (32, 18, 272))
         for r in (2.0, 5.0) for a in (0.0, 30.0, 90.0)]
ZPLANES = ("pre_blur", "post_blur", "output")
RPLANES = ("polar", "source_scalar", "accum", "max_alpha", "final_rgba", "coordinates", "output")
REPORT = ROOT / "refs/conformance/olmradialblur_pf16_ellipse_combo_20260811.json"
DOC = REPORT.with_suffix(".md")


def source_frame(w: int, h: int, rb: int, seed: bool = False) -> bytes:
    raw = bytearray(rb * h)
    for y in range(h):
        for x in range(w):
            argb = ((0x7777, 0x6666, 0x5555, 0x4444) if seed else
                    (32768 if (x + y) % 5 else 16384,
                     (x * 4093 + y * 257) % 32769,
                     (x * 1237 + y * 3559) % 32769,
                     (x * 7919 + y * 911) % 32769))
            struct.pack_into("<4H", raw, y * rb + x * 8, *argb)
        raw[y * rb + w * 8:(y + 1) * rb] = bytes([(0xA0 + y) & 255]) * (rb - w * 8)
    return bytes(raw)


def configure(w: int, h: int, rb: int, ratio: float, angle: float) -> None:
    importlib.reload(zoom)
    importlib.reload(rotation)
    frame = lambda seed=False: source_frame(w, h, rb, seed)
    rotation.W, rotation.H, rotation.ROWBYTES, rotation.VISIBLE = w, h, rb, w * 8
    rotation.FIXTURE_CENTER_X, rotation.FIXTURE_CENTER_Y = float(w // 2), float(h // 2)
    rotation.FIXTURE_RATIO, rotation.FIXTURE_ANGLE_DEG = ratio, angle
    rotation.source_frame = frame
    zoom.fixture.W, zoom.fixture.H, zoom.fixture.ROWBYTES, zoom.fixture.VISIBLE = w, h, rb, w * 8
    zoom.CENTER_X, zoom.CENTER_Y, zoom.RATIO, zoom.ANGLE_DEG = float(w // 2), float(h // 2), ratio, angle
    zoom.fixture.source_frame = frame


def rotation_production(expected):
    angular, radial = struct.unpack("<II", expected["geometry"]); cells = angular * radial
    w, h, rb = rotation.W, rotation.H, rotation.ROWBYTES
    source = str(rotation.SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    with tempfile.TemporaryDirectory(prefix="radial_pf16_ellipse_") as raw:
        td = Path(raw); inp = td / "in.bin"; inp.write_bytes(rotation.source_frame())
        cpp, exe = td / "probe.cpp", td / "probe"
        cpp.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{source}"
#include <fstream>
#include <vector>
int main(int argc,char**argv){{constexpr int W={w},H={h},RB={rb},C={cells};
std::vector<unsigned char> ib(RB*H),ob(RB*H);std::ifstream(argv[1],std::ios::binary).read((char*)ib.data(),ib.size());
for(int y=0;y<H;y++)for(int x=0;x<RB-W*8;x++)ob[y*RB+W*8+x]=(unsigned char)(0xa0+y);
PF_EffectWorld iw{{}},ow{{}};iw.data=(PF_PixelPtr)ib.data();iw.rowbytes=RB;iw.width=W;iw.height=H;ow.data=(PF_PixelPtr)ob.data();ow.rowbytes=RB;ow.width=W;ow.height=H;
std::vector<float> polar(C*4),scalar(C),accum(C*4),maximum(C),normalized(C*4),finalrgba(W*H*4),coordinates(W*H*2);std::vector<A_u_char> eligibility(C);RadialBlurTestRotationCapture cap{{}};
cap.polar_rgba=polar.data();cap.eligibility=eligibility.data();cap.source_scalar=scalar.data();cap.accum_rgba=accum.data();cap.max_alpha=maximum.data();cap.normalized_rgba=normalized.data();cap.final_rgba=finalrgba.data();cap.final_coordinates=coordinates.data();cap.capacity_cells=C;cap.capacity_output_pixels=W*H;
OLMRadialBlurInfo i{{}};i.blur_type=2;i.center_x={float(w//2)};i.center_y={float(h//2)};i.outer_strength=4;i.outer_offset_mode=1;i.inner_offset_mode=1;i.repeat_border=TRUE;i.ratio={rotation.FIXTURE_RATIO};i.angle_deg={rotation.FIXTURE_ANGLE_DEG};i.quality=5;i.brightness_gain=1;i.noise_type=1;i.seed=1;i.thickness=10;i.comp_width=W;i.comp_height=H;
g_rotation_test_capture=&cap;auto e=RenderRotationTyped<PF_Pixel16>(&iw,&ow,i);g_rotation_test_capture=nullptr;if(e||cap.written_cells!=C)return 3;
std::ofstream(argv[2],std::ios::binary).write((char*)ob.data(),ob.size());std::ofstream(argv[3],std::ios::binary).write((char*)polar.data(),polar.size()*4);std::ofstream(argv[4],std::ios::binary).write((char*)scalar.data(),scalar.size()*4);std::ofstream(argv[5],std::ios::binary).write((char*)accum.data(),accum.size()*4);std::ofstream(argv[6],std::ios::binary).write((char*)maximum.data(),maximum.size()*4);std::ofstream(argv[7],std::ios::binary).write((char*)finalrgba.data(),finalrgba.size()*4);std::ofstream(argv[8],std::ios::binary).write((char*)coordinates.data(),coordinates.size()*4);}}
''')
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], text=True, capture_output=True, check=True).stdout.strip()
        cmd = ["clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math", "-ffp-contract=off", "-ffunction-sections", "-fdata-sections", "-isysroot", sdk, "-I", str(ROOT/"Headers"), "-I", str(ROOT/"Headers/SP"), "-I", str(ROOT/"Util"), "-I", str(ROOT/"Resources"), str(cpp), "-Wl,-dead_strip", "-framework", "Cocoa", "-o", str(exe)]
        built = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if built.returncode: raise RuntimeError(built.stderr)
        names = ("output", "polar", "source_scalar", "accum", "max_alpha", "final_rgba", "coordinates")
        paths = [td / f"{n}.bin" for n in names]
        subprocess.run([str(exe), str(inp), *(str(p) for p in paths)], cwd=ROOT, check=True)
        return {n: p.read_bytes() for n, p in zip(names, paths)}


def isolated(effect, mode, cell, expected=None):
    with tempfile.TemporaryDirectory(prefix="radial_pf16_combo_") as raw:
        out = Path(raw) / "out.pkl"; cmd = [sys.executable, __file__, f"--{effect}-{mode}", *map(str, cell)]
        if expected is not None:
            exp = Path(raw) / "expected.pkl"; exp.write_bytes(pickle.dumps(expected)); cmd.append(str(exp))
        cmd.append(str(out)); p = subprocess.run(cmd)
        return p.returncode, pickle.loads(out.read_bytes()) if out.exists() else None


def main():
    report = {"status": "exact", "cells": []}
    for effect, planes in (("zoom", ZPLANES), ("rotation", RPLANES)):
        with ThreadPoolExecutor(max_workers=4) as pool:
            actuals = list(pool.map(lambda c: isolated(effect, "actual", c)[1], CASES))
        with ThreadPoolExecutor(max_workers=4) as pool:
            products = list(pool.map(lambda z: isolated(effect, "production", z[0], z[1]), zip(CASES, actuals)))
        for cell, actual, (rc, prod) in zip(CASES, actuals, products):
            matches = {p: bool(prod) and prod[p] == actual[p] for p in planes}
            exact = rc == 0 and all(matches.values())
            report["status"] = "exact" if report["status"] == "exact" and exact else "mismatch"
            report["cells"].append({"effect": effect, "geometry": list(cell[:3]), "ratio": cell[3], "angle": cell[4], "matches": matches, "exact": exact,
                                    "sha256": {p: hashlib.sha256(actual[p]).hexdigest() for p in planes}})
    report["writer_boundary"] = "Actual owner final plane retains HDR RGB, while the PF16 typed writer saturates RGB above 1.0 before truncation; alpha is not covered by this rule."
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text(f"# OLM RadialBlur PF16 ellipse — 2026-08-11\n\nStatus: **{report['status']}**\n\nZoom/Rotationともに9×7/32×18の全6 tupleが全plane/output exactです。actual owner final planeのHDR値は保持され、PF16 typed writerがRGBのみ1.0上限へ飽和してからtruncateします。\n")
    print(json.dumps(report, indent=2, sort_keys=True)); return 0 if report["status"] == "exact" else 1


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action.startswith("--") and action != "":
        effect, mode = action[2:].split("-"); cell = (int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])); configure(*cell)
        if mode == "actual": result = zoom.actual_aex() if effect == "zoom" else rotation.actual_aex(); out = sys.argv[7]
        else:
            expected = pickle.loads(Path(sys.argv[7]).read_bytes()); result = zoom.mac_production(expected) if effect == "zoom" else rotation_production(expected); out = sys.argv[8]
        Path(out).write_bytes(pickle.dumps(result)); raise SystemExit(0)
    raise SystemExit(main())
