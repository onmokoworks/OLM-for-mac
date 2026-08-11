#!/usr/bin/env python3
"""Zoom Size Variation x procedural Noise on the 1/4/9 component source.

This is intentionally a probe, not an admission change.  It captures the owner
source-factor/source-span arrays as well as the Zoom worker planes and padded
typed output from the pinned AEX.  The shared implementation is compiled
directly for comparison and may fail closed until the bounded family is added.
"""
from __future__ import annotations

import hashlib, json, pickle, struct, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "tools/emulation"
sys.path.insert(0, str(HERE))
import test_olmradialblur_offcenter_brightness_actual_aex_20260811 as base
import probe_olmradialblur_zoom_size_variation_components_actual_aex_20260811 as components
from unicorn.x86_const import UC_X86_REG_RBX, UC_X86_REG_RCX, UC_X86_REG_RDX
import numpy as np

REPORT = ROOT / "refs/conformance/olmradialblur_zoom_size_noise_components_actual_aex_20260811.json"
CELLS = [(d, sv, nv, nt) for d in (8, 16, 32) for sv in (25., 100.)
         for nv in (25., 100.) for nt in (1, 2)]


def sha(raw): return hashlib.sha256(raw).hexdigest()


def configure(depth, sv, nv, nt, gain=1.0):
    base.frame_for = components.component_frame_for
    try:
        target, frame, rb, _, _ = base.configure(("zoom", depth, 32, 18, 0., 0., gain))
    finally:
        base.frame_for = components.ORIGINAL_FRAME_FOR
    return target, frame, rb


def actual(cell):
    depth, sv, nv, nt = cell[:4]
    gain = cell[4] if len(cell) > 4 else 1.0
    target, frame, rb = configure(depth, sv, nv, nt, gain)
    fx = target.fixture
    params = fx.m4.load_case0010_params()
    params.update({
        "Blur Type": 1, "Center": (target.CENTER_X, target.CENTER_Y), "Quality": 5.,
        "Ratio": 1., "Angle": 0, "Outer Strength": 4, "Outer Offset Mode": 1,
        "Outer Offset": 0, "Inner Strength": 0, "Noise Variation": nv,
        "Noise Type": nt, "Seed": 1, "Noise Offset": 0., "Thickness": 10.,
        "Size Variation": sv, "Brightness Gain": gain,
    })
    loader = fx.AexLoader(str(fx.m4.AEX_PATH), fast=True)
    loader.register_libm_impls(max_threads=1)
    sp = fx.m4.build_host_suites(loader)
    render_ctx = fx.m4.build_render_context(loader, sp)
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
        if "pre_blur" in cap: return
        work = cap["work"]
        min_r = struct.unpack("<i", ld.read_bytes(work + 0x18, 4))[0]
        max_r = struct.unpack("<i", ld.read_bytes(work + 0x1c, 4))[0]
        angle_step = struct.unpack("<f", ld.read_bytes(work + 0x14, 4))[0]
        ac = int(round(6.283185307179586 / angle_step)); rc = max_r - min_r + 1
        cap["geometry"] = struct.pack("<II", ac, rc)
        cap["pre_blur"] = ld.read_bytes(fx.m4.u64(ld, work + 0x38), ac * rc * 16)

    def finish(ld, _address, _size):
        ac, rc = struct.unpack("<II", cap["geometry"]); work = cap["work"]
        cap["post_blur"] = ld.read_bytes(fx.m4.u64(ld, work + 0x38), ac * rc * 16)
        owner = ld.uc.reg_read(UC_X86_REG_RBX)
        cap["source_size_factor"] = ld.read_bytes(fx.m4.u64(ld, owner + 0x88), 32 * 18 * 4)
        cap["source_span"] = ld.read_bytes(fx.m4.u64(ld, owner + 0x90), 32 * 18 * 4)
        cap["final_rgba"] = ld.read_bytes(fx.m4.u64(ld, owner + 0xa0), 32 * 18 * 16)

    loader.add_code_hook(target.ZOOM_ENTRY, entry)
    loader.add_code_hook(target.ZOOM_COLLAPSE, collapse)
    loader.add_code_hook(target.ZOOM_RETURN, finish)
    loader.call_function(fx.m4.FUN_180008690, int_args=[0, 0, 0, param_ctx, render_ctx], max_instructions=5_000_000)
    loader.call_function(fx.OWNER, int_args=[render_ctx, 0, iw, ow, param_ctx], max_instructions=500_000_000)
    cap["output"] = loader.read_bytes(output_data, rb * 18)
    cap.pop("work")
    return cap


