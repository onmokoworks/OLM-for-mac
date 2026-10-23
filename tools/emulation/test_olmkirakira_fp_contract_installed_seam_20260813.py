#!/usr/bin/env python3
"""Compare the retained pre-fix and current installed Kira public PF outputs."""

from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import struct
import subprocess
import tempfile
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "tools/emulation/test_olmkirakira_public_smart_bounded_closure_20260812.py"
HARNESS = ROOT / "tools/emulation/olmkirakira_public_smart_bounded_closure_harness_20260812.cpp"
SHIM = ROOT / "tools/emulation/olmkirakira_installed_effectmain_shim_20260813.h"
OLD = ROOT / "handoffs/olmkirakira_fp_contract_incremental_install_20260813/moved_old/OLMKiraKira.plugin/Contents/MacOS/OLMKiraKira"
CURRENT = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMKiraKira.plugin/Contents/MacOS/OLMKiraKira"
REPORT = ROOT / "refs/conformance/olmkirakira_fp_contract_installed_seam_20260813.json"
MARKDOWN = REPORT.with_suffix(".md")

PINS = {
    "base_generator": "5b3e93d45632c3452e81b0b39f63786c6c146e28e0fb7ed5611a0217ec3ea9f1",
    "harness": "1623680d7fe2cf6525e0e2893d7c25b6d629accf5fd81318a35fab1e64af01c4",
    "shim": "eccf768d497919c1b875ea10e3c73ec53e35a16af9c4a561303497d25ae8097a",
    "old_binary": "69da64666478b25957aa268f6bb6fbc869c3d50b61759f9ca00172045afb5194",
    "current_binary": "260c2d5e635b38213adf88e01298510bf7f180b38bdb5e1d2b85a2906fbfbf18",
}
MISMATCH_KEYS = {
    ("m1_h7_r0", 32), ("m1_h7_r1", 32),
    ("m3_h50_r0", 32), ("m3_h50_r1", 32), ("m4_multiray", 32),
}
ROWS_SHA256 = "87d274191a15070ad98a8c9787b4064136e983e2cdd3cb6d1d1e6851c9444177"
STATUS = "PASS_OLMKIRAKIRA_INSTALLED_FP_CONTRACT_SEAM_OLD37_NEW42_NO_AE"
CLAIM_BOUNDARY = "AE-free same-harness counterfactual of retained predecessor and current installed public EffectMain. It localizes build-setting contraction drift; it is not native-AE or arbitrary-product evidence."
ROW_KEYS = {
    "tuple", "depth", "oracle_sha256", "old_installed_sha256",
    "current_installed_sha256", "old_oracle_exact", "current_oracle_exact",
    "old_pf32_word_differences", "old_pf32_max_ulp",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_base():
    spec = importlib.util.spec_from_file_location("kira_fp_seam_base", BASE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def parse_line(line: str) -> dict[str, str]:
    return dict(item.split("=", 1) for item in shlex.split(line)[1:] if "=" in item)


def compile_harness(executable: Path) -> None:
    sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
    define = '-DKIRA_SOURCE="' + str(SHIM) + '"'
    command = [
        _UCRT_CXX, "-std=c++20", "-O2", "-fno-fast-math", "-ffp-contract=off",
        "-isysroot", sdk, "-w", "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
        "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"), define, str(HARNESS),
        str(ROOT / "Util/AEGP_SuiteHandler.cpp"), str(ROOT / "Util/MissingSuiteError.cpp"),
        "-framework", "Cocoa", "-o", str(executable),
    ]
    run = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if run.returncode:
        raise RuntimeError(run.stdout + run.stderr)


def execute(executable: Path, binary: Path) -> dict[tuple[str, int], bytes]:
    environment = os.environ.copy()
    environment["OLMKIRAKIRA_INSTALLED_BINARY"] = str(binary)
    run = subprocess.run([str(executable)], cwd=ROOT, env=environment, text=True, capture_output=True)
    if run.returncode:
        raise RuntimeError(f"harness failed for {binary}: {run.returncode}\n{run.stdout[-4000:]}\n{run.stderr}")
    rows = {}
    for line in run.stdout.splitlines():
        if not line.startswith("CASE "):
            continue
        row = parse_line(line)
        if row["fail"] != "-1/-1":
            continue
        if row["smart_hex"] != row["classic_hex"]:
            raise RuntimeError("Classic and Smart differ inside one binary")
        rows[(row["tuple"], int(row["depth"]))] = bytes.fromhex(row["smart_hex"])
    if len(rows) != 42:
        raise RuntimeError(f"expected 42 positive rows, got {len(rows)}")
    return rows


def pf32_census(actual: bytes, expected: bytes) -> tuple[int, int]:
    left = struct.unpack("<" + "I" * (len(actual) // 4), actual)
    right = struct.unpack("<" + "I" * (len(expected) // 4), expected)
    differences = [abs(a - b) for a, b in zip(left, right) if a != b]
    return len(differences), max(differences, default=0)


def generate() -> dict[str, Any]:
    live = {"base_generator": sha256(BASE), "harness": sha256(HARNESS), "shim": sha256(SHIM), "old_binary": sha256(OLD), "current_binary": sha256(CURRENT)}
    if live != PINS:
        raise RuntimeError(f"seam authority drift: {live}")
    base = load_base()
    with tempfile.TemporaryDirectory(prefix="kira_fp_installed_seam_") as temporary:
        executable = Path(temporary) / "closure"
        compile_harness(executable)
        old_rows = execute(executable, OLD)
        current_rows = execute(executable, CURRENT)
    rows = []
    for key in sorted(old_rows):
        name, depth = key
        expected_hash = base.EXPECTED[name][depth]
        old_hash = hashlib.sha256(old_rows[key]).hexdigest()
        current_hash = hashlib.sha256(current_rows[key]).hexdigest()
        expected_bytes = current_rows[key] if current_hash == expected_hash else b""
        if not expected_bytes:
            raise RuntimeError(f"current installed row is not oracle exact: {key}")
        word_diff, max_ulp = pf32_census(old_rows[key], expected_bytes) if depth == 32 else (0, 0)
        rows.append({
            "tuple": name,
            "depth": depth,
            "oracle_sha256": expected_hash,
            "old_installed_sha256": old_hash,
            "current_installed_sha256": current_hash,
            "old_oracle_exact": old_hash == expected_hash,
            "current_oracle_exact": current_hash == expected_hash,
            "old_pf32_word_differences": word_diff,
            "old_pf32_max_ulp": max_ulp,
        })
    mismatch = {(row["tuple"], row["depth"]) for row in rows if not row["old_oracle_exact"]}
    if mismatch != MISMATCH_KEYS or sum(row["current_oracle_exact"] for row in rows) != 42:
        raise RuntimeError(f"unexpected installed mismatch set: {mismatch}")
    canonical = hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        "schema": "olmkirakira.installed-fp-contract-seam/1",
        "status": STATUS,
        "claim_boundary": CLAIM_BOUNDARY,
        "authorities": live,
        "rows": rows,
        "rows_sha256": canonical,
        "summary": {
            "row_count": 42,
            "old_oracle_exact": 37,
            "old_oracle_mismatched": 5,
            "current_oracle_exact": 42,
            "mismatch_keys": [[name, depth] for name, depth in sorted(MISMATCH_KEYS)],
        },
        "after_effects_processes": [],
        "scope": {"native_after_effects": False, "arbitrary_tuple_source_geometry": False},
    }


def validate(report: dict[str, Any]) -> None:
    if set(report) != {"schema", "status", "claim_boundary", "authorities", "rows", "rows_sha256", "summary", "after_effects_processes", "scope"}:
        raise RuntimeError("seam report schema drift")
    if report["schema"] != "olmkirakira.installed-fp-contract-seam/1" or report["status"] != STATUS or report["claim_boundary"] != CLAIM_BOUNDARY or report["authorities"] != PINS:
        raise RuntimeError("seam report identity drift")
    rows = report["rows"]
    digest = hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if len(rows) != 42 or any(set(row) != ROW_KEYS for row in rows):
        raise RuntimeError("seam row schema drift")
    if report["rows_sha256"] != digest or digest != ROWS_SHA256:
        raise RuntimeError("seam row digest drift")
    mismatch = {(row["tuple"], row["depth"]) for row in rows if not row["old_oracle_exact"]}
    if mismatch != MISMATCH_KEYS or not all(row["current_oracle_exact"] for row in rows):
        raise RuntimeError("seam mismatch set drift")
    expected_summary = {"row_count": 42, "old_oracle_exact": 37, "old_oracle_mismatched": 5, "current_oracle_exact": 42, "mismatch_keys": [[name, depth] for name, depth in sorted(MISMATCH_KEYS)]}
    if report["summary"] != expected_summary or report["after_effects_processes"] != []:
        raise RuntimeError("seam summary/process drift")
    if report["scope"] != {"native_after_effects": False, "arbitrary_tuple_source_geometry": False}:
        raise RuntimeError("seam scope escalation")


def markdown(report: dict[str, Any]) -> str:
    mismatch = [row for row in report["rows"] if not row["old_oracle_exact"]]
    lines = [
        "# OLMKiraKira installed FP-contract seam (2026-08-13)", "",
        f"Status: `{report['status']}`", "",
        "The retained predecessor is oracle-exact in 37/42 bounded public cells. The current installed correction is exact in 42/42. Both binaries retain Classic=Smart internally; the five old mismatches are PF32 only:", "",
        "| tuple | old word differences | old max ULP | old SHA | current/oracle SHA |", "|---|---:|---:|---|---|",
    ]
    for row in mismatch:
        lines.append(f"| {row['tuple']} | {row['old_pf32_word_differences']} | {row['old_pf32_max_ulp']} | `{row['old_installed_sha256']}` | `{row['oracle_sha256']}` |")
    lines += ["", "Boundary: same real-SDK AE-free harness and retained installed binaries only. No native-AE or unlisted-product claim.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    live = generate()
    validate(live)
    if args.write:
        REPORT.write_text(json.dumps(live, indent=2, sort_keys=True) + "\n")
        MARKDOWN.write_text(markdown(live))
    else:
        if not REPORT.is_file() or not MARKDOWN.is_file():
            raise RuntimeError("seam report missing; use --write intentionally")
        persisted = json.loads(REPORT.read_text())
        validate(persisted)
        if persisted != live or MARKDOWN.read_text() != markdown(live):
            raise RuntimeError("seam report differs from live retained binaries")
    print(STATUS)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL_OLMKIRAKIRA_INSTALLED_FP_CONTRACT_SEAM: {exc}", file=sys.stderr)
        raise
