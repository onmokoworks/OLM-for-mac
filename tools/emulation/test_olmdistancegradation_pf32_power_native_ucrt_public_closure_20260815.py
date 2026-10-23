#!/usr/bin/env python3
"""Close the fixed DistanceGradation PF32 Power public matrix with native UCRT."""
from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
FIELD = ROOT / "core/olmdistancegradation_fieldgen.cpp"
DIRECT = ROOT / "tools/emulation/dg_exported_typed_owner_compare_harness_20260811.cpp"
PUBLIC = ROOT / "tools/emulation/dg_public_smart_owner_contract_harness_20260812.cpp"
DUAL = ROOT / "tools/emulation/run_olm_math_ucrt_native_dual_owner_replay_20260814.py"
COMBINED = ROOT / "refs/conformance/olm_math_ucrt_batch_native_return_20260814.json"
XMM = ROOT / "refs/conformance/olmdistancegradation_actual_aex_powf_xmm_closure_20260814.json"
VECTORS = ROOT / "refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_pf32_power_ucrt_powf_20260813/powf_vectors.json"
REQUEST = ROOT / "refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_pf32_power_ucrt_powf_20260813/request_manifest.json"
REPORT = ROOT / "refs/conformance/olmdistancegradation_pf32_power_native_ucrt_public_closure_20260815.json"
DOC = REPORT.with_suffix(".md")

RETURN_SHA256 = "c50c7db94dfd0417dce6b681cd45209cba9259ff8b25737f28e3f239539a5bf1"
COMBINED_SHA256 = "87b6d72cac35baa860b0212a172c26b331b1f662e5188f8135244e23fc13b6ef"
XMM_SHA256 = "741dce6e7a1dd852d237072502341b40721b7cc7a9000c279f6234c10f07108a"
PUBLIC_MARKER = (
    "PASS_OLMDISTANCEGRADATION_PUBLIC_SMART_OWNER_CONTRACT positive=17 "
    "mode5_positive=8 power_positive=8 power_negative=7 negative=21 classic_guards=4"
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value: object) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def fixture() -> bytes:
    output = bytearray()
    for y in range(11):
        for x in range(17):
            transparent = 4 <= x < 13 and 2 <= y < 9
            rgba = (0, 0, 0, 0) if transparent else (
                (x * 613 + y * 1231) % 256,
                (x * 997 + y * 211) % 256,
                (x * 1499 + y * 307) % 256,
                255,
            )
            red, green, blue, alpha = rgba
            for value in (alpha, red, green, blue):
                output += struct.pack("<f", value / 255.0)
    return bytes(output)


def load_native(return_path: Path) -> tuple[dict, dict[tuple[str, str], dict], list[dict]]:
    require(return_path.is_file() and sha(return_path) == RETURN_SHA256, "return ZIP identity")
    frozen = json.loads(COMBINED.read_text())
    require(sha(COMBINED) == COMBINED_SHA256, "frozen combined analysis identity")
    require(frozen["status"] == "PASS_NATIVE_WINDOWS_UCRT_BATCH_RETURN_VALIDATED_NO_PROMOTION", "combined status")
    require(frozen["return_sha256"] == RETURN_SHA256, "combined return binding")
    require(frozen["distance_actual_aex_xmm_closure_sha256"] == XMM_SHA256, "combined XMM binding")
    with zipfile.ZipFile(return_path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), "duplicate return members")
        summary = json.loads(archive.read("distance\\run_summary.json"))
        require(archive.read("distance\\powf_vectors.json") == VECTORS.read_bytes(), "returned vectors drift")
        require(archive.read("distance\\request_manifest.json") == REQUEST.read_bytes(), "returned request drift")
    require(summary["status"] == "answered_native_windows_ucrt_powf", "distance return status")
    require(summary["process_bitness"] == 64 and summary["processor_architecture"] == "AMD64", "return architecture")
    require(summary["ucrtbase"] == frozen["ucrtbase"], "UCRT identity split")
    expected = json.loads(VECTORS.read_text())
    native = {(row["input_bits"], row["exponent_bits"]): row for row in summary["rows"]}
    require(len(expected) == len(native) == 63, "native vector cardinality")
    differences = []
    for row in expected:
        key = (row["input_bits"], row["exponent_bits"])
        require(key in native and native[key]["occurrences"] == row["occurrences"], "native key mapping")
        if row["host_result_bits"] != native[key]["native_ucrt_result_bits"]:
            differences.append({
                "input_bits": row["input_bits"],
                "exponent_bits": row["exponent_bits"],
                "macos_libsystem_bits": row["host_result_bits"],
                "native_ucrt_bits": native[key]["native_ucrt_result_bits"],
                "production_occurrences": row["occurrences"],
            })
    require(differences == [{
        "input_bits": "0x3f4d07a5", "exponent_bits": "0x40100000",
        "macos_libsystem_bits": "0x3f1b5785", "native_ucrt_bits": "0x3f1b5786",
        "production_occurrences": 8,
    }], "native/libSystem delta")
    return frozen, native, differences


