#!/usr/bin/env python3
"""Fail-closed smoke/verifier for the OLMKiraKira mode3 live Gaussian package."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.package_olmkirakira_mode3_live_gaussian_20260713 import (  # noqa: E402
    AEX_SHA256,
    AEX_SIZE,
    CASE_ID,
    OUTPUT_ZIP,
    OVERRIDES,
    PACKAGE_STEM,
    REQUEST_ID,
    SCHEMA,
    SUPPORT_DIR,
    package_manifest,
    reference_and_case,
    request_manifest,
    return_template,
    runtime_manifest,
)


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def case_params(case: dict[str, Any]) -> dict[str, Any]:
    return {row["name"]: row["value"] for row in case["effects"][0]["params"] if row.get("name")}


def expected_members() -> set[str]:
    prefix = PACKAGE_STEM + "/"
    return {
        prefix + "README.md",
        prefix + "RETURN_RUNTIME_TRACE_TEMPLATE.json",
        prefix + "ae_jsx_ready_preflight.jsx",
        prefix + "case/ae_render_single_case.jsx",
        prefix + "case/input/case_03_before_effects.png",
        prefix + "case/reference_manifest.json",
        prefix + "case/request_manifest.json",
        prefix + "manifest.json",
        prefix + "mode3_live_gaussian.cdb.in",
        prefix + "run_olmkirakira_mode3_live_gaussian_20260713.ps1",
        prefix + "runtime_trace_package_manifest.json",
    }


def verify_manifest_contracts(
    manifest: dict[str, Any],
    runtime: dict[str, Any],
    template: dict[str, Any],
    request: dict[str, Any],
    case: dict[str, Any],
) -> None:
    expect(manifest == package_manifest(case), "support manifest drifted from generator contract")
    expect(runtime == runtime_manifest(), "runtime trace manifest drifted from generator contract")
    expect(template == return_template(), "return template drifted from generator contract")
    expect(request == request_manifest(case), "request manifest drifted from generator contract")

    params = case_params(case)
    expect(manifest["request_id"] == REQUEST_ID, "request_id mismatch")
    expect(manifest["schema"] == SCHEMA, "schema mismatch")
    expect(manifest["case_id"] == CASE_ID, "case_id mismatch")
    expect(manifest["case_selection"]["manifest_blur_mode"] == 3, "manifest blur mode mismatch")
    expect(params["Blur Mode"] == 3, "reference manifest case blur mode is not 3")
    expect(manifest["parameter_overrides"]["match_name"] == OVERRIDES, "override map mismatch")
    expect(manifest["parameter_overrides"]["expected"] == {
        "Vertical Length": 5,
        "Horizontal Length": 0,
        "Diagonal Length": 0,
        "Diagonal 2 length": 0,
    }, "override expectation mismatch")
    expect(manifest["aex_pin"]["sha256"] == AEX_SHA256, "AEX sha mismatch")
    expect(manifest["aex_pin"]["size"] == AEX_SIZE, "AEX size mismatch")
    expect(manifest["rva"] == {
        "wrapper": "0x1272ec0",
        "create": "0x1266730",
        "getKernel": "0x12754a0",
        "getKernelReturn": "0x126685c",
    }, "RVA map mismatch")
    expect(manifest["capture"]["first_getKernel"] == {"ecx": 21, "xmm1": 2.5, "r8": 5}, "first-kernel contract mismatch")
    expect(manifest["capture"]["words"] == 21, "word-count contract mismatch")
    expect(manifest["preflight"]["script"] == "ae_jsx_ready_preflight.jsx", "preflight script contract mismatch")
    expect("no AEX" in manifest["preflight"]["scope"], "preflight scope must forbid an AEX claim")

    expect(request["cases"] == [{
        "id": CASE_ID,
        "before_effects_frame": "case_03_before_effects.png",
        "frame": "case_03.png",
    }], "request case payload mismatch")
    expect(template["run"]["module"] == "OLMKiraKira.aex", "return template module mismatch")
    expect(template["binding"] == {
        "wrapper_rva": "0x1272ec0",
        "create_rva": "0x1266730",
        "getKernel_rva": "0x12754a0",
        "getKernelReturn_rva": "0x126685c",
        "wrapper": None,
        "create": None,
        "getKernel": None,
        "getKernelReturn": None,
    }, "return template binding placeholders mismatch")
    expect(template["case"]["blur_mode_manifest"] == 3, "return template blur mode mismatch")
    expect(template["case"]["overrides_match_name"] == OVERRIDES, "return template override mismatch")
    expect(template["observation"]["raw_words_u32"] == [None] * 21, "return template raw-word placeholders mismatch")
    expect(template["observation"]["raw_bytes"] == 84, "return template raw-byte count mismatch")


def verify_zip(package: Path, support_dir: Path, runner_text: str, cdb_text: str) -> None:
    members = expected_members()
    with zipfile.ZipFile(package) as archive:
        names = set(archive.namelist())
        expect(names == members, f"zip members mismatch: missing={sorted(members - names)} extra={sorted(names - members)}")
        expect(
            archive.read(f"{PACKAGE_STEM}/run_olmkirakira_mode3_live_gaussian_20260713.ps1").decode("utf-8") == runner_text,
            "packed runner differs from support runner",
        )
        expect(
            archive.read(f"{PACKAGE_STEM}/mode3_live_gaussian.cdb.in").decode("utf-8") == cdb_text,
            "packed CDB template differs from support template",
        )
        for name in members:
            rel = name.removeprefix(PACKAGE_STEM + "/")
            expect(archive.read(name) == (support_dir / rel).read_bytes(), f"packed member differs from support artifact: {rel}")


def verify_ps1_fail_closed(runner_text: str, manifest: dict[str, Any]) -> None:
    marker_requirements = {
        "AE_JSX_PREFLIGHT_READY": "minimal AfterFX -r JSX did not emit ready marker",
        "AE_READY": "full case JSX did not emit ready after minimal JSX preflight passed",
        "MODULE": "Marker 'KK_MODULE'",
        "BREAKPOINTS_READY": "KK_BREAKPOINTS_READY",
        "KK_WRAPPER": "Marker 'KK_WRAPPER'",
        "KK_CREATE": "Marker 'KK_CREATE'",
        "KK_KERNEL_ENTRY": "Marker 'KK_KERNEL_ENTRY'",
        "KK_KERNEL_RETURN": "Marker 'KK_KERNEL_RETURN'",
    }
    for marker in manifest["required_markers"]:
        token = marker_requirements.get(marker)
        expect(token is not None and token in runner_text, f"runner missing required-marker handling for {marker}")

    for token in (
        "Finish 'exact_bind_failure'",
        "required live markers or exact first-kernel fields missing",
        "[void]$missing.Add('kernel_ecx_21')",
        "[void]$missing.Add('kernel_r8_5')",
        "[void]$missing.Add('kernel_xmm1_2.5')",
        "[void]$missing.Add('word_count_21')",
        "[void]$missing.Add('raw_words_file')",
        "[void]$missing.Add('raw_words_size_84')",
        "[void]$missing.Add('same_run_identity')",
        "[void]$missing.Add('case_identity')",
        "hash-pinned AEX not loaded at ready marker",
        "absolute base+RVA breakpoints not armed",
        "CDB artifact path contains whitespace",
        "no-space JSX launch path invariant failed",
        "size or SHA256 mismatch",
        "After Effects must be fully closed before this run",
        "SkipPowerShell51Relay",
        "interactive desktop, not SSH session 0",
        "[IO.Path]::IsPathRooted($WorkRoot)",
        "all cross-process paths must be absolute",
        "Get-CimInstance Win32_Process",
        "ExecutablePath",
        "SessionId",
        "Get-AfterFxProcessState",
        "Wait-ForAfterFxMarker",
        "Wait-ForAfterFxExit",
        "New-ProcessDiagnostics",
        "process_diagnostics",
        "observed_pids",
        "ae_jsx_ready_preflight.jsx",
        "$preflightArgs=('-m -r \"' + $preflightLaunch + '\"')",
        "-ArgumentList $preflightArgs",
        "$aeArgs=('-m -r \"' + $jsxLaunch + '\"')",
        "-ArgumentList $aeArgs",
        "full case JSX did not emit ready after minimal JSX preflight passed",
        "argument_string=$aeArgs",
        "cdb_trace.log",
        "cdb_stdout.txt",
        "minimal JSX wrote ready but AfterFX path/session candidate did not exit after app.quit",
        "AfterFX ready marker was emitted but no live AfterFX process matched executable path and session",
    ):
        expect(token in runner_text, f"runner token missing: {token}")

    expect("$ids.Count -ne 1" in runner_text, "runner does not fail closed on multi-run identity")
    expect("if($missing.Count){Finish 'exact_bind_failure'" in runner_text, "runner does not fail closed on missing markers")
    expect("$u32=for($i=0;$i -lt 21;$i++)" in runner_text, "runner does not decode 21 returned words")
    expect("preflight=@{status='ready'" in runner_text, "answered return omits successful preflight provenance")
    expect("-ArgumentList @('-m','-r'" not in runner_text, "PowerShell 5.1 may drop split Start-Process arguments")
    expect("while((Get-Date)-lt $deadline -and !(Test-Path -LiteralPath $preflightReady) -and !$preflight.HasExited)" not in runner_text, "preflight wait still terminates on launcher exit")
    expect("-p '+$ae.Id" not in runner_text, "CDB attach still uses launcher PID instead of tracked AE PID")


def verify_preflight_jsx(preflight_text: str) -> None:
    for token in (
        'OLM_AE_PREFLIGHT_READY_MARKER',
        'AE_JSX_PREFLIGHT_READY',
        'marker.open("w")',
        'app.quit()',
    ):
        expect(token in preflight_text, f"preflight JSX token missing: {token}")
    for forbidden in ("request_manifest", "OLMKiraKira", "CDB", "renderQueue", "saveFrameToPng"):
        expect(forbidden not in preflight_text, f"preflight JSX exceeds launch/ready scope: {forbidden}")


def verify_cdb_template(cdb_text: str) -> None:
    for token in (
        "__TRACE__",
        "__RUN_ID__",
        "__BASE__",
        "__WRAPPER__",
        "__CREATE__",
        "__KERNEL__",
        "__RETURN__",
        "__WORDS__",
        ".echo KK_MODULE run_id=__RUN_ID__ module=OLMKiraKira.aex module_base=__BASE__",
        "bp __WRAPPER__",
        "bp __CREATE__",
        "bp __KERNEL__",
        "bp __RETURN__",
        "word_count=21",
        ".writemem",
        "__WORDS__",
        "@$t3 @$t3+0x53",
        "source=cv_Mat_data_after_return",
        ".echo KK_BREAKPOINTS_READY",
    ):
        expect(token in cdb_text, f"CDB token missing: {token}")

    expect("0x180" not in cdb_text, "CDB template should keep live-base placeholders instead of hard-coded module addresses")
    expect(".logopen /t" not in cdb_text, "timestamped CDB log path breaks exact runner lookup")
    expect("bp poi(@rsp)" not in cdb_text, "dynamic nested return breakpoint is not parse-safe")


def verify_runner_path_guards(runner_text: str) -> None:
    expect(
        "if(($cdb,$trace,$words)|Where-Object{$_ -match '\\s'})" in runner_text,
        "runner must reject whitespace in every path interpolated into CDB commands",
    )


def verify_regeneration(generator: Path, committed_zip: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="kk_mode3_pkg_") as tmp:
        tmp_root = Path(tmp)
        tmp_support = tmp_root / "support"
        tmp_zip = tmp_root / "package.zip"
        proc = subprocess.run(
            [sys.executable, str(generator), "--support-dir", str(tmp_support), "--output", str(tmp_zip)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        expect(proc.returncode == 0, f"generator failed:\n{proc.stdout}")
        expect(tmp_zip.is_file() and zipfile.is_zipfile(tmp_zip), "generator did not materialize a valid zip")
        with zipfile.ZipFile(committed_zip) as lhs, zipfile.ZipFile(tmp_zip) as rhs:
            left_names = lhs.namelist()
            right_names = rhs.namelist()
            expect(left_names == right_names, "regenerated zip member order/content set mismatch")
            for name in left_names:
                expect(lhs.read(name) == rhs.read(name), f"regenerated zip member differs: {name}")


def main() -> int:
    generator = ROOT / "scripts/package_olmkirakira_mode3_live_gaussian_20260713.py"
    support_dir = ROOT / SUPPORT_DIR
    package = ROOT / OUTPUT_ZIP

    try:
        expect(support_dir.is_dir(), f"support dir missing: {support_dir}")
        expect(package.is_file() and zipfile.is_zipfile(package), f"package missing: {package}")

        reference, case = reference_and_case(ROOT)
        support_manifest = load_json(support_dir / "manifest.json")
        support_runtime = load_json(support_dir / "runtime_trace_package_manifest.json")
        support_template = load_json(support_dir / "RETURN_RUNTIME_TRACE_TEMPLATE.json")
        support_request = load_json(support_dir / "case/request_manifest.json")
        support_reference = load_json(support_dir / "case/reference_manifest.json")
        runner_text = (support_dir / "run_olmkirakira_mode3_live_gaussian_20260713.ps1").read_text(encoding="utf-8")
        cdb_text = (support_dir / "mode3_live_gaussian.cdb.in").read_text(encoding="utf-8")
        preflight_text = (support_dir / "ae_jsx_ready_preflight.jsx").read_text(encoding="utf-8")

        expect(reference == support_reference, "packaged support reference manifest drifted from source reference")
        verify_manifest_contracts(support_manifest, support_runtime, support_template, support_request, case)
        verify_zip(package, support_dir, runner_text, cdb_text)
        verify_ps1_fail_closed(runner_text, support_manifest)
        verify_preflight_jsx(preflight_text)
        verify_cdb_template(cdb_text)
        verify_runner_path_guards(runner_text)
        verify_regeneration(generator, package)
    except AssertionError as exc:
        return fail(str(exc))

    print("[OK] OLMKiraKira mode3 live Gaussian package smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
