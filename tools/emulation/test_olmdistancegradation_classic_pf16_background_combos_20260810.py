#!/usr/bin/env python3
"""Cross PF16 ownership/render/interpolation branches with background enabled."""
import hashlib
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "tools/emulation"
sys.path.insert(0, str(HERE))
from export_dg_fieldgen_fixture import run_aex_fieldgen
from test_dg_compose import (OFF_BG_B, OFF_BG_G, OFF_BG_R, OFF_DEGENERATE,
    OFF_FIELD_WORLD_PTR, OFF_GRAD_B, OFF_GRAD_G, OFF_GRAD_R, OFF_INOUT_MODE,
    OFF_INTERP_MODE, OFF_INVERT, OFF_POWER, OFF_RENDER_MODE, OFF_SRC_WORLD_PTR,
    OFF_USE_BG, alloc_refcon, build_world, call_compose, make_loader)

W, H = 17, 11
IRB, ORB = 146, 150
CASES = (
    ("inside_rgb_sphere", 1, 1, 3, 1.0),
    ("outside_layer_power", 2, 2, 4, 2.5),
    ("both_rgb_linear", 3, 1, 2, 1.0),
    ("both_layer_constant", 3, 2, 1, 1.0),
)
EXPECTED_ACTIVE_SHA256 = {
    "inside_rgb_sphere": "8c8cf232a33325d68b1eafe3462da723f065a9897461b1aaf1f36edac0c9d381",
    "outside_layer_power": "7198748cb408938006b28f1cddb0e2e8c986516cb4ddcd7fc09a996730121f18",
    "both_rgb_linear": "2ec0411672210c26c669b8f95cb5966623600610670dc4c28641da5c6d683c31",
    "both_layer_constant": "7d5524c0b93359d057c697ea6ea3ac46ba0ca843e2efbb8888ff4c95cb3e47d4",
}

def main() -> int:
    mask = np.ones((H, W), dtype=np.uint8)
    mask[2:9, 4:13] = 0
    inside, ti = run_aex_fieldgen(mask, 4, 0)
    outside, to = run_aex_fieldgen((mask == 0).astype(np.uint8), 4, 0)
    inside_constant, tic = run_aex_fieldgen(mask, 4, 1)
    outside_constant, toc = run_aex_fieldgen((mask == 0).astype(np.uint8), 4, 1)
    assert all(t["hits"] for t in (ti, to, tic, toc))
    fields = {
        "inside_rgb_sphere": inside,
        "outside_layer_power": outside,
        "both_rgb_linear": np.maximum(inside, outside),
        "both_layer_constant": np.maximum(inside_constant, outside_constant),
    }

    pixels = {}
    for y in range(H):
        for x in range(W):
            if mask[y, x]:
                pixels[x, y] = (32768, (x * 997 + y * 211) % 32769,
                                (x * 613 + y * 1231) % 32769,
                                (x * 1499 + y * 307) % 32769)
    loader = make_loader()
    loader.register_libm_impls(max_threads=1)
    source_world = build_world(loader, W, H, pixels)
    field_worlds = {}
    for name, field in fields.items():
        words = np.rint(np.clip(field, 0, 1) * 32768).astype("<u2")
        field_worlds[name] = build_world(loader, W, H,
            {(x, y): (0, int(words[y, x]), 0, 0) for y in range(H) for x in range(W)})
    refcon = alloc_refcon(loader)
    def put(offset, fmt, value): loader.write_bytes(refcon + offset, struct.pack(fmt, value))
    for item in ((OFF_SRC_WORLD_PTR,"<Q",source_world),(OFF_DEGENERATE,"<B",0),
                 (OFF_USE_BG,"<B",1),(OFF_INVERT,"<B",1),
                 (OFF_GRAD_G,"<f",0.0),(OFF_GRAD_R,"<f",28/255),(OFF_GRAD_B,"<f",238/255),
                 (OFF_BG_G,"<f",160/255),(OFF_BG_R,"<f",16/255),(OFF_BG_B,"<f",48/255)):
        put(*item)

    source_active = b"".join(struct.pack("<4H", a, r, g, b)
        for a,g,r,b in (pixels.get((x,y),(0,0,0,0)) for y in range(H) for x in range(W)))
    source = b"".join(source_active[y*W*8:(y+1)*W*8] + b"\xa5"*(IRB-W*8) for y in range(H))
    hashes = {}
    with tempfile.TemporaryDirectory() as td:
        td = Path(td); src = td/"src"; exp = td/"exp"; exe = td/"h"
        src.write_bytes(source)
        build = subprocess.run(["clang++","-std=c++17","-O0","-I",str(HERE/"dg_renderbits_real_harness_20260716"),
            str(HERE/"dg_classic_pf16_background_combo_harness_20260810.cpp"),
            str(ROOT/"core/olmdistancegradation_fieldgen.cpp"),"-o",str(exe)],capture_output=True,text=True)
        assert build.returncode == 0, build.stderr
        for name, inout, render, interp, power in CASES:
            put(OFF_FIELD_WORLD_PTR,"<Q",field_worlds[name]); put(OFF_INOUT_MODE,"<i",inout)
            put(OFF_RENDER_MODE,"<i",render); put(OFF_INTERP_MODE,"<i",interp); put(OFF_POWER,"<f",power)
            words = [call_compose(loader, refcon, x, y) for y in range(H) for x in range(W)]
            active = b"".join(struct.pack("<4H", a, r, g, b) for a, g, r, b in words)
            hashes[name] = hashlib.sha256(active).hexdigest()
            expected = b"".join(active[y*W*8:(y+1)*W*8] + b"\xa5"*(ORB-W*8) for y in range(H))
            exp.write_bytes(expected)
            run = subprocess.run([str(exe),str(src),str(exp),name],capture_output=True,text=True)
            assert run.returncode == 0, run.stderr
            print(run.stdout,end="")
    assert hashes == EXPECTED_ACTIVE_SHA256
    assert len(set(hashes.values())) == len(CASES)
    print("active_sha256", hashes)
    print("PASS_OLMDISTANCEGRADATION_CLASSIC_PF16_BACKGROUND_COMBOS_EXACT")
    return 0

if __name__ == "__main__": raise SystemExit(main())
