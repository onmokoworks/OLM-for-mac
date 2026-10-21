#!/usr/bin/env python3
"""Close the former six DirectionalBlur exported-Smart residual cells at expf."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
GAUSSIAN = ROOT / "core/dblur_gaussian.h"
BASE = ROOT / "tools/emulation/test_olmdirectionalblur_mac_smartrender_adapter_20260717.py"
INTERNAL_FIXTURE = ROOT / "tools/emulation/dblur_fullrender_host_fixture_20260711.py"
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
SOURCE_PNG = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"
PINNED_WORKER = ROOT / "handoffs/olmdirectionalblur_exported_smart_worker_ceil_20260814/bin/aex-guest-worker"
RAW_WORKER = ROOT / "handoffs/olmdirectionalblur_exported_smart_remaining6_census_20260814/bin/aex-guest-worker-raw-dump"
CEIL_PATCH = ROOT / "tools/emulation/aexcompat_olmdirectionalblur_double_ceil_import_20260814.patch"
RAW_PATCH = ROOT / "handoffs/olmdirectionalblur_exported_smart_remaining6_census_20260814/raw_dump.patch"
BUILD_IDENTITY = ROOT / "handoffs/olmdirectionalblur_exported_smart_remaining6_census_20260814/build_identity.json"
DECOMP = ROOT / "decomp/OLMDirectionalBlur.aex.c.txt"
DISASM = ROOT / "disasm/OLMDirectionalBlur.aex.asm.txt"
EXPORTED = ROOT / "refs/conformance/olmdirectionalblur_dual_side_exported_smart_closure_20260814.json"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_exported_smart_remaining6_census_20260814.json"
NOTE = REPORT.with_suffix(".md")

TUPLES = (
    (50, 50, 100, 100, 0, 25, 1),
    (50, 100, 50, 50, 50, 100, 2),
    (100, 50, 50, 100, 0, 100, 2),
    (100, 100, 100, 50, 50, 25, 1),
)
CELLS = ((8, 2), (16, 2), (32, 0), (32, 1), (32, 2), (32, 3))
EXPECTED_ROWS_SHA256 = "a1c8f62218bd274c4509f10c88c41ca79f99640439c24c230cfa98bd60c5e796"
IDENTITY_KEYS = {
    "production_source_sha256", "aex_sha256", "source_png_sha256", "pinned_worker_sha256",
    "raw_dump_worker_sha256", "ceil_patch_sha256", "raw_dump_patch_sha256",
    "raw_dump_build_identity_sha256", "exported_closure_sha256", "core_sha256",
    "internal_owner_fixture_sha256",
    "decomp_sha256", "disasm_sha256", "gaussian_header_sha256",
}
CORE_KEYS = {"dblur_frontonly.cpp", "dblur_rotate.cpp", "dblur_rowdriver.cpp", "dblur_field.cpp"}
ROW_KEYS = {"depth", "tuple_index", "geometry", "historical_double_round_raw_sha256",
            "production_direct_raw_sha256", "actual_aex_native_expf_raw_sha256",
            "exported_raw_sha256", "production_matches_exported",
            "actual_aex_native_expf_matches_exported", "raw_bytes", "historical_diff_count",
            "historical_diffs"}
DIFF_KEYS = {"x", "y", "channel", "mac_value", "worker_value", "bit_delta", "mac_hex", "worker_hex"}
EXPECTED_SHAS = {
    (8, 2): ("312a602e939e68cae1b8d966af9ec33e0a8c3646c1c326664abbcb73456bce0e", "636e649414ff0ad3968aabb97733dbb67f92900898829361b3f44c58758cfdb3"),
    (16, 2): ("902490856e0c784d2c2fb9b1ba91d4e1ada5053acbeddaef5da15ade471a815e", "4846a56aea99d2db6be3e56930a8ef1143394e89ca97e316d84a8ec165b4179d"),
    (32, 0): ("27ed24ed8bf54b48af831e6ec5a44dd195c89b2fdd0acea5dee123b37d5adc20", "05989b2976a2056c738a2c41cf6c9ac39a3fcf8caa35eba4ca1d828fecb9fe19"),
    (32, 1): ("0b74caf1aef39ab242ca09b10d65bdc77a3646f31511a72f29c3e5e6d70635c2", "814ae4ec073d6e6ad4c83dea25227de5362d0ae6b8346d155c6aafe086149ac7"),
    (32, 2): ("ea11382502f61da8a5a1408dd294b15dd5af0fda81f18b9823c2d2a453f0b792", "453bbdf19955a3c6b91f2ca9b756e0d0aa9f2949b5855050636170a117039fc1"),
    (32, 3): ("faa5ad5686a58a4f390a354e14c72ac4255212b1be05ddf174345e8d11d42782", "3424989500b9b05791c1ce9e33e99fb810b5e3c63ad6b4e8c3897c6a2d832c09"),
}
EXPECTED_DIFFS = {
    (8, 2): ((9, 10, "R", -1), (10, 10, "R", 1), (9, 13, "R", -1), (9, 19, "R", -1), (9, 24, "R", -1)),
    (16, 2): ((9, 10, "R", -1), (10, 10, "R", 1), (9, 13, "R", -1), (9, 19, "R", -1), (9, 24, "R", -1)),
    (32, 0): ((53, 35, "A", 1),),
    (32, 1): ((59, 33, "A", 1),),
    (32, 2): ((9, 6, "A", 1), (9, 7, "A", 1), (10, 7, "A", 1), (9, 10, "A", 1),
              (9, 10, "R", -1), (10, 10, "R", 1), (9, 13, "A", 2), (9, 13, "R", -1),
              (10, 16, "A", 1), (9, 19, "A", 1), (9, 19, "R", -1), (9, 20, "A", 1),
              (10, 23, "A", 1), (9, 24, "A", 2), (9, 24, "R", -1), (58, 34, "A", 1)),
    (32, 3): ((53, 35, "A", 1), (54, 35, "A", 1)),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_base():
    spec = importlib.util.spec_from_file_location("dblur_remaining6_base", BASE)
    if not spec or not spec.loader:
        raise RuntimeError("base probe import")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_direct_probe(temp: Path) -> Path:
    base = load_base()
    base.compile_probe(temp)
    cpp = temp / "olmdirectionalblur_mac_smartrender_adapter_probe.cpp"
    text = cpp.read_text()
    if text.count("int main()") != 1:
        raise RuntimeError("base main drift")
    text = text.replace("int main()", "int old_main()", 1)
    text += r'''
static bool read_all(const char *path, std::vector<std::uint8_t> &data) {
  FILE *f = std::fopen(path, "rb");
  if (!f) return false;
  const bool ok = std::fread(data.data(), 1, data.size(), f) == data.size();
  std::fclose(f); return ok;
}
static bool write_all(const char *path, const void *data, std::size_t size) {
  FILE *f = std::fopen(path, "wb");
  if (!f) return false;
  const bool ok = std::fwrite(data, 1, size, f) == size;
  std::fclose(f); return ok;
}
int main(int argc, char **argv) {
  if (argc != 3) return 2;
  constexpr int W=64,H=36,N=W*H;
  std::vector<std::uint8_t> rgba(N*4);
  if (!read_all(argv[1], rgba)) return 3;
  const int tuples[4][7]={{50,50,100,100,0,25,1},{50,100,50,50,50,100,2},
                          {100,50,50,100,0,100,2},{100,100,100,50,50,25,1}};
  char path[4096];
  {
    std::vector<std::uint8_t> source(N*4), destination(N*4,0xee);
    for(int p=0;p<N;++p){source[p*4]=rgba[p*4+3];source[p*4+1]=rgba[p*4];
      source[p*4+2]=rgba[p*4+1];source[p*4+3]=rgba[p*4+2];}
    PF_EffectWorld in{source.data(),W*4,W,H,8,{0,0,W,H}};
    PF_EffectWorld out{destination.data(),W*4,W,H,8,{0,0,W,H}};
    OLMDirectionalBlurInfo info{}; const int *t=tuples[2];
    info.angle_deg=45;info.brightness_gain=1;info.size_variation=t[4];
    info.front_strength=8;info.front_alpha_fade=t[0];info.front_sharp_tail=t[1];
    info.back_strength=8;info.back_alpha_fade=t[2];info.back_sharp_tail=t[3];
    info.noise_variation=t[5];info.noise_type=t[6];info.seed=1;info.thickness=3;
    info.render_scale_x=info.render_scale_y=1;
    if(RenderExact8(&in,&out,nullptr,info)!=PF_Err_NONE) return 4;
    std::snprintf(path,sizeof(path),"%s/mac-pf8-t2.raw",argv[2]);
    if(!write_all(path,destination.data(),destination.size())) return 5;
  }
  std::vector<std::uint16_t> source16(N*4),destination16(N*4);
  std::vector<float> source32(N*4),destination32(N*4);
  for(int p=0;p<N;++p){const int q=p*4;const std::uint8_t c[4]={rgba[q+3],rgba[q],rgba[q+1],rgba[q+2]};
    for(int k=0;k<4;++k){source16[q+k]=(std::uint32_t(c[k])*32768+127)/255;source32[q+k]=float(c[k])/255.0f;}}
  {
    const int *t=tuples[2];
    if(olm_dblur_full_argb16(source16.data(),destination16.data(),W,H,8,t[0],float(t[1]),8,t[2],float(t[3]),
       float(t[4]),1.0f,45.0f,float(t[5]),t[6],1,0,3.0f,nullptr,0,1)!=0) return 6;
    std::snprintf(path,sizeof(path),"%s/mac-pf16-t2.raw",argv[2]);
    if(!write_all(path,destination16.data(),destination16.size()*sizeof(std::uint16_t))) return 7;
  }
  for(int i=0;i<4;++i){const int *t=tuples[i];
    if(olm_dblur_full_argb32(source32.data(),destination32.data(),W,H,8,t[0],float(t[1]),8,t[2],float(t[3]),
       float(t[4]),45.0f,1.0f,float(t[5]),t[6],1,0,3.0f,nullptr,0,1)!=0) return 8;
    std::snprintf(path,sizeof(path),"%s/mac-pf32-t%d.raw",argv[2],i);
    if(!write_all(path,destination32.data(),destination32.size()*sizeof(float))) return 9;
  }
  return 0;
}
'''
    cpp.write_text(text)
    executable = temp / "remaining6-direct"
    sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
    command = ["clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math", "-ffp-contract=off",
               "-isysroot", sdk, "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
               "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"), str(cpp),
               str(ROOT / "core/dblur_frontonly.cpp"), str(ROOT / "core/dblur_rotate.cpp"),
               str(ROOT / "core/dblur_rowdriver.cpp"), str(ROOT / "core/dblur_field.cpp"),
               "-framework", "Cocoa", "-o", str(executable)]
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "tools/emulation") + os.pathsep + environment.get("PYTHONPATH", "")
    run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, env=environment)
    if run.returncode:
        raise RuntimeError(run.stderr)
    return executable


def params(index: int) -> list[str]:
    ff, fs, bf, bs, size, nv, noise_type = TUPLES[index]
    return ["Angle@1=45", "Brightness Gain@2=1", f"Size Variation@3={size}", "Blur Strength@5=8",
            f"Alpha Fade@6={ff}", f"Sharp Tail@7={fs}", "Blur Strength@10=8",
            f"Alpha Fade@11={bf}", f"Sharp Tail@12={bs}", f"Noise Variation@15={nv}",
            f"Noise Type@16={noise_type}", "Seed@18=1", "Offset@19=0", "Thickness@20=3"]


def identities() -> dict[str, object]:
    return {
        "production_source_sha256": sha256(SOURCE), "aex_sha256": sha256(AEX),
        "source_png_sha256": sha256(SOURCE_PNG), "pinned_worker_sha256": sha256(PINNED_WORKER),
        "raw_dump_worker_sha256": sha256(RAW_WORKER), "ceil_patch_sha256": sha256(CEIL_PATCH),
        "raw_dump_patch_sha256": sha256(RAW_PATCH),
        "raw_dump_build_identity_sha256": sha256(BUILD_IDENTITY),
        "exported_closure_sha256": sha256(EXPORTED),
        "internal_owner_fixture_sha256": sha256(INTERNAL_FIXTURE),
        "decomp_sha256": sha256(DECOMP), "disasm_sha256": sha256(DISASM),
        "gaussian_header_sha256": sha256(GAUSSIAN),
        "core_sha256": {name: sha256(ROOT / "core" / name) for name in sorted(CORE_KEYS)},
    }


def static_control_flow() -> dict[str, object]:
    decomp = DECOMP.read_text()
    assembly = DISASM.read_text()
    section = assembly[assembly.index("; === FUN_180007bd0 @ 180007bd0 ==="):
                       assembly.index("; === FUN_180007eb0 @ 180007eb0 ===")]
    required = (
        "case 0x18:\n    uVar6 = FUN_180007bd0(param_2,param_3,param_6);",
        "CALL 0x180006c50",
        "CALL 0x180004a20",
        "CALL 0x180003c90",
        "CALL 0x1800057b0",
        "180007e68  CALL 0x180003240",
        "180007e73  CALL 0x180008780",
    )
    if required[0] not in decomp or any(token not in section for token in required[1:]):
        raise RuntimeError("exported Smart static control-flow drift")
    if section.count("CALL 0x180006c50") != 3:
        raise RuntimeError("parameter materializer call count drift")
    return {
        "effectmain_smart_command": "case 0x18 -> FUN_180007bd0",
        "parameter_materializer": "FUN_180006c50 once per selected depth branch",
        "depth_owners": {"PF8": "FUN_180004a20", "PF16": "FUN_180003c90", "PF32": "FUN_1800057b0"},
        "post_depth_owner_path": "store PF_Err -> local teardown FUN_180003240 -> suite teardown FUN_180008780 -> return",
        "separate_post_owner_pixel_transform_call": False,
        "iterate_callback_leaf_executed_as_guest_code": True,
        "gaussian_leaf_import": "expf",
    }


def compare(depth: int, index: int, historical: bytes, production: bytes,
            actual_native_expf: bytes, worker: bytes) -> dict[str, object]:
    unit = {8: 1, 16: 2, 32: 4}[depth]
    channels = "ARGB"
    diffs = []
    for offset in range(0, len(historical), unit):
        left, right = historical[offset:offset+unit], worker[offset:offset+unit]
        if left == right:
            continue
        word = offset // unit; pixel = word // 4
        if depth == 8:
            mac_value, worker_value = left[0], right[0]
        elif depth == 16:
            mac_value, worker_value = int.from_bytes(left, "little"), int.from_bytes(right, "little")
        else:
            mac_value, worker_value = struct.unpack("<f", left)[0], struct.unpack("<f", right)[0]
        diffs.append({"x": pixel % 64, "y": pixel // 64, "channel": channels[word % 4],
                      "mac_value": mac_value, "worker_value": worker_value,
                      "bit_delta": int.from_bytes(left, "little") - int.from_bytes(right, "little"),
                      "mac_hex": left.hex(), "worker_hex": right.hex()})
    observed = tuple((d["x"], d["y"], d["channel"], d["bit_delta"]) for d in diffs)
    if observed != EXPECTED_DIFFS[(depth, index)]:
        raise RuntimeError(f"diff census drift PF{depth}/tuple{index}: {observed}")
    historical_sha, worker_sha = hashlib.sha256(historical).hexdigest(), hashlib.sha256(worker).hexdigest()
    if (historical_sha, worker_sha) != EXPECTED_SHAS[(depth, index)]:
        raise RuntimeError(f"raw identity drift PF{depth}/tuple{index}")
    production_sha = hashlib.sha256(production).hexdigest()
    actual_sha = hashlib.sha256(actual_native_expf).hexdigest()
    if production != worker or production_sha != worker_sha:
        raise RuntimeError(f"production expf split PF{depth}/tuple{index}")
    if actual_native_expf != worker or actual_sha != worker_sha:
        raise RuntimeError(f"actual AEX native expf split PF{depth}/tuple{index}")
    return {"depth": depth, "tuple_index": index, "geometry": [64, 36],
            "historical_double_round_raw_sha256": historical_sha,
            "production_direct_raw_sha256": production_sha,
            "actual_aex_native_expf_raw_sha256": actual_sha,
            "exported_raw_sha256": worker_sha, "production_matches_exported": True,
            "actual_aex_native_expf_matches_exported": True,
            "raw_bytes": len(historical), "historical_diff_count": len(diffs),
            "historical_diffs": diffs}


def run_internal_owner(fixture: Path, png: Path, output: Path, depth: int, index: int,
                       expf_leaf: str) -> None:
    ff, fs, bf, bs, size, nv, noise_type = TUPLES[index]
    meta = output.with_suffix(".json")
    command = [sys.executable, str(fixture), "--aex", str(AEX), "--source", str(png), "--output", str(meta),
               "--host-output-raw", str(output), "--bitdepth", str(depth), "--angle", "45",
               "--brightness-gain", "1", "--downsample-num", "1", "--downsample-den", "1",
               "--front-strength", "8", "--size-variation", str(size), "--front-alpha-fade", str(ff),
               "--front-sharp-tail", str(fs), "--back-strength", "8", "--back-alpha-fade", str(bf),
               "--back-sharp-tail", str(bs), "--noise-variation", str(nv), "--noise-type", str(noise_type),
               "--seed", "1", "--noise-offset", "0", "--thickness", "3", "--world-area", "0", "0", "64", "36",
               "--row-padding", "0", "--no-detour-rotate", "--max-instructions", "30000000",
               "--actual-iterate-callbacks", "--expf-leaf", expf_leaf]
    if depth == 16:
        command.extend(["--pf16-source-scale", "sdk-32768"])
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "tools/emulation") + os.pathsep + environment.get("PYTHONPATH", "")
    run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, env=environment)
    if run.returncode:
        raise RuntimeError(f"internal owner PF{depth}/tuple{index}: {run.stderr}")


def run_fresh() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="olmdblur_remaining6_") as raw:
        temp = Path(raw)
        crop = Image.open(SOURCE_PNG).convert("RGBA").crop((472, 262, 536, 298))
        png = temp / "input.png"; crop.save(png)
        rgba = temp / "input.rgba"
        rgba.write_bytes(bytes(v for pixel in crop.get_flattened_data() for v in pixel))
        direct = build_direct_probe(temp)
        run = subprocess.run([str(direct), str(rgba), str(temp)], cwd=ROOT, capture_output=True, text=True)
        if run.returncode:
            raise RuntimeError(f"direct probe rc={run.returncode}: {run.stderr}")
        rows = []
        formats = {8: "argb8", 16: "argb16", 32: "argb32f"}
        for depth, index in CELLS:
            output = temp / f"worker-pf{depth}-t{index}.png"
            worker = subprocess.run([str(RAW_WORKER), "render-png", str(AEX), str(png), str(output),
                                     "--pixel-format", formats[depth], *params(index)],
                                    cwd=ROOT, capture_output=True, text=True)
            if worker.returncode:
                raise RuntimeError(worker.stderr)
            meta = json.loads(worker.stdout)
            raw_path = Path(meta["output_raw"])
            if meta["raw_pixel_sha256"] != EXPECTED_SHAS[(depth, index)][1]:
                raise RuntimeError("worker report/raw drift")
            historical_path = temp / f"actual-double-pf{depth}-t{index}.raw"
            native_path = temp / f"actual-native-pf{depth}-t{index}.raw"
            run_internal_owner(INTERNAL_FIXTURE, png, historical_path, depth, index, "double-round")
            run_internal_owner(INTERNAL_FIXTURE, png, native_path, depth, index, "native-f32")
            rows.append(compare(depth, index, historical_path.read_bytes(),
                                (temp / f"mac-pf{depth}-t{index}.raw").read_bytes(),
                                native_path.read_bytes(), raw_path.read_bytes()))
    return {
        "schema": "olmdirectionalblur.exported-smart-former-remaining6-expf-closure/4",
        "status": "PASS_FORMER_REMAINING6_EXPF_RAW_EXACT",
        "identities": identities(), "static_control_flow": static_control_flow(),
        "rows": rows, "rows_sha256": digest(rows),
        "summary": {"cells": 6, "PF8_words_different": 5, "PF16_words_different": 5,
                    "PF32_words_different": 20, "PF32_max_ulp": 2,
                    "actual_aex_native_expf_matches_exported_cells": 6,
                    "production_direct_matches_exported_cells": 6,
                    "integer_tuple2_red_coordinates_shared": True,
                    "PF32_other_tuple_differences_alpha_only": True},
        "boundary": {"production_policy": "all six cells are admitted on arm64 only; x86_64 keeps the six cells fail-closed",
                     "root_cause": "double-round exp versus imported single-precision expf leaf",
                     "actual_aex_iterate_callback_guest_code_executed": True,
                     "double_round_counterfactual_recreates_all_residuals": True,
                     "aexcompat_native_f32_is_not_native_windows_ucrt": True,
                     "windows_ucrt_return_table_counts": [96, 240],
                     "remaining_six_required_gaussian_counts": [8, 50, 100],
                     "windows_ucrt_return_covers_remaining_six": False,
                     "native_windows_or_after_effects": False, "expectation_compensation": False},
    }


def validate(report: dict[str, object], live: bool = False) -> bool:
    if set(report) != {"schema", "status", "identities", "static_control_flow", "rows", "rows_sha256", "summary", "boundary"}:
        return False
    if report["schema"] != "olmdirectionalblur.exported-smart-former-remaining6-expf-closure/4" or report["status"] != "PASS_FORMER_REMAINING6_EXPF_RAW_EXACT":
        return False
    retained_identities = json.loads(REPORT.read_text())["identities"]
    if report["identities"] != (identities() if live else retained_identities):
        return False
    if not isinstance(report["identities"], dict) or set(report["identities"]) != IDENTITY_KEYS:
        return False
    if not isinstance(report["identities"].get("core_sha256"), dict) or set(report["identities"]["core_sha256"]) != CORE_KEYS:
        return False
    try:
        if report["static_control_flow"] != static_control_flow():
            return False
    except (KeyError, RuntimeError, ValueError):
        return False
    rows = report["rows"]
    if report["rows_sha256"] != digest(rows) or report["rows_sha256"] != EXPECTED_ROWS_SHA256 or len(rows) != 6:
        return False
    if tuple((row.get("depth"), row.get("tuple_index")) for row in rows) != CELLS:
        return False
    for row in rows:
        if not isinstance(row, dict) or set(row) != ROW_KEYS:
            return False
        key = (row.get("depth"), row.get("tuple_index"))
        if key not in EXPECTED_SHAS or (row.get("historical_double_round_raw_sha256"), row.get("exported_raw_sha256")) != EXPECTED_SHAS[key]:
            return False
        if row.get("production_direct_raw_sha256") != row.get("exported_raw_sha256") or row.get("production_matches_exported") is not True:
            return False
        if row.get("actual_aex_native_expf_raw_sha256") != row.get("exported_raw_sha256") or row.get("actual_aex_native_expf_matches_exported") is not True:
            return False
        if row.get("geometry") != [64, 36] or row.get("raw_bytes") != 64 * 36 * 4 * {8: 1, 16: 2, 32: 4}[key[0]]:
            return False
        if not isinstance(row.get("historical_diffs"), list) or any(not isinstance(d, dict) or set(d) != DIFF_KEYS for d in row["historical_diffs"]):
            return False
        observed = tuple((d.get("x"), d.get("y"), d.get("channel"), d.get("bit_delta")) for d in row.get("historical_diffs", []))
        if observed != EXPECTED_DIFFS[key] or row.get("historical_diff_count") != len(observed):
            return False
        unit = {8: 1, 16: 2, 32: 4}[key[0]]
        for difference in row["historical_diffs"]:
            try:
                left = bytes.fromhex(difference["mac_hex"])
                right = bytes.fromhex(difference["worker_hex"])
            except (TypeError, ValueError):
                return False
            if len(left) != unit or len(right) != unit:
                return False
            if int.from_bytes(left, "little") - int.from_bytes(right, "little") != difference["bit_delta"]:
                return False
            if key[0] == 32:
                if difference["mac_value"] != struct.unpack("<f", left)[0] or difference["worker_value"] != struct.unpack("<f", right)[0]:
                    return False
            elif difference["mac_value"] != int.from_bytes(left, "little") or difference["worker_value"] != int.from_bytes(right, "little"):
                return False
    return report["summary"] == {"cells": 6, "PF8_words_different": 5, "PF16_words_different": 5,
        "PF32_words_different": 20, "PF32_max_ulp": 2,
        "actual_aex_native_expf_matches_exported_cells": 6,
        "production_direct_matches_exported_cells": 6,
        "integer_tuple2_red_coordinates_shared": True,
        "PF32_other_tuple_differences_alpha_only": True} and report["boundary"] == {
        "production_policy": "all six cells are admitted on arm64 only; x86_64 keeps the six cells fail-closed",
        "root_cause": "double-round exp versus imported single-precision expf leaf",
        "actual_aex_iterate_callback_guest_code_executed": True,
        "double_round_counterfactual_recreates_all_residuals": True,
        "aexcompat_native_f32_is_not_native_windows_ucrt": True,
        "windows_ucrt_return_table_counts": [96, 240],
        "remaining_six_required_gaussian_counts": [8, 50, 100],
        "windows_ucrt_return_covers_remaining_six": False,
        "native_windows_or_after_effects": False, "expectation_compensation": False}


def write_note(report: dict[str, object]) -> None:
    NOTE.write_text(
        "# OLMDirectionalBlur exported-Smart former remaining-six expf closure\n\n"
        "The six formerly rejected 64×36 cells are raw-exact on arm64. The historical double-round "
        "counterfactual differs at the same five red "
        "coordinates in PF8 and PF16. PF32 exposes those five red residuals plus eleven alpha "
        "residuals; the other three PF32 tuples differ only in alpha at 1, 1, and 2 words. "
        "All historical float residuals are at most two ULP. The fixture executes the actual guest AEX "
        "Iterate callback body. Selecting the imported single-precision `expf` leaf makes all six outputs "
        "byte-identical to the pinned exported Smart worker, while the double-round counterfactual recreates "
        "every residual. Production admits those exact source/world/tuple cells on arm64 only. x86_64 remains "
        "fail-closed because the AEXCompat native-f32 leaf is not Windows UCRT, and the retained native-Windows "
        "UCRT return covers Gaussian counts 96 and 240 rather than the required 8, 50, and 100. No value "
        "compensation, native-Windows result, or After Effects claim is made.\n\n"
        f"Rows digest: `{report['rows_sha256']}`.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    report = run_fresh() if args.write or args.run else json.loads(REPORT.read_text())
    if not validate(report):
        raise RuntimeError("remaining-six census validation failed")
    if args.write:
        REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        write_note(report)
    elif not REPORT.exists() or json.loads(REPORT.read_text()) != report:
        raise RuntimeError("persisted remaining-six census drift")
    print(report["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
