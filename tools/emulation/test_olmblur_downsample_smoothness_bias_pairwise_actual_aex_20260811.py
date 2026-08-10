#!/usr/bin/env python3
"""Pairwise OLMBlur downsample x Smoothness/Bias complete-buffer proof."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import subprocess
import tempfile
from pathlib import Path

import test_olmblur_amount_repeat_legacy_matrix_actual_aex_20260810 as base
from aex_loader import AexLoader
from test_olmblur_fullentry import build_context, build_pf_suites

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / "fixtures/olmblur_downsample_smoothness_bias_pairwise_20260811"
MANIFEST = FIXTURE / "manifest.json"
REPORT = ROOT / "refs/conformance/olmblur_downsample_smoothness_bias_pairwise_actual_aex_20260811.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def covering_rows(legacy: int) -> list[dict]:
    """Strength-2 binary OA(8, 6), independently applied per Legacy branch."""
    rows = []
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                rows.append({"downsample_x": ((1,2),(2,1))[a], "downsample_y": ((1,1),(2,1))[b],
                    "amount": (5.0,129.4)[c], "repeat": (1,2)[a ^ b],
                    "smoothness": (25.0,100.0)[b ^ c], "bias_direction": (1,2)[a ^ b ^ c],
                    "legacy": legacy, "oa_bits": [a,b,c]})
    return rows


def alloc(loader: AexLoader, data: bytes) -> int:
    address = loader.bump_alloc(len(data), align=64)
    loader.write_bytes(address, data)
    return address


def run_actual(depth: int, row: dict, source: bytes) -> tuple[bytes, dict]:
    loader = AexLoader(str(base.AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    loader.register_import_impl("pow", lambda uc,args: (loader.write_xmm_f64(0, math.pow(loader.read_xmm_f64(0), loader.read_xmm_f64(1))) or 0))
    loader.register_import_impl("powf", lambda uc,args: (loader.write_xmm_f32(0, math.pow(loader.read_xmm_f32(0), loader.read_xmm_f32(1))) or 0))
    spbasic, events = build_pf_suites(loader)
    context = build_context(loader, spbasic)
    xn, xd = row["downsample_x"]
    loader.write_bytes(context + 0x11C, struct.pack("<i", xn))
    loader.write_bytes(context + 0x120, struct.pack("<I", xd))
    source_data, output_data = alloc(loader, source), alloc(loader, source)

    def world(data: int) -> int:
        address = loader.host_alloc(0x80)
        loader.write_bytes(address, b"\0" * 0x80)
        loader.write_bytes(address + 0x18, struct.pack("<Q", data))
        loader.write_bytes(address + 0x20, struct.pack("<I", 24 * base.PIXEL_BYTES[depth]))
        loader.write_bytes(address + 0x24, struct.pack("<I", 24))
        loader.write_bytes(address + 0x28, struct.pack("<I", 24))
        loader.write_bytes(address + 0x2C, struct.pack("<H", depth))
        return address

    params = loader.host_alloc(0x40)
    loader.write_bytes(params, b"\0" * 0x40)
    loader.write_bytes(params + 0x18, struct.pack("<I", depth))
    loader.write_bytes(params + 0x20, struct.pack("<f", row["amount"]))
    loader.write_bytes(params + 0x24, struct.pack("<f", row["smoothness"]))
    loader.write_bytes(params + 0x28, struct.pack("<I", row["repeat"]))
    loader.write_bytes(params + 0x2C, struct.pack("<I", row["bias_direction"]))
    loader.write_bytes(params + 0x30, bytes((row["legacy"],)))
    result = loader.call_function(base.ENTRIES[(depth,row["legacy"])],
        int_args=[context,world(source_data),world(output_data),params], max_instructions=100_000_000)
    if result["instructions"] >= 100_000_000:
        raise RuntimeError("actual AEX instruction cap")
    return loader.read_bytes(output_data,len(source)), {"instructions": result["instructions"], "callback_count": len(events)}


def export() -> None:
    assert sha256(base.AEX.read_bytes()) == base.AEX_SHA256
    FIXTURE.mkdir(parents=True, exist_ok=True)
    cases=[]
    for depth in (8,16,32):
        source=base.source_bytes(depth)
        source_name=f"source_{base.FILE_NAMES[depth]}"
        (FIXTURE/source_name).write_bytes(source)
        for legacy in (0,1):
            for index,row in enumerate(covering_rows(legacy)):
                expected,run=run_actual(depth,row,source)
                case_id=f"pf{depth}_legacy{legacy}_oa{index}"
                expected_name=f"expected_{case_id}.bin"
                (FIXTURE/expected_name).write_bytes(expected)
                cases.append({"id":case_id,"depth":depth,**row,"source":source_name,"source_sha256":sha256(source),
                    "expected":expected_name,"expected_sha256":sha256(expected),**run})
                print(f"AEX {case_id} x={row['downsample_x']} y={row['downsample_y']} smooth={row['smoothness']} bias={row['bias_direction']}",flush=True)
    MANIFEST.write_text(json.dumps({"schema":"olmblur.downsample-smoothness-bias-pairwise.actual-aex/1",
        "plugin":"OLMBlur","actual_aex_sha256":base.AEX_SHA256,"geometry":[24,24],
        "design":"two independent OA(8,6,2) matrices per depth, one per Legacy branch; strength 2",
        "ui_bias":{"1":"Vertical (horizontal then vertical)","2":"Horizontal (vertical then horizontal)"},
        "cases":cases},indent=2,sort_keys=True)+"\n")


def probe_source() -> str:
    source=base.public_probe_source()
    replacements={
        "if (argc != 12) return 2;":"if (argc != 16) return 2;",
        "const int repeat = std::atoi(argv[6]), bias = std::atoi(argv[7]), legacy = std::atoi(argv[8]), padding = std::atoi(argv[9]);":
          "const int repeat = std::atoi(argv[6]), bias = std::atoi(argv[7]), legacy = std::atoi(argv[8]), xn = std::atoi(argv[9]), xd = std::atoi(argv[10]), yn = std::atoi(argv[11]), yd = std::atoi(argv[12]), padding = std::atoi(argv[13]);",
        "const auto source = read_file(argv[10]), expected = read_file(argv[11]);":"const auto source = read_file(argv[14]), expected = read_file(argv[15]);",
        "in_data.downsample_x = {1,1}; in_data.downsample_y = {1,1};":"in_data.downsample_x = {xn,xd}; in_data.downsample_y = {yn,yd};"}
    for old,new in replacements.items():
        if old not in source: raise RuntimeError(f"probe shape drift: {old}")
        source=source.replace(old,new)
    return source


def compile_probe(directory: Path) -> Path:
    source=directory/"probe.cpp"
    source.write_text(probe_source().replace("__OLMBLUR_MAC_SOURCE__",str(ROOT/"mac/OLMBlur/OLMBlur.cpp").replace("\\","\\\\").replace('"','\\"')))
    executable=directory/"probe"
    sdk=subprocess.run(["xcrun","--show-sdk-path"],capture_output=True,text=True,check=True).stdout.strip()
    command=["clang++","-std=c++17","-arch","arm64","-O2","-DOLMBLUR_HOSTLESS_RENDER_HARNESS=1","-fno-fast-math","-ffp-contract=off","-isysroot",sdk,
      "-I",str(ROOT/"Headers"),"-I",str(ROOT/"Headers/SP"),"-I",str(ROOT/"Util"),"-I",str(ROOT/"Resources"),"-I",str(ROOT/"core"),str(source),
      *[str(ROOT/p) for p in ("core/olmblur_helper.cpp","core/olmblur_fullworker_helper.cpp","core/olmblur_worker16_nonlegacy.cpp","core/olmblur_worker16_legacy.cpp","core/olmblur_worker32_nonlegacy.cpp","core/olmblur_worker32_legacy.cpp","core/olmblur_worker8_legacy.cpp","core/olmblur_worker_orchestration.cpp")],"-framework","Cocoa","-o",str(executable)]
    subprocess.run(command,cwd=ROOT,check=True)
    return executable


def verify() -> None:
    assert sha256(base.AEX.read_bytes())==base.AEX_SHA256
    manifest=json.loads(MANIFEST.read_text()); assert len(manifest["cases"])==48
    results=[]
    with tempfile.TemporaryDirectory(prefix="olmblur_ds_smooth_bias_") as name:
        executable=compile_probe(Path(name))
        for case in manifest["cases"]:
            source,expected=FIXTURE/case["source"],FIXTURE/case["expected"]
            assert sha256(source.read_bytes())==case["source_sha256"] and sha256(expected.read_bytes())==case["expected_sha256"]
            xn,xd=case["downsample_x"]; yn,yd=case["downsample_y"]
            padding={8:17,16:23,32:32}[case["depth"]]
            run=subprocess.run([str(executable),str(case["depth"]),"24","24",str(case["amount"]),str(case["smoothness"]),str(case["repeat"]),str(case["bias_direction"]),str(case["legacy"]),str(xn),str(xd),str(yn),str(yd),str(padding),str(source),str(expected)],capture_output=True,text=True,cwd=ROOT)
            if run.returncode: raise RuntimeError(f"{case['id']}: {run.stdout}\n{run.stderr}")
            observed=json.loads(run.stdout); assert observed["mismatched_bytes"]==observed["padding_mismatches"]==0
            results.append({"id":case["id"],"oa_bits":case["oa_bits"],"production":observed})
    REPORT.write_text(json.dumps({"schema":"olmblur.downsample-smoothness-bias-pairwise.production/1","status":"exact_pairwise","actual_aex_sha256":base.AEX_SHA256,"case_count":48,"geometry":[24,24],
      "matrix":{"depth":[8,16,32],"downsample_x":[[1,2],[2,1]],"downsample_y":[[1,1],[2,1]],"amount":[5,129.4],"repeat":[1,2],"legacy":[0,1],"smoothness":[25,100],"bias_direction":[1,2]},
      "coverage":"within each Legacy branch every pair of the six binary factors occurs in all four value combinations",
      "decision":"downsample_x scales NonLegacy Amount and Legacy radius only; Legacy sigma retains UI Amount; neither axis transforms Smoothness or Bias",
      "cases":results,"not_proven":["three-way interactions outside covering rows","native AE world resizing","other geometry/values"]},indent=2,sort_keys=True)+"\n")
    print("PASS_OLMBLUR_DOWNSAMPLE_SMOOTHNESS_BIAS_PAIRWISE cases=48 exact=1")


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--export",action="store_true"); args=parser.parse_args()
    export() if args.export else verify()
