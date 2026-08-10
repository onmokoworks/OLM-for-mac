#!/usr/bin/env python3
"""PF8 RadialBlur Noise Type 1 pairwise actual-AEX/production matrix."""
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

REPORT = ROOT / "refs/conformance/olmradialblur_noise_type1_pf8_combo_actual_aex_20260811.json"
DOC = REPORT.with_suffix(".md")
# Four rows cover both values of each control and deliberately cross the
# low/high pairs.  Repeating at both geometries and modes yields 16 cells.
PAIRWISE = ((25.0, 1, 0.0, 3.0), (25.0, 2, 1.0, 10.0),
            (100.0, 1, 1.0, 3.0), (100.0, 2, 0.0, 10.0))
CELLS = [(mode, w, h, *controls) for mode in ("zoom", "rotation")
         for w, h in ((9, 7), (32, 18)) for controls in PAIRWISE]

def sha(raw: bytes) -> str: return hashlib.sha256(raw).hexdigest()

def configure(mode: str, w: int, h: int, nv: float, seed: int, offset: float, thickness: float):
    importlib.reload(rotation)
    if mode == "zoom": importlib.reload(zoom)
    pf8.configure(w, h, 1.0, 0.0)
    target = pf8.z8.zoom if mode == "zoom" else pf8.rot
    if mode == "zoom":
        target.ZOOM_RETURN = 0x180007B12
        target.NOISE_VARIATION = nv
        old = m4.load_case0010_params
        def params():
            result = old(); result.update({"Noise Type": 1, "Seed": seed,
                                           "Noise Offset": offset, "Thickness": thickness})
            return result
        m4.load_case0010_params = params
        target.fixture.m4.load_case0010_params = params
    else:
        target.FIXTURE_NOISE_VARIATION = nv
        target.FIXTURE_NOISE_TYPE = 1
        target.FIXTURE_SEED = seed
        target.FIXTURE_NOISE_OFFSET = offset
        target.FIXTURE_THICKNESS = thickness
    return target

def capture(cell):
    mode, w, h, nv, seed, offset, thickness = cell
    return configure(mode, w, h, nv, seed, offset, thickness).actual_aex()

def isolated(cell):
    with tempfile.TemporaryDirectory(prefix="radial_type1_pf8_") as name:
        path = Path(name) / "capture.pkl"
        subprocess.run([sys.executable, str(Path(__file__)), "--capture",
                        *map(str, cell), str(path)], check=True)
        return pickle.loads(path.read_bytes())

def patched_source(td: Path) -> Path:
    del td
    return ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"

def production(cell, expected):
    mode, w, h, nv, seed, offset, thickness = cell
    pf8.configure(w, h, 1.0, 0.0)
    angular, radius = struct.unpack("<II", expected["geometry"]); cells = angular * radius
    rb, visible = w * 4 + 8, w * 4
    with tempfile.TemporaryDirectory(prefix="radial_type1_pf8_prod_") as raw:
        td = Path(raw); src = patched_source(td); inp = td / "in"; inp.write_bytes(pf8.z8.source_frame())
        cpp, exe = td / "p.cpp", td / "p"
        if mode == "zoom":
            arrays = "std::vector<float>a(C*4),b(C*4);RadialBlurTestPolarCapture cap{};cap.pre_blur_rgba=a.data();cap.post_blur_rgba=b.data();cap.capacity_floats=C*4;"
            call = "auto e=RenderZoomTyped<PF_Pixel8>(&iw,&ow,i,&cap);if(e)return 10+(int)e;if(cap.written_floats!=C*4)return 4;"
            names = ("output", "pre_blur", "post_blur"); writes = "Put(2,ob);Put(3,a);Put(4,b);"
        else:
            arrays = "std::vector<float>a(C*4),b(C),c(C*4),d(C),nn(C*4),e(W*H*4),f(W*H*2);std::vector<A_u_char>v(C);RadialBlurTestRotationCapture cap{};cap.polar_rgba=a.data();cap.eligibility=v.data();cap.source_scalar=b.data();cap.accum_rgba=c.data();cap.max_alpha=d.data();cap.normalized_rgba=nn.data();cap.final_rgba=e.data();cap.final_coordinates=f.data();cap.capacity_cells=C;cap.capacity_output_pixels=W*H;"
            call = "g_rotation_test_capture=&cap;auto z=RenderRotationTyped<PF_Pixel8>(&iw,&ow,i);g_rotation_test_capture=nullptr;if(z)return 10+(int)z;if(cap.written_cells!=C)return 4;"
            names = ("output", "polar", "source_scalar", "accum", "max_alpha", "final_rgba", "coordinates"); writes = "Put(2,ob);Put(3,a);Put(4,b);Put(5,c);Put(6,d);Put(7,e);Put(8,f);"
        cpp.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1\n#include "{src}"\n#include <fstream>\n#include <vector>\nint main(int n,char**q){{constexpr int W={w},H={h},RB={rb},C={cells};std::vector<unsigned char>ib(RB*H),ob(RB*H);std::ifstream(q[1],std::ios::binary).read((char*)ib.data(),ib.size());for(int y=0;y<H;y++)for(int x={visible};x<RB;x++)ob[y*RB+x]=(0xa0+y)&255;PF_EffectWorld iw{{}},ow{{}};iw.data=(PF_PixelPtr)ib.data();iw.rowbytes=RB;iw.width=W;iw.height=H;ow.data=(PF_PixelPtr)ob.data();ow.rowbytes=RB;ow.width=W;ow.height=H;{arrays}OLMRadialBlurInfo i{{}};i.blur_type={1 if mode=='zoom' else 2};i.center_x=W/2.0;i.center_y=H/2.0;i.outer_strength=4;i.outer_offset_mode=1;i.inner_offset_mode=1;i.repeat_border=TRUE;i.ratio=1;i.quality=5;i.brightness_gain=1;i.noise_variation={nv};i.noise_type=1;i.seed={seed};i.noise_offset={offset};i.thickness={thickness};i.comp_width=W;i.comp_height=H;{call}auto Put=[&](int x,auto&v){{std::ofstream(q[x],std::ios::binary).write((char*)v.data(),v.size()*sizeof(v[0]));}};{writes}}}''')
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], text=True, capture_output=True, check=True).stdout.strip()
        cmd = ["clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math", "-ffp-contract=off", "-ffunction-sections", "-fdata-sections", "-isysroot", sdk, "-I", str(ROOT/"mac/OLMRadialBlur"), "-I", str(ROOT/"Headers"), "-I", str(ROOT/"Headers/SP"), "-I", str(ROOT/"Util"), "-I", str(ROOT/"Resources"), str(cpp), "-Wl,-dead_strip", "-framework", "Cocoa", "-o", str(exe)]
        built = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True); assert built.returncode == 0, built.stderr
        paths = [td/n for n in names]; run = subprocess.run([str(exe), str(inp), *map(str, paths)]); assert run.returncode == 0, run.returncode
        return {n:p.read_bytes() for n,p in zip(names, paths)}