def xmm_mapping(native: dict[tuple[str, str], dict]) -> tuple[list[dict], dict]:
    require(sha(XMM) == XMM_SHA256, "XMM closure identity")
    xmm = json.loads(XMM.read_text())
    require(xmm["status"].startswith("PASS_ACTUAL_AEX_POWER8_XMM_INPUTS"), "XMM status")
    rows = []
    for cell in xmm["cells"]:
        mapped = []
        native_changed = 0
        for call in cell["actual_trace"]:
            key = (call["input_bits"], call["exponent_bits"])
            require(key in native, "actual-AEX XMM key absent from native table")
            result = native[key]["native_ucrt_result_bits"]
            native_changed += result != call["host_substituted_result_bits"]
            mapped.append((call["input_bits"], call["exponent_bits"], result))
        require(len(mapped) == cell["actual_aex_calls"] == 124, "actual call count")
        rows.append({
            "cell": f"mode{cell['blur_mode']}.bg{int(cell['use_background'])}",
            "actual_aex_calls": len(mapped),
            "unique_pairs": len({(a, b) for a, b, _ in mapped}),
            "native_changed_calls": native_changed,
            "native_mapped_sequence_sha256": digest(mapped),
        })
    require(len(rows) == 8 and sum(row["actual_aex_calls"] for row in rows) == 992, "XMM total")
    require([row["native_changed_calls"] for row in rows] == [4, 4, 0, 0, 0, 0, 0, 0],
            "native delta call distribution")
    return rows, xmm["summary"]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_native_exported(return_path: Path, root: Path) -> dict:
    dual = load_module(DUAL, "dg_native_exported_replay")
    downstream = dual.load(dual.DOWNSTREAM, "dg_native_exported_downstream")
    worker_builder = dual.load(dual.DB_PLUMBING, "dg_native_exported_worker")
    plumbing = dual.load(dual.DG_PLUMBING, "dg_native_exported_plumbing")
    matrix = dual.load(dual.DG_MATRIX, "dg_native_exported_matrix")
    expf, powf, validated = downstream.maps_from_return(return_path)
    require(len(expf) == 377 and len(powf) == 850, "native table cardinality")
    table = root / "native-ucrt-table.txt"
    downstream.write_table(table, expf, powf)
    worker, build = worker_builder.build_worker(root)
    aex_root = root / "aex"
    aex_root.mkdir()
    rows = dual.distance_aex(worker, table, aex_root, matrix, plumbing)
    require(len(rows) == 8 and all(row["guards_intact"] for row in rows), "native exported rows")
    return {"rows": rows, "worker_build": build, "return_analysis": validated,
            "native_table_sha256": sha(table)}


