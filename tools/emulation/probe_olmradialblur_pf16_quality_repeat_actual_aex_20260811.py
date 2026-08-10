#!/usr/bin/env python3
"""Actual-owner PF16 Quality x Repeat matrix (no production admission)."""
from __future__ import annotations

import hashlib, json, pickle, struct, subprocess, sys, tempfile, types
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "tools/emulation"
sys.path.insert(0, str(HERE))
import test_olmradialblur_zoom_pf16_small_actual_aex_20260805 as zoom
import test_olmradialblur_rotation_pf16_small_actual_aex_20260805 as rotation_base

REPORT = ROOT / "refs/conformance/olmradialblur_pf16_quality_repeat_actual_aex_20260811.json"
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
CASES = [(mode, w, h, rb, quality, repeat)
         for mode in ("zoom", "rotation")
         for w, h, rb in ((9, 7, 80), (32, 18, 272))
         for quality in (1.0, 3.0, 5.0) for repeat in (0, 1)]


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


def parameter_override(m4, quality: float, repeat: int) -> None:
    original = m4.load_case0010_params

    class Forced(dict):
        def update(self, *args, **kwargs):
            super().update(*args, **kwargs)
            self["Quality"] = quality
            self["Repeat Border"] = repeat
            self["Ratio"] = 1.0
            self["Angle"] = 0

    m4.load_case0010_params = lambda: Forced(original())


def generalized_rotation_module():
    """Load the existing owner probe with its Quality-5 capture assumption removed."""
    path = Path(rotation_base.__file__)
    source = path.read_text()
    source = source.replace(
        "cells = (max_radius - min_radius + 1) * 1800",
        "angular_count = int(round(struct.unpack('<f', ld.read_bytes(work + 8, 4))[0] * 6.283185307179586))\n"
        "        cells = (max_radius - min_radius + 1) * angular_count")
    source = source.replace(
        "if int(captured[\"cells\"]) % 1800:\n"
        "        raise RuntimeError(f\"Rotation cells do not divide the quality-5 angular extent: {captured['cells']}\")\n"
        "    planes[\"geometry\"] = struct.pack(\"<II\", 1800, int(captured[\"cells\"]) // 1800)",
        "angular_count = int(round(angle_scale * 6.283185307179586))\n"
        "    if int(captured['cells']) % angular_count:\n"
        "        raise RuntimeError(f\"Rotation cells do not divide angular extent {angular_count}: {captured['cells']}\")\n"
        "    planes['geometry'] = struct.pack('<II', angular_count, int(captured['cells']) // angular_count)")
    source = source.replace("planes[\"coordinates\"] = bytes(coordinates)",
                            "planes['coordinates'] = bytes(coordinates)\n    planes['angle_scale'] = struct.pack('<f', angle_scale)")
    module = types.ModuleType("radial_rotation_quality_probe")
    module.__file__ = str(path)
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