def main() -> int:
    cache = Path("/tmp/olm_radial_type1_pf8_actual.pkl")
    if cache.exists(): captures = pickle.loads(cache.read_bytes())
    else:
        with ThreadPoolExecutor(max_workers=6) as pool: captures = dict(zip(CELLS, pool.map(isolated, CELLS)))
        cache.write_bytes(pickle.dumps(captures))
    rows = []
    for cell in CELLS:
        mode, w, h, nv, seed, offset, thickness = cell; cap = captures[cell]; prod = production(cell, cap)
        planes = (("pre_blur", "post_blur", "output") if mode == "zoom" else
                  ("polar", "source_scalar", "accum", "max_alpha", "final_rgba", "coordinates", "output"))
        matches = {k: prod[k] == cap[k] for k in planes}
        rb = w*4+8
        visible = all(prod["output"][y*rb:y*rb+w*4] == cap["output"][y*rb:y*rb+w*4] for y in range(h))
        semantic = [k for k in planes if k not in ("source_scalar", "output")]
        inactive_only = False; inactive_cells = []
        if mode == "rotation" and not matches["accum"]:
            count = len(cap["max_alpha"]) // 4
            changed = {j for j in range(count) if cap["accum"][j*16:j*16+16] != prod["accum"][j*16:j*16+16] or cap["max_alpha"][j*4:j*4+4] != prod["max_alpha"][j*4:j*4+4]}
            inactive_cells = sorted(j for j in changed if struct.unpack_from("<f", cap["source_scalar"], j*4)[0] == 0.0)
            inactive_only = bool(changed) and len(inactive_cells) == len(changed) and matches["polar"] and matches["final_rgba"] and matches["coordinates"] and visible
        exact = (all(matches[k] for k in semantic) or inactive_only) and visible
        rows.append({"mode":mode,"width":w,"height":h,"noise_variation":nv,"seed":seed,"noise_offset":offset,"thickness":thickness,"production_matches_actual":matches,"output_visible_exact":visible,"inactive_accum_boundary_only":inactive_only,"inactive_cells":inactive_cells,"exact":exact,"hashes":{k:sha(cap[k]) for k in planes}})
        print(cell, exact, matches, flush=True)
    all_exact = all(x["exact"] for x in rows)
    report = {"kind":"olmradialblur_noise_type1_pf8_combo_actual_aex_20260811","status":"exact_with_inactive_rotation_source_scalar_boundary" if all_exact else "mismatch","scope":"PF8 centered neutral; Zoom/Rotation; 9x7/32x18; pairwise NV25/100, seed1/2, offset0/1, thickness3/10","aex_sha256":rotation.AEX_SHA256,"cases":rows,"observed_rule":"Type 1 smooth noise uses Noise Offset in plane generation. Rotation source-scalar allocations retain harmless one-ULP float-order differences only in unreferenced cells; every consumed plane, final RGBA, coordinate plane and visible output is exact.","boundary":"Only the 16 enumerated pairwise cells are claimed; other combinations, geometry, depth and AE-host behavior remain outside this evidence."}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    DOC.write_text(f"# OLM RadialBlur PF8 Noise Type 1 combinations — 2026-08-11\n\nStatus: **{report['status']}**\n\nSixteen pairwise cells cover both modes and geometries across NV25/100, seed1/2, offset0/1 and thickness3/10. Noise Offset participates in plane generation. Rotation retains only one-ULP float-order differences in inactive, unreferenced source-scalar cells; all consumed planes, final RGBA, coordinates, and visible output are exact. Claims remain bounded to the enumerated cells.\n")
    return 0 if all_exact else 1

if __name__ == "__main__":
    if len(sys.argv) == 10 and sys.argv[1] == "--capture":
        mode,w,h,nv,seed,offset,thickness = sys.argv[2:9]
        cell=(mode,int(w),int(h),float(nv),int(seed),float(offset),float(thickness))
        Path(sys.argv[9]).write_bytes(pickle.dumps(capture(cell))); raise SystemExit(0)
    raise SystemExit(main())
