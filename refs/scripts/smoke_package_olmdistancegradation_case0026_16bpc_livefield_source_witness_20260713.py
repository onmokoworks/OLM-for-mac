#!/usr/bin/env python3
"""Fail-closed smoke for the case_0026 live field/source witness package."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.package_olmdistancegradation_16bpc_livefield_source_witness_20260713 import (  # noqa: E402
    AEX_SHA256,
    CASE_ID,
    CASE_SHORT_ID,
    OUTPUT_ZIP,
    PACKAGE_STEM,
    REQUEST_ID,
    SCHEMA,
    SUPPORT_DIR,
    TARGET_POINTS,
    parse_trace_lines,
)


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def build_lines(include_all: bool = True) -> list[str]:
    lines = [
        f"OLMDG_LFS_RUN_START request_id={REQUEST_ID} run_id=run-001 case_id={CASE_SHORT_ID}",
    ]
    for idx, (x, y) in enumerate(TARGET_POINTS):
        lines.extend(
            [
                (
                    "OLMDG_LFS_ENTRY "
                    f"run_id=run-001 case_id={CASE_SHORT_ID} x={x} y={y} "
                    f"module_base=0x181000000 output=0x2200000{idx} "
                    "pre_output_words_agrb=61166,61166,61166,61166 "
                    "in_out=3 inside_threshold=158 outside_threshold=13 "
                    "use_bg=1 invert=1 render_mode=1 interp_mode=4 "
                    "power_bits=0x40263bec grad_r_bits=0x3de0e0ff grad_g_bits=0x00000000 "
                    "grad_b_bits=0x3f6eeeef bg_r_bits=0x3f800000 bg_g_bits=0x00000000 bg_b_bits=0x00000000"
                ),
                (
                    "OLMDG_LFS_FIELD "
                    f"run_id=run-001 case_id={CASE_SHORT_ID} x={x} y={y} "
                    f"rcx=0x2100000{idx} rcx_plus2_word={12345 + idx} "
                    f"field_words_agrb=65535,{12345 + idx},0,{42 + idx} field_base=0x20000018 field_header=0x20000000 "
                    "field_rowbytes=15360 field_pixel_size=8"
                ),
                (
                    "OLMDG_LFS_SOURCE "
                    f"run_id=run-001 case_id={CASE_SHORT_ID} x={x} y={y} "
                    f"rdx=0x2300000{idx} source_words_agrb=65535,{65535 - idx},0,{10794 + idx}"
                ),
            ]
        )
        if include_all or idx != len(TARGET_POINTS) - 1:
            lines.append(
                "OLMDG_LFS_RETURN "
                f"run_id=run-001 case_id={CASE_SHORT_ID} x={x} y={y} "
                f"output=0x2200000{idx} post_output_words_agrb={32645 - idx},0,{129 + idx},65535"
            )
    lines.append(f"OLMDG_LFS_RUN_END request_id={REQUEST_ID} run_id=run-001")
    return lines


def main() -> int:
    generator = ROOT / "scripts/package_olmdistancegradation_16bpc_livefield_source_witness_20260713.py"
    support_dir = ROOT / SUPPORT_DIR
    package = ROOT / OUTPUT_ZIP

    if not support_dir.is_dir():
        return fail(f"support dir missing: {support_dir}")
    if not package.is_file() or not zipfile.is_zipfile(package):
        return fail(f"package missing: {package}")

    manifest = json.loads((support_dir / "manifest.json").read_text(encoding="utf-8"))
    runtime_manifest = json.loads((support_dir / "runtime_trace_package_manifest.json").read_text(encoding="utf-8"))
    template = json.loads((support_dir / "RETURN_RUNTIME_TRACE_TEMPLATE.json").read_text(encoding="utf-8"))
    runner = (
        support_dir / "run_olmdistancegradation_case0026_16bpc_livefield_source_witness_20260713.ps1"
    ).read_text(encoding="utf-8")
    cdb_template = (support_dir / "case0026_livefield_source_witness.cdb.in").read_text(encoding="utf-8")
    contract = (support_dir / "CONTRACT.md").read_text(encoding="utf-8")

    if manifest["request_id"] != REQUEST_ID or manifest["schema"] != SCHEMA:
        return fail("request id/schema mismatch")
    if manifest["case_id"] != CASE_ID:
        return fail("case id mismatch")
    if manifest["target_points"] != [list(point) for point in TARGET_POINTS]:
        return fail("target points mismatch")
    if manifest["aex_pin"]["sha256"] != AEX_SHA256:
        return fail("AEX pin mismatch")
    if runtime_manifest.get("kind") != "olm_runtime_trace_request_package":
        return fail("runtime manifest kind mismatch")
    if template["schema"] != SCHEMA or len(template["points"]) != 4:
        return fail("template mismatch")

    for token in (
        "PowerShell51",
        "Start-Process -FilePath $PowerShell51 -ArgumentList $relayArgs",
        "Start-Process -FilePath $Cdb -ArgumentList $cdbArgs",
        "gpuAccelType=SOFTWARE",
        "project_bits_per_channel",
        "exact_bind_failure",
    ):
        if token not in runner:
            return fail(f"runner token missing: {token}")
    for forbidden in (
        "Start-Process -FilePath $PowerShell51 -ArgumentList @(",
        "Start-Process -FilePath $Cdb -ArgumentList @(",
        "answered_partial",
    ):
        if forbidden in runner:
            return fail(f"forbidden runner token present: {forbidden}")

    for token in (
        "DistanceGradation+0x1170480",
        "DistanceGradation+0x117057d",
        "DistanceGradation+0x11705f1",
        "bp /1 @$t2",
        "OLMDG_LFS_ENTRY",
        "OLMDG_LFS_FIELD",
        "OLMDG_LFS_SOURCE",
        "OLMDG_LFS_RETURN",
        "pre_output_words_agrb",
        "source_words_agrb",
        "field_words_agrb",
        "post_output_words_agrb",
    ):
        if token not in cdb_template:
            return fail(f"cdb token missing: {token}")
    for token in ("same run", "PowerShell 5.1", "exact_bind_failure"):
        if token not in contract:
            return fail(f"contract token missing: {token}")

    prefix = PACKAGE_STEM + "/"
    expected = {
        prefix + "CONTRACT.md",
        prefix + "README.md",
        prefix + "manifest.json",
        prefix + "runtime_trace_package_manifest.json",
        prefix + "RETURN_RUNTIME_TRACE_TEMPLATE.json",
        prefix + "case0026_livefield_source_witness.cdb.in",
        prefix + "run_olmdistancegradation_case0026_16bpc_livefield_source_witness_20260713.ps1",
        prefix + "case/request_manifest.json",
        prefix + "case/reference_manifest.json",
        prefix + "case/ae_render_single_case.jsx",
        prefix + "case/input/case_0026_before_effects.png",
        prefix + "case/expected/case_0026.png",
    }
    with zipfile.ZipFile(package) as archive:
        names = set(archive.namelist())
        if not expected <= names:
            return fail(f"package members missing: {sorted(expected - names)}")
        packed_runner = archive.read(
            prefix + "run_olmdistancegradation_case0026_16bpc_livefield_source_witness_20260713.ps1"
        ).decode("utf-8")
        if packed_runner != runner:
            return fail("packed runner differs from support runner")

    answered = parse_trace_lines(build_lines(include_all=True))
    if answered.get("status") != "answered":
        return fail("synthetic complete trace did not answer")
    if answered["run"]["current_aex"]["sha256"] != AEX_SHA256:
        return fail("synthetic answered AEX pin mismatch")
    if answered["points"][0]["field_raw_words_agrb"][1] != 12345:
        return fail("synthetic field words mismatch")

    failed = parse_trace_lines(build_lines(include_all=False))
    if failed.get("status") != "exact_bind_failure":
        return fail("incomplete trace did not fail closed")
    if not any("post_output_words_agrb" in item or "record_count" in item for item in failed["failure"]["missing"]):
        return fail("failure missing list did not mention missing return capture")

    with tempfile.TemporaryDirectory(prefix="dglfs_pkg_") as tmp:
        tmp_support = Path(tmp) / "support"
        tmp_zip = Path(tmp) / "package.zip"
        proc = subprocess.run(
            [sys.executable, str(generator), "--support-dir", str(tmp_support), "--output", str(tmp_zip)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if proc.returncode != 0:
            return fail(f"generator failed: {proc.stdout}")
        if not tmp_zip.is_file() or not zipfile.is_zipfile(tmp_zip):
            return fail("generator did not materialize zip")

    print("[OK] DG case0026 live field/source witness package smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