def configure(module, w: int, h: int, rb: int) -> None:
    frame = lambda seed=False: source_frame(w, h, rb, seed)
    module.W, module.H, module.ROWBYTES, module.VISIBLE = w, h, rb, w * 8
    module.FIXTURE_CENTER_X, module.FIXTURE_CENTER_Y = float(w // 2), float(h // 2)
    module.FIXTURE_RATIO, module.FIXTURE_ANGLE_DEG = 1.0, 0.0
    module.source_frame = frame


def run_cell(mode: str, w: int, h: int, rb: int, quality: float, repeat: int):
    if mode == "zoom":
        zoom.fixture.W, zoom.fixture.H, zoom.fixture.ROWBYTES, zoom.fixture.VISIBLE = w, h, rb, w * 8
        zoom.CENTER_X, zoom.CENTER_Y, zoom.RATIO, zoom.ANGLE_DEG = float(w // 2), float(h // 2), 1.0, 0.0
        zoom.fixture.source_frame = lambda seed=False: source_frame(w, h, rb, seed)
        parameter_override(zoom.fixture.m4, quality, repeat)
        result = zoom.actual_aex()
        planes = ("pre_blur", "post_blur", "output")
    else:
        module = generalized_rotation_module()
        configure(module, w, h, rb)
        parameter_override(module.m4, quality, repeat)
        result = module.actual_aex()
        planes = ("polar", "source_scalar", "accum", "max_alpha", "final_rgba", "coordinates", "output")
    angular, radius = struct.unpack("<II", result["geometry"])
    production = production_cell(mode, w, h, rb, quality, repeat, result)
    matches = {name: production[name] == result[name] for name in planes}
    return {"mode": mode, "depth": 16, "geometry": [w, h], "quality": quality,
            "repeat_border": bool(repeat), "polar_geometry": [angular, radius],
            "matches": matches, "exact": all(matches.values()),
            "actual_sha256": {name: hashlib.sha256(result[name]).hexdigest() for name in planes},
            "plane_bytes": {name: len(result[name]) for name in planes}}


def patched_source(td: Path) -> Path:
    path = td / "OLMRadialBlur.cpp"
    path.write_text(SOURCE.read_text())
    return path


def production_cell(mode, w, h, rb, quality, repeat, expected):
    angular, radius = struct.unpack("<II", expected["geometry"])
    cells = angular * radius
    with tempfile.TemporaryDirectory(prefix="radial_quality_production_") as raw:
        td = Path(raw); source = patched_source(td); inp = td / "in.bin"
        inp.write_bytes(source_frame(w, h, rb))
        names = (("output", "pre_blur", "post_blur", "eligibility", "span", "source_scalar") if mode == "zoom" else
                 ("output", "polar", "source_scalar", "accum", "max_alpha", "final_rgba", "coordinates"))
        if mode == "zoom":
            arrays = "std::vector<float>a(C*4),b(C*4),s(C),t(C);std::vector<A_u_char>v(C);RadialBlurTestPolarCapture cap{};cap.pre_blur_rgba=a.data();cap.post_blur_rgba=b.data();cap.eligibility=v.data();cap.span_plane=s.data();cap.source_scalar_plane=t.data();cap.capacity_floats=C*4;cap.capacity_cells=C;"
            call = "auto err=RenderZoomTyped<PF_Pixel16>(&iw,&ow,i,&cap);if(err||cap.written_floats!=C*4)return 3;"
            writes = "Put(2,ob);Put(3,a);Put(4,b);Put(5,v);Put(6,s);Put(7,t);"
        else:
            arrays = "std::vector<float>a(C*4),b(C),c(C*4),d(C),n(C*4),e(W*H*4),f(W*H*2);std::vector<A_u_char>v(C);RadialBlurTestRotationCapture cap{};cap.polar_rgba=a.data();cap.eligibility=v.data();cap.source_scalar=b.data();cap.accum_rgba=c.data();cap.max_alpha=d.data();cap.normalized_rgba=n.data();cap.final_rgba=e.data();cap.final_coordinates=f.data();cap.capacity_cells=C;cap.capacity_output_pixels=W*H;"
            call = "g_rotation_test_capture=&cap;auto err=RenderRotationTyped<PF_Pixel16>(&iw,&ow,i);g_rotation_test_capture=nullptr;if(err||cap.written_cells!=C)return 3;"
            writes = "Put(2,ob);Put(3,a);Put(4,b);Put(5,c);Put(6,d);Put(7,e);Put(8,f);"
        cpp, exe = td / "probe.cpp", td / "probe"
        cpp.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{source}"
#include <fstream>
#include <vector>
int main(int argc,char**q){{constexpr int W={w},H={h},RB={rb},C={cells};std::vector<unsigned char>ib(RB*H),ob(RB*H);std::ifstream(q[1],std::ios::binary).read((char*)ib.data(),ib.size());for(int y=0;y<H;y++)for(int x=W*8;x<RB;x++)ob[y*RB+x]=(0xa0+y)&255;PF_EffectWorld iw{{}},ow{{}};iw.data=(PF_PixelPtr)ib.data();iw.rowbytes=RB;iw.width=W;iw.height=H;ow.data=(PF_PixelPtr)ob.data();ow.rowbytes=RB;ow.width=W;ow.height=H;{arrays}OLMRadialBlurInfo i{{}};i.blur_type={1 if mode == 'zoom' else 2};i.center_x=W/2;i.center_y=H/2;i.outer_strength=4;i.outer_offset_mode=1;i.inner_offset_mode=1;i.repeat_border={repeat};i.ratio=1;i.angle_deg=0;i.quality={quality};i.brightness_gain=1;i.noise_type=1;i.seed=1;i.thickness=10;i.comp_width=W;i.comp_height=H;{call}auto Put=[&](int x,auto&v){{std::ofstream(q[x],std::ios::binary).write((char*)v.data(),v.size()*sizeof(v[0]));}};{writes}}}''')
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], text=True, capture_output=True, check=True).stdout.strip()
        cmd = ["clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math", "-ffp-contract=off", "-ffunction-sections", "-fdata-sections", "-isysroot", sdk, "-I", str(ROOT/"mac/OLMRadialBlur"), "-I", str(ROOT/"Headers"), "-I", str(ROOT/"Headers/SP"), "-I", str(ROOT/"Util"), "-I", str(ROOT/"Resources"), str(cpp), "-Wl,-dead_strip", "-framework", "Cocoa", "-o", str(exe)]
        built = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
        if built.returncode: raise RuntimeError(built.stderr)
        paths = [td / name for name in names]
        subprocess.run([str(exe), str(inp), *map(str, paths)], cwd=ROOT, check=True)
        return {name: path.read_bytes() for name, path in zip(names, paths)}


def isolated(cell):
    with tempfile.TemporaryDirectory(prefix="radial_quality_repeat_") as raw:
        output = Path(raw) / "out.pkl"
        process = subprocess.run([sys.executable, __file__, "--cell", *map(str, cell), str(output)])
        return process.returncode, pickle.loads(output.read_bytes()) if output.exists() else None


def main() -> int:
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(isolated, CASES))
    rows = [row for rc, row in results if rc == 0 and row]
    status = "exact" if len(rows) == len(CASES) and all(row["exact"] for row in rows) else "mismatch"
    repeat_pairs = []
    for mode in ("zoom", "rotation"):
        for geometry in ([9, 7], [32, 18]):
            for quality in (1.0, 3.0, 5.0):
                off = next(row for row in rows if row["mode"] == mode and row["geometry"] == geometry and
                           row["quality"] == quality and not row["repeat_border"])
                on = next(row for row in rows if row["mode"] == mode and row["geometry"] == geometry and
                          row["quality"] == quality and row["repeat_border"])
                repeat_pairs.append({"mode": mode, "geometry": geometry, "quality": quality,
                                     "same_planes": [name for name, digest in off["actual_sha256"].items()
                                                     if digest == on["actual_sha256"][name]],
                                     "different_planes": [name for name, digest in off["actual_sha256"].items()
                                                          if digest != on["actual_sha256"][name]]})
    report = {
        "kind": "olmradialblur_pf16_quality_repeat_actual_aex_20260811",
        "status": status,
        "scope": "PF16 actual owner only; Zoom/Rotation, 9x7/32x18, Quality{1,3,5}, Repeat Border{off,on}, neutral centered tuple.",
        "cells": rows,
        "repeat_off_vs_on": repeat_pairs,
        "evidence_boundary": "Production comparison compiles the current shared OLMRadialBlur.cpp and exercises its bounded PF16-only Quality/Repeat predicate.",
        "integration_candidate": {
            "admission": "PF16 only, centered neutral tuple, 9x7/32x18, Quality {1,3,5}, Repeat either.",
            "quality_3": "angle_scale=(Quality*180.0f)/(float)pi; step_rad=1.0f/angle_scale. Quality 1/5 retain the existing rounding path.",
            "rotation_span": "ceil(RotationEffectiveLength(strength)*Quality/5).",
            "repeat_off_zoom_span": "1.0f for this neutral source-factor family (equivalent to normalizing valid bilinear taps).",
            "repeat_off_rotation_scalar": "sampled.eligible ? 1.0f : 0.0f.",
        },
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": status, "cells": len(rows)}, sort_keys=True))
    return 0 if status == "exact" else 1


if __name__ == "__main__":
    if len(sys.argv) == 9 and sys.argv[1] == "--cell":
        mode, w, h, rb, quality, repeat, output = sys.argv[2:]
        Path(output).write_bytes(pickle.dumps(run_cell(mode, int(w), int(h), int(rb), float(quality), int(repeat))))
        raise SystemExit(0)
    raise SystemExit(main())
