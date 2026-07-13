#!/usr/bin/env python3
"""Verify the sendable DG 8bpc typed-boundary v4 package."""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path


PACKAGE_DIR = Path("refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712")
PACKAGE_ZIP = PACKAGE_DIR.with_suffix(".zip")
RUNNER_NAME = "artifacts/run_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712.ps1"
CASES = ("case_0001", "case_0015", "case_0029")
STAGES = ("FIELD_IN", "FIELD_OUT", "COMPOSE_IN", "COMPOSE_OUT", "HOST_STORE")
EXPECTED_HASH = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"


def classify_fixture(path: Path) -> tuple[bool, list[str]]:
    records: dict[str, dict[str, list[dict[str, str]]]] = {}
    depths: dict[tuple[str, str], dict[str, str]] = {}
    missing: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        depth = re.match(r"^DG8_DEPTH_SUMMARY\s+(.+)$", line)
        if depth:
            fields = dict(re.findall(r"([a-z0-9_]+)=([^\s]+)", depth.group(1)))
            depths[(fields.get("case_id", ""), fields.get("rva", ""))] = fields
            continue
        marker = re.match(r"^DG8_(FIELD_IN|FIELD_OUT|COMPOSE_IN|COMPOSE_OUT|HOST_STORE)\s+(.+)$", line)
        if not marker:
            continue
        fields = dict(re.findall(r"([a-z0-9_]+)=([^\s]+)", marker.group(2)))
        key = f"{fields.get('case_id')}|{fields.get('x')}|{fields.get('y')}"
        records.setdefault(key, {}).setdefault(marker.group(1), []).append(fields)

    all_markers: list[dict[str, str]] = []
    identity_fields = ("run_id", "ae_pid", "module_base", "aex_sha256", "project_bpc", "case_id", "x", "y", "output_addr")
    for case in CASES:
        key = f"{case}|397|281"
        row = records.get(key, {})
        for stage in STAGES:
            stage_rows = row.get(stage, [])
            if len(stage_rows) != 1:
                missing.append(f"{key}:{stage}:count")
                continue
            item = stage_rows[0]
            all_markers.append(item)
            for field in (*identity_fields, "typed_rgba"):
                if not item.get(field):
                    missing.append(f"{key}:{stage}:{field}")
            if len(item.get("typed_rgba", "").split(",")) != 4:
                missing.append(f"{key}:{stage}:typed_rgba4")
        for stage in ("FIELD_IN", "FIELD_OUT"):
            if stage in row:
                for field in ("field_base", "field_rowbytes", "field_addr", "pixel_size", "address_formula"):
                    if not row[stage][0].get(field):
                        missing.append(f"{key}:{stage}:{field}")
        if "COMPOSE_IN" in row:
            for field in ("source_base", "source_rowbytes", "source_addr", "field_green", "x_before_invert", "x_after_invert"):
                if not row["COMPOSE_IN"][0].get(field):
                    missing.append(f"{key}:COMPOSE_IN:{field}")
        if "COMPOSE_OUT" in row and not row["COMPOSE_OUT"][0].get("pre_store_rgba_float"):
            missing.append(f"{key}:COMPOSE_OUT:pre_store_rgba_float")
        if all(stage in row and len(row[stage]) == 1 for stage in STAGES):
            identities = {tuple(row[stage][0].get(field) for field in identity_fields) for stage in STAGES}
            if len(identities) != 1:
                missing.append(f"{key}:stage_identity")
        for rva, predicate in (("1170870", lambda n: n > 0), ("1170c90", lambda n: n == 0)):
            depth = depths.get((case, rva))
            if depth is None or not depth.get("hit_count", "").isdigit() or not predicate(int(depth["hit_count"])):
                missing.append(f"{key}:depth:{rva}")
            elif stage_rows := row.get("FIELD_IN"):
                anchor = stage_rows[0]
                for field in ("run_id", "ae_pid", "module_base", "aex_sha256", "project_bpc"):
                    if depth.get(field) != anchor.get(field):
                        missing.append(f"{key}:depth:{rva}:{field}")

    if all_markers:
        for field in ("run_id", "ae_pid", "module_base", "aex_sha256", "project_bpc"):
            values = {item.get(field) for item in all_markers}
            if len(values) != 1:
                missing.append(f"shared:{field}")
        if {item.get("aex_sha256") for item in all_markers} != {EXPECTED_HASH}:
            missing.append("shared:expected_hash")
        if {item.get("project_bpc") for item in all_markers} != {"8"}:
            missing.append("shared:project_bpc_8")
    return not missing, missing


