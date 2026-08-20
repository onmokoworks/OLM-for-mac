#!/usr/bin/env python3
"""O2 production-source ToonDilate HD/UHD driver (no Adobe host)."""

from __future__ import annotations

import argparse
import ast
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "tests/test_olmtoondilate_generic_beta.py"
SOURCE = ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp"


def load_stub() -> str:
    tree = ast.parse(TEST.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "STUB" for t in node.targets):
            return ast.literal_eval(node.value)
    raise RuntimeError("ToonDilate production-source STUB not found")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geometry", choices=("hd", "uhd"), required=True)
    args = parser.parse_args()
    width, height = (1920, 1080) if args.geometry == "hd" else (3840, 2160)
    compiler = shutil.which(os.environ.get("CXX", "clang++"))
    if not compiler:
        raise RuntimeError("C++ compiler unavailable")
    stub = load_stub()
    begin = stub.index("int main(){")
    stub = stub[:begin] + f'''int main(){{
 bool ok=true;
 ok&=run<PF_Pixel8>({width},{height},5,29,13.0,{width}.0);
 ok&=run<PF_Pixel16>({width},{height},13,3,2.5,{width * 2}.0);
 ok&=run<PF_PixelFloat>({width},{height},64,7,0.99,{width}.0);
 return ok?0:1;
}}
'''
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="toondilate_perf_") as raw:
        directory = Path(raw)
        (directory / "AEFX_SuiteHelper.h").write_text("#pragma once\n", encoding="utf-8")
        cpp, executable = directory / "probe.cpp", directory / "probe"
        cpp.write_text(stub.replace("SOURCE_PATH", str(SOURCE)), encoding="utf-8")
        build = subprocess.run(
            [compiler, "-std=c++17", "-O2", "-fno-fast-math", "-ffp-contract=off",
             "-I", str(directory), str(cpp), "-o", str(executable)],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        if build.returncode:
            raise RuntimeError(build.stderr[-12000:])
        run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True, text=True,
                             timeout=150, check=False)
        if run.returncode:
            raise RuntimeError(run.stdout[-4000:] + run.stderr[-12000:])
    cases = [{
        "geometry": args.geometry, "width": width, "height": height,
        "depth": depth, "status": "passed", "oracle": "chebyshev_single_seed_full_words",
        "independent_strides": True,
        "radius": radius, "comp_width": comp,
    } for depth, radius, comp in ((8, 13.0, width), (16, 2.5, width * 2), (32, 0.99, width))]
    print("OLM_PERF_CASES_JSON=" + json.dumps(cases, separators=(",", ":")))
    print(f"ok: ToonDilate {args.geometry} PF8/PF16/PF32 O2 in {time.monotonic()-started:.3f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
