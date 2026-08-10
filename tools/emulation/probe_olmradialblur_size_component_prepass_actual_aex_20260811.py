#!/usr/bin/env python3
"""Actual-AEX probe for RadialBlur Size Variation connected components.

This is deliberately an owner-plane probe, not a production differential.  It
captures the per-source-pixel size-factor plane after the typed owner has built
it, before polar sampling can obscure the component labelling rule.
"""
from __future__ import annotations

import importlib
import json
import math
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "tools/emulation"
sys.path.insert(0, str(HERE))
import test_olmradialblur_offcenter_brightness_actual_aex_20260811 as matrix
import test_m4_case0010 as m4_fixture

W, H = 20, 14
SV_VALUES = (25.0, 100.0)
REPORT = ROOT / "refs/conformance/olmradialblur_size_component_prepass_actual_aex_20260811.json"


def occupied(pattern: str) -> set[tuple[int, int]]:
    if pattern == "empty":
        return set()
    # Disjoint areas 1, 4 and 16, plus a diagonally touching pair.  The pair
    # distinguishes 4-connectivity (two area-1 labels) from 8-connectivity
    # (one area-2 label).
    out = {(0, 0)}
    out |= {(x, y) for y in range(0, 2) for x in range(10, 12)}
    out |= {(x, y) for y in range(6, 10) for x in range(10, 14)}
    out |= {(x, y) for y in range(6, 14) for x in range(0, 8)}
    out |= {(17, 0), (18, 1)}
    return out


def source_bytes(depth: int, pattern: str, rb: int, seed: bool = False) -> bytes:
    on = occupied(pattern)
    pb = {8: 4, 16: 8, 32: 16}[depth]
    visible = W * pb
    raw = bytearray(rb * H)
    for y in range(H):
        for x in range(W):
            active = (x, y) in on
            if seed:
                active = True
            if depth == 8:
                struct.pack_into("<4B", raw, y * rb + x * 4,
                                 255 if active else 0, 71, 89, 107)
            elif depth == 16:
                struct.pack_into("<4H", raw, y * rb + x * 8,
                                 32768 if active else 0, 9001, 12001, 15001)
            else:
                struct.pack_into("<4f", raw, y * rb + x * 16,
                                 1.0 if active else 0.0, .25, .5, .75)
        raw[y * rb + visible:(y + 1) * rb] = bytes([0xA0 + y]) * (rb - visible)
    return bytes(raw)


def install_source(depth: int, pattern: str, sv: float):
    # Matrix helpers intentionally monkey-patch the shared reader; reset it so
    # sequential values cannot retain an older Size Variation closure.
    importlib.reload(m4_fixture)
    target, _, rb, _, _ = matrix.configure(("rotation", depth, W, H, 0., 0., 1.))
    def frame(seed: bool = False) -> bytes:
        return source_bytes(depth, pattern, rb, seed)

    if depth == 32:
        target.source_frame = frame
        target.base.CAPTURE_NOISE_INTERNALS = True
    else:
        target.source_frame = frame
        target.CAPTURE_NOISE_INTERNALS = True
        if depth == 8:
            # The shared PF16 fixture predates PF8 and installs its composition
            # hooks at PF16 owner-relative addresses. Translate only those two
            # observation hooks to the homologous PF8 owner addresses.
            original_loader = target.AexLoader
            class PF8Loader(original_loader):
                def add_code_hook(self, address, callback):
                    address = {0x180007162: 0x180007962,
                               0x1800072D3: 0x180007AE3}.get(address, address)
                    return super().add_code_hook(address, callback)
            target.AexLoader = PF8Loader
    m4 = target.base.m4 if depth == 32 else target.m4
    old = m4.install_reader_detours

    def params(loader, values):
        values = dict(values)
        values["Size Variation"] = sv
        # The reusable fixture's source-factor capture hook is at the common
        # size/noise composition boundary.  A nonzero Type-1 value guarantees
        # that boundary is reached; the captured size-factor allocation is the
        # input to (and therefore independent of) the subsequent noise product.
        values["Noise Variation"] = 25.0
        return old(loader, values)

    m4.install_reader_detours = params
    return target


def capture(depth: int, pattern: str, sv: float) -> list[float]:
    target = install_source(depth, pattern, sv)
    planes = target.actual_aex()
    raw = planes.get("source_size_factor")
    if raw is None:
        raise RuntimeError(f"PF{depth} owner did not expose source_size_factor")
    return list(struct.unpack(f"<{W * H}f", raw))


def build_shared_direct(td: Path) -> Path:
    cpp = td / "size_factor.cpp"
    exe = td / "size_factor"
    cpp.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{ROOT / 'mac/OLMRadialBlur/OLMRadialBlur.cpp'}"
