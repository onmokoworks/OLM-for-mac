#!/usr/bin/env python3
"""Actual-AEX Zoom Edge Fade x ignored Offset x procedural Noise matrix."""
from __future__ import annotations

import hashlib
import json
import pickle
import struct
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "tools/emulation"
sys.path.insert(0, str(HERE))
import probe_olmradialblur_edge_noise_endpoints_32x18_actual_aex_20260811 as edge_noise
import probe_olmradialblur_zoom_edge_fade_offset_actual_aex_20260811 as zoom_edge
from unicorn.x86_const import UC_X86_REG_RBX, UC_X86_REG_RCX, UC_X86_REG_RDX

REPORT = ROOT / "refs/conformance/olmradialblur_zoom_edge_offset_noise_actual_aex_20260811.json"
DOC = REPORT.with_suffix(".md")
CACHE = Path("/tmp/olmradialblur_zoom_edge_offset_noise_20260811")
CELLS = [(depth, fade, mode, 4, nv, noise_type)
         for depth in (8, 16, 32)
         for fade in (50, 100)
         for mode in (2, 3)
         for nv in (25.0, 100.0)
         for noise_type in (1, 2)]
BASELINES = [(depth, fade, 1, 0, nv, noise_type)
             for depth in (8, 16, 32)
             for fade in (50, 100)
             for nv in (25.0, 100.0)
             for noise_type in (1, 2)]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def configure(cell):
    depth, fade, mode, offset, nv, noise_type = cell
    target, frame, rowbytes, cx, cy = zoom_edge.configure((depth, mode, offset), fade)
    return target, frame, rowbytes, cx, cy, nv, noise_type


def actual(cell):
    target, frame, rowbytes, _cx, _cy, nv, noise_type = configure(cell)
    depth, fade, mode, offset, _, _ = cell
    fx = target.fixture
    params = fx.m4.load_case0010_params()
    params.update({
        "Blur Type": 1, "Center": (target.CENTER_X, target.CENTER_Y),
        "Quality": 5.0, "Ratio": 1.0, "Angle": 0,
        "Outer Strength": 4, "Outer Edge Fade": fade,
        "Outer Offset Mode": mode, "Outer Offset": offset,
        "Inner Strength": 0, "Inner Edge Fade": 0,
        "Inner Offset Mode": 1, "Inner Offset": 0,
        "Size Variation": 0.0, "Noise Variation": nv, "Noise Type": noise_type,
        "Seed": 1, "Noise Offset": 0.0, "Thickness": 10.0,
        "Brightness Gain": 1.0, "Repeat Border": 1,
    })
    loader = fx.AexLoader(str(fx.m4.AEX_PATH), fast=True)
    loader.register_libm_impls(max_threads=1)
    suites = fx.m4.build_host_suites(loader)
    render_ctx = fx.m4.build_render_context(loader, suites)
    iw, _ = fx.build_world(loader, frame())
    ow, output_data = fx.build_world(loader, frame(True))
    param_ctx = fx.m4.build_param_block(loader)
    fx.m4.install_reader_detours(loader, params)
    cap = {}

    def entry(ld, _address, _size):
        cap["work"] = ld.uc.reg_read(UC_X86_REG_RCX)
        setup = ld.uc.reg_read(UC_X86_REG_RDX)
        cap["transform_setup"] = ld.read_bytes(setup + 0x28, 0x58)

    def collapse(ld, _address, _size):
        if "pre_blur" in cap:
            return
        work = cap["work"]
        min_r = struct.unpack("<i", ld.read_bytes(work + 0x18, 4))[0]
        max_r = struct.unpack("<i", ld.read_bytes(work + 0x1c, 4))[0]
        angle_step = struct.unpack("<f", ld.read_bytes(work + 0x14, 4))[0]
        angular = int(round(6.283185307179586 / angle_step))
        radial = max_r - min_r + 1
        cap["geometry"] = struct.pack("<II", angular, radial)
        cap["pre_blur"] = ld.read_bytes(fx.m4.u64(ld, work + 0x38), angular * radial * 16)

    def finish(ld, _address, _size):
        angular, radial = struct.unpack("<II", cap["geometry"])
        work = cap["work"]
        cap["post_blur"] = ld.read_bytes(fx.m4.u64(ld, work + 0x38), angular * radial * 16)
        owner = ld.uc.reg_read(UC_X86_REG_RBX)
        cap["source_size_factor"] = ld.read_bytes(fx.m4.u64(ld, owner + 0x88), 32 * 18 * 4)
        cap["source_span"] = ld.read_bytes(fx.m4.u64(ld, owner + 0x90), 32 * 18 * 4)
        cap["final_rgba"] = ld.read_bytes(fx.m4.u64(ld, owner + 0xa0), 32 * 18 * 16)

    loader.add_code_hook(target.ZOOM_ENTRY, entry)
    loader.add_code_hook(target.ZOOM_COLLAPSE, collapse)
    loader.add_code_hook(target.ZOOM_RETURN, finish)
    loader.call_function(fx.m4.FUN_180008690, int_args=[0, 0, 0, param_ctx, render_ctx],
                         max_instructions=5_000_000)
    loader.call_function(fx.OWNER, int_args=[render_ctx, 0, iw, ow, param_ctx],
                         max_instructions=500_000_000)
    cap["output"] = loader.read_bytes(output_data, rowbytes * 18)
    cap.pop("work")
    return cap


