#!/usr/bin/env python3
"""Prove DistanceGradation exported-AEX/Mac same-table plumbing without native claims."""
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


ROOT = Path(__file__).resolve().parents[2]
DIRECTIONAL_PLUMBING = ROOT / "tools/emulation/test_olmdirectionalblur_same_table_dual_owner_plumbing_20260814.py"
DOWNSTREAM = ROOT / "tools/emulation/test_olm_math_ucrt_downstream_replay_20260814.py"
MATRIX = ROOT / "tools/emulation/test_olmdistancegradation_exported_typed_owner_matrix_20260811.py"
REQUEST = ROOT / "tools/emulation/test_olmdistancegradation_pf32_power_ucrt_request_20260813.py"
SOURCE = ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
REPORT = ROOT / "refs/conformance/olmdistancegradation_same_table_dual_owner_plumbing_20260814.json"
MARKDOWN = REPORT.with_suffix(".md")

EXPECTED_ROWS_SHA256 = "afb02055b0dd20eb8e64e237cf1777a77b76d726dfd1a27da9d63561736fe97e"
EXPECTED_BUILD: dict[str, Any] = {
    "clean_clone": True,
    "release_build": True,
    "worker_sha256": "c2f28fd0f28b73ebb57b68e7ffefc9e11c254f016aae5d0ed157f7ab3d3f6af7",
    "worker_bytes": 3887728,
    "patched_callbacks_sha256": "c6db8fea04e2db211943ff923bbfe8b22655859dcf07210e403516a80c4b9aca",
    "patched_imports_sha256": "27ad9a37a640c13dbed6e95a8eb7cca27406db8d48b3c89b9573075546f4d466",
    "patched_main_sha256": "5efc9609220a4cf5f077ef975e92a5815359d6323d2019f14c6bddc307df90b7",
}


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


def identities() -> dict[str, str]:
    return {
        "directional_plumbing_tool_sha256": sha256(DIRECTIONAL_PLUMBING),
        "downstream_tool_sha256": sha256(DOWNSTREAM),
        "exported_matrix_tool_sha256": sha256(MATRIX),
        "request_tool_sha256": sha256(REQUEST),
        "production_source_sha256": sha256(SOURCE),
    }


def framed(value: dict[str, Any]) -> bytes:
    payload = json.dumps(value).encode()
    return struct.pack("<I", len(payload)) + payload


def parameters(mode: int, background: int) -> str:
    return "v2|" + ";".join((
        "param_1@1:i32=1", "param_2@2:i32=1", "param_3@3:i32=4", "param_4@4:i32=4",
        "param_5@5:i32=1", f"param_6@6:i32={background}",
        "param_7@7:argb8=255,28,0,238", "param_8@8:argb8=255,16,160,48",
        "param_9@9:i32=4", "param_10@10:f64=2.25", f"param_11@11:i32={mode}",
        "param_12@12:i32=1",
    ))


def run_exported(worker: Path, table: Path, root: Path, matrix, expected: dict[str, str]) -> list[dict[str, Any]]:
    source = root / "source-pf32.raw"
    source.write_bytes(matrix.promoted(matrix.rgba_fixture(), "PF32"))
    environment = dict(os.environ, OLM_NATIVE_UCRT_TABLE=str(table))
    rows = []
    for mode in range(2, 6):
        for background in (0, 1):
            key = f"mode{mode}.bg{background}"
            output = root / f"aex-{key}.raw"
            request = {"type": "render_frame", "v": 2, "frame_index": 0,
                       "current_time": {"value": 0, "scale": 30},
                       "parameters": parameters(mode, background)}
            run = subprocess.run([
                str(worker), "session", str(matrix.AEX), str(source), str(output),
                "17", "11", "30", "--pixel-format", "argb32f",
            ], cwd=ROOT, env=environment, input=framed(request) + framed({"type": "close", "v": 1}),
               capture_output=True)
            if run.returncode:
                raise RuntimeError(f"AEX {key}: {run.stderr.decode(errors='replace')}")
            messages = []
            cursor = 0
            while cursor < len(run.stdout):
                length = struct.unpack_from("<I", run.stdout, cursor)[0]
                cursor += 4
                messages.append(json.loads(run.stdout[cursor:cursor + length]))
                cursor += length
            frame = next(message for message in messages if message.get("type") == "frame_done")
            got = sha256(output)
            if got != expected[key] or frame.get("status") != "ok" or frame.get("render_error") != 0:
                raise RuntimeError(f"AEX output drift {key}: {got}")
            rows.append({"cell": key, "blur_mode": mode, "use_background": bool(background),
                         "raw_bytes": output.stat().st_size, "raw_sha256": got,
                         "render_error": 0, "render_mode": frame.get("render_mode"),
                         "guards_intact": frame.get("output", {}).get("guards_intact")})
    return rows


