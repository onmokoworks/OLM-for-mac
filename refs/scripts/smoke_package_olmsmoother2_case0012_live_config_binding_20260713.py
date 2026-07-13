#!/usr/bin/env python3
"""Fail-closed smoke for the case0012 live config-binding package."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.package_olmsmoother2_case0012_live_config_binding_20260713 import (  # noqa: E402
    CASE_ID,
    OUTPUT_ZIP,
    PACKAGE_STEM,
    REQUEST_ID,
    SCHEMA,
    SUPPORT_DIR,
    TARGET_DESCRIPTOR,
    TARGET_IDX,
    TARGET_PIXEL,
    parse_trace_lines,
)


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def main() -> int:
    generator = ROOT / "scripts/package_olmsmoother2_case0012_live_config_binding_20260713.py"
    support_dir = ROOT / SUPPORT_DIR
    package = ROOT / OUTPUT_ZIP

    if not support_dir.is_dir():
        return fail(f"support dir missing: {support_dir}")
    if not package.is_file() or not zipfile.is_zipfile(package):
        return fail(f"package missing: {package}")

    manifest = json.loads((support_dir / "manifest.json").read_text(encoding="utf-8"))
    runtime_manifest = json.loads((support_dir / "runtime_trace_package_manifest.json").read_text(encoding="utf-8"))
    template = json.loads((support_dir / "RETURN_RUNTIME_TRACE_TEMPLATE.json").read_text(encoding="utf-8"))
    runner = (support_dir / "run_olmsmoother2_case0012_live_config_binding_20260713.ps1").read_text(encoding="utf-8")
    cdb_template = (support_dir / "case0012_live_config_binding.cdb.in").read_text(encoding="utf-8")
    request = json.loads((support_dir / "case/request_manifest.json").read_text(encoding="utf-8"))

    if manifest["request_id"] != REQUEST_ID or manifest["schema"] != SCHEMA:
        return fail("request id/schema mismatch")
    if manifest["case_id"] != CASE_ID or manifest["pixel"] != TARGET_PIXEL:
        return fail("witness case/pixel mismatch")
    if manifest["idx"] != TARGET_IDX or manifest["descriptor"] != TARGET_DESCRIPTOR:
        return fail("idx/descriptor mismatch")
    if runtime_manifest.get("kind") != "olm_runtime_trace_request_package":
        return fail("runtime manifest kind mismatch")
    actions = runtime_manifest.get("runtime_actions") or []
    if len(actions) != 1 or actions[0].get("request_id") != REQUEST_ID:
        return fail("runtime action wiring mismatch")
    if template["schema"] != SCHEMA or template["observations"]["c280"]["config_raw_bytes"] != [None] * 8:
        return fail("c280 template mismatch")
    if template["observations"]["cce0"]["config_raw_bytes"] != [None] * 7:
        return fail("cce0 template mismatch")
    if request.get("cases", [{}])[0].get("id") != CASE_ID:
        return fail("packaged request manifest case mismatch")

    for token in (
        "S2_CFG_RUN_START",
        "S2_CFG_BIND",
        "S2_CFG_C280",
        "S2_CFG_CCE0",
        "S2_CFG_WRITER",
        "config_raw_bytes",
        "scale_fixed",
        "mode_byte",
        "DecodeModeName",
        "exact_bind_failure",
    ):
        if token not in runner:
            return fail(f"runner token missing: {token}")
    for token in (
        "OLMSmoother2+0xc280",
        "OLMSmoother2+0xcce0",
        "rax+0x20_scale_fixed_words",
        "poi(rsp+0x28)_gamma_context",
    ):
        if token not in cdb_template:
            return fail(f"cdb token missing: {token}")

    prefix = PACKAGE_STEM + "/"
    expected = {
        prefix + "CONTRACT.md",
        prefix + "README.md",
        prefix + "manifest.json",
        prefix + "runtime_trace_package_manifest.json",
        prefix + "RETURN_RUNTIME_TRACE_TEMPLATE.json",
        prefix + "case0012_live_config_binding.cdb.in",
        prefix + "run_olmsmoother2_case0012_live_config_binding_20260713.ps1",
        prefix + "case/request_manifest.json",
        prefix + "case/reference_manifest.json",
        prefix + "case/ae_render_single_case.jsx",
        prefix + "case/input/case_0012_before_effects.png",
        prefix + "case/input/current_olm_cells.png",
    }
    with zipfile.ZipFile(package) as archive:
        names = set(archive.namelist())
        if not expected <= names:
            return fail(f"package members missing: {sorted(expected - names)}")
        packed_runner = archive.read(prefix + "run_olmsmoother2_case0012_live_config_binding_20260713.ps1").decode("utf-8")
        if packed_runner != runner:
            return fail("packed runner differs from support runner")

    answered = parse_trace_lines(
        [
            "S2_CFG_RUN_START request_id=olmsmoother2_case0012_live_config_binding_20260713 run_id=run-001 case_id=legacy_case_0012_gamma5_red_blue_current_aex x=91 y=841 idx=105 descriptor=91,841,1,91,843,5",
            "S2_CFG_BIND run_id=run-001 module=OLMSmoother2 module_base=0x180000000 writer_hook=OLMSmoother2+0x3370 c280_hook=OLMSmoother2+0xc280 cce0_hook=OLMSmoother2+0xcce0 binding_expression=writer_xy_anchor_then_config_reads pointer_context=rsp+0x34_x_rsp+0x38_y",
            "S2_CFG_C280 run_id=run-001 config_pointer=0x180100000 config_pointer_arithmetic=rax+0x20_scale_fixed_words config_raw_bytes=00,00,01,00,00,00,01,00 scale_fixed=65536,65536",
            "S2_CFG_CCE0 run_id=run-001 config_pointer=0x180200000 config_pointer_arithmetic=poi(rsp+0x28)_gamma_context config_raw_bytes=00,00,80,3f,04,00,03 mode_byte=3",
            "S2_CFG_WRITER run_id=run-001 writer_site=OLMSmoother2+0x3610 writer_rgba_u8=0,0,0,0 writer_rgba_float=0.0,0.0,0.0,0.0",
        ]
    )
    if answered.get("status") != "answered":
        return fail("synthetic complete trace did not answer")
    if answered["observations"]["c280"]["scale_fixed"] != [65536, 65536]:
        return fail("synthetic c280 scale decode mismatch")
    if answered["observations"]["cce0"]["mode_name"] != "gamma_colors":
        return fail("synthetic cce0 mode decode mismatch")

    failed = parse_trace_lines(
        [
            "S2_CFG_RUN_START request_id=olmsmoother2_case0012_live_config_binding_20260713 run_id=run-001 case_id=legacy_case_0012_gamma5_red_blue_current_aex x=91 y=841 idx=105 descriptor=91,841,1,91,843,5",
            "S2_CFG_BIND run_id=run-001 module=OLMSmoother2 module_base=0x180000000 writer_hook=OLMSmoother2+0x3370 c280_hook=OLMSmoother2+0xc280 cce0_hook=OLMSmoother2+0xcce0 binding_expression=writer_xy_anchor_then_config_reads pointer_context=rsp+0x34_x_rsp+0x38_y",
            "S2_CFG_C280 run_id=run-001 config_pointer=0x180100000 config_pointer_arithmetic=rax+0x20_scale_fixed_words config_raw_bytes=00,00,01,00,00,00,01,00 scale_fixed=65536,65536",
            "S2_CFG_WRITER run_id=run-001 writer_site=OLMSmoother2+0x3610 writer_rgba_u8=0,0,0,0 writer_rgba_float=0.0,0.0,0.0,0.0",
        ]
    )
    if failed.get("status") != "exact_bind_failure":
        return fail("incomplete trace did not fail closed")
    if "mode_byte" not in failed["failure"]["reason"] and "cce0_config_pointer" not in failed["failure"]["reason"]:
        return fail("failure reason did not mention missing cce0 fields")

    with tempfile.TemporaryDirectory(prefix="sm2_cfg_pkg_") as tmp:
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

    print("[OK] OLMSmoother2 case0012 live config-binding package smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