def run_current(expected: dict[str, str], root: Path) -> tuple[list[dict], dict]:
    direct = root / "direct"
    public = root / "public"
    include = ROOT / "tools/emulation/dg_renderbits_real_harness_20260716"
    for source, output in ((DIRECT, direct), (PUBLIC, public)):
        build = subprocess.run([
            _UCRT_CXX, "-std=c++17", "-O0", "-I", str(include), str(source), str(FIELD), "-o", str(output),
        ], cwd=ROOT, text=True, capture_output=True)
        require(build.returncode == 0, f"build {source.name}: {build.stderr}")
    source = root / "source.raw"
    source.write_bytes(fixture())
    rows = []
    for mode in range(2, 6):
        for background in (0, 1):
            cell = f"mode{mode}.bg{background}"
            output = root / f"{cell}.raw"
            run = subprocess.run([
                str(direct), "PF32", str(source), str(output), "power", str(background), str(mode),
            ], cwd=ROOT, text=True, capture_output=True)
            require(run.returncode == 0, f"current direct {cell}: {run.stderr}")
            got = sha(output)
            require(got == expected[cell] and output.stat().st_size == 2992, f"current RAW {cell}")
            rows.append({"cell": cell, "blur_mode": mode, "use_background": bool(background),
                         "raw_bytes": 2992, "native_exported_aex_sha256": expected[cell],
                         "current_production_raw_sha256": got, "full_raw_exact": True})
    run = subprocess.run([str(public)], cwd=ROOT, text=True, capture_output=True)
    require(run.returncode == 0 and PUBLIC_MARKER in run.stdout, f"public closure: {run.stderr}")
    return rows, {
        "selector": "PF_Cmd_SMART_RENDER",
        "marker": PUBLIC_MARKER,
        "positive_cells": 17,
        "pf32_power_positive_cells": 8,
        "pf32_power_negative_cells": 7,
        "negative_cells": 21,
        "classic_guards": 4,
        "input_immutable": True,
        "padding_preserved": True,
        "public_equals_direct": True,
        "balanced_layer_and_parameter_lifecycle": True,
    }


def generate(return_path: Path) -> dict:
    frozen, native, differences = load_native(return_path)
    mappings, xmm_summary = xmm_mapping(native)
    with tempfile.TemporaryDirectory(prefix="dg-pf32-power-native-") as raw:
        root = Path(raw)
        exported = run_native_exported(return_path, root)
        expected = {row["cell"]: row["raw_sha256"] for row in exported["rows"]}
        rows, public = run_current(expected, root)
    return {
        "schema": "olmdistancegradation.pf32-power-native-ucrt-public-closure/1",
        "status": "PASS_NATIVE_UCRT_ACTUAL_XMM_EXPORTED_AEX_MAC_PUBLIC_RAW_EXACT_8_OF_8",
        "identities": {
            "production_source_sha256": sha(SOURCE),
            "fieldgen_sha256": sha(FIELD),
            "direct_harness_sha256": sha(DIRECT),
            "public_harness_sha256": sha(PUBLIC),
            "dual_replay_tool_sha256": sha(DUAL),
            "combined_return_analysis_sha256": sha(COMBINED),
            "actual_aex_xmm_closure_sha256": sha(XMM),
            "return_zip_sha256": sha(return_path),
        },
        "native_return": {
            "ucrtbase": frozen["ucrtbase"], "vectors": 63,
            "native_equals_libsystem": 62, "native_differs_libsystem": 1,
            "differences": differences,
        },
        "actual_aex_xmm": {"summary": xmm_summary, "cells": mappings},
        "rows": rows,
        "rows_sha256": digest(rows),
        "public_contract": public,
        "summary": {"pf32_power_cells": 8, "same_source_full_raw_exact": 8,
                    "actual_aex_calls_native_mapped": 992, "production_powf_calls": 1496},
        "bounded_admission": {
            "width": 17, "height": 11, "depth": "PF32", "owner": "SmartRender CPU",
            "blur_modes": [2, 3, 4, 5], "use_background": [False, True],
            "interpolation": "Power", "power": 2.25, "blur_size": 1,
            "canonical_pf32_source_bytes_required": True,
            "native_override": {"input_bits": "0x3f4d07a5", "result_bits": "0x3f1b5786"},
        },
        "decision": {"production_promoted": True, "installed_binary_changed": False,
                     "after_effects_launched": False, "unlisted_ranges_fail_closed": True},
        "claims_not_made": ["No arbitrary Power/geometry/source admission", "No installed or native AE claim"],
    }