#include <fstream>
#include <vector>
template<class P> int Run(const char* in_path,const char* out_path,int rb,float sv){{
 std::vector<unsigned char> raw(rb*{H});std::ifstream(in_path,std::ios::binary).read((char*)raw.data(),raw.size());
 PF_EffectWorld w{{}};w.data=(PF_PixelPtr)raw.data();w.rowbytes=rb;w.width={W};w.height={H};
 std::vector<float> factors;std::vector<A_long> areas;
 if(!BuildRadialSizeFactorPlaneAEX<P>(&w,sv,&factors,&areas)||factors.size()!={W*H+1}||factors.back()!=0.0f)return 3;
 std::ofstream(out_path,std::ios::binary).write((char*)factors.data(),{W*H}*sizeof(float));return 0;
}}
int main(int n,char**v){{if(n!=6)return 2;int d=atoi(v[1]),rb=atoi(v[2]);float sv=strtof(v[3],nullptr);
 if(d==8)return Run<PF_Pixel8>(v[4],v[5],rb,sv);if(d==16)return Run<PF_Pixel16>(v[4],v[5],rb,sv);if(d==32)return Run<PF_PixelFloat>(v[4],v[5],rb,sv);return 4;}}
''')
    sdk = subprocess.run(["xcrun", "--show-sdk-path"], text=True, capture_output=True, check=True).stdout.strip()
    cmd = ["clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math",
           "-ffp-contract=off", "-ffunction-sections", "-fdata-sections",
           "-isysroot", sdk, "-I", str(ROOT / "mac/OLMRadialBlur"),
           "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
           "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"), str(cpp),
           "-Wl,-dead_strip", "-framework", "Cocoa", "-o", str(exe)]
    built = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if built.returncode:
        raise RuntimeError(built.stderr)
    return exe


def shared_direct(exe: Path, depth: int, pattern: str, sv: float, td: Path) -> bytes:
    rb = W * {8: 4, 16: 8, 32: 16}[depth] + {8: 8, 16: 16, 32: 16}[depth]
    inp, out = td / f"in-{depth}-{pattern}-{sv}", td / f"out-{depth}-{pattern}-{sv}"
    inp.write_bytes(source_bytes(depth, pattern, rb))
    subprocess.run([str(exe), str(depth), str(rb), str(sv), str(inp), str(out)], check=True)
    return out.read_bytes()


def classify(values: list[float], pattern: str) -> dict:
    by_coord = {(x, y): values[y * W + x] for y in range(H) for x in range(W)}
    probes = {name: by_coord[p] for name, p in {
        "area1": (0, 0), "area4": (10, 0), "area16": (10, 6),
        "area64": (0, 6), "diagonal_a": (17, 0),
        "diagonal_b": (18, 1), "background": (19, 13),
    }.items()}
    return {
        "pattern": pattern,
        "unique_values": sorted(set(values)),
        "probes": probes,
        "all_finite": all(math.isfinite(v) for v in values),
        "row_major_plane": values,
    }


def main() -> int:
    rows = []
    with tempfile.TemporaryDirectory(prefix="radial_size_factor_direct_") as raw:
      td = Path(raw); exe = build_shared_direct(td)
      for depth in (8, 16, 32):
        for sv in SV_VALUES:
          for pattern in ("components", "empty"):
            actual = capture(depth, pattern, sv)
            direct_raw = shared_direct(exe, depth, pattern, sv, td)
            actual_raw = struct.pack(f"<{W * H}f", *actual)
            row = {"depth": depth, "size_variation": sv,
                   "shared_direct_byte_exact": direct_raw == actual_raw,
                   **classify(actual, pattern)}
            assert row["shared_direct_byte_exact"], (depth, pattern, sv)
            rows.append(row)
            print(f"PF{depth} {pattern}: {row['unique_values']} {row['probes']} direct=exact", flush=True)
    expected_by_sv = {
        25.0: {"background": .75, "area1": .75390625, "area4": .765625,
               "area16": .8125, "area64": 1.0,
               "diagonal_a": .75390625, "diagonal_b": .75390625},
        100.0: {"background": 0.0, "area1": .015625, "area4": .0625,
                "area16": .25, "area64": 1.0,
                "diagonal_a": .015625, "diagonal_b": .015625},
    }
    for row in rows:
        expected = ({name: 1.0 - row["size_variation"] / 100.0
                     for name in row["probes"]}
                    if row["pattern"] == "empty" else
                    expected_by_sv[row["size_variation"]])
        assert row["probes"] == expected, (row, expected)
    REPORT.write_text(json.dumps({
        "kind": "olmradialblur_size_component_prepass_actual_aex_20260811",
        "aex_sha256": matrix.rotation.AEX_SHA256,
        "scope": "Rotation 20x14 typed PF8/PF16/PF32 owner, Size Variation 25/100, alpha-binary fixed component and all-transparent fixtures",
        "fixture": {"areas": [1, 4, 16, 64], "diagonal_pair": [[17, 0], [18, 1]], "purpose": "4-neighbor versus 8-neighbor"},
        "status": "exact_typed_owner_component_rule",
		"boundary": "The helper is byte-exact for the enumerated 20x14 finite-alpha component and all-transparent fixtures. The AEX right-edge run lookahead and PF32 NaN/Inf alpha behavior are intentionally outside production admission.",
        "shared_direct": "BuildRadialSizeFactorPlaneAEX raw float plane is byte-exact in all 12 cases",
        "observed_connectivity": "4-neighbor; the diagonal pair remains two area-1 components",
        "observed_factor": "float32((float32(area * float32(1/max_area)) * SV) + float32(1-SV)), with SV=UI*0.01; zero-alpha/background uses area=0",
        "all_transparent": "every factor is 1-SV (0.75 at UI25, 0 at UI100); no NaN/Inf",
        "cases": rows,
    }, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
