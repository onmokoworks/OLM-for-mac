#!/usr/bin/env python3
"""Run the accepted native UCRT table through exported AEX and Mac direct owners."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
ANALYZER = ROOT / "scripts/analyze_olm_math_ucrt_batch_return_20260814.py"
DOWNSTREAM = ROOT / "tools/emulation/test_olm_math_ucrt_downstream_replay_20260814.py"
DB_PLUMBING = ROOT / "tools/emulation/test_olmdirectionalblur_same_table_dual_owner_plumbing_20260814.py"
DG_PLUMBING = ROOT / "tools/emulation/test_olmdistancegradation_same_table_dual_owner_plumbing_20260814.py"
DB_CENSUS = ROOT / "tools/emulation/test_olmdirectionalblur_exported_smart_remaining6_census_20260814.py"
DG_MATRIX = ROOT / "tools/emulation/test_olmdistancegradation_exported_typed_owner_matrix_20260811.py"
OUTPUT = ROOT / "refs/conformance/olm_math_ucrt_native_dual_owner_replay_20260814.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def directional_aex(worker: Path, table: Path, root: Path, census) -> list[dict[str, Any]]:
    crop = Image.open(census.SOURCE_PNG).convert("RGBA").crop((472, 262, 536, 298))
    source = root / "source.png"
    crop.save(source)
    formats = {8: "argb8", 16: "argb16", 32: "argb32f"}
    environment = dict(os.environ, OLM_NATIVE_UCRT_TABLE=str(table))
    rows = []
    for depth, index in census.CELLS:
        output = root / f"aex-pf{depth}-t{index}.png"
        run = subprocess.run([
            str(worker), "render-png", str(census.AEX), str(source), str(output),
            "--pixel-format", formats[depth], *census.params(index),
        ], cwd=ROOT, env=environment, text=True, capture_output=True)
        if run.returncode:
            raise RuntimeError(f"Directional AEX PF{depth}/t{index}: {run.stderr}")
        observed = json.loads(run.stdout)
        raw = output.with_suffix(".raw")
        expected_bytes = 64 * 36 * 4 * {8: 1, 16: 2, 32: 4}[depth]
        if raw.stat().st_size != expected_bytes or observed.get("raw_pixel_sha256") != sha256(raw):
            raise RuntimeError("Directional AEX RAW identity")
        if (observed.get("render_error"), observed.get("render_mode"), observed.get("guards_intact"),
            observed.get("input_requests"), observed.get("output_request")) != \
                (0, "smart-cpu", True, [[0, 0, 64, 36]], [0, 0, 64, 36]):
            raise RuntimeError("Directional AEX lifecycle")
        rows.append({"depth": depth, "tuple_index": index, "raw_bytes": expected_bytes,
                     "raw_sha256": sha256(raw), "render_mode": "smart-cpu",
                     "guards_intact": True})
    return rows


def directional_mac(table: Path, root: Path, downstream, census, db_plumbing) -> \
        tuple[list[dict[str, Any]], dict[str, int]]:
    rows, counters = db_plumbing.run_mac_table(
        table, root, downstream, census, require_host_oracle=False)
    return [{"depth": row["depth"], "tuple_index": row["tuple_index"],
             "raw_bytes": 64 * 36 * 4 * {8: 1, 16: 2, 32: 4}[row["depth"]],
             "raw_sha256": row["raw_sha256"]} for row in rows], counters


def distance_aex(worker: Path, table: Path, root: Path, matrix, dg_plumbing) -> list[dict[str, Any]]:
    source = root / "source.raw"
    source.write_bytes(matrix.promoted(matrix.rgba_fixture(), "PF32"))
    environment = dict(os.environ, OLM_NATIVE_UCRT_TABLE=str(table))
    rows = []
    for mode in range(2, 6):
        for background in (0, 1):
            key = f"mode{mode}.bg{background}"
            output = root / f"aex-{key}.raw"
            request = {"type": "render_frame", "v": 2, "frame_index": 0,
                       "current_time": {"value": 0, "scale": 30},
                       "parameters": dg_plumbing.parameters(mode, background)}
            run = subprocess.run([
                str(worker), "session", str(matrix.AEX), str(source), str(output),
                "17", "11", "30", "--pixel-format", "argb32f",
            ], cwd=ROOT, env=environment,
               input=dg_plumbing.framed(request) + dg_plumbing.framed({"type": "close", "v": 1}),
               capture_output=True)
            if run.returncode:
                raise RuntimeError(f"Distance AEX {key}: {run.stderr.decode(errors='replace')}")
            messages = []
            cursor = 0
            while cursor < len(run.stdout):
                length = struct.unpack_from("<I", run.stdout, cursor)[0]
                cursor += 4
                messages.append(json.loads(run.stdout[cursor:cursor + length]))
                cursor += length
            frame = next(message for message in messages if message.get("type") == "frame_done")
            if frame.get("status") != "ok" or frame.get("render_error") != 0 or \
                    frame.get("output", {}).get("guards_intact") is not True:
                raise RuntimeError(f"Distance AEX lifecycle {key}")
            rows.append({"cell": key, "blur_mode": mode, "use_background": bool(background),
                         "raw_bytes": output.stat().st_size, "raw_sha256": sha256(output),
                         "guards_intact": True})
    return rows


def distance_mac(table: Path, root: Path, downstream) -> list[dict[str, Any]]:
    executable = root / "distance-table"
    interposer = downstream.build_interposer(root)
    command = ["clang++", "-std=c++17", "-O0", "-fno-builtin-powf",
               "-I", str(ROOT / "tools/emulation/dg_renderbits_real_harness_20260716"),
               str(downstream.DG_HARNESS), str(downstream.DG_FIELD), str(interposer), "-o", str(executable)]
    build = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if build.returncode:
        raise RuntimeError(build.stderr)
    environment = dict(os.environ, OLM_UCRT_TABLE=str(table))
    run = subprocess.run([str(executable), str(root)], cwd=ROOT, env=environment,
                         text=True, capture_output=True)
    if run.returncode:
        raise RuntimeError(f"Distance Mac direct replay: {run.stderr}")
    return [{"cell": f"mode{mode}.bg{background}", "raw_bytes": 17 * 11 * 16,
             "raw_sha256": sha256(root / f"power.mode{mode}.bg{background}.raw")}
            for mode in range(2, 6) for background in (0, 1)]


def generate(return_path: Path) -> dict[str, Any]:
    downstream = load(DOWNSTREAM, "olm_native_dual_downstream")
    db_plumbing = load(DB_PLUMBING, "olm_native_dual_db_builder")
    dg_plumbing = load(DG_PLUMBING, "olm_native_dual_dg_builder")
    census = load(DB_CENSUS, "olm_native_dual_db_census")
    matrix = load(DG_MATRIX, "olm_native_dual_dg_matrix")
    expf, powf, validated = downstream.maps_from_return(return_path)
    # The 494 expf request rows collapse to 377 production keys after the
    # analyzer proves expf(-0)=+1 and normalizes only that signed-zero key.
    if len(expf) != 377 or len(powf) != 850:
        raise RuntimeError("native result table cardinality")
    with tempfile.TemporaryDirectory(prefix="olm-native-ucrt-dual-owner-") as raw:
        root = Path(raw)
        table = root / "native-ucrt-table.txt"
        downstream.write_table(table, expf, powf)
        table_sha = sha256(table)
        worker, build = db_plumbing.build_worker(root)
        db_aex_root = root / "db-aex"; db_aex_root.mkdir()
        db_mac_root = root / "db-mac"; db_mac_root.mkdir()
        dg_aex_root = root / "dg-aex"; dg_aex_root.mkdir()
        dg_mac_root = root / "dg-mac"; dg_mac_root.mkdir()
        db_aex = directional_aex(worker, table, db_aex_root, census)
        db_mac, db_mac_table_calls = directional_mac(table, db_mac_root, downstream, census, db_plumbing)
        dg_aex = distance_aex(worker, table, dg_aex_root, matrix, dg_plumbing)
        dg_mac = distance_mac(table, dg_mac_root, downstream)
    directional_rows = []
    for aex, mac in zip(db_aex, db_mac, strict=True):
        if (aex["depth"], aex["tuple_index"]) != (mac["depth"], mac["tuple_index"]):
            raise RuntimeError("Directional row order")
        directional_rows.append({
            "depth": aex["depth"], "tuple_index": aex["tuple_index"],
            "raw_bytes": aex["raw_bytes"], "render_mode": aex["render_mode"],
            "guards_intact": aex["guards_intact"], "aex_raw_sha256": aex["raw_sha256"],
            "mac_production_direct_raw_sha256": mac["raw_sha256"],
            "same_table_full_raw_exact": aex["raw_sha256"] == mac["raw_sha256"],
        })
    distance_rows = []
    for aex, mac in zip(dg_aex, dg_mac, strict=True):
        if aex["cell"] != mac["cell"]:
            raise RuntimeError("Distance row order")
        distance_rows.append({**aex, "aex_raw_sha256": aex["raw_sha256"],
                              "mac_renderbits_raw_sha256": mac["raw_sha256"],
                              "same_table_full_raw_exact": aex["raw_sha256"] == mac["raw_sha256"]})
        distance_rows[-1].pop("raw_sha256")
    directional_exact = sum(row["same_table_full_raw_exact"] for row in directional_rows)
    distance_exact = sum(row["same_table_full_raw_exact"] for row in distance_rows)
    if directional_exact != 6 or distance_exact != 8:
        raise RuntimeError(f"native same-table owner split Directional={directional_exact}/6 Distance={distance_exact}/8")
    return {
        "schema": "olm.math-ucrt-native-dual-owner-replay/1",
        "status": "PASS_NATIVE_TABLE_EXPORTED_AEX_MAC_DIRECT_FULL_RAW_14_OF_14",
        "inputs": {"return_analysis": validated, "return_analyzer_sha256": sha256(ANALYZER),
                   "downstream_tool_sha256": sha256(DOWNSTREAM),
                   "directional_plumbing_tool_sha256": sha256(DB_PLUMBING),
                   "distance_plumbing_tool_sha256": sha256(DG_PLUMBING)},
        "table": {"expf_unique_keys": len(expf), "powf_unique_keys": len(powf),
                  "total_unique_keys": len(expf) + len(powf), "sha256": table_sha,
                  "source": "validated_native_windows_ucrt_return"},
        "worker_build": build,
        "directional_mac_table_calls": db_mac_table_calls,
        "directional_rows": directional_rows,
        "directional_rows_sha256": digest(directional_rows),
        "distance_rows": distance_rows,
        "distance_rows_sha256": digest(distance_rows),
        "summary": {"directional_same_table_exact": 6, "distance_same_table_exact": 8,
                    "total_same_table_exact": 14},
        "decision": {"production_promoted": False, "installed_binary_changed": False,
                     "directional_public_effectmain_closure_still_required": True,
                     "distance_public_smart_closure_still_required": True,
                     "after_effects_launched": False, "network_changed": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("return_path", type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    value = generate(args.return_path)
    if args.write:
        if args.output.exists():
            raise RuntimeError("refusing to overwrite native dual-owner replay evidence")
        args.output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    print(value["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
