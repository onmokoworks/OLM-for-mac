#!/usr/bin/env python3
"""Replay Radial Strength290 exported Smart with the returned native UCRT table.

Normal execution validates frozen evidence.  ``--run-build --write`` is the only
mode that clones/builds AEXCompat and replaces the report.  It never installs a
plug-in or launches After Effects.
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import zipfile

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
AEX_REPO = Path("/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue851-smart-primary-checkout")
RETURN = Path("/Volumes/onmk/olm_pr/new/mac_returns/olm_runtime_trace_olmradialblur_strength290_ucrt_math_return_windows_20260815_020556.zip")
ANALYZER = ROOT / "scripts/analyze_olmradialblur_strength290_ucrt_math_return_20260814.py"
FROZEN_RETURN = ROOT / "refs/conformance/olmradialblur_strength290_ucrt_math_native_return_20260814.json"
PRIOR = ROOT / "refs/conformance/olmradialblur_strength290_exported_math_boundary_20260814.json"
PRIOR_TOOL = ROOT / "tools/emulation/test_olmradialblur_strength290_exported_math_boundary_20260814.py"
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
AEX = resolve_asset(ROOT / "aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex")
PATCHES = [
    ROOT / "tools/emulation/aexcompat_olmradialblur_float_math_imports_20260814.patch",
    ROOT / "tools/emulation/aexcompat_exact_raw_input_20260815.patch",
    ROOT / "tools/emulation/aexcompat_raw_output_dump_20260814.patch",
    ROOT / "tools/emulation/aexcompat_olmradialblur_native_ucrt_table_20260815.patch",
    ROOT / "tools/emulation/aexcompat_olmradialblur_native_ucrt_trace_20260815.patch",
]
REPORT = ROOT / "refs/conformance/olmradialblur_strength290_native_ucrt_exported_public_boundary_20260815.json"
DOC = REPORT.with_suffix(".md")
EXPECTED_HEAD = "28d535469f84f67236ef3425afe4291ea2fb0991"
EXPECTED_RETURN_SHA = "2adf1d5ac2ddcff79e4da492ee61985935c2f83a75224c85d19b6f01ba1a0d91"
EXPECTED_NATIVE_ROWS_SHA = "52bf76720eef963c77db0a9325f3902bbc9986ad9ce853930ca6f7ad0854d2bd"
EXPECTED_OUTPUT_SHA = "5c70fe269db5c2923c1ce1a63645f83075975ab6b13eb34e09c240b999351f28"
EXPECTED_MAC_SHA = "940c1e7e1ef45a58ebd81df06c263c1e7a1e0a38a209f9a800f1d2c5d51614e5"


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def canonical(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(args: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True)


def identities() -> dict[str, object]:
    head = run(["git", "rev-parse", "HEAD"], AEX_REPO)
    if head.returncode or head.stdout.strip() != EXPECTED_HEAD:
        raise RuntimeError("AEXCompat HEAD drift")
    if RETURN.exists() and sha(RETURN) != EXPECTED_RETURN_SHA:
        raise RuntimeError("NAS return archive identity drift")
    return {
        "aexcompat_head": EXPECTED_HEAD,
        "return_zip": {"operational_source_path": str(RETURN), "sha256": EXPECTED_RETURN_SHA},
        "validated_return_report_sha256": sha(FROZEN_RETURN),
        "prior_boundary_sha256": sha(PRIOR),
        "prior_boundary_tool_sha256": sha(PRIOR_TOOL),
        "production_source_sha256": sha(SOURCE),
        "aex_sha256": sha(AEX),
        "patches": [{"path": str(p.relative_to(ROOT)), "sha256": sha(p)} for p in PATCHES],
    }


def return_rows() -> tuple[dict[str, object], list[dict[str, object]]]:
    analyzer = load_module(ANALYZER, "radial_native_return_analyzer")
    observed = analyzer.analyze(RETURN)
    frozen = json.loads(FROZEN_RETURN.read_text())
    if observed != frozen or observed["return_sha256"] != EXPECTED_RETURN_SHA:
        raise RuntimeError("validated/frozen native return drift")
    with zipfile.ZipFile(RETURN) as archive:
        summary = json.loads(archive.read("run_summary.json"))
    return observed, summary["rows"]


def write_table(path: Path, rows: list[dict[str, object]]) -> None:
    lines = []
    for row in rows:
        result = str(row["native_ucrt_result_bits"])[2:]
        if row["function"] == "log2f":
            lines.append(f"l {str(row['argument_bits'])[2:]} {result}")
        else:
            lines.append(f"a {str(row['left_bits'])[2:]} {str(row['right_bits'])[2:]} {result}")
    path.write_text("\n".join(lines) + "\n")


def build_worker(temp: Path) -> tuple[Path, dict[str, object]]:
    clone = temp / "aexcompat"
    result = run(["git", "clone", "--quiet", "--no-hardlinks", str(AEX_REPO), str(clone)], temp)
    if result.returncode:
        raise RuntimeError("AEXCompat clone failed: " + result.stderr)
    for patch in PATCHES:
        result = run(["git", "apply", str(patch)], clone)
        if result.returncode:
            raise RuntimeError(f"patch failed {patch.name}: {result.stderr}")
    result = run(["cargo", "build", "--release", "-p", "aex-guest-worker",
                  "--manifest-path", str(clone / "guest/Cargo.toml")], clone)
    if result.returncode:
        raise RuntimeError("AEXCompat build failed: " + result.stdout + result.stderr)
    worker = clone / "guest/target/release/aex-guest-worker"
    return worker, {
        "clean_temporary_clone": True,
        "release_build": True,
        "worker_sha256": sha(worker),
        "worker_bytes": worker.stat().st_size,
        "patched_main_sha256": sha(clone / "guest/crates/aex-guest-worker/src/main.rs"),
        "patched_callbacks_sha256": sha(clone / "guest/crates/aex-guest-worker/src/x64/callbacks.rs"),
        "patched_imports_sha256": sha(clone / "guest/crates/aex-guest-worker/src/x64/imports.rs"),
    }


PARAMS = [
    "Blur Type=2", "Center=16,9", "Strength@4=290", "Offset Mode@5=1", "Offset@6=0",
    "Edge Fade@7=0", "Strength@10=0", "Offset Mode@11=1", "Offset@12=0", "Edge Fade@13=0",
    "Repeat Border=1", "Ratio=1", "Angle=deg:0", "Quality=5", "Brightness Gain=1",
    "Size Variation=25", "Noise Variation=100", "Noise Type=1", "Seed=1",
    "Offset@28=deg:0", "Thickness=10",
]


def replay(worker: Path, temp: Path, rows: list[dict[str, object]]) -> dict[str, object]:
    prior_tool = load_module(PRIOR_TOOL, "radial_strength290_prior")
    source = prior_tool.reconstruct_source()
    internal = prior_tool.unpack(prior_tool.INTERNAL_B85)
    source_path, table, trace = temp / "source.raw", temp / "native-table.txt", temp / "replay.trace"
    source_path.write_bytes(source)
    write_table(table, rows)
    dummy, output = temp / "dimensions.png", temp / "native-output.png"
    Image.new("RGBA", (32, 18), (0, 0, 0, 0)).save(dummy)
    env = dict(os.environ, OLM_EXACT_RAW_INPUT=str(source_path),
               OLM_RADIAL_NATIVE_UCRT_TABLE=str(table),
               OLM_RADIAL_NATIVE_UCRT_REPLAY_TRACE=str(trace))
    result = run([str(worker), "render-png", str(AEX), str(dummy), str(output),
                  "--pixel-format", "argb32f", *PARAMS], ROOT, env)
    if result.returncode:
        raise RuntimeError("exported Smart replay failed: " + result.stdout + result.stderr)
    worker_report = json.loads(result.stdout)
    raw = output.with_suffix(".raw").read_bytes()
    calls = trace.read_text().splitlines()
    census = Counter(line.split()[0] for line in calls)
    unique = len(set(calls))
    if len(calls) != 725 or census != {"log2f": 149, "atan2f": 576} or unique != 577:
        raise RuntimeError(f"replay call census drift: {len(calls)}/{census}/{unique}")
    differences = []
    for index, ((left,), (right,)) in enumerate(zip(struct.iter_unpack("<I", raw),
                                                     struct.iter_unpack("<I", internal), strict=True)):
        if left != right:
            differences.append([index, left, right, abs(left - right)])
    return {
        "fixture": {"width": 32, "height": 18, "pixel_format": "PF32_ARGB_FLOAT_LE",
                    "rowbytes": 512, "bytes": len(source), "source_sha256": sha_bytes(source),
                    "source_file_unchanged_after_replay": sha(source_path) == sha_bytes(source)},
        "native_table": {"vectors": len(rows), "original_calls": len(calls),
                         "log2f_calls": census["log2f"], "atan2f_calls": census["atan2f"],
                         "unique_replayed_vectors": unique, "table_sha256": sha(table),
                         "trace_sha256": sha(trace)},
        "exported_smart": {"render_error": worker_report["render_error"],
                           "render_mode": worker_report["render_mode"],
                           "guards_intact": worker_report["guards_intact"],
                           "input_requests": worker_report["input_requests"],
                           "output_request": worker_report["output_request"],
                           "raw_bytes": len(raw), "raw_sha256": sha_bytes(raw)},
        "comparison": {"native_exported_sha256": sha_bytes(raw), "mac_typed_owner_sha256": sha_bytes(internal),
                       "same_source_full_raw_exact": raw == internal,
                       "different_float_words": len(differences),
                       "max_ulp": max(row[3] for row in differences),
                       "ulp_histogram": dict(sorted(Counter(row[3] for row in differences).items())),
                       "canonical_diff_sha256": sha_bytes(json.dumps(differences, separators=(",", ":")).encode())},
    }


def generate(run_build: bool) -> dict[str, object]:
    if not run_build:
        raise RuntimeError("fresh evidence requires --run-build")
    validated, rows = return_rows()
    with tempfile.TemporaryDirectory(prefix="olm-radial-native-ucrt-") as raw:
        temp = Path(raw)
        worker, build = build_worker(temp)
        result = replay(worker, temp, rows)
    exact = result["comparison"]["same_source_full_raw_exact"]
    return {
        "schema": "olmradialblur.strength290-native-ucrt-exported-public-boundary/1",
        "status": "PASS_NATIVE_UCRT_EXPORTED_SMART_MISMATCH_STRENGTH290_REMAINS_FAIL_CLOSED",
        "identities": identities(), "native_return": validated, "native_rows": rows,
        "native_rows_sha256": sha_bytes(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()),
        "build": build, **result,
        "public_admission": {"justified": bool(exact), "production_changed": False,
                             "current_result": "PF_Err_BAD_CALLBACK_PARAM_before_iteration",
                             "decision": "retain_fail_closed_because_native_exported_and_mac_typed_final_raw_differ"},
        "scope": {"after_effects_launched": False, "plugin_installed": False,
                  "universal_candidate_built": False, "native_after_effects_claimed": False,
                  "padding_claimed": False, "unlisted_tuple_or_geometry_claimed": False},
    }


def markdown(value: dict[str, object]) -> str:
    comparison = value["comparison"]
    return (
        "# OLMRadialBlur Strength 290 native-UCRT exported/public boundary\n\n"
        f"Status: `{value['status']}`.\n\n"
        "The validated 64-bit AMD64 System32 UCRT return drove every one of the actual exported "
        "Smart route's 725 math calls (577 unique keys) on the exact PF32 32×18 source and tuple. "
        f"Its full RAW output is `{comparison['native_exported_sha256']}`, while the current Mac typed "
        f"owner is `{comparison['mac_typed_owner_sha256']}`; {comparison['different_float_words']} float "
        "words differ. Strength 290 therefore remains rejected before iteration. No production source, "
        "installed bundle, Universal candidate, or After Effects process was changed. Tight exported RAW "
        "does not establish a padding claim.\n"
    )


def validate(value: object, live: bool = True) -> bool:
    if not isinstance(value, dict) or value.get("schema") != \
            "olmradialblur.strength290-native-ucrt-exported-public-boundary/1":
        return False
    if value.get("status") != "PASS_NATIVE_UCRT_EXPORTED_SMART_MISMATCH_STRENGTH290_REMAINS_FAIL_CLOSED":
        return False
    if live:
        try:
            if value.get("identities") != identities():
                return False
            if RETURN.exists():
                validated, archive_rows = return_rows()
                if value.get("native_return") != validated or value.get("native_rows") != archive_rows:
                    return False
        except (OSError, RuntimeError, ValueError, KeyError, zipfile.BadZipFile):
            return False
    native_rows = value.get("native_rows")
    if not isinstance(native_rows, list) or len(native_rows) != 577 or \
            value.get("native_rows_sha256") != EXPECTED_NATIVE_ROWS_SHA or \
            sha_bytes(json.dumps(native_rows, sort_keys=True, separators=(",", ":")).encode()) != EXPECTED_NATIVE_ROWS_SHA:
        return False
    comparison = value.get("comparison", {})
    if comparison.get("native_exported_sha256") != EXPECTED_OUTPUT_SHA or \
            comparison.get("mac_typed_owner_sha256") != EXPECTED_MAC_SHA or \
            comparison.get("same_source_full_raw_exact") is not False or \
            comparison.get("different_float_words") != 80:
        return False
    table = value.get("native_table", {})
    if (table.get("vectors"), table.get("original_calls"), table.get("log2f_calls"),
            table.get("atan2f_calls"), table.get("unique_replayed_vectors")) != (577, 725, 149, 576, 577):
        return False
    admission = value.get("public_admission", {})
    return admission == {"justified": False, "production_changed": False,
                         "current_result": "PF_Err_BAD_CALLBACK_PARAM_before_iteration",
                         "decision": "retain_fail_closed_because_native_exported_and_mac_typed_final_raw_differ"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-build", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        value = generate(args.run_build)
        REPORT.write_text(canonical(value))
        DOC.write_text(markdown(value))
    else:
        value = json.loads(REPORT.read_text())
    if not validate(value) or DOC.read_text() != markdown(value):
        raise RuntimeError("Radial Strength290 native-UCRT boundary evidence invalid")
    print(value["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
