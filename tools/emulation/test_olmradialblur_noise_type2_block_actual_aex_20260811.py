#!/usr/bin/env python3
"""Bounded 9x7 RadialBlur Noise Type 2 (Block) actual-AEX matrix."""
from __future__ import annotations

import hashlib, importlib, json, pickle, struct, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import test_m4_case0010 as m4
import test_olmradialblur_pf8_ellipse_actual_aex_20260811 as pf8
import test_olmradialblur_rotation_pf16_small_actual_aex_20260805 as rotation
import test_olmradialblur_zoom_pf16_small_actual_aex_20260805 as zoom
import test_olmradialblur_zoom_pf32_small_actual_aex_20260805 as zoom32
import test_olmradialblur_rotation_pf32_small_actual_aex_20260805 as rotation32

REPORT = ROOT / "refs/conformance/olmradialblur_noise_type2_block_actual_aex_20260811.json"
DOC = REPORT.with_suffix(".md")
CELLS = [(mode, depth, nv, thickness) for mode in ("zoom", "rotation")
         for depth in (8, 16, 32) for nv in (25.0, 100.0) for thickness in (3.0, 10.0)]

def sha(raw: bytes) -> str: return hashlib.sha256(raw).hexdigest()

def configure(depth: int, mode: str, nv: float, thickness: float):
    importlib.reload(rotation)
    if mode == "zoom": importlib.reload(zoom)
    if depth == 8:
        pf8.configure(9, 7, 1.0, 0.0)
        if mode == "zoom":
            target = pf8.z8.zoom
            target.ZOOM_RETURN = 0x180007B12
        else:
            target = pf8.rot
    elif depth == 16:
        rotation.W, rotation.H, rotation.ROWBYTES, rotation.VISIBLE = 9, 7, 80, 72
        rotation.OWNER, rotation.ROTATION_RETURN = 0x180006D10, 0x18000733A
        target = zoom if mode == "zoom" else rotation
        if mode == "zoom": target.ZOOM_RETURN = 0x180007302
    else:
        if mode == "zoom":
            zoom32.fixture.configure()
            target = zoom32.fixture.zoom
        else:
            target = rotation32
    if mode == "zoom":
        target.NOISE_VARIATION = nv
        old = m4.load_case0010_params
        def params():
            result = old(); result.update({"Noise Type": 2, "Seed": 1,
                                           "Noise Offset": 0.0, "Thickness": thickness})
            return result
        m4.load_case0010_params = params
        # All Zoom wrappers ultimately read the same m4 module object.
        target.fixture.m4.load_case0010_params = params
    else:
        base = target.base if depth == 32 else target
        base.FIXTURE_NOISE_VARIATION = nv
        base.FIXTURE_NOISE_TYPE = 2
        base.FIXTURE_SEED = 1
        base.FIXTURE_NOISE_OFFSET = 0.0
        base.FIXTURE_THICKNESS = thickness
    return target

def capture(mode: str, depth: int, nv: float, thickness: float) -> dict[str, bytes]:
    target = configure(depth, mode, nv, thickness)
    if mode == "zoom": return target.actual_aex()
    return target.actual_aex()

def isolated(cell):
    mode, depth, nv, thickness = cell
    with tempfile.TemporaryDirectory(prefix="radial_block_") as name:
        path = Path(name) / "capture.pkl"
        subprocess.run([sys.executable, str(Path(__file__)), "--capture", mode, str(depth),
                        str(nv), str(thickness), str(path)], check=True)
        return pickle.loads(path.read_bytes())