def isolated(cell):
    with tempfile.TemporaryDirectory(prefix="radial_zoom_sv_noise_") as d:
        p = Path(d) / "a.pkl"
        subprocess.run([sys.executable, __file__, "--actual", *map(str, cell), str(p)], check=True)
        return pickle.loads(p.read_bytes())


def production(cell, expected):
    depth, sv, nv, noise_type = cell[:4]
    gain = cell[4] if len(cell) > 4 else 1.0
    original = Path.write_text

    def write_text(path, data, *args, **kwargs):
        if path.name == "p.cpp":
            needle = "i.noise_type=1;i.seed=1;i.thickness=10;"
            if needle not in data:
                raise RuntimeError("noise info marker absent")
            data = data.replace(
                needle,
                f"i.noise_variation={nv};i.noise_type={noise_type};"
                "i.seed=1;i.noise_offset=0;i.thickness=10;",
                1,
            )
            brightness = next((marker for marker in
                               ("i.brightness_gain=1;", "i.brightness_gain=1.0;")
                               if marker in data), None)
            if brightness is None:
                raise RuntimeError("brightness info marker absent")
            data = data.replace(brightness, f"i.brightness_gain={gain};", 1)
        return original(path, data, *args, **kwargs)

    Path.write_text = write_text
    try:
        return components.production(depth, sv, expected)
    finally:
        Path.write_text = original


def generated_source_noise(noise_type):
    """Compile the shared generator/sampler and return its source-space 32x18 plane."""
    with tempfile.TemporaryDirectory(prefix="radial_zoom_noise_source_") as d:
        td = Path(d); cpp = td / "n.cpp"; exe = td / "n"; out = td / "n.bin"
        cpp.write_text('''#include "core/dblur_noise.h"
#include <fstream>
int main(int n,char**q){std::vector<float> p;int w=0,h=0;
if(!olm::dblur::generate_radial_noise_plane(32,18,10.0f,0.0f,1,&p,&w,&h))return 2;
olm::dblur::NoisePlaneView v{p.data(),w,10.0f};float out[32*18];
for(int y=0;y<18;y++)for(int x=0;x<32;x++)out[y*32+x]=olm::dblur::sample_radial_noise_plane(v,x,y,'''
                       + ("true" if noise_type == 1 else "false") + ''');
std::ofstream(q[1],std::ios::binary).write((char*)out,sizeof(out));}''')
        subprocess.run(["c++", "-std=c++17", "-O2", "-fno-fast-math", "-ffp-contract=off",
                        "-I", str(ROOT), str(cpp), "-o", str(exe)], check=True)
        subprocess.run([str(exe), str(out)], check=True)
        return np.frombuffer(out.read_bytes(), dtype="<f4").copy()


def f32_span(noise, nv, factor):
    nv32 = np.float32(nv * .01); one = np.float32(1.)
    scaled = np.multiply(noise, nv32, dtype=np.float32)
    base = np.subtract(one, nv32, dtype=np.float32)
    mixed = np.add(scaled, base, dtype=np.float32)
    return np.multiply(mixed, factor, dtype=np.float32).astype("<f4")