def isolated_actual(cell):
    CACHE.mkdir(parents=True, exist_ok=True)
    output = CACHE / ("_".join(map(str, cell)) + ".pkl")
    if not output.exists():
        temporary = output.with_suffix(".tmp")
        subprocess.run([sys.executable, __file__, "--capture", *map(str, cell), str(temporary)],
                       check=True)
        temporary.replace(output)
    return pickle.loads(output.read_bytes())


def temporary_source(path: Path) -> None:
    text = (ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp").read_text()
    path.write_text(text)


def production(cell, expected):
    depth, fade, mode, offset, nv, noise_type = cell
    _, frame, rowbytes, cx, cy, _, _ = configure(cell)
    angular, radial = struct.unpack("<II", expected["geometry"])
    cells = angular * radial
    pixel = {8: "PF_Pixel8", 16: "PF_Pixel16", 32: "PF_PixelFloat"}[depth]
    pixel_bytes = {8: 4, 16: 8, 32: 16}[depth]
    with tempfile.TemporaryDirectory(prefix="radial_zoom_edge_offset_noise_prod_") as raw:
        td = Path(raw)
        source = td / "OLMRadialBlur.cpp"
        temporary_source(source)
        inp = td / "input.bin"
        inp.write_bytes(frame())
        cpp, exe = td / "probe.cpp", td / "probe"
        cpp.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{source}"
#include <fstream>
#include <vector>
int main(int n,char**q){{constexpr int W=32,H=18,RB={rowbytes},C={cells};std::vector<unsigned char>ib(RB*H),ob(RB*H);std::ifstream(q[1],std::ios::binary).read((char*)ib.data(),ib.size());for(int y=0;y<H;y++)for(int x=W*{pixel_bytes};x<RB;x++)ob[y*RB+x]=(0xa0+y)&255;PF_EffectWorld iw{{}},ow{{}};iw.data=(PF_PixelPtr)ib.data();iw.rowbytes=RB;iw.width=W;iw.height=H;ow.data=(PF_PixelPtr)ob.data();ow.rowbytes=RB;ow.width=W;ow.height=H;std::vector<float>a(C*4),b(C*4);RadialBlurTestPolarCapture cap{{}};cap.pre_blur_rgba=a.data();cap.post_blur_rgba=b.data();cap.capacity_floats=C*4;OLMRadialBlurInfo i{{}};i.blur_type=1;i.center_x={cx};i.center_y={cy};i.outer_strength=4;i.outer_edge_fade={fade};i.outer_offset_mode={mode};i.outer_offset={offset};i.inner_offset_mode=1;i.repeat_border=TRUE;i.ratio=1;i.quality=5;i.brightness_gain=1;i.noise_variation={nv};i.noise_type={noise_type};i.seed=1;i.noise_offset=0;i.thickness=10;i.comp_width=W;i.comp_height=H;auto e=RenderZoomTyped<{pixel}>(&iw,&ow,i,&cap);if(e||cap.written_floats!=C*4)return 3;auto put=[&](int x,auto&v){{std::ofstream(q[x],std::ios::binary).write((char*)v.data(),v.size()*sizeof(v[0]));}};put(2,ob);put(3,a);put(4,b);}}
''')
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], text=True,
                             capture_output=True, check=True).stdout.strip()
        command = ["clang++", "-std=c++17", "-arch", "arm64", "-O2",
                   "-fno-fast-math", "-ffp-contract=off", "-ffunction-sections",
                   "-fdata-sections", "-isysroot", sdk,
                   "-I", str(ROOT / "mac/OLMRadialBlur"), "-I", str(ROOT / "Headers"),
                   "-I", str(ROOT / "Headers/SP"), "-I", str(ROOT / "Util"),
                   "-I", str(ROOT / "Resources"), str(cpp), "-Wl,-dead_strip",
                   "-framework", "Cocoa", "-o", str(exe)]
        built = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        if built.returncode:
            raise RuntimeError(built.stderr)
        outputs = [td / name for name in ("output", "pre_blur", "post_blur")]
        subprocess.run([str(exe), str(inp), *map(str, outputs)], check=True)
        return {name: output.read_bytes()
                for name, output in zip(("output", "pre_blur", "post_blur"), outputs)}


def main() -> int:
    capture_cells = BASELINES + CELLS
    with ThreadPoolExecutor(max_workers=6) as pool:
        captures = dict(zip(capture_cells, pool.map(isolated_actual, capture_cells)))
    source_spans = {(nv, noise_type): edge_noise.shared_source_span(nv, noise_type)
                    for nv in (25.0, 100.0) for noise_type in (1, 2)}
    rows = []
    for cell in CELLS:
        depth, fade, mode, offset, nv, noise_type = cell
        actual_result = captures[cell]
        baseline = captures[(depth, fade, 1, 0, nv, noise_type)]
        produced = production(cell, actual_result)
        planes = ("pre_blur", "post_blur", "output")
        matches = {name: produced[name] == actual_result[name] for name in planes}
        baseline_planes = ("source_size_factor", "source_span", "pre_blur", "post_blur",
                           "final_rgba", "output")
        baseline_matches = {name: actual_result[name] == baseline[name]
                            for name in baseline_planes}
        size_factor_one = set(np.frombuffer(actual_result["source_size_factor"],
                                             dtype="<f4")) == {1.0}
        source_span_exact = actual_result["source_span"] == source_spans[(nv, noise_type)]
        exact = (all(matches.values()) and all(baseline_matches.values()) and
                 size_factor_one and source_span_exact)
        rows.append({
            "depth": f"PF{depth}", "edge_fade": fade, "offset_mode": mode,
            "offset_ui": offset, "noise_variation": nv, "noise_type": noise_type,
            "exact": exact, "production_matches_actual": matches,
            "actual_matches_mode1_offset0": baseline_matches,
            "source_size_factor_is_one": size_factor_one,
            "source_span_matches_radial_formula": source_span_exact,
            "actual_sha256": {name: sha(actual_result[name]) for name in baseline_planes},
        })
        print(cell, exact, matches, flush=True)
    exact = all(row["exact"] for row in rows)
    status = "48/48 exact" if exact else "mismatch"
    report = {
        "kind": "olmradialblur_zoom_edge_offset_noise_actual_aex_20260811",
        "status": status,
        "scope": "Centered 32x18 PF8/PF16/PF32 Zoom Outer Strength4; Edge Fade50/100 x ignored Offset Mode2/3 UI4 x Noise Variation25/100 x procedural Type1/2; Seed1 Offset0 Thickness10, Size Variation0 and neutral remaining tuple.",
        "ordering": "The owner source size-factor is exactly 1 at Size Variation0. Procedural noise produces the independent source span; the Zoom B150 Edge Fade prepass consumes size-factor before the length-4 strength scatter consumes the noise span. Offset controls are ignored by the Zoom owner.",
        "captured": ["source size-factor", "source span", "pre-blur float32 RGBA",
                     "post-blur float32 RGBA", "owner final RGBA", "typed padded output"],
        "mode1_baseline": "Every actual-AEX crossed cell is byte-identical to the same depth/Fade/NV/Type Mode1 Offset0 capture across all captured source/worker/final planes.",
        "cache_policy": "No persistent capture cache is used; each report invocation launches an isolated actual-AEX subprocess per cell.",
        "cases": rows,
        "boundary": "Only these 48 fixed-fixture cells are proven. Zoom B150-only faded alpha is not separately exported; direct post-worker/final/output equality plus exact independent source inputs forms the evidence. Other offsets, values, Type3, Size Variation intersections, geometry, seed/noise offset/thickness, and AE-host behavior remain unproved.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text("# OLM RadialBlur Zoom Edge Fade × Offset × procedural Noise — 2026-08-11\n\n"
                   f"Status: **{status}**\n\n" + report["scope"] + "\n\n" +
                   report["ordering"] + "\n\n" + report["mode1_baseline"] +
                   "\n\nEvidence boundary: " + report["boundary"] + "\n")
    return 0 if exact else 1


if __name__ == "__main__":
    if len(sys.argv) == 9 and sys.argv[1] == "--capture":
        cell = (int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]),
                float(sys.argv[6]), int(sys.argv[7]))
        Path(sys.argv[8]).write_bytes(pickle.dumps(actual(cell)))
        raise SystemExit(0)
    raise SystemExit(main())
