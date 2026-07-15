#!/usr/bin/env python3
"""Smoke the direct three-case DG 8bpc residual witness package."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "scripts/package_olmdistancegradation_8bpc_current_aex_typed_witness_20260716.py"
PACKAGE = ROOT / "refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_three_case_residuals_20260716"
ZIP = PACKAGE.with_suffix(".zip")
RUNNER = PACKAGE / "artifacts/run_olmdistancegradation_8bpc_three_case_residuals_20260716.ps1"
HASH = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
REQUEST_ID = "olmdistancegradation_8bpc_current_aex_typed_witness_three_case_residuals_20260716"
STAGES = ("ENTRY_FIELD_ADDR_SNAPSHOT", "FIELD_READ_INPUT", "SOURCE_READ", "COMPOSE_PRE_U8_SCALE", "U8_PRE_STORE", "POST_STORE")
OBSOLETE_STAGES = {"FIELD_IN", "FIELD_OUT", "COMPOSE_IN", "COMPOSE_OUT", "HOST_STORE"}
TARGETS = {
    "case_0001": {"chain": (0, 0), "residual": (17, 0), "mode": "derived", "mac": "57,0,0,57", "windows": "56,0,0,56"},
    "case_0015": {"chain": (780, 495), "residual": (780, 495), "mode": "direct", "mac": "0,0,0,10", "windows": "10,0,0,10"},
    "case_0029": {"chain": (987, 496), "residual": (987, 496), "mode": "direct", "mac": "7,0,60,64", "windows": "7,0,63,67"},
}


def parse_fields(line: str) -> dict[str, str]:
    return dict(re.findall(r"([a-z0-9_]+)=([^\s]+)", line))


def classify(path: Path) -> bool:
    stages: dict[tuple[str, str, str, str], list[dict[str, str]]] = {}
    bounds: dict[str, list[dict[str, str]]] = {}
    residuals: dict[str, list[dict[str, str]]] = {}
    depths: dict[tuple[str, str], list[dict[str, str]]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        marker = re.match(r"^DG8_([A-Z0-9_]+)\s+", line)
        if not marker:
            continue
        kind = marker.group(1)
        row = parse_fields(line)
        case = row.get("case_id", "")
        if kind in OBSOLETE_STAGES:
            return False
        if kind in STAGES:
            stages.setdefault((case, row.get("x", ""), row.get("y", ""), kind), []).append(row)
        elif kind == "OUTPUT_ADDR_BOUND":
            bounds.setdefault(case, []).append(row)
        elif kind == "RESIDUAL_DATA_STORE":
            residuals.setdefault(case, []).append(row)
        elif kind == "DEPTH_SUMMARY":
            depths.setdefault((case, row.get("rva", "")), []).append(row)
    identities = set()
    pids = set()
    for case, target in TARGETS.items():
        chain_rows = []
        for stage in STAGES:
            rows = stages.get((case, str(target["chain"][0]), str(target["chain"][1]), stage), [])
            if len(rows) != 1:
                return False
            row = rows[0]
            if row.get("request_id") != REQUEST_ID or not row.get("run_id") or not row.get("ae_pid") or not row.get("module_base") or row.get("aex_sha256") != HASH or row.get("renderer") != "Software" or row.get("project_bpc") != "8" or row.get("case_id") != case or row.get("x") != str(target["chain"][0]) or row.get("y") != str(target["chain"][1]) or not row.get("output_addr") or not row.get("typed_rgba"):
                return False
            chain_rows.append(row)
            identities.add((row.get("request_id"), row.get("run_id"), row.get("aex_sha256"), row.get("renderer"), row.get("project_bpc")))
            pids.add(row.get("ae_pid"))
        if len({(row.get("ae_pid"), row.get("module_base"), row.get("output_addr")) for row in chain_rows}) != 1:
            return False
        if len(bounds.get(case, [])) != 1 or len(residuals.get(case, [])) != 1:
            return False
        bound = bounds[case][0]
        residual = residuals[case][0]
        if bound.get("mode") != target["mode"] or (bound.get("chain_x"), bound.get("chain_y")) != tuple(map(str, target["chain"])) or (bound.get("residual_x"), bound.get("residual_y")) != tuple(map(str, target["residual"])):
            return False
        required_residual = ("request_id", "run_id", "ae_pid", "module_base", "aex_sha256", "renderer", "project_bpc", "case_id", "x", "y", "output_addr", "store_addr", "anchor_output_addr", "residual_output_addr", "expected_rgba_mac", "expected_rgba_windows")
        if any(not residual.get(field) for field in required_residual):
            return False
        anchor = chain_rows[0]
        if (residual.get("request_id"), residual.get("run_id"), residual.get("ae_pid"), residual.get("module_base"), residual.get("aex_sha256"), residual.get("renderer"), residual.get("project_bpc"), residual.get("case_id")) != (REQUEST_ID, anchor.get("run_id"), anchor.get("ae_pid"), anchor.get("module_base"), HASH, "Software", "8", case):
            return False
        if (residual.get("x"), residual.get("y")) != tuple(map(str, target["residual"])) or residual.get("expected_rgba_mac") != target["mac"] or residual.get("expected_rgba_windows") != target["windows"] or residual.get("output_addr") != bound.get("residual_output_addr") or residual.get("store_addr") != bound.get("residual_output_addr") or residual.get("anchor_output_addr") != bound.get("anchor_output_addr") or residual.get("residual_output_addr") != bound.get("residual_output_addr"):
            return False
        if target["mode"] == "derived":
            try:
                if int(bound["residual_output_addr"], 16) != int(bound["anchor_output_addr"], 16) + 68:
                    return False
            except (KeyError, ValueError):
                return False
            if chain_rows[0]["output_addr"] != bound.get("anchor_output_addr"):
                return False
        elif chain_rows[0]["output_addr"] != bound.get("residual_output_addr"):
            return False
        for rva, predicate in (("1170870", lambda n: n > 0), ("1170c90", lambda n: n == 0)):
            rows = depths.get((case, rva), [])
            if len(rows) != 1 or any(rows[0].get(field) != anchor.get(field) for field in ("request_id", "run_id", "ae_pid", "module_base", "aex_sha256", "renderer", "project_bpc", "case_id")) or rows[0].get("rva") != rva:
                return False
            try:
                if not predicate(int(rows[0]["hit_count"])):
                    return False
            except (KeyError, ValueError):
                return False
    return len(identities) == 1 and len(pids) == 3


def windows_ast_parse(path: Path) -> str:
    script = (
        "$text=[Console]::In.ReadToEnd();$tokens=$null;$errors=$null;"
        "[System.Management.Automation.Language.Parser]::ParseInput($text,[ref]$tokens,[ref]$errors)|Out-Null;"
        "if($errors.Count){$errors|ForEach-Object{$_.ToString()};exit 1};"
        'Write-Output "[OK] Windows PowerShell 5.1 AST parse"'
    )
    pwsh = shutil.which("pwsh")
    if pwsh:
        result = subprocess.run([pwsh, "-NoProfile", "-Command", script], input=path.read_text(encoding="utf-8"), text=True, capture_output=True, check=True)
        return result.stdout.strip()
    return "[SKIP] pwsh unavailable; Windows PowerShell 5.1 AST parse not run"

def main() -> int:
    canonical = subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, text=True, capture_output=True, check=True)
    report = json.loads(canonical.stdout)
    assert Path(report["zip"]).resolve() == ZIP.resolve()
    assert report["sha256"] == hashlib.sha256(ZIP.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix="olmdg8_three_case_smoke_") as raw:
        second = Path(raw) / "second.zip"
        second_report = json.loads(subprocess.run([sys.executable, str(GENERATOR), "--output", str(second)], cwd=ROOT, text=True, capture_output=True, check=True).stdout)
        assert second_report["sha256"] == report["sha256"]
    with zipfile.ZipFile(ZIP) as archive:
        names = {name for name in archive.namelist() if not name.endswith("/")}
        disk_names = {path.relative_to(PACKAGE).as_posix() for path in PACKAGE.rglob("*") if path.is_file()}
        assert names == disk_names
        manifest = json.loads(archive.read("runtime_trace_package_manifest.json"))
        assert manifest["request_id"] == REQUEST_ID and manifest["schema"] == 5
        assert manifest["exactness_claim"] == "forbidden" and manifest["renderer"] == "Software" and manifest["project_bits_per_channel"] == 8
        assert {row["case_id"] for row in manifest["cases"]} == set(TARGETS)
        assert manifest["process_contract"] == {"fresh_process_per_case": True, "shared_request_id": True, "shared_run_id": True}
        request = json.loads(archive.read("request/request_manifest.json"))
        assert [row["id"] for row in request["cases"]] == list(TARGETS)
        assert all(info.date_time == (2026, 7, 16, 0, 0, 0) for info in archive.infolist() if not info.is_dir())
    runner = RUNNER.read_text(encoding="utf-8")
    for term in ("('{0}:{1}' -f $key,$field)", "DG8_RESIDUAL_DATA_STORE", "DG8_OUTPUT_ADDR_BOUND", "residual_output_addr_not_anchor_plus_68", "Test-RawLogsComplete", "gpuAccelType=SOFTWARE", "renderer=Software", "@`$t10", "@`$t11", "poi(@rsp+0xe0)", ".if (@`$t12==0)", "r @`$t12=1", "store_addr=%p anchor_output_addr=%p residual_output_addr=%p", "pre_cvtt_lane_1_3_2_0=%f,%f,%f,%f", "xmm5_scale_pending=1", "0x1170c20", "0x1170c29", "0x1170c30", "0x1170c37", "0x1170c3e", "0x1170c40", HASH):
        assert term in runner, term
    assert "$key:" not in runner
    depth_lines = [
        line for line in runner.splitlines()
        if line.lstrip().startswith(("$depthSummary0 =", "$depthSummary1 ="))
    ]
    assert len(depth_lines) == 2
    assert all("@`$t" not in line for line in depth_lines)
    assert all('.printf \\\\\\\"DG8_DEPTH_SUMMARY' in line for line in depth_lines)
    for old in ("DG8_FIELD_IN", "DG8_FIELD_OUT", "DG8_COMPOSE_IN", "DG8_COMPOSE_OUT", "DG8_HOST_STORE"):
        assert old not in runner, old
    for jsx in (PACKAGE / "scripts").glob("*.jsx"):
        subprocess.run(["node", "--check"], input=jsx.read_text(encoding="utf-8"), cwd=ROOT, check=True, text=True, capture_output=True)
    ast_output = windows_ast_parse(RUNNER)
    assert "[OK] Windows PowerShell 5.1 AST parse" in ast_output or "[SKIP] pwsh unavailable" in ast_output
    assert classify(PACKAGE / "fixtures/complete_cdb_stdout.txt")
    for name in ("missing_stage_cdb_stdout.txt", "identity_drift_cdb_stdout.txt", "wrong_hash_cdb_stdout.txt", "wrong_depth_cdb_stdout.txt", "bad_derived_address_cdb_stdout.txt"):
        assert not classify(PACKAGE / "fixtures" / name), name
    with tempfile.TemporaryDirectory(prefix="olmdg8_parser_fail_closed_") as raw:
        complete_lines = (PACKAGE / "fixtures/complete_cdb_stdout.txt").read_text(encoding="utf-8").splitlines()
        obsolete = Path(raw) / "obsolete.txt"
        obsolete.write_text("\n".join(complete_lines + ["DG8_FIELD_IN request_id=obsolete case_id=case_0001 x=0 y=0\n"]), encoding="utf-8")
        assert not classify(obsolete)
        missing_residual = Path(raw) / "missing_residual.txt"
        missing_residual.write_text("\n".join(line for line in complete_lines if not line.startswith("DG8_RESIDUAL_DATA_STORE ") or "case_id=case_0015" not in line) + "\n", encoding="utf-8")
        assert not classify(missing_residual)
        duplicate_residual = Path(raw) / "duplicate_residual.txt"
        residual_line = next(line for line in complete_lines if line.startswith("DG8_RESIDUAL_DATA_STORE ") and "case_id=case_0015" in line)
        duplicate_residual.write_text("\n".join(complete_lines + [residual_line]) + "\n", encoding="utf-8")
        assert not classify(duplicate_residual)
    print(f"[OK] DG 8bpc direct three-case package smoke; {ast_output}; sha256={report['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