def generate(*, run_build: bool) -> dict[str, Any]:
    if not run_build:
        raise RuntimeError("fresh proof requires --run-build")
    plumbing = load(DIRECTIONAL_PLUMBING, "olm_dg_same_table_builder")
    downstream = load(DOWNSTREAM, "olm_dg_same_table_downstream")
    matrix = load(MATRIX, "olm_dg_same_table_matrix")
    request = load(REQUEST, "olm_dg_same_table_request")
    expected = request.EXPECTED_CELL_SHA256
    with tempfile.TemporaryDirectory(prefix="olm-dg-same-table-") as raw:
        root = Path(raw)
        table, table_identity = plumbing.make_table(root, downstream)
        worker, build = plumbing.build_worker(root)
        aex_rows = run_exported(worker, table, root, matrix, expected)
        mac_root = root / "mac"
        mac_root.mkdir()
        mac_result = downstream.replay_distance(mac_root, table)
    if mac_result.get("matching_host_substituted_cells") != 8:
        raise RuntimeError("Mac Distance same-table replay mismatch")
    rows = []
    for aex, mac in zip(aex_rows, mac_result["cells"], strict=True):
        if aex["cell"] != mac["cell"] or aex["raw_sha256"] != mac["raw_sha256"]:
            raise RuntimeError("Distance same-table owner split")
        rows.append({"cell": aex["cell"], "blur_mode": aex["blur_mode"],
                     "use_background": aex["use_background"], "raw_bytes": aex["raw_bytes"],
                     "raw_sha256": aex["raw_sha256"], "aex_exported": aex,
                     "mac_renderbits": mac, "same_table_full_raw_exact": True})
    return {
        "schema": "olmdistancegradation.same-table-dual-owner-plumbing/1",
        "status": "PASS_HOST_SUBSTITUTE_SAME_TABLE_EXPORTED_AEX_MAC_RENDERBITS_8_OF_8",
        "identities": identities(), "build": build, "table": table_identity,
        "rows": rows, "rows_sha256": digest(rows),
        "summary": {"cells": 8, "same_table_full_raw_exact": 8, "aex_exported_cells": 8,
                    "mac_renderbits_cells": 8},
        "scope": {"plumbing_control_only": True, "host_substitute_only": True,
                  "mac_public_admission": False, "native_windows_ucrt_return_received": False,
                  "native_windows_result_claimed": False, "production_promoted": False,
                  "installed_binary_changed": False, "after_effects_launched": False,
                  "network_changed": False},
    }


def validate(value: Any, *, live: bool = True) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "schema", "status", "identities", "build", "table", "rows", "rows_sha256", "summary", "scope"
    }:
        return False
    if value["schema"] != "olmdistancegradation.same-table-dual-owner-plumbing/1" or value["status"] != \
            "PASS_HOST_SUBSTITUTE_SAME_TABLE_EXPORTED_AEX_MAC_RENDERBITS_8_OF_8":
        return False
    if live:
        try:
            if value["identities"] != identities():
                return False
        except (OSError, RuntimeError, ValueError):
            return False
    if value["build"] != EXPECTED_BUILD or value["table"] != {
        "kind": "macos_libsystem_host_substitute_plumbing_control", "expf_unique_keys": 378,
        "powf_unique_keys": 850, "total_unique_keys": 1228,
        "sha256": "94924f457072cb7a27c8f899b3c9b21d8301b381de68a48032c06344928a83bb",
        "native_windows_ucrt": False,
    }:
        return False
    rows = value["rows"]
    request = load(REQUEST, "olm_dg_same_table_validate_request")
    expected = request.EXPECTED_CELL_SHA256
    expected_cells = [f"mode{mode}.bg{background}" for mode in range(2, 6) for background in (0, 1)]
    if not isinstance(rows, list) or [row.get("cell") for row in rows] != expected_cells or \
            value["rows_sha256"] != digest(rows) or value["rows_sha256"] != EXPECTED_ROWS_SHA256:
        return False
    for row in rows:
        if set(row) != {"cell", "blur_mode", "use_background", "raw_bytes", "raw_sha256",
                       "aex_exported", "mac_renderbits", "same_table_full_raw_exact"}:
            return False
        key = row["cell"]
        if row["raw_sha256"] != expected[key] or row["raw_bytes"] != 17 * 11 * 16 or \
                row["same_table_full_raw_exact"] is not True:
            return False
        aex, mac = row["aex_exported"], row["mac_renderbits"]
        if aex != {"cell": key, "blur_mode": row["blur_mode"],
                   "use_background": row["use_background"], "raw_bytes": 17 * 11 * 16,
                   "raw_sha256": expected[key], "render_error": 0, "render_mode": None,
                   "guards_intact": True}:
            return False
        if mac != {"cell": key, "raw_sha256": expected[key],
                   "host_substituted_oracle_sha256": expected[key],
                   "matches_host_substituted_oracle": True}:
            return False
    return value["summary"] == {"cells": 8, "same_table_full_raw_exact": 8,
                                 "aex_exported_cells": 8, "mac_renderbits_cells": 8} and value["scope"] == {
        "plumbing_control_only": True, "host_substitute_only": True, "mac_public_admission": False,
        "native_windows_ucrt_return_received": False, "native_windows_result_claimed": False,
        "production_promoted": False, "installed_binary_changed": False,
        "after_effects_launched": False, "network_changed": False,
    }


def markdown(value: dict[str, Any]) -> str:
    return (
        "# DistanceGradation same-table dual-owner plumbing control\n\n"
        f"Status: `{value['status']}`.\n\n"
        "A clean temporary AEXCompat release build injected one exact keyed host-substitute table into "
        "the eight exported Windows-AEX Smart PF32 Power cells. The same table drove the matching Mac "
        "RenderBits diagnostic replay, and all eight full RAW buffers matched. This proves only table "
        "lookup/injection and owner plumbing. It is not native Windows UCRT evidence; the Mac public "
        "Power route remains fail-closed, production was not promoted, and After Effects/network state "
        "were untouched. The accepted native 1,344-row return must replace this table and repeat the proof.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-build", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        value = generate(run_build=args.run_build)
        REPORT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        MARKDOWN.write_text(markdown(value))
    else:
        value = json.loads(REPORT.read_text())
    if not validate(value) or MARKDOWN.read_text() != markdown(value):
        raise RuntimeError("Distance same-table dual-owner plumbing evidence invalid")
    print(value["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