def main():
    controls = [(d, 0., 100., nt) for d in (8, 16, 32) for nt in (1, 2)]
    requested = controls + CELLS
    with ThreadPoolExecutor(max_workers=6) as pool:
        captures = dict(zip(requested, pool.map(isolated, requested)))
    # At NV100/SV0 the owner's source_span is exactly its generated/sampled
    # source-space noise plane.  Use that actual-AEX plane as the formula input;
    # this avoids silently treating a portable sampler approximation as proof.
    noise = {nt: np.frombuffer(captures[(32, 0., 100., nt)]["source_span"],
                              dtype="<f4").copy() for nt in (1, 2)}
    portable_noise = {nt: generated_source_noise(nt) for nt in (1, 2)}
    control_cross_depth = {}
    for nt in (1, 2):
        same = len({captures[(d, 0., 100., nt)]["source_span"] for d in (8, 16, 32)}) == 1
        assert same, nt
        differing = int(np.count_nonzero(portable_noise[nt].view("<u4") != noise[nt].view("<u4")))
        control_cross_depth[str(nt)] = {
            "actual_generated_noise_identical_pf8_pf16_pf32": same,
            "portable_shared_sampler_different_float_count": differing,
        }
    rows = []
    for cell in CELLS:
        got = captures[cell]
        produced = production(cell, got)
        production_matches = {name: produced[name] == got[name]
                              for name in ("pre_blur", "post_blur", "output")}
        factor_np = np.frombuffer(got["source_size_factor"], dtype="<f4")
        span_np = np.frombuffer(got["source_span"], dtype="<f4")
        factor = tuple(float(v) for v in factor_np)
        span = tuple(float(v) for v in span_np)
        expected_span = f32_span(noise[cell[3]], cell[2], factor_np)
        formula_exact = expected_span.tobytes() == got["source_span"]
        assert formula_exact, cell
        zero_factor = sum(v == 0. for v in factor)
        zero_span = sum(v == 0. for v in span)
        row = {
            "depth": cell[0], "size_variation": cell[1], "noise_variation": cell[2],
            "noise_type": cell[3], "source_size_factor_unique": sorted(set(factor)),
            "source_span_min_max": [min(span), max(span)], "zero_factor": zero_factor,
            "zero_span": zero_span, "source_span_formula_bit_exact": formula_exact,
            "production_matches_actual": production_matches,
            "sha256": {k: sha(got[k]) for k in ("source_size_factor", "source_span", "pre_blur", "post_blur", "final_rgba", "output")},
        }
        rows.append(row); print(cell, row["source_size_factor_unique"], row["source_span_min_max"], flush=True)
    cross_depth = {}
    for sv in (25., 100.):
        for nv in (25., 100.):
            for nt in (1, 2):
                selected = [captures[(d, sv, nv, nt)] for d in (8, 16, 32)]
                factors_same = len({v["source_size_factor"] for v in selected}) == 1
                spans_same = len({v["source_span"] for v in selected}) == 1
                assert factors_same and spans_same, (sv, nv, nt)
                cross_depth[f"sv{int(sv)}_nv{int(nv)}_type{nt}"] = {
                    "source_size_factor_identical_pf8_pf16_pf32": factors_same,
                    "source_span_identical_pf8_pf16_pf32": spans_same,
                }
    production_exact = all(all(r["production_matches_actual"].values()) for r in rows)
    REPORT.write_text(json.dumps({
        "kind": "olmradialblur_zoom_size_noise_components_actual_aex_20260811",
        "status": ("24/24 actual-AEX source-span and shared-direct output exact"
                   if production_exact
                   else "actual-AEX/shared-direct mismatch"),
        "scope": "Pinned actual AEX; centered Zoom 32x18; PF8/PF16/PF32; disconnected component areas 1/4/9; SV25/100 x NV25/100 x Noise Type1/2; seed1 offset0 thickness10; Outer4 neutral tuple.",
        "compared_or_captured": ["source_size_factor", "source_span", "pre_blur", "post_blur", "owner_final_rgba", "typed_padded_output"],
        "structural_note": "Zoom has no separately exposed accum/max-alpha planes; post_blur is its normalized worker result and owner_final_rgba is the inverse-transform result before typed packing.",
        "binary_rule": "source_span = f32(f32(f32(noise * NV) + f32(1-NV)) * source_size_factor); size factor is multiplied last; zero is tested by exact equality.",
        "actual_generated_noise_sha256": {str(nt): sha(noise[nt].tobytes()) for nt in (1, 2)},
        "generated_noise_controls": control_cross_depth,
        "all_source_span_formula_bit_exact": all(r["source_span_formula_bit_exact"] for r in rows),
        "cross_depth": cross_depth,
        "cases": rows,
        "boundary": "Only these 24 shared-direct cells and the fixed component fixture are admitted. Other masks, geometry, values, seed/offset/thickness, Type3, and AE-host output remain unproven.",
    }, indent=2, sort_keys=True) + "\n")
    return 0 if production_exact else 1


if __name__ == "__main__":
    if len(sys.argv) == 7 and sys.argv[1] == "--actual":
        cell = (int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5]))
        Path(sys.argv[6]).write_bytes(pickle.dumps(actual(cell))); raise SystemExit(0)
    raise SystemExit(main())