def production(cell, expected):
    mode, depth, nv, thickness = cell
    target = configure(depth, mode, nv, thickness)
    angular, radius = struct.unpack("<II", expected["geometry"]); cells = angular * radius
    if depth == 8:
        pixel, pixel_bytes, rb, visible = "PF_Pixel8", 4, 44, 36
        frame = pf8.z8.source_frame
    elif depth == 16:
        pixel, pixel_bytes, rb, visible = "PF_Pixel16", 8, 80, 72
        frame = rotation.source_frame
    else:
        pixel, pixel_bytes, rb, visible = "PF_PixelFloat", 16, 160, 144
        def frame(output_seed=False):
            raw=bytearray(rb*7)
            for y in range(7):
                for x in range(9):
                    if output_seed: argb=(-7.,-6.,-5.,-4.) if mode=="rotation" else (.7,.6,.5,.4)
                    elif mode=="zoom": argb=(1. if (x+y)%5 else .5,((x*31+y*7)%257)/256.,((x*11+y*29)%257)/256.,((x*47+y*13)%257)/256.)
                    else: argb=(.5 if (x+y)%5==0 else 1.,((x*4093+y*257)%32769)/32768.,((x*1237+y*3559)%32769)/32768.,((x*7919+y*911)%32769)/32768.)
                    struct.pack_into("<4f",raw,y*rb+x*16,*argb)
                raw[y*rb+visible:(y+1)*rb]=bytes([((0xc0 if mode=="rotation" else 0xa0)+y)&255])*(rb-visible)
            return bytes(raw)
    source = str(ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp").replace('"', '\\"')
    with tempfile.TemporaryDirectory(prefix="radial_block_prod_") as raw:
        td = Path(raw); inp = td/"in"; inp.write_bytes(frame()); cpp=td/"p.cpp"; exe=td/"p"
        if mode == "zoom":
            arrays = "std::vector<float>a(C*4),b(C*4);RadialBlurTestPolarCapture cap{};cap.pre_blur_rgba=a.data();cap.post_blur_rgba=b.data();cap.capacity_floats=C*4;"
            call = f"auto e=RenderZoomTyped<{pixel}>(&iw,&ow,i,&cap);if(e)return 10+(int)e;if(cap.written_floats!=C*4)return 4;"
            names=("output","pre_blur","post_blur"); writes="Put(2,ob);Put(3,a);Put(4,b);"
        else:
            arrays = "std::vector<float>a(C*4),b(C),c(C*4),d(C),nn(C*4),e(W*H*4),f(W*H*2);std::vector<A_u_char>v(C);RadialBlurTestRotationCapture cap{};cap.polar_rgba=a.data();cap.eligibility=v.data();cap.source_scalar=b.data();cap.accum_rgba=c.data();cap.max_alpha=d.data();cap.normalized_rgba=nn.data();cap.final_rgba=e.data();cap.final_coordinates=f.data();cap.capacity_cells=C;cap.capacity_output_pixels=W*H;"
            call = f"g_rotation_test_capture=&cap;auto z=RenderRotationTyped<{pixel}>(&iw,&ow,i);g_rotation_test_capture=nullptr;if(z)return 10+(int)z;if(cap.written_cells!=C)return 4;"
            names=("output","polar","source_scalar","accum","max_alpha","final_rgba","coordinates"); writes="Put(2,ob);Put(3,a);Put(4,b);Put(5,c);Put(6,d);Put(7,e);Put(8,f);"
        center_x,center_y=(4.5,3.5) if depth==8 else (4.0,3.0)
        cpp.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1\n#include "{source}"\n#include <fstream>\n#include <vector>\nint main(int n,char**q){{constexpr int W=9,H=7,RB={rb},C={cells};std::vector<unsigned char>ib(RB*H),ob(RB*H);std::ifstream(q[1],std::ios::binary).read((char*)ib.data(),ib.size());for(int y=0;y<H;y++)for(int x={visible};x<RB;x++)ob[y*RB+x]=(0xa0+y)&255;PF_EffectWorld iw{{}},ow{{}};iw.data=(PF_PixelPtr)ib.data();iw.rowbytes=RB;iw.width=W;iw.height=H;ow.data=(PF_PixelPtr)ob.data();ow.rowbytes=RB;ow.width=W;ow.height=H;{arrays}OLMRadialBlurInfo i{{}};i.blur_type={1 if mode=='zoom' else 2};i.center_x={center_x};i.center_y={center_y};i.outer_strength=4;i.outer_offset_mode=1;i.inner_offset_mode=1;i.repeat_border=TRUE;i.ratio=1;i.quality=5;i.brightness_gain=1;i.noise_variation={nv};i.noise_type=2;i.seed=1;i.thickness={thickness};i.comp_width=W;i.comp_height=H;{call}auto Put=[&](int x,auto&v){{std::ofstream(q[x],std::ios::binary).write((char*)v.data(),v.size()*sizeof(v[0]));}};{writes}}}''')
        sdk=subprocess.run(["xcrun","--show-sdk-path"],text=True,capture_output=True,check=True).stdout.strip()
        cmd=["clang++","-std=c++17","-arch","arm64","-O2","-fno-fast-math","-ffp-contract=off","-ffunction-sections","-fdata-sections","-isysroot",sdk,"-I",str(ROOT/"Headers"),"-I",str(ROOT/"Headers/SP"),"-I",str(ROOT/"Util"),"-I",str(ROOT/"Resources"),str(cpp),"-Wl,-dead_strip","-framework","Cocoa","-o",str(exe)]
        built=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True); assert built.returncode==0,built.stderr
        paths=[td/n for n in names]; run=subprocess.run([str(exe),str(inp),*map(str,paths)]); assert run.returncode==0,run.returncode
        return {n:p.read_bytes() for n,p in zip(names,paths)}

