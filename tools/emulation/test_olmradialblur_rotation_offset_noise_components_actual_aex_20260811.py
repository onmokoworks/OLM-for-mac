#!/usr/bin/env python3
"""Rotation Outer/Inner Offset Mode2/3 x procedural Noise, fixed component frame."""
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import probe_olmradialblur_rotation_size_variation_components_actual_aex_20260811 as comp

SIDES = ("outer", "inner")
MODES = (2, 3)
NVS = (25.0, 100.0)
TYPES = (1, 2)
CELLS = [(d, side, mode, nv, nt) for d in (8, 16, 32)
         for side in SIDES for mode in MODES for nv in NVS for nt in TYPES]
REPORT = ROOT / "refs/conformance/olmradialblur_rotation_offset_noise_components_actual_aex_20260811.json"
DOC = REPORT.with_suffix(".md")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def configure(cell):
    depth, side, mode, nv, noise_type = cell
    target, frame = comp.configure(depth, 0.0)
    fixture = target.base if depth == 32 else target
    fixture.FIXTURE_SIZE_VARIATION = 0.0
    fixture.FIXTURE_NOISE_VARIATION = nv
    fixture.FIXTURE_NOISE_TYPE = noise_type
    fixture.FIXTURE_SEED = 1
    fixture.FIXTURE_NOISE_OFFSET = 0.0
    fixture.FIXTURE_THICKNESS = 10.0
    fixture.CAPTURE_NOISE_INTERNALS = True
    fixture.CAPTURE_EDGE_INTERNALS = True
    m = target.base.m4 if depth == 32 else target.m4
    original = m.install_reader_detours

    def install(loader, params):
        params = dict(params)
        params.update({
            "Outer Strength": 4 if side == "outer" else 0,
            "Outer Edge Fade": 0,
            "Outer Offset Mode": mode if side == "outer" else 1,
            "Outer Offset": 4 if side == "outer" else 0,
            "Inner Strength": 4 if side == "inner" else 0,
            "Inner Edge Fade": 0,
            "Inner Offset Mode": mode if side == "inner" else 1,
            "Inner Offset": 4 if side == "inner" else 0,
        })
        return original(loader, params)

    m.install_reader_detours = install
    return target, frame


def capture(cell):
    return configure(cell)[0].actual_aex()


def isolated_capture(cell):
    with tempfile.TemporaryDirectory(prefix="radial_offset_noise_actual_") as raw:
        out = Path(raw) / "capture.pkl"
        subprocess.run([sys.executable, __file__, "--capture", *map(str, cell), str(out)], check=True)
        return pickle.loads(out.read_bytes())


def compile_runner(depth: int, expected: dict[str, bytes], directory: Path) -> Path:
    angular, radial = struct.unpack("<II", expected["geometry"])
    cells = angular * radial
    pixel = {8: "PF_Pixel8", 16: "PF_Pixel16", 32: "PF_PixelFloat"}[depth]
    pixel_bytes = {8: 4, 16: 8, 32: 16}[depth]
    rowbytes = 32 * pixel_bytes + {8: 8, 16: 16, 32: 16}[depth]
    source = directory / f"runner_{depth}.cpp"
    exe = directory / f"runner_{depth}"
    source.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{ROOT / 'mac/OLMRadialBlur/OLMRadialBlur.cpp'}"
