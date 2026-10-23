#!/usr/bin/env python3
"""Prove DirectionalBlur exported-AEX/Mac same-table plumbing without native claims."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
AEX_REPO = Path("/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue851-smart-primary-checkout")
AEX = resolve_asset(ROOT / "plugins_2025/OLMDirectionalBlur.aex")
SOURCE_PNG = resolve_asset(ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png")
PRODUCTION = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
CENSUS = ROOT / "tools/emulation/test_olmdirectionalblur_exported_smart_remaining6_census_20260814.py"
DOWNSTREAM = ROOT / "tools/emulation/test_olm_math_ucrt_downstream_replay_20260814.py"
CEIL_PATCH = ROOT / "tools/emulation/aexcompat_olmdirectionalblur_double_ceil_import_20260814.patch"
RAW_PATCH = ROOT / "tools/emulation/aexcompat_raw_output_dump_20260814.patch"
TABLE_PATCH = ROOT / "tools/emulation/aexcompat_native_ucrt_table_replay_20260814.patch"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_same_table_dual_owner_plumbing_20260814.json"
MARKDOWN = REPORT.with_suffix(".md")

EXPECTED_HEAD = "28d535469f84f67236ef3425afe4291ea2fb0991"
EXPECTED_TABLE_SHA256 = "94924f457072cb7a27c8f899b3c9b21d8301b381de68a48032c06344928a83bb"
EXPECTED_ROWS_SHA256 = "84dc592b2471025842cb707edc6a5dde61689c7a2736c66180a648571f7ff3be"
EXPECTED_BUILD = {
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


def command(args: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True)


def static_identities() -> dict[str, Any]:
    head = command(["git", "rev-parse", "HEAD"], cwd=AEX_REPO)
    if head.returncode or head.stdout.strip() != EXPECTED_HEAD:
        raise RuntimeError("AEXCompat identity drift")
    return {
        "aexcompat_head": EXPECTED_HEAD,
        "aex_sha256": sha256(AEX),
        "source_png_sha256": sha256(SOURCE_PNG),
        "production_source_sha256": sha256(PRODUCTION),
        "census_tool_sha256": sha256(CENSUS),
        "downstream_tool_sha256": sha256(DOWNSTREAM),
        "ceil_patch_sha256": sha256(CEIL_PATCH),
        "raw_patch_sha256": sha256(RAW_PATCH),
        "table_patch_sha256": sha256(TABLE_PATCH),
    }


def build_worker(root: Path) -> tuple[Path, dict[str, Any]]:
    clone = root / "aexcompat"
    run = command(["git", "clone", "--quiet", "--no-hardlinks", str(AEX_REPO), str(clone)], cwd=root)
    if run.returncode:
        raise RuntimeError("AEXCompat clone failed: " + run.stderr)
    for patch in (CEIL_PATCH, RAW_PATCH, TABLE_PATCH):
        run = command(["git", "apply", str(patch)], cwd=clone)
        if run.returncode:
            raise RuntimeError(f"patch apply failed {patch.name}: {run.stderr}")
    run = command(["cargo", "build", "--release", "-p", "aex-guest-worker",
                   "--manifest-path", str(clone / "guest/Cargo.toml")], cwd=clone)
    if run.returncode:
        raise RuntimeError("worker build failed: " + run.stdout + run.stderr)
    worker = clone / "guest/target/release/aex-guest-worker"
    if not worker.is_file():
        raise RuntimeError("worker binary absent")
    return worker, {
        "clean_clone": True,
        "release_build": True,
        "worker_sha256": sha256(worker),
        "worker_bytes": worker.stat().st_size,
        "patched_callbacks_sha256": sha256(clone / "guest/crates/aex-guest-worker/src/x64/callbacks.rs"),
        "patched_imports_sha256": sha256(clone / "guest/crates/aex-guest-worker/src/x64/imports.rs"),
        "patched_main_sha256": sha256(clone / "guest/crates/aex-guest-worker/src/main.rs"),
    }


def make_table(root: Path, downstream) -> tuple[Path, dict[str, Any]]:
    expf, powf = downstream.maps_from_host()
    if len(expf) != 378 or len(powf) != 850:
        raise RuntimeError(f"host table cardinality drift: {len(expf)}/{len(powf)}")
    table = root / "host-substitute-table.txt"
    downstream.write_table(table, expf, powf)
    identity = {
        "kind": "macos_libsystem_host_substitute_plumbing_control",
        "expf_unique_keys": len(expf),
        "powf_unique_keys": len(powf),
        "total_unique_keys": len(expf) + len(powf),
        "sha256": sha256(table),
        "native_windows_ucrt": False,
    }
    return table, identity


def run_exported(worker: Path, table: Path, root: Path, census) -> list[dict[str, Any]]:
    crop = Image.open(SOURCE_PNG).convert("RGBA").crop((472, 262, 536, 298))
    input_png = root / "directional-input.png"
    crop.save(input_png)
    formats = {8: "argb8", 16: "argb16", 32: "argb32f"}
    environment = dict(os.environ, OLM_NATIVE_UCRT_TABLE=str(table))
    rows = []
    for depth, index in census.CELLS:
        output = root / f"aex-pf{depth}-t{index}.png"
        run = command([str(worker), "render-png", str(AEX), str(input_png), str(output),
                       "--pixel-format", formats[depth], *census.params(index)], cwd=ROOT, env=environment)
        if run.returncode:
            raise RuntimeError(f"AEX PF{depth}/t{index}: {run.stderr}")
        observed = json.loads(run.stdout)
        raw = output.with_suffix(".raw")
        expected = census.EXPECTED_SHAS[(depth, index)][1]
        got = sha256(raw)
        if got != expected or observed.get("raw_pixel_sha256") != got:
            raise RuntimeError(f"AEX RAW mismatch PF{depth}/t{index}: {got}")
        rows.append({
            "depth": depth,
            "tuple_index": index,
            "raw_bytes": raw.stat().st_size,
            "raw_sha256": got,
            "expected_exported_sha256": expected,
            "render_error": observed.get("render_error"),
            "render_mode": observed.get("render_mode"),
            "guards_intact": observed.get("guards_intact"),
            "input_requests": observed.get("input_requests"),
            "output_request": observed.get("output_request"),
        })
    return rows


def run_mac_table(table: Path, root: Path, downstream, census,
                  *, require_host_oracle: bool) -> tuple[list[dict[str, Any]], dict[str, int]]:
    interposer_text = downstream.INTERPOSER
    marker = 'extern "C" float expf(float a) noexcept {'
    replacement = ('static unsigned long olm_expf_calls=0,olm_powf_calls=0,olm_pow_calls=0;\n' +
                   marker + '++olm_expf_calls;')
    if interposer_text.count(marker) != 1:
        raise RuntimeError("expf interposer marker drift")
    interposer_text = interposer_text.replace(marker, replacement, 1)
    marker = 'extern "C" float powf(float a,float b) noexcept {'
    replacement = marker + '++olm_powf_calls;'
    if interposer_text.count(marker) != 1:
        raise RuntimeError("powf interposer marker drift")
    interposer_text = interposer_text.replace(marker, replacement, 1)
    interposer_text += r'''
extern "C" double pow(double a,double b) noexcept {++olm_pow_calls;auto x=word((float)a),y=word((float)b);
 for(int i=0;i<np;i++)if(ps[i].a==x&&ps[i].b==y)return (double)real(ps[i].r);std::_Exit(88);}
__attribute__((destructor)) static void counters(){const char*p=std::getenv("OLM_UCRT_COUNTERS");if(!p)return;
 FILE*f=std::fopen(p,"w");if(!f)return;std::fprintf(f,"expf=%lu\npowf=%lu\npow=%lu\n",olm_expf_calls,olm_powf_calls,olm_pow_calls);std::fclose(f);}
'''
    interposer = root / "ucrt_table.cpp"
    interposer.write_text(interposer_text)
    census.build_direct_probe(root)
    cpp = root / "olmdirectionalblur_mac_smartrender_adapter_probe.cpp"
    executable = root / "directional-full-table"
    sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
    command_line = ["clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math",
                    "-ffp-contract=off", "-fno-builtin-expf", "-fno-builtin-powf", "-fno-builtin-pow",
                    "-isysroot", sdk, "-I", str(resolve_asset(ROOT / "Headers")), "-I", str(resolve_asset(ROOT / "Headers/SP")),
                    "-I", str(resolve_asset(ROOT / "Util")), "-I", str(resolve_asset(ROOT / "Resources")), str(cpp), str(interposer),
                    str(ROOT / "core/dblur_frontonly.cpp"), str(ROOT / "core/dblur_rotate.cpp"),
                    str(ROOT / "core/dblur_rowdriver.cpp"), str(ROOT / "core/dblur_field.cpp"),
                    "-framework", "Cocoa", "-o", str(executable)]
    built = command(command_line, cwd=ROOT)
    if built.returncode:
        raise RuntimeError(built.stderr)
    crop = Image.open(census.SOURCE_PNG).convert("RGBA").crop((472, 262, 536, 298))
    rgba = root / "input.rgba"
    rgba.write_bytes(bytes(v for pixel in crop.get_flattened_data() for v in pixel))
    counter_path = root / "table-counters.txt"
    environment = dict(os.environ, OLM_UCRT_TABLE=str(table), OLM_UCRT_STRICT_EXPF="1",
                       OLM_UCRT_COUNTERS=str(counter_path))
    run = command([str(executable), str(rgba), str(root)], cwd=ROOT, env=environment)
    if run.returncode:
        raise RuntimeError(f"Directional Mac table replay: {run.stderr}")
    counters = {}
    for line in counter_path.read_text().splitlines():
        key, value = line.split("=", 1)
        counters[key] = int(value)
    if counters != {"expf": 996, "powf": 0, "pow": 47514}:
        raise RuntimeError(f"Directional Mac table call census drift: {counters}")
    rows = []
    for depth, index in census.CELLS:
        path = root / f"mac-pf{depth}-t{index}.raw"
        actual = sha256(path)
        expected = census.EXPECTED_SHAS[(depth, index)][1]
        if require_host_oracle and actual != expected:
            raise RuntimeError(f"Mac host table oracle mismatch PF{depth}/t{index}")
        rows.append({"depth": depth, "tuple_index": index, "raw_sha256": actual,
                     "exported_oracle_sha256": expected,
                     "matches_exported_oracle": actual == expected})
    return rows, counters


def run_mac(table: Path, root: Path, downstream) -> tuple[list[dict[str, Any]], dict[str, int]]:
    census = load(CENSUS, "olm_directional_same_table_mac")
    return run_mac_table(table, root, downstream, census, require_host_oracle=True)


def generate(*, run_build: bool) -> dict[str, Any]:
    if not run_build:
        raise RuntimeError("fresh proof requires --run-build")
    census = load(CENSUS, "olm_directional_same_table_census")
    downstream = load(DOWNSTREAM, "olm_directional_same_table_downstream")
    with tempfile.TemporaryDirectory(prefix="olm-dblur-same-table-") as raw:
        root = Path(raw)
        table, table_identity = make_table(root, downstream)
        worker, build = build_worker(root)
        aex_rows = run_exported(worker, table, root, census)
        mac_root = root / "mac"
        mac_root.mkdir()
        mac_rows, mac_table_calls = run_mac(table, mac_root, downstream)
    rows = []
    for aex, mac in zip(aex_rows, mac_rows, strict=True):
        if (aex["depth"], aex["tuple_index"]) != (mac["depth"], mac["tuple_index"]):
            raise RuntimeError("owner row order drift")
        if aex["raw_sha256"] != mac["raw_sha256"]:
            raise RuntimeError("same-table owner split")
        rows.append({
            "depth": aex["depth"], "tuple_index": aex["tuple_index"],
            "raw_bytes": aex["raw_bytes"], "raw_sha256": aex["raw_sha256"],
            "aex_exported": aex, "mac_production_direct": mac,
            "same_table_full_raw_exact": True,
        })
    return {
        "schema": "olmdirectionalblur.same-table-dual-owner-plumbing/1",
        "status": "PASS_HOST_SUBSTITUTE_SAME_TABLE_EXPORTED_AEX_MAC_PRODUCTION_DIRECT_6_OF_6",
        "identities": static_identities(),
        "build": build,
        "table": table_identity,
        "rows": rows,
        "rows_sha256": digest(rows),
        "mac_table_calls": mac_table_calls,
        "summary": {"cells": 6, "same_table_full_raw_exact": 6, "aex_exported_cells": 6,
                    "mac_production_direct_cells": 6},
        "scope": {
            "plumbing_control_only": True,
            "host_substitute_only": True,
            "native_windows_ucrt_return_received": False,
            "native_windows_result_claimed": False,
            "mac_public_effectmain_claimed": False,
            "production_promoted": False,
            "installed_binary_changed": False,
            "after_effects_launched": False,
            "network_changed": False,
        },
    }


def validate(value: Any, *, live: bool = True) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "schema", "status", "identities", "build", "table", "rows", "rows_sha256",
        "mac_table_calls", "summary", "scope"
    }:
        return False
    if value["schema"] != "olmdirectionalblur.same-table-dual-owner-plumbing/1" or value["status"] != \
            "PASS_HOST_SUBSTITUTE_SAME_TABLE_EXPORTED_AEX_MAC_PRODUCTION_DIRECT_6_OF_6":
        return False
    if live:
        try:
            if value["identities"] != static_identities():
                return False
        except (OSError, RuntimeError, ValueError):
            return False
    if value["build"] != EXPECTED_BUILD:
        return False
    if value["table"] != {
        "kind": "macos_libsystem_host_substitute_plumbing_control", "expf_unique_keys": 378,
        "powf_unique_keys": 850, "total_unique_keys": 1228,
        "sha256": EXPECTED_TABLE_SHA256, "native_windows_ucrt": False,
    }:
        return False
    if value["mac_table_calls"] != {"expf": 996, "powf": 0, "pow": 47514}:
        return False
    rows = value["rows"]
    if not isinstance(rows, list) or len(rows) != 6 or value["rows_sha256"] != digest(rows) or \
            value["rows_sha256"] != EXPECTED_ROWS_SHA256:
        return False
    census = load(CENSUS, "olm_directional_same_table_validate")
    if [(r.get("depth"), r.get("tuple_index")) for r in rows] != list(census.CELLS):
        return False
    for row in rows:
        if set(row) != {"depth", "tuple_index", "raw_bytes", "raw_sha256", "aex_exported", "mac_production_direct",
                        "same_table_full_raw_exact"}:
            return False
        depth, index = row["depth"], row["tuple_index"]
        expected = census.EXPECTED_SHAS[(depth, index)][1]
        expected_bytes = 64 * 36 * 4 * {8: 1, 16: 2, 32: 4}[depth]
        if row["raw_sha256"] != expected or row["raw_bytes"] != expected_bytes or \
                row["same_table_full_raw_exact"] is not True:
            return False
        aex, mac = row["aex_exported"], row["mac_production_direct"]
        if set(aex) != {"depth", "tuple_index", "raw_bytes", "raw_sha256", "expected_exported_sha256",
                       "render_error", "render_mode", "guards_intact", "input_requests", "output_request"}:
            return False
        if aex != {"depth": depth, "tuple_index": index, "raw_bytes": expected_bytes,
                   "raw_sha256": expected, "expected_exported_sha256": expected,
                   "render_error": 0, "render_mode": "smart-cpu", "guards_intact": True,
                   "input_requests": [[0, 0, 64, 36]], "output_request": [0, 0, 64, 36]}:
            return False
        if set(mac) != {"depth", "tuple_index", "raw_sha256", "exported_oracle_sha256",
                       "matches_exported_oracle"} or mac != {
            "depth": depth, "tuple_index": index, "raw_sha256": expected,
            "exported_oracle_sha256": expected, "matches_exported_oracle": True,
        }:
            return False
    return value["summary"] == {"cells": 6, "same_table_full_raw_exact": 6,
                                 "aex_exported_cells": 6, "mac_production_direct_cells": 6} and value["scope"] == {
        "plumbing_control_only": True, "host_substitute_only": True,
        "native_windows_ucrt_return_received": False, "native_windows_result_claimed": False,
        "mac_public_effectmain_claimed": False,
        "production_promoted": False, "installed_binary_changed": False,
        "after_effects_launched": False, "network_changed": False,
    }


def markdown(value: dict[str, Any]) -> str:
    return (
        "# DirectionalBlur same-table dual-owner plumbing control\n\n"
        f"Status: `{value['status']}`.\n\n"
        "A clean temporary AEXCompat release build injected one exact keyed table into the six exported "
        "Windows-AEX Smart cells, while the same table drove the matching Mac production typed/direct replay. All six full "
        "RAW allocations matched the pinned exported oracles. The table is deliberately generated from the "
        "local macOS host leaves; Mac routes all 996 expf calls and all 47,514 double-pow calls through the keyed table. This proves only lookup/injection and owner plumbing, not Mac public EffectMain. It is not native "
        "Windows UCRT evidence, does not promote production, and did not launch After Effects or change network "
        "state. The future accepted 1,344-row native return must replace this table and repeat both owners.\n"
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
        raise RuntimeError("same-table dual-owner plumbing evidence invalid")
    print(value["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