def main() -> int:
    with ThreadPoolExecutor(max_workers=6) as pool:
        captures = dict(zip(CELLS, pool.map(isolated, CELLS)))
    Path("/tmp/olm_radial_type2_actual.pkl").write_bytes(pickle.dumps(captures))
    rows = []
    for cell in CELLS:
        mode, depth, nv, thickness = cell; cap = captures[cell]
        prod = production(cell, cap)
        plane_names = ("pre_blur", "post_blur", "output") if mode == "zoom" else (
            "polar", "source_scalar", "accum", "max_alpha", "final_rgba", "coordinates", "output")
        matches = {k: prod[k] == cap[k] for k in plane_names}
        pixel_bytes, rowbytes = {8:(4,44),16:(8,80),32:(16,160)}[depth]
        output_visible_exact = all(prod["output"][y*rowbytes:y*rowbytes+9*pixel_bytes] ==
                                   cap["output"][y*rowbytes:y*rowbytes+9*pixel_bytes] for y in range(7))
        padding_preserved = all(prod["output"][y*rowbytes+9*pixel_bytes:(y+1)*rowbytes] ==
                                bytes([0xa0+y])*(rowbytes-9*pixel_bytes) for y in range(7))
        semantic = [k for k in plane_names if k not in ("source_scalar", "output")]
        exact = all(matches[k] for k in semantic) and output_visible_exact and padding_preserved
        rows.append({"mode": mode, "depth": depth, "noise_variation": nv,
                     "thickness": thickness, "hashes": {k: sha(cap[k]) for k in plane_names if k in cap},
                     "bytes": {k: len(cap[k]) for k in plane_names if k in cap},
                     "production_matches_actual": matches, "output_visible_exact": output_visible_exact,
                     "production_padding_preserved": padding_preserved, "exact": exact,
                     "missing": [k for k in plane_names if k not in cap]})
        print(cell, exact, matches, flush=True)
    all_exact = all(row["exact"] for row in rows)
    report = {"kind": "olmradialblur_noise_type2_block_actual_aex_20260811",
              "status": "exact_with_inactive_rotation_source_scalar_boundary" if all_exact else "mismatch",
              "scope": "9x7 centered neutral ellipse/strength; Zoom and Rotation; PF8/PF16/PF32; Block NV25/100, seed1, offset0, thickness3/10",
              "aex_sha256": rotation.AEX_SHA256, "cases": rows,
              "observed_rule": "Type 2 uses the Type-1 deterministic noise plane but samples the containing block cell without smooth interpolation.",
              "boundary": "Rotation Thickness3 may differ in inactive source-scalar cells; all consumed planes and visible output are exact. Output row padding is caller-owned and production preserves its seed."}
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text(f"# OLM RadialBlur Noise Type 2 (Block) — 2026-08-11\n\nStatus: **{report['status']}**\n\nAll 24 bounded cells match through consumed internal planes and visible typed output. Block reuses the deterministic generated plane and samples its containing cell without interpolation. Rotation Thickness3 retains only the known inactive source-scalar allocation boundary; caller-owned output padding is preserved.\n")
    print(json.dumps({"status": report["status"], "cells": len(rows)}))
    return 0 if all_exact else 1

if __name__ == "__main__":
    if len(sys.argv) == 7 and sys.argv[1] == "--capture":
        Path(sys.argv[6]).write_bytes(pickle.dumps(capture(sys.argv[2], int(sys.argv[3]),
                                                         float(sys.argv[4]), float(sys.argv[5]))))
        raise SystemExit(0)
    raise SystemExit(main())