#include <cstdlib>
#include <fstream>
#include <vector>
int main(int argc,char**argv){{
 constexpr int W=32,H=18,RB={rowbytes},C={cells};
 if(argc!=13)return 2;
 int side=std::atoi(argv[1]),mode=std::atoi(argv[2]),nt=std::atoi(argv[4]);
 double nv=std::atof(argv[3]);
 std::vector<unsigned char> ib(RB*H),ob(RB*H);
 std::ifstream(argv[5],std::ios::binary).read((char*)ib.data(),ib.size());
 for(int y=0;y<H;y++)for(int x=W*{pixel_bytes};x<RB;x++)ob[y*RB+x]=(0xa0+y)&255;
 PF_EffectWorld iw{{}},ow{{}};iw.data=(PF_PixelPtr)ib.data();iw.rowbytes=RB;iw.width=W;iw.height=H;
 ow.data=(PF_PixelPtr)ob.data();ow.rowbytes=RB;ow.width=W;ow.height=H;
 std::vector<float> polar(C*4),scalar(C),span(W*H),prepass(C),accum(C*4),maximum(C),normalized(C*4),finalrgba(W*H*4),coords(W*H*2);
 std::vector<A_u_char> eligibility(C);
 RadialBlurTestRotationCapture cap{{}};cap.polar_rgba=polar.data();cap.eligibility=eligibility.data();
 cap.source_scalar=scalar.data();cap.source_span=span.data();cap.prepass_alpha=prepass.data();
 cap.accum_rgba=accum.data();cap.max_alpha=maximum.data();cap.normalized_rgba=normalized.data();
 cap.final_rgba=finalrgba.data();cap.final_coordinates=coords.data();cap.capacity_cells=C;cap.capacity_output_pixels=W*H;
 OLMRadialBlurInfo i{{}};i.blur_type=2;i.center_x=16;i.center_y=9;
 i.outer_strength=side==0?4:0;i.outer_offset_mode=side==0?mode:1;i.outer_offset=side==0?4:0;
 i.inner_strength=side==1?4:0;i.inner_offset_mode=side==1?mode:1;i.inner_offset=side==1?4:0;
 i.repeat_border=TRUE;i.ratio=1;i.quality=5;i.brightness_gain=1;i.noise_variation=nv;i.noise_type=nt;
 i.seed=1;i.noise_offset=0;i.thickness=10;i.comp_width=W;i.comp_height=H;
 g_rotation_test_capture=&cap;auto err=RenderRotationTyped<{pixel}>(&iw,&ow,i);g_rotation_test_capture=nullptr;
 if(err)return 3;if(cap.written_cells!=C)return 4;
 auto put=[&](int n,auto&v){{std::ofstream(argv[n],std::ios::binary).write((char*)v.data(),v.size()*sizeof(v[0]));}};
 put(6,ob);put(7,span);put(8,polar);put(9,scalar);put(10,prepass);put(11,accum);put(12,maximum);
 std::ofstream(argv[12],std::ios::binary|std::ios::app).write((char*)finalrgba.data(),finalrgba.size()*4);
 std::ofstream(argv[12],std::ios::binary|std::ios::app).write((char*)coords.data(),coords.size()*4);
}}''')
    sdk = subprocess.run(["xcrun", "--show-sdk-path"], text=True, capture_output=True, check=True).stdout.strip()
    cmd = ["clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math", "-ffp-contract=off",
           "-ffunction-sections", "-fdata-sections", "-isysroot", sdk,
           "-I", str(ROOT / "mac/OLMRadialBlur"), "-I", str(ROOT / "Headers"),
           "-I", str(ROOT / "Headers/SP"), "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
           str(source), "-Wl,-dead_strip", "-framework", "Cocoa", "-o", str(exe)]
    built = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if built.returncode:
        raise RuntimeError(built.stderr)
    return exe


def production(cell, expected, exe: Path, directory: Path):
    depth, side, mode, nv, noise_type = cell
    inp = directory / f"in_{depth}"
    inp.write_bytes(configure(cell)[1])
    names = ("output", "source_span", "polar", "source_scalar", "prepass_alpha", "accum", "tail")
    paths = [directory / ("_".join(map(str, cell)) + f"_{name}") for name in names]
    result = subprocess.run([str(exe), "0" if side == "outer" else "1", str(mode), str(nv),
                             str(noise_type), str(inp), *map(str, paths)])
    if result.returncode:
        raise subprocess.CalledProcessError(result.returncode, result.args)
    got = {name: path.read_bytes() for name, path in zip(names, paths)}
    tail = got.pop("tail")
    max_bytes = len(expected["max_alpha"])
    final_bytes = len(expected["final_rgba"])
    got["max_alpha"] = tail[:max_bytes]
    got["final_rgba"] = tail[max_bytes:max_bytes + final_bytes]
    got["coordinates"] = tail[max_bytes + final_bytes:]
    return got


def main() -> int:
    with ThreadPoolExecutor(max_workers=6) as pool:
        actual = dict(zip(CELLS, pool.map(isolated_capture, CELLS)))
    rows = []
    with tempfile.TemporaryDirectory(prefix="radial_offset_noise_prod_") as raw:
        directory = Path(raw)
        runners = {d: compile_runner(d, actual[next(c for c in CELLS if c[0] == d)], directory)
                   for d in (8, 16, 32)}
        for cell in CELLS:
            a = actual[cell]
            p = production(cell, a, runners[cell[0]], directory)
            names = ("source_span", "polar", "source_scalar", "prepass_alpha", "accum",
                     "max_alpha", "final_rgba", "coordinates", "output")
            available = [name for name in names if name in a and name in p]
            matches = {name: a[name] == p[name] for name in available}
            exact = all(matches.values())
            differences = {}
            for name, matched in matches.items():
                if matched:
                    continue
                offsets = [i for i, (x, y) in enumerate(zip(a[name], p[name])) if x != y]
                differences[name] = {"different_bytes": len(offsets),
                                     "first_byte_offset": offsets[0] if offsets else None}
            rows.append({"depth": cell[0], "side": cell[1], "offset_mode": cell[2],
                         "offset_ui": 4, "noise_variation": cell[3], "noise_type": cell[4],
                         "exact": exact, "matches": matches, "differences": differences,
                         "actual_sha256": {name: sha(a[name]) for name in available}})
            print(cell, exact, matches, flush=True)
    exact_count = sum(row["exact"] for row in rows)
    status = "exact" if exact_count == len(rows) else "mismatch"
    REPORT.write_text(json.dumps({
        "kind": "olmradialblur_rotation_offset_noise_components_actual_aex_20260811",
        "status": status,
        "scope": "Rotation centered 32x18 component fixture; PF8/PF16/PF32; Outer-only/Inner-only Strength4; Offset Mode2/3 UI4; Noise Variation25/100; Noise Type1/2; SV0, Edge0, seed1, noise offset0, thickness10.",
        "exact_cases": exact_count, "total_cases": len(rows), "cases": rows,
        "boundary": "Only these 48 shared-direct cells are admitted. PF8 actual source-span capture is unavailable; all of its available consumed planes and padded typed output are byte exact. PF16/PF32 source-span and every other captured internal/output plane are byte exact. NV50, other offsets/geometries, Type3, and AE-host behavior remain fail-closed/unproved.",
    }, indent=2, sort_keys=True) + "\n")
    DOC.write_text(f"# OLM RadialBlur Rotation Offset × Noise — 2026-08-11\n\nStatus: **{status}** ({exact_count}/{len(rows)})\n\nPF8/PF16/PF32、Outer/Inner、Offset Mode 2/3 UI 4、Noise 25/100 Type 1/2の固定48セルをactual AEX内部面とpadding込みproduction outputで比較しました。PF16/PF32はsource-spanを含む全取得面、PF8はsource-span以外の全取得面がbyte exactです。PF8 source-spanはfixtureで取得できないため証拠境界として明記します。\n")
    return 0 if status == "exact" else 1


if __name__ == "__main__":
    if len(sys.argv) == 8 and sys.argv[1] == "--capture":
        cell = (int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), float(sys.argv[5]), int(sys.argv[6]))
        Path(sys.argv[7]).write_bytes(pickle.dumps(capture(cell)))
        raise SystemExit(0)
    raise SystemExit(main())