def fail(message: str) -> int:
    print(f"[FAIL] {message}")
    return 1


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    package_dir = root / PACKAGE_DIR
    package_zip = root / PACKAGE_ZIP
    required = {
        "README_RUNTIME_TRACE.md",
        "runtime_trace_package_manifest.json",
        "RETURN_RUNTIME_TRACE_TEMPLATE.json",
        RUNNER_NAME,
        "scripts/ae_render_olmdistancegradation_8bpc_queue.jsx",
        "scripts/ae_render_single_case.jsx",
        "request/request_manifest.json",
        "request/reference_manifest.json",
        "fixtures/complete_cdb_stdout.txt",
        "fixtures/missing_stage_cdb_stdout.txt",
        "fixtures/identity_drift_cdb_stdout.txt",
        "fixtures/wrong_hash_cdb_stdout.txt",
        "fixtures/wrong_depth_cdb_stdout.txt",
    }
    if not package_dir.is_dir() or not package_zip.is_file():
        return fail("package directory or zip is missing")
    files = {p.relative_to(package_dir).as_posix() for p in package_dir.rglob("*") if p.is_file()}
    if not required <= files:
        return fail(f"package directory missing: {sorted(required - files)}")
    if b"/Users/onmk" in b"".join(p.read_bytes() for p in package_dir.rglob("*") if p.is_file()):
        return fail("workstation absolute path found in package")

    with zipfile.ZipFile(package_zip) as archive:
        names = {name for name in archive.namelist() if not name.endswith("/")}
        if names != files:
            return fail(f"zip/directory drift; zip-only={sorted(names-files)}, dir-only={sorted(files-names)}")
        if any(".." in Path(name).parts for name in names):
            return fail("unsafe zip member path")
        if any(info.date_time != (2026, 7, 13, 0, 0, 0) for info in archive.infolist() if not info.is_dir()):
            return fail("zip timestamps are not deterministic")
        manifest = json.loads(archive.read("runtime_trace_package_manifest.json"))
        action = manifest["runtime_actions"][0]
        if manifest.get("schema") != 4 or manifest.get("submission_status") != "ready" or manifest.get("sendable") is not True or action.get("status") != "ready":
            return fail("manifest is not sendable v4")
        accepted = manifest.get("accepted_depth_control", {})
        if accepted.get("ae_pid") != 5936 or accepted.get("module_base") != "0x7fffcd660000" or accepted.get("aex_sha256") != EXPECTED_HASH:
            return fail("accepted depth-control identity is missing")
        if accepted.get("rvas") != [{"rva": "1170870", "hit_count": 24377}, {"rva": "1170c90", "hit_count": 0}]:
            return fail("accepted PF8/PF32 depth control is missing")

    accepted, details = classify_fixture(package_dir / "fixtures/complete_cdb_stdout.txt")
    if not accepted:
        return fail(f"complete fixture rejected: {details}")
    for fixture in ("missing_stage_cdb_stdout.txt", "identity_drift_cdb_stdout.txt", "wrong_hash_cdb_stdout.txt", "wrong_depth_cdb_stdout.txt"):
        accepted, _ = classify_fixture(package_dir / "fixtures" / fixture)
        if accepted:
            return fail(f"fail-closed classifier accepted {fixture}")

    runner = (package_dir / RUNNER_NAME).read_text(encoding="utf-8")
    required_runner_terms = (
        "Get-CimInstance Win32_Process",
        "SessionId",
        "Get-FileHash",
        "effect_loaded=1",
        "parameters_applied=1",
        "DG8_DEPTH_BREAKPOINTS_ARMED",
        "DG8_DEPTH_CONTROL_CONFIRMED",
        "DG8_TYPED_BREAKPOINTS_ARMED_AFTER_DEPTH_CONTROL",
        "0x1170870",
        "0x1170c90",
        "0x117098f",
        "0x1170a09",
        "0x1170c11",
        "0x1170c40",
        "RawLogs",
        "launcher_stdout",
        "launcher_stderr",
        "combined_cdb_trace",
        "exact_bind_failure",
    )
    for term in required_runner_terms:
        if term not in runner:
            return fail(f"runner missing contract term: {term}")
    depth_arm = runner.find("bp $pf8")
    confirmed = runner.find("DG8_DEPTH_CONTROL_CONFIRMED", depth_arm)
    typed_arm = runner.find("bp $fieldOut", confirmed)
    if min(depth_arm, confirmed, typed_arm) < 0 or not depth_arm < confirmed < typed_arm:
        return fail("typed breakpoints are not armed after the depth-control confirmation")
    if "Start-Process -FilePath $CdbPath" not in runner or "ArgumentList @('-cf',$cdbScript,$afterFx" in runner:
        return fail("runner does not use desktop launch followed by CDB attach")

    queue = (package_dir / "scripts/ae_render_olmdistancegradation_8bpc_queue.jsx").read_text(encoding="utf-8")
    for term in ("OLM_DG_LIVE_REQUEST_DIR", "OLM_AE_REQUEST_DIR", "OLM_AE_READY_MARKER", "OLM_AE_CONTINUE_MARKER", "cases.length - 1"):
        if term not in queue:
            return fail(f"queue missing same-process readiness term: {term}")
    renderer = (package_dir / "scripts/ae_render_single_case.jsx").read_text(encoding="utf-8")
    for term in ('getenv("OLM_AE_PAUSE_BEFORE_RENDER") === "1"', "effect_loaded=1", "parameters_applied=1"):
        if term not in renderer:
            return fail(f"included renderer missing readiness term: {term}")

    print("[OK] DG 8bpc typed-boundary v4 is sendable and fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
