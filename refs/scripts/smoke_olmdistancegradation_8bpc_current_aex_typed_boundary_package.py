#!/usr/bin/env python3
"""Verify the bounded DG 8bpc typed-boundary request package."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


PACKAGE_DIR = Path("refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712")
PACKAGE_ZIP = Path("refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712.zip")
RUNNER = PACKAGE_DIR / "artifacts/run_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712.ps1"
CASES = {"case_0001", "case_0015", "case_0029"}
STAGES = {"FIELD_IN", "FIELD_OUT", "COMPOSE_IN", "COMPOSE_OUT", "HOST_STORE"}
HASH = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


def parse_fixture(path: Path) -> bool:
    records: dict[str, dict[str, dict[str, str]]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^DG8_(FIELD_IN|FIELD_OUT|COMPOSE_IN|COMPOSE_OUT|HOST_STORE)\s+(.+)$", line)
        if not match:
            continue
        fields = dict(re.findall(r"([a-z0-9_]+)=([^\s]+)", match.group(2)))
        key = f"{fields.get('case_id')}|{fields.get('x')}|{fields.get('y')}"
        records.setdefault(key, {})[match.group(1)] = fields
    for case in CASES:
        row = records.get(f"{case}|397|281")
        if row is None or set(row) != STAGES:
            return False
        identities = {(v.get("run_id"), v.get("output_addr"), v.get("aex_sha256")) for v in row.values()}
        if len(identities) != 1 or next(iter(identities))[2] != HASH:
            return False
        if any(not v.get("typed_rgba") for v in row.values()):
            return False
    return True


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    package_dir = root / PACKAGE_DIR
    package_zip = root / PACKAGE_ZIP
    required = {
        "README_RUNTIME_TRACE.md",
        "runtime_trace_package_manifest.json",
        "RETURN_RUNTIME_TRACE_TEMPLATE.json",
        "artifacts/run_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712.ps1",
        "scripts/ae_render_olmdistancegradation_8bpc_queue.jsx",
        "scripts/ae_render_single_case.jsx",
        "request/request_manifest.json",
        "request/reference_manifest.json",
        "fixtures/complete_cdb_stdout.txt",
        "fixtures/missing_stage_cdb_stdout.txt",
    }
    if not package_dir.is_dir() or not package_zip.is_file():
        print("[FAIL] package directory or zip is missing")
        return 1
    files = {p.relative_to(package_dir).as_posix() for p in package_dir.rglob("*") if p.is_file()}
    if not required <= files:
        print(f"[FAIL] package directory missing: {sorted(required - files)}")
        return 1
    all_bytes = b"".join(p.read_bytes() for p in package_dir.rglob("*") if p.is_file())
    if b"/Users/onmk" in all_bytes:
        print("[FAIL] workstation absolute path found in package directory")
        return 1
    with zipfile.ZipFile(package_zip) as archive:
        names = {name for name in archive.namelist() if not name.endswith("/")}
        if names != files:
            print(f"[FAIL] zip/directory drift; zip-only={sorted(names-files)}, dir-only={sorted(files-names)}")
            return 1
        if any("/Users/onmk" in name or ".." in Path(name).parts for name in names):
            print("[FAIL] unsafe zip member path")
            return 1
        manifest = json.loads(archive.read("runtime_trace_package_manifest.json"))
        if manifest["kind"] != "olm_runtime_trace_request_package" or len(manifest["runtime_actions"]) != 1:
            print("[FAIL] manifest kind/action contract mismatch")
            return 1
        if manifest.get("submission_status") != "pending" or manifest.get("sendable") is not False or manifest["runtime_actions"][0].get("status") != "pending":
            print("[FAIL] typed-boundary package is not explicitly pending/non-sendable")
            return 1
    if not parse_fixture(package_dir / "fixtures/complete_cdb_stdout.txt"):
        print("[FAIL] complete fixture does not satisfy typed-boundary acceptance")
        return 1
    if parse_fixture(package_dir / "fixtures/missing_stage_cdb_stdout.txt"):
        print("[FAIL] missing-stage fixture was accepted")
        return 1
    text = RUNNER.read_text(encoding="utf-8")
    for needle in ("exact_bind_failure", "aex_sha256", "FIELD_IN", "FIELD_OUT", "COMPOSE_IN", "COMPOSE_OUT", "HOST_STORE", "answered"):
        if needle not in text:
            print(f"[FAIL] runner missing fail-closed contract term: {needle}")
            return 1
    pre_load = text.split(".logopen", 1)[0]
    if "bp " in pre_load or "bu " in pre_load:
        print("[FAIL] runner arms an AEX breakpoint before the load stop")
        return 1
    if "OLM_DG8_REQUEST_DIR" in text:
        print("[FAIL] runner uses the stale request-dir environment name")
        return 1
    queue_text = (package_dir / "scripts/ae_render_olmdistancegradation_8bpc_queue.jsx").read_text(encoding="utf-8")
    if "OLM_DG_REQUEST_DIR" not in queue_text or "OLM_DG8_WORK_ROOT" not in queue_text or "OLM_AE_REQUEST_DIR" not in queue_text:
        print("[FAIL] queue does not bind the package request root to the single-case renderer")
        return 1
    if "OLM_AE_KEEP_OPEN" not in queue_text or "cases.length - 1" not in queue_text:
        print("[FAIL] queue does not preserve one AE process across the serial cases")
        return 1
    print("[OK] DG 8bpc typed-boundary package is explicitly pending/non-sendable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
