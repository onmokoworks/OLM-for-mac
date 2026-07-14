#!/usr/bin/env python3
"""Verify the DG 8bpc package is a reachable liveness probe, not typed proof."""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path


PACKAGE_DIR = Path("refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_depth_control_20260713")
PACKAGE_ZIP = PACKAGE_DIR.with_suffix(".zip")
RUNNER = PACKAGE_DIR / "artifacts/run_olmdistancegradation_8bpc_depth_control_20260713.ps1"
RVAS = {"1170870", "1170c90"}


def parse_fixture(path: Path, expected_hash: str) -> bool:
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^DG8_DEPTH_SUMMARY\s+(.+)$", line)
        if not match:
            continue
        fields = dict(re.findall(r"([a-z0-9_]+)=([^\s]+)", match.group(1)))
        rows[fields.get("rva")] = fields
    if set(rows) != RVAS:
        return False
    return all(
        rows[rva].get("run_id") == "dglive-fixture"
        and rows[rva].get("ae_pid") == "4242"
        and rows[rva].get("module_base") == "0x7ff600000000"
        and rows[rva].get("aex_sha256") == expected_hash
        and rows[rva].get("hit_count", "").isdigit()
        for rva in RVAS
    ) and int(rows["1170870"]["hit_count"]) > 0 and int(rows["1170c90"]["hit_count"]) == 0


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    package_dir = root / PACKAGE_DIR
    package_zip = root / PACKAGE_ZIP
    required = {
        "README_RUNTIME_TRACE.md",
        "runtime_trace_package_manifest.json",
        "RETURN_RUNTIME_TRACE_TEMPLATE.json",
        "artifacts/run_olmdistancegradation_8bpc_depth_control_20260713.ps1",
        "scripts/ae_render_olmdistancegradation_8bpc_depth_control_queue.jsx",
        "scripts/ae_render_single_case.jsx",
        "fixtures/complete_cdb_stdout.txt",
        "fixtures/missing_rva_cdb_stdout.txt",
        "fixtures/adversarial_wrong_hash_cdb_stdout.txt",
        "fixtures/latest_ae_ready_missing_failure.json",
    }
    if not package_dir.is_dir() or not package_zip.is_file():
        print("[FAIL] liveness package directory or zip is missing")
        return 1
    files = {p.relative_to(package_dir).as_posix() for p in package_dir.rglob("*") if p.is_file()}
    if not required <= files:
        print(f"[FAIL] package missing: {sorted(required - files)}")
        return 1
    with zipfile.ZipFile(package_zip) as archive:
        names = {name for name in archive.namelist() if not name.endswith("/")}
        if names != files:
            print("[FAIL] zip/directory drift")
            return 1
        manifest = json.loads(archive.read("runtime_trace_package_manifest.json"))
        template = json.loads(archive.read("RETURN_RUNTIME_TRACE_TEMPLATE.json"))
        latest_failure = json.loads(archive.read("fixtures/latest_ae_ready_missing_failure.json"))
    accepted_aex = manifest.get("accepted_current_aex", {})
    expected_hash = str(accepted_aex.get("sha256", "")).lower()
    action = manifest["runtime_actions"][0]
    if manifest.get("submission_status") != "ready" or manifest.get("sendable") is not True or set(action["rvas"]) != RVAS:
        print("[FAIL] liveness manifest is not runnable or has the wrong RVA set")
        return 1
    if accepted_aex.get("module") != "DistanceGradation.aex" or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
        print("[FAIL] manifest does not pin one accepted current DistanceGradation.aex SHA-256")
        return 1
    if (
        "ae_pid" not in template
        or "module_base" not in template
        or template.get("project_bits_per_channel") != 8
        or template.get("expected_current_aex_sha256") != expected_hash
    ):
        print("[FAIL] return template does not bind the AE process/module/depth identity")
        return 1
    if not parse_fixture(package_dir / "fixtures/complete_cdb_stdout.txt", expected_hash):
        print("[FAIL] complete liveness fixture rejected")
        return 1
    if parse_fixture(package_dir / "fixtures/missing_rva_cdb_stdout.txt", expected_hash):
        print("[FAIL] missing-RVA liveness fixture accepted")
        return 1
    if parse_fixture(package_dir / "fixtures/adversarial_wrong_hash_cdb_stdout.txt", expected_hash):
        print("[FAIL] adversarial wrong-hash liveness fixture accepted")
        return 1
    failure = latest_failure["failure"]
    observation = failure["last_observation"]
    diagnostics = failure["runtime_diagnostics"]
    if latest_failure.get("status") != "exact_bind_failure" or failure["reason"] != "AE pause ready marker missing":
        print("[FAIL] latest ready-marker failure fixture is not fail-closed")
        return 1
    if observation.get("launch_pid") != 12708 or observation.get("launcher_exited") is not True or observation.get("candidate_afterfx") != [] or observation.get("ae_log") is not None:
        print("[FAIL] latest ready-marker failure observation drifted")
        return 1
    for key in ("launcher_exit_code", "launcher_stderr", "ae_result", "process_diagnostics"):
        if key not in observation and key not in diagnostics:
            print(f"[FAIL] latest failure omits diagnostic key {key}")
            return 1
    runner = RUNNER.read_text(encoding="utf-8")
    for needle in ("-ParseOnly", "DG8_DEPTH_HIT", "DG8_DEPTH_SUMMARY", "Get-FileHash", "DG8_DEPTH_BREAKPOINTS_ARMED"):
        if needle not in runner:
            print(f"[FAIL] liveness runner missing {needle}")
            return 1
    if "bp /1" in runner or "typed_rgba" in runner or "COMPOSE_IN" in runner or "algorithm proof" in runner.lower():
        print("[FAIL] liveness runner contains typed-boundary or algorithm-proof behavior")
        return 1
    if "hit_count=%u\\\\n" in runner:
        print("[FAIL] liveness summary uses a double-escaped CDB newline")
        return 1
    if "@`$t0" not in runner or ", @\n" in runner:
        print("[FAIL] CDB pseudo-registers are not protected from PowerShell expansion")
        return 1
    for needle in (
        "Start-Process -FilePath $AfterFxPath -ArgumentList @('-m','-r',$queue)",
        "OLM_AE_PAUSE_BEFORE_RENDER = '1'",
        "OLM_AE_READY_MARKER = $readyMarker",
        "effect_loaded=1",
        "parameters_applied=1",
        "Get-CimInstance Win32_Process",
        "SessionId",
        ".Modules | Where-Object { $_.FileName -ieq $AexPath }",
        "$expectedHash = '" + expected_hash + "'",
        "shared_expected_aex_sha256",
        "DistanceGradation.aex is not the accepted current binary",
        "loaded module hash does not match the accepted current binary",
        "ArgumentList ('-cf \"' + $cdbScript + '\" -p ' + $aePid)",
        "Set-Content -LiteralPath $continueMarker -Value 'continue'",
        "Stop-Process -Id $cdb.Id -Force",
        "if ($launchStarted) { foreach ($candidate in @(MatchingAfterFX))",
        "candidate_afterfx=@(Get-AfterFxState)",
        "$work = (Get-Item -LiteralPath $work).FullName",
        "project_bits_per_channel -ne 8",
        "AE did not render the requested 8bpc case",
        "$baseValue + 0x1170870",
        "$baseValue + 0x1170c90",
        "PF8_hit_count_gt_0",
        "PF32_hit_count_eq_0",
        "launcher_exit_code",
        "launcher_stderr",
        "ae_result",
        "process_diagnostics",
        "runtime_diagnostics",
        "Get-AfterFxState",
    ):
        if needle not in runner:
            print(f"[FAIL] depth-control runner missing {needle}")
            return 1
    if "sxe ld:DistanceGradation" in runner or "$afterFx,'-r',$queue" in runner:
        print("[FAIL] depth-control runner still launches AE as the CDB debuggee")
        return 1
    if re.search(r"while\s*\([^\r\n]*readyMarker[^\r\n]*launch\.HasExited", runner):
        print("[FAIL] ready-marker wait is incorrectly cut short by launcher PID exit")
        return 1
    ordered = (
        "Start-Process -FilePath $AfterFxPath",
        "$readyText = Get-Content -LiteralPath $readyMarker -Raw",
        ".Modules | Where-Object { $_.FileName -ieq $AexPath }",
        "Start-Process -FilePath $CdbPath",
        "if ((Test-Path -LiteralPath $trace) -and ((Get-Content -LiteralPath $trace -Raw) -match 'DG8_DEPTH_BREAKPOINTS_ARMED'))",
        "Set-Content -LiteralPath $continueMarker -Value 'continue'",
        "project_bits_per_channel -ne 8",
        "$parsed = Parse $trace",
    )
    positions = [runner.find(needle) for needle in ordered]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        print("[FAIL] normal-launch/ready/attach/arm/continue/depth/parse order regressed")
        return 1
    embedded_renderer = (package_dir / "scripts/ae_render_single_case.jsx").read_text(encoding="utf-8")
    if "referenceManifest.comp && referenceManifest.comp.bpc" not in embedded_renderer:
        print("[FAIL] embedded AE runner ignores comp.bpc and can silently inherit 32bpc")
        return 1
    readme = (package_dir / "README_RUNTIME_TRACE.md").read_text(encoding="utf-8").lower()
    if "does not" not in readme or "algorithm proof" not in readme:
        print("[FAIL] liveness README does not bound the claim")
        return 1
    print("[OK] DG 8bpc current-AEX depth-control package, reachable parser, and bounded claim")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
