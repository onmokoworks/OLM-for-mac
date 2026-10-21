#!/usr/bin/env python3
"""Replay the DirectionalBlur/DistanceGradation outputs from keyed expf/powf words.

The default self-test uses the local host leaves only to prove the table plumbing.
Passing --return-path first runs the strict native-Windows return validator.  This
tool never edits production admission and never launches After Effects.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
ANALYZER = ROOT / "scripts/analyze_olm_math_ucrt_batch_return_20260814.py"
DIRECTIONAL = ROOT / "tools/emulation/test_olmdirectionalblur_exported_smart_remaining6_census_20260814.py"
DG_HARNESS = ROOT / "tools/emulation/dg_pf32_power_powf_census_harness_20260813.cpp"
DG_FIELD = ROOT / "core/olmdistancegradation_fieldgen.cpp"
DG_VECTORS = ROOT / "refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_pf32_power_ucrt_powf_20260813/powf_vectors.json"
DB_VECTORS = ROOT / "refs/runtime_trace_packages/olm_runtime_trace_olmdirectionalblur_remaining6_ucrt_expf_20260814/expf_vectors.json"
DB_POWF_VECTORS = ROOT / "refs/runtime_trace_packages/olm_runtime_trace_olmdirectionalblur_remaining6_ucrt_powf_20260814/powf_vectors.json"
REPORT = ROOT / "refs/conformance/olm_math_ucrt_downstream_replay_readiness_20260814.json"

DG_EXPECTED = {
    "mode2.bg0": "3e04fab22152eb32638a4864f256f76bd118ffbb6315b0c7a8b852b27509fc39",
    "mode2.bg1": "6c86caeab878b256f933d03e105085f86810f255296cc2fa5ac434dc5067e496",
    "mode3.bg0": "12bdf0c207bff9fb8c0390f848883281b8484802baea72c82f98db96c3176849",
    "mode3.bg1": "dfeb76265a320e6aae3945fdb2aaa76cd9e77f7e63f586046bca744bfad9cb07",
    "mode4.bg0": "849be120ac0c5e4990c8a19135ebfccdb2f6350ffe53cd0bb1a9f6aafb486c2a",
    "mode4.bg1": "0d8860db7bffd87c6737298482eb60d0378b2dc63841d861ee8e174aaee0a81c",
    "mode5.bg0": "40b5d262cdc0ab372036c9d2774fa9400f74daa7895c75c2222a246b01c485a5",
    "mode5.bg1": "fe715e7973fa79d6043cbe86dcfce3205869fb23ac9d69a8d98b288ab20ad6d7",
}


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bits(value: float) -> str:
    return f"{struct.unpack('<I', struct.pack('<f', value))[0]:08x}"


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def gaussian_argument_bits(count: int, index: int) -> str:
    ratio = f32(float(count) / 3.0)
    square = f32(ratio * ratio)
    denominator = f32(float(square) + float(square) + 1.0e-5)
    numerator = f32(float(-(index * index)))
    return "0x" + bits(f32(numerator / denominator))


def write_table(path: Path, expf: dict[str, str], powf: dict[tuple[str, str], str]) -> None:
    lines = [f"e {key.removeprefix('0x')} {value.removeprefix('0x')}" for key, value in sorted(expf.items())]
    lines += [f"p {left.removeprefix('0x')} {right.removeprefix('0x')} {value.removeprefix('0x')}"
              for (left, right), value in sorted(powf.items())]
    path.write_text("\n".join(lines) + "\n")


INTERPOSER = r'''
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <dlfcn.h>
struct E { std::uint32_t a,r; }; struct P { std::uint32_t a,b,r; };
static E es[600]; static P ps[1024]; static int ne=0,np=0;
static std::uint32_t word(float v){std::uint32_t x;std::memcpy(&x,&v,4);return x;}
static float real(std::uint32_t x){float v;std::memcpy(&v,&x,4);return v;}
__attribute__((constructor)) static void init(){const char *p=std::getenv("OLM_UCRT_TABLE");if(!p)std::_Exit(80);
 FILE*f=std::fopen(p,"r");if(!f)std::_Exit(81);char k;unsigned a,b,r;
 while(std::fscanf(f," %c",&k)==1){if(k=='e'){if(std::fscanf(f," %x %x",&a,&r)!=2||ne>=600)std::_Exit(82);es[ne++]={(std::uint32_t)a,(std::uint32_t)r};}
 else if(k=='p'){if(std::fscanf(f," %x %x %x",&a,&b,&r)!=3||np>=1024)std::_Exit(83);ps[np++]={(std::uint32_t)a,(std::uint32_t)b,(std::uint32_t)r};}
 else std::_Exit(84);}std::fclose(f);}
extern "C" float expf(float a) noexcept {auto x=word(a);for(int i=0;i<ne;i++)if(es[i].a==x)return real(es[i].r);
 if(std::getenv("OLM_UCRT_STRICT_EXPF"))std::_Exit(85);using F=float(*)(float);static F next=(F)dlsym(RTLD_NEXT,"expf");if(!next)std::_Exit(87);return next(a);}
extern "C" float powf(float a,float b) noexcept {auto x=word(a),y=word(b);for(int i=0;i<np;i++)if(ps[i].a==x&&ps[i].b==y)return real(ps[i].r);std::_Exit(86);}
'''


def build_interposer(temp: Path) -> Path:
    source = temp / "ucrt_table.cpp"
    source.write_text(INTERPOSER)
    return source


def compile_directional(temp: Path, census, interposer: Path) -> Path:
    census.build_direct_probe(temp)
    cpp = temp / "olmdirectionalblur_mac_smartrender_adapter_probe.cpp"
    executable = temp / "directional-table"
    sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
    command = ["clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math",
               "-ffp-contract=off", "-fno-builtin-expf", "-fno-builtin-powf", "-isysroot", sdk,
               "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"), "-I", str(ROOT / "Util"),
               "-I", str(ROOT / "Resources"), str(cpp), str(interposer),
               str(ROOT / "core/dblur_frontonly.cpp"), str(ROOT / "core/dblur_rotate.cpp"),
               str(ROOT / "core/dblur_rowdriver.cpp"), str(ROOT / "core/dblur_field.cpp"),
               "-framework", "Cocoa", "-o", str(executable)]
    run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if run.returncode:
        raise RuntimeError(run.stderr)
    return executable


def replay_directional(temp: Path, table: Path) -> dict[str, object]:
    census = load(DIRECTIONAL, "olm_dblur_ucrt_downstream")
    executable = compile_directional(temp, census, build_interposer(temp))
    crop = Image.open(census.SOURCE_PNG).convert("RGBA").crop((472, 262, 536, 298))
    rgba = temp / "input.rgba"
    rgba.write_bytes(bytes(v for pixel in crop.get_flattened_data() for v in pixel))
    environment = dict(os.environ, OLM_UCRT_TABLE=str(table), OLM_UCRT_STRICT_EXPF="1")
    run = subprocess.run([str(executable), str(rgba), str(temp)], cwd=ROOT, env=environment,
                         capture_output=True, text=True)
    if run.returncode:
        raise RuntimeError(f"directional replay rc={run.returncode}: {run.stderr}")
    rows = []
    for depth, index in census.CELLS:
        path = temp / f"mac-pf{depth}-t{index}.raw"
        actual = sha(path)
        expected = census.EXPECTED_SHAS[(depth, index)][1]
        rows.append({"depth": depth, "tuple_index": index, "raw_sha256": actual,
                     "exported_oracle_sha256": expected, "matches_exported_oracle": actual == expected})
    return {"cells": rows, "matching_cells": sum(row["matches_exported_oracle"] for row in rows)}


def replay_distance(temp: Path, table: Path) -> dict[str, object]:
    executable = temp / "distance-table"
    interposer = build_interposer(temp)
    command = ["clang++", "-std=c++17", "-O0", "-fno-builtin-powf",
               "-I", str(ROOT / "tools/emulation/dg_renderbits_real_harness_20260716"),
               str(DG_HARNESS), str(DG_FIELD), str(interposer), "-o", str(executable)]
    build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if build.returncode:
        raise RuntimeError(build.stderr)
    environment = dict(os.environ, OLM_UCRT_TABLE=str(table))
    run = subprocess.run([str(executable), str(temp)], cwd=ROOT, env=environment,
                         capture_output=True, text=True)
    if run.returncode:
        raise RuntimeError(f"distance replay rc={run.returncode}: {run.stderr}")
    rows = []
    for mode in range(2, 6):
        for background in (0, 1):
            key = f"mode{mode}.bg{background}"
            actual = sha(temp / f"power.mode{mode}.bg{background}.raw")
            rows.append({"cell": key, "raw_sha256": actual, "host_substituted_oracle_sha256": DG_EXPECTED[key],
                         "matches_host_substituted_oracle": actual == DG_EXPECTED[key]})
    return {"cells": rows, "matching_host_substituted_cells":
            sum(row["matches_host_substituted_oracle"] for row in rows)}


def maps_from_host() -> tuple[dict[str, str], dict[tuple[str, str], str]]:
    lib = ctypes.CDLL(None)
    expf = lib.expf; expf.argtypes = [ctypes.c_float]; expf.restype = ctypes.c_float
    emap = {}
    for row in json.loads(DB_VECTORS.read_text()):
        value = struct.unpack("<f", int(row["argument_bits"], 16).to_bytes(4, "little"))[0]
        emap[row["argument_bits"]] = "0x" + bits(expf(value))
    for count in (96, 240):
        for index in range(count):
            key = gaussian_argument_bits(count, index)
            value = struct.unpack("<f", int(key, 16).to_bytes(4, "little"))[0]
            emap[key] = "0x" + bits(expf(value))
    powf = lib.powf; powf.argtypes = [ctypes.c_float, ctypes.c_float]; powf.restype = ctypes.c_float
    pmap = {}
    for row in json.loads(DB_POWF_VECTORS.read_text()):
        left = struct.unpack("<f", int(row["input_bits"], 16).to_bytes(4, "little"))[0]
        right = struct.unpack("<f", int(row["exponent_bits"], 16).to_bytes(4, "little"))[0]
        pmap[(row["input_bits"], row["exponent_bits"])] = "0x" + bits(powf(left, right))
    pmap.update({(row["input_bits"], row["exponent_bits"]): row["host_result_bits"]
                 for row in json.loads(DG_VECTORS.read_text())})
    return emap, pmap


def maps_from_return(path: Path) -> tuple[dict[str, str], dict[tuple[str, str], str], dict[str, object]]:
    analyzer = load(ANALYZER, "olm_math_ucrt_return_analyzer")
    validated = analyzer.analyze(path)
    members = analyzer.load_members(path)
    _, directional_bytes = analyzer.suffix_member(members, "directional/run_summary.json")
    _, directional_powf_bytes = analyzer.suffix_member(members, "directional_powf/run_summary.json")
    _, distance_bytes = analyzer.suffix_member(members, "distance/run_summary.json")
    directional = json.loads(directional_bytes); directional_powf = json.loads(directional_powf_bytes)
    distance = json.loads(distance_bytes)
    # The request records the source expression's -0 word at index zero, while
    # the compiled production call materializes +0.  The strict analyzer has
    # already required expf(-0) == +1 exactly, so normalize only this IEEE-754
    # zero-sign pair before keyed replay; no nonzero argument is generalized.
    emap = {("0x00000000" if row["argument_bits"] == "0x80000000" else row["argument_bits"]):
            row["native_ucrt_result_bits"] for row in directional["rows"]}
    pmap = {(row["input_bits"], row["exponent_bits"]): row["native_ucrt_result_bits"]
            for row in directional_powf["rows"]}
    pmap.update({(row["input_bits"], row["exponent_bits"]): row["native_ucrt_result_bits"]
                 for row in distance["rows"]})
    return emap, pmap, validated


def replay(return_path: Path | None) -> dict[str, object]:
    if return_path is None:
        emap, pmap = maps_from_host(); mode = "host_substitute_plumbing_self_test"; validated = None
    else:
        emap, pmap, validated = maps_from_return(return_path); mode = "native_windows_ucrt_return"
    if len(emap) > 494 or len(pmap) != 850:
        raise RuntimeError("result map cardinality")
    with tempfile.TemporaryDirectory(prefix="olm-ucrt-downstream-") as raw:
        temp = Path(raw); table = temp / "table.txt"; write_table(table, emap, pmap)
        directional = replay_directional(temp, table)
        distance = replay_distance(temp, table)
    native = mode == "native_windows_ucrt_return"
    # A native return is necessary but not sufficient.  These two hostless
    # replays execute the Mac production arithmetic with the returned table;
    # they do not execute the Windows AEX owner with that same table.  In
    # particular, equality with the older host-substituted RAW hashes cannot
    # stand in for a native-table AEX replay when UCRT genuinely differs.
    actual_aex_table_replay = {
        "available": False,
        "directional_cells": 0,
        "distance_cells": 0,
        "required_for_promotion": True,
        "boundary": "same native result table must be injected into exported Windows AEX owners and compared against these Mac public outputs",
    }
    return {
        "schema": "olm.math-ucrt-downstream-replay/1",
        "status": "PASS_UCRT_DOWNSTREAM_REPLAY_NO_PRODUCTION_MUTATION",
        "mode": mode,
        "inputs": {
            "strict_return_analyzer_sha256": sha(ANALYZER),
            "directional_census_sha256": sha(DIRECTIONAL),
            "directional_vectors_sha256": sha(DB_VECTORS),
            "directional_powf_vectors_sha256": sha(DB_POWF_VECTORS),
            "distance_harness_sha256": sha(DG_HARNESS),
            "distance_vectors_sha256": sha(DG_VECTORS),
        },
        "validated_return": validated,
        "directional": directional,
        "distance": distance,
        "actual_aex_table_replay": actual_aex_table_replay,
        "decision": {
            "directional_six_candidate_for_promotion": False,
            "distance_power_eight_candidate_for_promotion": False,
            "distance_blocker": "actual-AEX native-table replay remains absent" if native
                                else "native Windows UCRT return remains absent",
            "production_changed": False,
            "after_effects_launched": False,
        },
    }


def validate_report(report: object) -> bool:
    if not isinstance(report, dict) or set(report) != {
        "schema", "status", "mode", "inputs", "validated_return", "directional", "distance",
        "actual_aex_table_replay", "decision"
    }:
        return False
    if report["schema"] != "olm.math-ucrt-downstream-replay/1" or report["status"] != "PASS_UCRT_DOWNSTREAM_REPLAY_NO_PRODUCTION_MUTATION":
        return False
    if report["mode"] != "host_substitute_plumbing_self_test" or report["validated_return"] is not None:
        return False
    expected_inputs = {
        "strict_return_analyzer_sha256": sha(ANALYZER), "directional_census_sha256": sha(DIRECTIONAL),
        "directional_vectors_sha256": sha(DB_VECTORS), "distance_harness_sha256": sha(DG_HARNESS),
        "directional_powf_vectors_sha256": sha(DB_POWF_VECTORS),
        "distance_vectors_sha256": sha(DG_VECTORS),
    }
    if report["inputs"] != expected_inputs:
        return False
    directional = report["directional"]
    if not isinstance(directional, dict) or set(directional) != {"cells", "matching_cells"} or directional["matching_cells"] != 6:
        return False
    census = load(DIRECTIONAL, "olm_dblur_ucrt_validate")
    if [(row.get("depth"), row.get("tuple_index")) for row in directional["cells"]] != list(census.CELLS):
        return False
    if any(set(row) != {"depth", "tuple_index", "raw_sha256", "exported_oracle_sha256", "matches_exported_oracle"}
           or row["raw_sha256"] != census.EXPECTED_SHAS[(row["depth"], row["tuple_index"])][1]
           or row["exported_oracle_sha256"] != row["raw_sha256"] or row["matches_exported_oracle"] is not True
           for row in directional["cells"]):
        return False
    distance = report["distance"]
    if not isinstance(distance, dict) or set(distance) != {"cells", "matching_host_substituted_cells"} or distance["matching_host_substituted_cells"] != 8:
        return False
    if [row.get("cell") for row in distance["cells"]] != list(DG_EXPECTED):
        return False
    if any(set(row) != {"cell", "raw_sha256", "host_substituted_oracle_sha256", "matches_host_substituted_oracle"}
           or row["raw_sha256"] != DG_EXPECTED[row["cell"]]
           or row["host_substituted_oracle_sha256"] != row["raw_sha256"]
           or row["matches_host_substituted_oracle"] is not True for row in distance["cells"]):
        return False
    if report["actual_aex_table_replay"] != {
        "available": False,
        "directional_cells": 0,
        "distance_cells": 0,
        "required_for_promotion": True,
        "boundary": "same native result table must be injected into exported Windows AEX owners and compared against these Mac public outputs",
    }:
        return False
    return report["decision"] == {
        "after_effects_launched": False, "directional_six_candidate_for_promotion": False,
        "distance_blocker": "native Windows UCRT return remains absent",
        "distance_power_eight_candidate_for_promotion": False, "production_changed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--return-path", type=Path)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=REPORT)
    args = parser.parse_args()
    if args.return_path is None and not args.run and not args.write:
        report = json.loads(args.output.read_text())
        if not validate_report(report):
            raise RuntimeError("persisted downstream replay readiness drift")
    else:
        report = replay(args.return_path)
        if args.return_path is None and not validate_report(report):
            raise RuntimeError("fresh downstream replay self-test drift")
    if args.write:
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(report["status"])
    print(f"directional={report['directional']['matching_cells']}/6 distance-host={report['distance']['matching_host_substituted_cells']}/8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
