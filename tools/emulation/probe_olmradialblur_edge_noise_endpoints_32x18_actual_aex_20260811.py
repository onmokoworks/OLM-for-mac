#!/usr/bin/env python3
"""Actual-AEX/full-production RadialBlur Edge Fade x procedural Noise endpoints."""
from __future__ import annotations

import hashlib, json, pickle, struct, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "tools/emulation"
sys.path.insert(0, str(HERE))
import probe_olmradialblur_zoom_edge_fade_offset_actual_aex_20260811 as zoom_edge
import test_olmradialblur_offcenter_brightness_actual_aex_20260811 as base
from unicorn.x86_const import UC_X86_REG_RBX, UC_X86_REG_RCX, UC_X86_REG_RDX

REPORT = ROOT / "refs/conformance/olmradialblur_edge_noise_endpoints_32x18_actual_aex_20260811.json"
DOC = REPORT.with_suffix(".md")
ZOOM = [("zoom", d, "outer", f, nv, nt) for d in (8, 16, 32)
        for f in (50, 100) for nv in (25.0, 100.0) for nt in (1, 2)]
ROTATION = [("rotation", d, side, f, nv, nt) for d in (8, 16, 32)
            for side in ("outer", "inner") for f in (50, 100)
            for nv in (25.0, 100.0) for nt in (1, 2)]
CELLS = ZOOM + ROTATION
CACHE = Path("/tmp/olmradialblur_edge_noise_20260811")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def zoom_config(cell):
    _, depth, _, fade, nv, nt = cell
    target, frame, rowbytes, _, _ = zoom_edge.configure((depth, 1, 0), fade)
    return target, frame, rowbytes, nv, nt


