#!/usr/bin/env python3
"""Smoke-test the fresh Smoother2 0012 typed bind/read package."""

from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.package_smoother2_current_aex_0012_typed_bind_read import parse_trace_lines

REQUIRED = {
    "idx",
    "descriptor",
    "class_bytes.center_b0",
    "class_bytes.prev_b0",
    "class_bytes.left_b1",
    "e170.c",
    "f270.append",
    "f270.source_xy",
    "f270.weight",
    "e3a0.append",
    "e3a0.source_xy",
    "e3a0.weight",
    "polygon_count",
    "cce0.output_rgba_float",
    "cce0.output_rgba_hex",
    "final_writer",
}
SCHEMA = "olm_smoother2_current_aex_0012_typed_bind_read_return_v2"
REQUEST_ID = "olmsmoother2_current_aex_0012_typed_bind_read_20260710"


def validate_fail_closed(result: dict[str, object]) -> None:
    status = result.get("status")
    if status == "answered_partial" or status == "partial":
        raise AssertionError("partial status is forbidden")
    if status != "exact_bind_failure":
        raise AssertionError("missing typed field did not fail closed")
    failure = result.get("failure")
    if not isinstance(failure, dict):
        raise AssertionError("exact_bind_failure lacks failure object")
    for key in ("stage", "reason", "module", "hook", "run_id", "case_id", "pixel", "pointer_context", "last_observation"):
        if key not in failure:
            raise AssertionError(f"failure lacks {key}")


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def main() -> int:
    if len(sys.argv) != 2:
        return fail("usage: smoke_smoother2_current_aex_0012_typed_bind_read.py PACKAGE.zip")
    package = Path(sys.argv[1])
    if not zipfile.is_zipfile(package):
        return fail("not a zip")
    with zipfile.ZipFile(package) as archive:
        names = set(archive.namelist())
        if any(name.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:[\\/]", name) for name in names):
            return fail("absolute archive path present")
        root = next((name.split("/", 1)[0] for name in names if "/manifest.json" in name), None)
        if root is None:
            return fail("manifest missing")
        manifest = json.loads(archive.read(f"{root}/manifest.json"))
        runtime_manifest = json.loads(archive.read(f"{root}/runtime_trace_package_manifest.json"))
        template = json.loads(archive.read(f"{root}/RETURN_TEMPLATE.json"))
        contract = archive.read(f"{root}/CONTRACT.md").decode()
        runner = archive.read(f"{root}/runner/run_olmsmoother2_current_aex_0012_typed_bind_read_20260710.ps1").decode()
        jsx = archive.read(f"{root}/runner/ae_render_single_case.jsx").decode()
        request = json.loads(archive.read(f"{root}/request/request_manifest.json"))
        reference = json.loads(archive.read(f"{root}/request/reference_manifest.json"))
    if manifest["request_id"] != REQUEST_ID or manifest["schema"] != SCHEMA:
        return fail("request id/schema mismatch")
    if manifest["idx"] != 105 or manifest["descriptor"] != [91, 841, 1, 91, 843, 5]:
        return fail("witness identity mismatch")
    if runtime_manifest.get("kind") != "olm_runtime_trace_request_package":
        return fail("runtime package manifest kind mismatch")
    actions = runtime_manifest.get("runtime_actions") or []
    if len(actions) != 1 or actions[0].get("request_id") != REQUEST_ID or actions[0].get("request_schema") != SCHEMA:
        return fail("runtime package manifest action mismatch")
    if manifest["run_policy"] != "one_fresh_windows_run_for_bind_and_all_reads":
        return fail("same-run policy missing")
    if manifest["failure_status"] != "exact_bind_failure" or template["schema"] != SCHEMA:
        return fail("exact failure contract missing")
    if "answered_partial" in manifest["forbidden_statuses"] or "partial" in manifest["forbidden_statuses"]:
        pass
    else:
        return fail("forbidden partial statuses missing")
    if set(manifest["required_fields"]) != REQUIRED:
        return fail("required field set mismatch")
    if "Mac local witness" not in contract or "field schema evidence only" not in contract:
        return fail("Mac witness limitation missing")
    if "exact_bind_failure" not in contract or "NAS" not in contract:
        return fail("failure/transport rule missing")
    required_runner_tokens = (
        "Start-Process", "AfterFX.exe", "cdb.exe", "OLMSmoother2+0xe170",
        "OLMSmoother2+0xf270", "OLMSmoother2+0xe3a0", "OLMSmoother2+0xcce0",
        "OLMSmoother2+0x3370", "OLMSmoother2+0x3610", "S2_TYPED_BIND",
        "S2_TYPED_E170", "S2_TYPED_F270", "S2_TYPED_E3A0", "S2_TYPED_POLYGON",
        "S2_TYPED_CCE0", "S2_TYPED_WRITER", "exact_bind_failure", "answered",
    )
    if any(token not in runner for token in required_runner_tokens):
        return fail("runner is not wired for one strict fresh run")
    if "request_manifest.json" not in jsx or "importFootage" not in jsx or "comp.layers.add" not in jsx:
        return fail("proven AE fixture renderer missing")
    if request.get("cases", [{}])[0].get("id") != "legacy_case_0012_gamma5_red_blue_current_aex":
        return fail("exact case missing from request manifest")
    if request.get("input_dir") != "input" or not reference.get("cases"):
        return fail("packaged fixture manifests missing")
    if not {"request/input/case_0012_before_effects.png", "request/input/current_olm_cells.png"}.issubset(
        {name[len(root) + 1:] for name in names if name.startswith(root + "/")}
    ):
        return fail("exact case fixture input missing")
    if any(token in "\n".join(names) for token in ("/Users/", "/Volumes/", "C:/Users/")):
        return fail("machine-local absolute archive path present")
    try:
        validate_fail_closed({"status": "answered_partial", "failure": {}})
    except AssertionError:
        pass
    else:
        return fail("smoke accepted answered_partial")
    complete_trace = [
        "S2_TYPED_RUN_START run_id=run-001 case_id=legacy_case_0012_gamma5_red_blue_current_aex x=91 y=841 idx=105 descriptor=91,841,1,91,843,5",
        "S2_TYPED_BIND run_id=run-001 module=OLMSmoother2 module_base=0x1000 hook=OLMSmoother2+0x3370 binding_expression=writer_xy pointer_arithmetic=rsp+0x30",
        "S2_TYPED_E170 run_id=run-001 center_b0=0 prev_b0=1 left_b1=0 e170_c=2",
        "S2_TYPED_F270 run_id=run-001 f270_append=1 f270_source_xy=91,840 f270_weight=0.35632184",
        "S2_TYPED_E3A0 run_id=run-001 e3a0_append=1 e3a0_source_xy=91,840 e3a0_weight=0.35632184",
        "S2_TYPED_POLYGON run_id=run-001 polygon_count=1",
        "S2_TYPED_CCE0 run_id=run-001 cce0_rgba=0.99106723,0.99106723,0.99106723,0.35492450 cce0_raw=0x3f7dbb00,0x3f7dbb00,0x3eb5a000,0x3eb5a000",
        "S2_TYPED_WRITER run_id=run-001 writer_site=OLMSmoother2+0x3610 writer_rgba_u8=0,0,0,0 writer_rgba_float=0.0,0.0,0.0,0.0",
    ]
    answered = parse_trace_lines(complete_trace)
    if answered.get("status") != "answered" or answered["observations"]["f270"]["source_xy"] != [91, 840]:
        return fail("synthetic complete CDB stream did not parse to answered tuple")
    missing = parse_trace_lines(complete_trace[:-3])
    if missing.get("status") != "exact_bind_failure" or "polygon_count" not in missing.get("missing", []):
        return fail("synthetic missing-field CDB stream did not fail closed")
    validate_fail_closed({"status": "exact_bind_failure", "failure": {key: None for key in ("stage", "reason", "module", "hook", "run_id", "case_id", "pixel", "pointer_context", "last_observation")}})
    print("[OK] Smoother2 current-AEX 0012 typed bind/read package smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