def validate(value: object, live: bool = True) -> bool:
    if not isinstance(value, dict) or value.get("schema") != \
            "olmdistancegradation.pf32-power-native-ucrt-public-closure/1" or value.get("status") != \
            "PASS_NATIVE_UCRT_ACTUAL_XMM_EXPORTED_AEX_MAC_PUBLIC_RAW_EXACT_8_OF_8":
        return False
    try:
        if value["summary"] != {"pf32_power_cells": 8, "same_source_full_raw_exact": 8,
                               "actual_aex_calls_native_mapped": 992, "production_powf_calls": 1496}:
            return False
        if len(value["rows"]) != 8 or value["rows_sha256"] != digest(value["rows"]):
            return False
        if not all(row["full_raw_exact"] and row["raw_bytes"] == 2992 and
                   row["native_exported_aex_sha256"] == row["current_production_raw_sha256"]
                   for row in value["rows"]):
            return False
        if value["native_return"]["native_differs_libsystem"] != 1 or \
                value["native_return"]["native_equals_libsystem"] != 62 or \
                value["native_return"]["vectors"] != 63 or \
                value["native_return"]["ucrtbase"]["sha256"] != \
                "5e7709a6b71bb818260b6f05c5bb3b6ca0c3ca9bc2f58c6242c1cd9d826d0079":
            return False
        xmm = value["actual_aex_xmm"]
        if len(xmm["cells"]) != 8 or sum(row["actual_aex_calls"] for row in xmm["cells"]) != 992 or \
                [row["native_changed_calls"] for row in xmm["cells"]] != [4, 4, 0, 0, 0, 0, 0, 0]:
            return False
        public = value["public_contract"]
        if public["pf32_power_positive_cells"] != 8 or public["pf32_power_negative_cells"] != 7 or \
                public["marker"] != PUBLIC_MARKER or public["input_immutable"] is not True or \
                public["padding_preserved"] is not True or public["public_equals_direct"] is not True:
            return False
        if value["bounded_admission"] != {
            "width": 17, "height": 11, "depth": "PF32", "owner": "SmartRender CPU",
            "blur_modes": [2, 3, 4, 5], "use_background": [False, True],
            "interpolation": "Power", "power": 2.25, "blur_size": 1,
            "canonical_pf32_source_bytes_required": True,
            "native_override": {"input_bits": "0x3f4d07a5", "result_bits": "0x3f1b5786"},
        }:
            return False
        if value["decision"] != {"production_promoted": True, "installed_binary_changed": False,
                                 "after_effects_launched": False, "unlisted_ranges_fail_closed": True} or \
                value["claims_not_made"] != ["No arbitrary Power/geometry/source admission",
                                              "No installed or native AE claim"]:
            return False
        if live and value["identities"] != {
            "production_source_sha256": sha(SOURCE), "fieldgen_sha256": sha(FIELD),
            "direct_harness_sha256": sha(DIRECT), "public_harness_sha256": sha(PUBLIC),
            "dual_replay_tool_sha256": sha(DUAL), "combined_return_analysis_sha256": sha(COMBINED),
            "actual_aex_xmm_closure_sha256": sha(XMM), "return_zip_sha256": RETURN_SHA256,
        }:
            return False
    except (KeyError, TypeError, OSError):
        return False
    return True


def markdown(value: dict) -> str:
    return (
        "# OLMDistanceGradation PF32 Power native-UCRT public closure\n\n"
        f"Status: **{value['status']}**.\n\n"
        "The validated 64-bit Windows UCRT return differs from macOS/libSystem at one of 63 "
        "exact `powf` pairs. All 992 actual-AEX XMM calls map to that native table. Replaying the "
        "same table through the exported Windows AEX and current Mac body, then through the public "
        "SmartRender contract, closes all eight fixed 17x11 PF32 Power cells at full 2,992-byte RAW "
        "identity. Input immutability, row padding and callback cleanup remain closed. Admission is "
        "limited to the named tuple/source mask; no install or After Effects launch occurred.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("return_path", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        value = generate(args.return_path)
        REPORT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        DOC.write_text(markdown(value))
    else:
        value = json.loads(REPORT.read_text())
    require(validate(value), "persisted closure validation")
    require(DOC.read_text() == markdown(value), "closure markdown drift")
    print(value["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