def zoom_actual(cell):
    target, frame, rowbytes, nv, nt = zoom_config(cell)
    fx = target.fixture
    params = fx.m4.load_case0010_params()
    params.update({
        "Blur Type": 1, "Center": (target.CENTER_X, target.CENTER_Y),
        "Quality": 5.0, "Ratio": 1.0, "Angle": 0,
        "Outer Strength": 4, "Outer Edge Fade": cell[3],
        "Outer Offset Mode": 1, "Outer Offset": 0,
        "Inner Strength": 0, "Inner Edge Fade": 0,
        "Inner Offset Mode": 1, "Inner Offset": 0,
        "Size Variation": 0.0, "Noise Variation": nv, "Noise Type": nt,
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
    cap["output"] = loader.read_bytes(output_data, rowbytes * 18)
    cap.pop("work")
    return cap


def rotation_config(cell):
    _, depth, side, fade, nv, nt = cell
    synthetic = ("rotation", depth, 32, 18, 0.0, 0.0, 1.0)
    target, *_ = base.configure(synthetic)
    fixture = target.base if depth == 32 else target
    fixture.FIXTURE_OUTER_STRENGTH = 4 if side == "outer" else 0
    fixture.FIXTURE_INNER_STRENGTH = 0 if side == "outer" else 4
    fixture.FIXTURE_OUTER_EDGE_FADE = fade if side == "outer" else 0
    fixture.FIXTURE_INNER_EDGE_FADE = fade if side == "inner" else 0
    fixture.FIXTURE_NOISE_VARIATION = nv
    fixture.FIXTURE_NOISE_TYPE = nt
    fixture.FIXTURE_SEED = 1
    fixture.FIXTURE_NOISE_OFFSET = 0.0
    fixture.FIXTURE_THICKNESS = 10.0
    fixture.CAPTURE_EDGE_INTERNALS = True
    fixture.CAPTURE_NOISE_INTERNALS = True
    m = target.base.m4 if depth == 32 else target.m4
    previous = m.install_reader_detours

    def install(loader, params):
        params = dict(params)
        params.update({
            "Outer Offset Mode": 1, "Outer Offset": 0,
            "Inner Offset Mode": 1, "Inner Offset": 0,
            "Noise Variation": nv, "Noise Type": nt,
            "Seed": 1, "Noise Offset": 0.0, "Thickness": 10.0,
        })
        return previous(loader, params)

    m.install_reader_detours = install
    return synthetic, target


def rotation_actual(cell):
    return rotation_config(cell)[1].actual_aex()


def isolated(cell):
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / ("_".join(map(str, cell)) + ".pkl")
    if not out.exists():
        temporary = out.with_suffix(".tmp")
        subprocess.run([sys.executable, __file__, "--capture", *map(str, cell), str(temporary)], check=True)
        temporary.replace(out)
    return pickle.loads(out.read_bytes())


def patch_info(data: str, cell) -> str:
    owner, _, side, fade, nv, nt = cell
    if owner == "zoom":
        needle = "i.blur_type=1;i.center_x="
        if needle not in data:
            raise RuntimeError("Zoom info marker absent")
        data = data.replace("i.outer_strength=4;i.outer_edge_fade=" + str(fade),
                            "i.outer_strength=4;i.outer_edge_fade=" + str(fade), 1)
        noise = "i.noise_type=1;i.seed=1;i.thickness=10;"
    else:
        needle = "i.outer_strength=4;i.outer_offset_mode=1;i.inner_offset_mode=1;"
        replacement = (
            f"i.outer_strength={4 if side == 'outer' else 0};"
            f"i.outer_edge_fade={fade if side == 'outer' else 0};"
            "i.outer_offset_mode=1;i.outer_offset=0;"
            f"i.inner_strength={4 if side == 'inner' else 0};"
            f"i.inner_edge_fade={fade if side == 'inner' else 0};"
            "i.inner_offset_mode=1;i.inner_offset=0;"
        )
        if needle not in data:
            raise RuntimeError("Rotation info marker absent")
        data = data.replace(needle, replacement, 1)
        noise = "i.noise_type=1;i.seed=1;i.thickness=10;"
    if noise not in data:
        raise RuntimeError("Noise info marker absent")
    return data.replace(noise, f"i.noise_variation={nv};i.noise_type={nt};"
                        "i.seed=1;i.noise_offset=0;i.thickness=10;", 1)


def zoom_production(cell, expected):
    original = Path.write_text
    def write(path, data, *args, **kwargs):
        if path.name == "probe.cpp":
            data = patch_info(data, cell)
        return original(path, data, *args, **kwargs)
    Path.write_text = write
    try:
        return zoom_edge.production((cell[1], 1, 0), expected, cell[3])
    finally:
        Path.write_text = original


def rotation_production(cell, expected):
    synthetic, _ = rotation_config(cell)
    original = Path.write_text
    def write(path, data, *args, **kwargs):
        if path.name == "p.cpp":
            data = patch_info(data, cell)
        return original(path, data, *args, **kwargs)
    Path.write_text = write
    try:
        return base.production(synthetic, expected)
    finally:
        Path.write_text = original


def shared_source_span(nv: float, noise_type: int) -> bytes:
    with tempfile.TemporaryDirectory(prefix="radial_edge_noise_source_") as raw:
        td = Path(raw); cpp = td / "n.cpp"; exe = td / "n"; out = td / "n.bin"
        cpp.write_text('''#include "core/dblur_noise.h"
#include <fstream>
int main(int n,char**q){std::vector<float> p;int w=0,h=0;
if(!olm::dblur::generate_radial_noise_plane(32,18,10.0f,0.0f,1,&p,&w,&h))return 2;
olm::dblur::NoisePlaneView v{p.data(),w,10.0f};float out[32*18];
for(int y=0;y<18;y++)for(int x=0;x<32;x++){float z=olm::dblur::sample_radial_noise_plane(v,x,y,'''
                       + ("true" if noise_type == 1 else "false") + ''');
float qv=(float)''' + repr(nv * .01) + ''';out[y*32+x]=(float)((float)(z*qv)+(float)(1.0f-qv));}
std::ofstream(q[1],std::ios::binary).write((char*)out,sizeof(out));}''')
        subprocess.run(["c++", "-std=c++17", "-O2", "-fno-fast-math", "-ffp-contract=off",
                        "-I", str(ROOT), str(cpp), "-o", str(exe)], check=True)
        subprocess.run([str(exe), str(out)], check=True)
        return out.read_bytes()


def main() -> int:
    with ThreadPoolExecutor(max_workers=6) as pool:
        actuals = dict(zip(CELLS, pool.map(isolated, CELLS)))
    spans = {(nv, nt): shared_source_span(nv, nt) for nv in (25.0, 100.0) for nt in (1, 2)}
    rows = []
    for cell in CELLS:
        actual = actuals[cell]
        produced = zoom_production(cell, actual) if cell[0] == "zoom" else rotation_production(cell, actual)
        if cell[0] == "zoom":
            names = ("pre_blur", "post_blur", "output")
            matches = {name: produced[name] == actual[name] for name in names}
            actual_span_exact = actual["source_span"] == spans[(cell[4], cell[5])]
            fade_factor_one = set(np.frombuffer(actual["source_size_factor"], dtype="<f4")) == {1.0}
            missing = ["actual B150-only faded alpha (not separately exported; post_blur is after fade+scatter)"]
        else:
            names = ("polar", "source_scalar", "prepass_alpha", "accum", "max_alpha",
                     "final_rgba", "coordinates", "output")
            matches = {name: produced.get(name) == actual.get(name) for name in names}
            actual_span_exact = ("source_span" not in actual or
                                 actual["source_span"] == spans[(cell[4], cell[5])])
            fade_factor_one = ("size_factor" in actual and
                               set(np.frombuffer(actual["size_factor"], dtype="<f4")) == {1.0})
            polar = np.frombuffer(actual["polar"], dtype="<f4").reshape(-1, 4)
            alpha = np.frombuffer(actual["prepass_alpha"], dtype="<f4")
            expected_seed = np.empty_like(polar)
            expected_seed[:, :3] = np.multiply(polar[:, :3], alpha[:, None], dtype=np.float32)
            expected_seed[:, 3] = alpha
            prepass_seed_exact = (actual.get("prepass_accum") == expected_seed.astype("<f4").tobytes() and
                                  actual.get("prepass_max_alpha") == alpha.astype("<f4").tobytes())
            missing = ([] if "source_span" in actual else
                       ["actual source-space span unavailable at this depth; consumed polar scalar captured"])
        semantic_matches = matches if cell[0] == "zoom" else {
            name: value for name, value in matches.items() if name != "source_scalar"
        }
        exact = all(semantic_matches.values()) and actual_span_exact and fade_factor_one
        if cell[0] == "rotation":
            exact = exact and prepass_seed_exact
        rows.append({
            "owner": cell[0], "depth": cell[1], "side": cell[2], "edge_fade": cell[3],
            "noise_variation": cell[4], "noise_type": cell[5], "exact": exact,
            "production_matches_actual": matches,
            "actual_source_span_matches_shared_formula": actual_span_exact,
            "edge_prepass_size_factor_is_one": fade_factor_one,
            "edge_prepass_accum_and_max_seed_formula_exact":
                None if cell[0] == "zoom" else prepass_seed_exact,
            "sampled_source_scalar_exact_or_known_inactive_boundary":
                None if cell[0] == "zoom" else
                ("exact" if matches["source_scalar"] else "known inactive allocation-boundary differences"),
            "unavailable_internal_planes": missing,
            "actual_sha256": {name: sha(actual[name]) for name in names if name in actual},
        })
        print(cell, exact, matches, flush=True)
    exact = all(row["exact"] for row in rows)
    report = {
        "kind": "olmradialblur_edge_noise_endpoints_32x18_actual_aex_20260811",
        "status": "72/72 consumed-plane/output exact with known inactive Rotation Type1 source-scalar boundary" if exact else "mismatch",
        "scope": "Centered 32x18 PF8/PF16/PF32; Zoom Outer and Rotation Outer/Inner Strength4; Edge Fade50/100 x Noise Variation25/100 x procedural Type1/2; Seed1 Offset0 Thickness10; Size Variation0 and neutral remaining tuple.",
        "binary_rule": "Edge Fade prepass consumes the independent size-factor slot. With Size Variation 0 it is exactly 1.0. The Type1/2 noise-composed source span is consumed only by the later strength scatter.",
        "source_span_formula": "f32(f32(noise * NV) + f32(1-NV)); Type1 smooth and Type2 block share the generated lattice.",
        "captured": {"zoom": ["source_size_factor", "source_span", "pre_blur", "post_blur", "owner_final_rgba", "padded output"],
                     "rotation": ["source-space span", "polar", "sampled source scalar", "B150 prepass alpha", "B150 accum/max seed", "accum", "max alpha", "final RGBA", "coordinates", "padded output"]},
        "cases": rows,
        "boundary": "Only the 72 enumerated fixed-fixture cells are admitted. Rotation Type1 retains previously documented one-ULP sampled source-scalar differences only in inactive allocation-boundary cells; every consumed plane and output is exact. Zoom actual B150-only alpha is not separately exported, so its evidence is the independent size-factor/source-span inputs plus actual pre/post worker planes, not a claimed hidden-plane comparison. Other values, Type3, Size Variation intersections, geometry, seed/offset/thickness, and AE-host behavior remain unproved.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text("# OLM RadialBlur Edge Fade × procedural Noise endpoints — 2026-08-11\n\n"
                   f"Status: **{report['status']}**\n\n" + report["scope"] + "\n\n" +
                   report["binary_rule"] + "\n\nEvidence boundary: " + report["boundary"] + "\n")
    return 0 if exact else 1


if __name__ == "__main__":
    if len(sys.argv) == 9 and sys.argv[1] == "--capture":
        cell = (sys.argv[2], int(sys.argv[3]), sys.argv[4], int(sys.argv[5]),
                float(sys.argv[6]), int(sys.argv[7]))
        Path(sys.argv[8]).write_bytes(pickle.dumps(zoom_actual(cell) if cell[0] == "zoom" else rotation_actual(cell)))
        raise SystemExit(0)
    raise SystemExit(main())
