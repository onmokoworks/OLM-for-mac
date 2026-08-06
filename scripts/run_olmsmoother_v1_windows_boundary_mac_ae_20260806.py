#!/usr/bin/env python3
"""Replay the accepted Windows AE OLMSmoother v1 PF16 boundary in Mac AE."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.report_olmdistancegradation_32bpc_mac_validation_20260715 import compare

REQUEST = ROOT / "refs/reference_requests/olm_windows_ae_release_boundary_minimal_20260806.zip"
RETURN = ROOT / "refs/returns/windows/RETURN_OLM_WINDOWS_AE_RELEASE_BOUNDARY_MINIMAL_20260806.zip"
JSX = ROOT / "scripts/ae_render_olm_windows_ae_release_boundary_20260806.jsx"
REPORT = ROOT / "refs/conformance/olmsmoother_v1_windows_ae_release_boundary_mac_exact_20260806.json"
PLUGIN = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMSmoother.plugin/Contents/MacOS/OLMSmoother"
ROW_ID = "olmsmoother_v1__canonical_3__case_0001__16bpc"
EXPECTED_REQUEST_SHA256 = "6a060641dc867cbb5cb858136f6fd294fb49d274fa252cec71459bc9b20a4652"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_files(path: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    folded: set[str] = set()
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = info.filename.replace("\\", "/")
            parts = Path(name).parts
            if name.startswith("/") or ".." in parts or name.casefold() in folded:
                raise ValueError(f"unsafe or duplicate member: {name}")
            folded.add(name.casefold())
            files[name] = archive.read(info)
    return files


def write_tree(files: dict[str, bytes], target: Path) -> None:
    for name, data in files.items():
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def ae_pids() -> list[int]:
    result = subprocess.run(["pgrep", "-x", "After Effects"], capture_output=True, text=True)
    return [int(value) for value in result.stdout.split() if value.isdigit()]


def loaded_smoother(pid: int) -> list[str]:
    result = subprocess.run(["lsof", "-Fn", "-p", str(pid)], capture_output=True, text=True)
    return sorted({
        line[1:] for line in result.stdout.splitlines()
        if line.startswith("n/") and line.endswith("/OLMSmoother")
    })


def wrapper(payload: Path, values: dict[str, str]) -> str:
    lines = ["(function(){"]
    for key, value in values.items():
        lines.append(f"$.setenv({json.dumps(key)}, {json.dumps(value)});")
    lines.extend((f"$.evalFile(new File({json.dumps(str(payload))}));", "}());"))
    return "\n".join(lines) + "\n"


def invoke_ae(script: Path) -> subprocess.CompletedProcess[str]:
    apple = (
        "with timeout of 900 seconds\n"
        + 'tell application "Adobe After Effects 2026" to DoScriptFile POSIX file '
        + json.dumps(str(script)) + " with override\nend timeout\n"
    )
    return subprocess.run(["osascript"], input=apple, text=True, capture_output=True, timeout=900)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--keep-dir", type=Path)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    request_files = safe_files(REQUEST)
    return_files = safe_files(RETURN)
    contract = json.loads(request_files["BATCH_CONTRACT.json"])
    rows = [row for row in contract["acquire"] if row["row_id"] == ROW_ID]
    row = rows[0] if len(rows) == 1 else None
    expected_readback = [] if row is None else [{
        "match_name": item["match_name"],
        "display_name": item["display_name"],
        "property_index": item["property_index"],
        "property_type": item["property_type"],
        "value": item["default"],
    } for item in row["parameter_surface"]["exact_rows"]]
    attestation_name = f"outputs/{ROW_ID}/attestation.json"
    attestation = json.loads(return_files[attestation_name].decode("utf-8-sig")) if attestation_name in return_files else {}
    returned_no_effect = return_files.get(f"outputs/{ROW_ID}/no_effect.exr", b"")
    returned_effect_on = return_files.get(f"outputs/{ROW_ID}/effect_on.exr", b"")
    windows_attestation_exact = row is not None and all((
        attestation.get("row_id") == ROW_ID,
        attestation.get("execution_row_sha256") == row["execution_row_sha256"],
        attestation.get("ae_version") == "26.3x87",
        attestation.get("renderer_raw") == 1816,
        attestation.get("bits_per_channel") == 16,
        attestation.get("working_space_raw") in (None, ""),
        attestation.get("linear_blending") is False,
        attestation.get("aex_sha256") == row["aex_sha256"],
        attestation.get("source_sha256") == row["source_sha256"],
        attestation.get("parameters_before") == expected_readback,
        attestation.get("parameters_after") == expected_readback,
        attestation.get("no_effect_sha256") == hashlib.sha256(returned_no_effect).hexdigest(),
        attestation.get("effect_on_sha256") == hashlib.sha256(returned_effect_on).hexdigest(),
        isinstance(attestation.get("ae_pid"), int) and not isinstance(attestation.get("ae_pid"), bool),
        bool(attestation.get("module_base")),
        bool(attestation.get("ae_process_start_utc")),
    ))
    checks = {
        "request_sha256_exact": sha(REQUEST) == EXPECTED_REQUEST_SHA256,
        "return_exists": RETURN.is_file(),
        "jsx_exists": JSX.is_file(),
        "plugin_exists": PLUGIN.is_file(),
        "one_exact_contract_row": len(rows) == 1,
        "native_pf16_contract": row is not None and row["depth"] == 16,
        "windows_members_complete": row is not None and all(
            f"outputs/{ROW_ID}/{branch}.exr" in return_files
            for branch in ("no_effect", "effect_on")
        ),
        "windows_attestation_exact": windows_attestation_exact,
    }
    report: dict = {
        "schema": "olmsmoother-v1-windows-boundary-mac-ae-exact/1",
        "row_id": ROW_ID,
        "status": "preflight_ready" if all(checks.values()) else "blocked",
        "checks": checks,
        "request_zip": {"path": str(REQUEST.relative_to(ROOT)), "sha256": sha(REQUEST)},
        "return_zip": {"path": str(RETURN.relative_to(ROOT)), "sha256": sha(RETURN)},
        "installed_plugin": {"path": str(PLUGIN), "sha256": sha(PLUGIN) if PLUGIN.is_file() else None},
        "harness": {
            "runner": {"path": str(Path(__file__).resolve().relative_to(ROOT)), "sha256": sha(Path(__file__).resolve())},
            "jsx": {"path": str(JSX.relative_to(ROOT)), "sha256": sha(JSX)},
        },
        "claim_boundary": "AE 26.3x87, Software raw 1816, None working space, linear blending off, preserve-RGB straight-alpha smoother_v1_case0001_rgba8.png, Use Color Key=0, Color Key=white, Do Smooth Range=6, native PF16 only.",
    }
    args.report = args.report.resolve()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    if not args.run or not all(checks.values()):
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "report": str(args.report)}))
        return 0 if all(checks.values()) else 2

    pids = ae_pids()
    if len(pids) != 1:
        report["status"] = "blocked"
        report["host_error"] = f"expected one running After Effects process, got {pids}"
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return 2

    base_jsx = JSX.read_text(encoding="utf-8").replace(
        'var marker=new File(go),deadline=(new Date()).getTime()+600000; while(!marker.exists&&(new Date()).getTime()<deadline) $.sleep(100); if(!marker.exists) die("continue timeout");',
        'var marker=new File(go); if(!marker.exists) die("continue marker missing");',
    ).replace(
        'var no=render(comp,effect,false,out+"/no_effect.exr",template,cs.render_time_span_start_seconds,cs.render_time_span_duration_seconds);',
        'app.beginSuppressDialogs(); var no=render(comp,effect,false,out+"/no_effect.exr",template,cs.render_time_span_start_seconds,cs.render_time_span_duration_seconds);',
    ).replace(
        'var yes=render(comp,effect,true,out+"/effect_on.exr",template,cs.render_time_span_start_seconds,cs.render_time_span_duration_seconds);',
        'var yes=render(comp,effect,true,out+"/effect_on.exr",template,cs.render_time_span_start_seconds,cs.render_time_span_duration_seconds); app.endSuppressDialogs(false);',
    ).replace('    try { app.quit(); } catch(_) {}\n', '')

    if args.keep_dir:
        keep = args.keep_dir.resolve()
        if keep.exists():
            raise SystemExit(f"--keep-dir must not exist: {keep}")
        keep.mkdir(parents=True)
        workspace = contextlib.nullcontext(str(keep))
    else:
        workspace = tempfile.TemporaryDirectory(prefix="olmsmoother-v1-boundary-mac-")
    with workspace as temp_name:
        temp = Path(temp_name)
        package_root = temp / "package"
        write_tree(request_files, package_root)
        payload = temp / "render.jsx"
        payload.write_text(base_jsx, encoding="utf-8")
        output = temp / "mac" / ROW_ID
        output.mkdir(parents=True)
        result = output / "ae_result.json"
        ready = output / "ready.json"
        marker = output / "continue.marker"
        marker.touch()
        launch = temp / "launch_pf16.jsx"
        launch.write_text(wrapper(payload, {
            "OLM_BOUNDARY_ROOT": str(package_root),
            "OLM_BOUNDARY_ROW_ID": ROW_ID,
            "OLM_BOUNDARY_ROW_OUTPUT": str(output),
            "OLM_BOUNDARY_RESULT": str(result),
            "OLM_BOUNDARY_READY": str(ready),
            "OLM_BOUNDARY_CONTINUE": str(marker),
            "OLM_BOUNDARY_NONCE": "mac-smoother-v1-pf16",
            "OLM_BOUNDARY_OUTPUT_TEMPLATE": "OLM EXR 32 Float",
        }), encoding="utf-8")
        call = invoke_ae(launch)
        ae_result = json.loads(result.read_text(encoding="utf-8")) if result.is_file() else None
        current_pids = ae_pids()
        modules = loaded_smoother(pids[0]) if current_pids == pids else []
        branch_results = {}
        for branch in ("no_effect", "effect_on"):
            mac = output / f"{branch}_00024.exr"
            if not mac.is_file():
                mac = output / f"{branch}_00000.exr"
            win = temp / "windows" / f"{branch}.exr"
            win.parent.mkdir(parents=True, exist_ok=True)
            win.write_bytes(return_files[f"outputs/{ROW_ID}/{branch}.exr"])
            comparison = compare(mac, win) if mac.is_file() else {"equal": False, "error": "Mac EXR missing"}
            branch_results[branch] = {
                "mac_sha256": sha(mac) if mac.is_file() else None,
                "windows_sha256": sha(win),
                "raw_float32_compare": comparison,
            }
        parameter_exact = (
            ae_result is not None
            and ae_result.get("parameters_before") == expected_readback
            and ae_result.get("parameters_after") == expected_readback
        )
        exact = (
            call.returncode == 0
            and ae_result is not None and ae_result.get("status") == "ok"
            and ae_result.get("ae_version") == "26.3x87"
            and ae_result.get("renderer_raw") == 1816
            and ae_result.get("bits_per_channel") == 16
            and parameter_exact
            and current_pids == pids and modules == [str(PLUGIN.resolve())]
            and all(value["raw_float32_compare"].get("equal") is True for value in branch_results.values())
        )
        report.update({
            "status": "exact" if exact else "mismatch",
            "ae_result": ae_result,
            "osascript": {"returncode": call.returncode, "stdout": call.stdout, "stderr": call.stderr},
            "host_identity": {"ae_pids": current_pids, "loaded_smoother_modules": modules,
                              "exact": current_pids == pids and modules == [str(PLUGIN.resolve())]},
            "parameter_surface_exact": parameter_exact,
            "branches": branch_results,
            "pf16_exact_eligible": exact,
        })
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "pf16_exact_eligible": report["pf16_exact_eligible"], "report": str(args.report)}))
    return 0 if report["status"] == "exact" else 1


if __name__ == "__main__":
    raise SystemExit(main())
