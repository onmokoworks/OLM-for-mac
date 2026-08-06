#!/usr/bin/env python3
"""Replay the accepted Windows AE KiraKira boundary rows in Mac AE.

The runner consumes the hash-bound minimal request and its accepted return.
Without ``--run`` it only verifies those inputs.  With ``--run`` it renders the
same template, source, parameters, Software renderer and PF8/PF16/PF32 rows in
one already-running AE 26.3 process, then compares raw FLOAT32 EXR words.
"""
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
REQUEST = ROOT / "handoffs/windows_batch/olm_windows_ae_release_boundary_minimal_20260806.zip"
RETURN = ROOT / "refs/returns/windows/RETURN_OLM_WINDOWS_AE_RELEASE_BOUNDARY_MINIMAL_20260806.zip"
JSX = ROOT / "scripts/ae_render_olm_windows_ae_release_boundary_20260806.jsx"
REPORT = ROOT / "refs/conformance/olmkirakira_windows_ae_release_boundary_mac_exact_20260806.json"
PLUGIN = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMKiraKira.plugin/Contents/MacOS/OLMKiraKira"
CASE = "kk_mapped_bm4_mm1_hi_r5_orange_opaque"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_files(path: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = info.filename.replace("\\", "/")
            parts = Path(name).parts
            if name.startswith("/") or ".." in parts:
                raise ValueError(f"unsafe member: {name}")
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


def loaded_kira(pid: int) -> list[str]:
    result = subprocess.run(["lsof", "-Fn", "-p", str(pid)], capture_output=True, text=True)
    return sorted({line[1:] for line in result.stdout.splitlines() if line.startswith("n/") and line.endswith("/OLMKiraKira")})


def wrapper(payload: Path, values: dict[str, str]) -> str:
    lines = ["(function(){"]
    for key, value in values.items():
        lines.append(f"$.setenv({json.dumps(key)}, {json.dumps(value)});")
    lines.append(f"$.evalFile(new File({json.dumps(str(payload))}));")
    lines.append("}());")
    return "\n".join(lines) + "\n"


def invoke_ae(script: Path) -> subprocess.CompletedProcess[str]:
    apple = (
        "with timeout of 900 seconds\n"
        + 'tell application "Adobe After Effects 2026" to DoScriptFile POSIX file '
        + json.dumps(str(script))
        + " with override\nend timeout\n"
    )
    return subprocess.run(["osascript"], input=apple, text=True, capture_output=True, timeout=900)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--depth", type=int, choices=(8, 16, 32), action="append")
    parser.add_argument("--keep-dir", type=Path)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    request_files = safe_files(REQUEST)
    return_files = safe_files(RETURN)
    contract = json.loads(request_files["BATCH_CONTRACT.json"])
    rows = [row for row in contract["acquire"] if row["plugin"] == "OLMKiraKira" and row["case_id"] == CASE]
    selected_rows = [row for row in rows if not args.depth or row["depth"] in args.depth]
    checks = {
        "request_exists": REQUEST.is_file(),
        "return_exists": RETURN.is_file(),
        "jsx_exists": JSX.is_file(),
        "plugin_exists": PLUGIN.is_file(),
        "depths_exact": sorted(row["depth"] for row in rows) == [8, 16, 32],
        "rows_unique": len({row["row_id"] for row in rows}) == 3,
        "windows_members_complete": all(
            f"outputs/{row['row_id']}/{branch}.exr" in return_files
            for row in rows for branch in ("no_effect", "effect_on")
        ),
    }
    report: dict = {
        "schema": "olmkirakira-windows-boundary-mac-ae-exact/1",
        "case_id": CASE,
        "status": "preflight_ready" if all(checks.values()) else "blocked",
        "checks": checks,
        "request_zip": {"path": str(REQUEST.relative_to(ROOT)), "sha256": sha(REQUEST)},
        "return_zip": {"path": str(RETURN.relative_to(ROOT)), "sha256": sha(RETURN)},
        "installed_plugin": {"path": str(PLUGIN), "sha256": sha(PLUGIN) if PLUGIN.is_file() else None},
        "rows": [],
        "claim_boundary": "AE 26.3x87, Software renderer raw 1816, None working space, linear blending off, preserve-RGB straight-alpha opaque_cells_rgba8.png, case kk_mapped_bm4_mm1_hi_r5_orange_opaque, PF8/PF16/PF32 only.",
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

    base_jsx = JSX.read_text(encoding="utf-8")
    # Keep the host available for all three rows and remove the Windows
    # launcher handshake; every row still opens a fresh project and effect.
    base_jsx = base_jsx.replace(
        'var marker=new File(go),deadline=(new Date()).getTime()+600000; while(!marker.exists&&(new Date()).getTime()<deadline) $.sleep(100); if(!marker.exists) die("continue timeout");',
        'var marker=new File(go); if(!marker.exists) die("continue marker missing");',
    ).replace(
        'var no=render(comp,effect,false,out+"/no_effect.exr",template,cs.render_time_span_start_seconds,cs.render_time_span_duration_seconds);',
        'app.beginSuppressDialogs(); var no=render(comp,effect,false,out+"/no_effect.exr",template,cs.render_time_span_start_seconds,cs.render_time_span_duration_seconds);',
    ).replace(
        'var yes=render(comp,effect,true,out+"/effect_on.exr",template,cs.render_time_span_start_seconds,cs.render_time_span_duration_seconds);',
        'var yes=render(comp,effect,true,out+"/effect_on.exr",template,cs.render_time_span_start_seconds,cs.render_time_span_duration_seconds); app.endSuppressDialogs(false);',
    ).replace(
        'summary={status:"ok",row_id:rowId,',
        'summary={status:"ok",input_interpretation:{alpha_mode:Number(footage[0].mainSource.alphaMode),premul_color:footage[0].mainSource.premulColor,preserve_rgb:footage[0].mainSource.preserveRGB,color_profile_name:footage[0].mainSource.colorProfileName},row_id:rowId,',
    ).replace('    try { app.quit(); } catch(_) {}\n', '')

    if args.keep_dir:
        keep = args.keep_dir.resolve()
        if keep.exists():
            raise SystemExit(f"--keep-dir must not exist: {keep}")
        keep.mkdir(parents=True)
        workspace = contextlib.nullcontext(str(keep))
    else:
        workspace = tempfile.TemporaryDirectory(prefix="olmkira-boundary-mac-")
    with workspace as temp_name:
        temp = Path(temp_name)
        package_root = temp / "package"
        write_tree(request_files, package_root)
        payload = temp / "render.jsx"
        payload.write_text(base_jsx, encoding="utf-8")
        for row in sorted(selected_rows, key=lambda value: value["depth"]):
            row_id = row["row_id"]
            out = temp / "mac" / row_id
            out.mkdir(parents=True)
            result = out / "ae_result.json"
            ready = out / "ready.json"
            marker = out / "continue.marker"
            marker.touch()
            launch = temp / f"launch_{row['depth']}.jsx"
            launch.write_text(wrapper(payload, {
                "OLM_BOUNDARY_ROOT": str(package_root),
                "OLM_BOUNDARY_ROW_ID": row_id,
                "OLM_BOUNDARY_ROW_OUTPUT": str(out),
                "OLM_BOUNDARY_RESULT": str(result),
                "OLM_BOUNDARY_READY": str(ready),
                "OLM_BOUNDARY_CONTINUE": str(marker),
                "OLM_BOUNDARY_NONCE": f"mac-kira-{row['depth']}",
                "OLM_BOUNDARY_OUTPUT_TEMPLATE": "OLM EXR 32 Float",
            }), encoding="utf-8")
            call = invoke_ae(launch)
            ae_result = json.loads(result.read_text(encoding="utf-8")) if result.is_file() else None
            current_pids = ae_pids()
            modules = loaded_kira(pids[0]) if current_pids == pids else []
            branch_results = {}
            for branch in ("no_effect", "effect_on"):
                mac = out / f"{branch}_00024.exr"
                if not mac.is_file():
                    mac = out / f"{branch}_00000.exr"
                win = temp / "windows" / row_id / f"{branch}.exr"
                win.parent.mkdir(parents=True, exist_ok=True)
                win.write_bytes(return_files[f"outputs/{row_id}/{branch}.exr"])
                comparison = compare(mac, win) if mac.is_file() else {"equal": False, "error": "Mac EXR missing"}
                branch_results[branch] = {
                    "mac_sha256": sha(mac) if mac.is_file() else None,
                    "windows_sha256": sha(win),
                    "raw_float32_compare": comparison,
                }
            exact = (
                call.returncode == 0
                and ae_result is not None and ae_result.get("status") == "ok"
                and current_pids == pids and modules == [str(PLUGIN.resolve())]
                and all(value["raw_float32_compare"].get("equal") is True for value in branch_results.values())
            )
            report["rows"].append({
                "row_id": row_id,
                "depth": row["depth"],
                "status": "exact" if exact else "mismatch",
                "ae_result": ae_result,
                "osascript": {"returncode": call.returncode, "stdout": call.stdout, "stderr": call.stderr},
                "host_identity": {"ae_pids": current_pids, "loaded_kira_modules": modules, "exact": current_pids == pids and modules == [str(PLUGIN.resolve())]},
                "branches": branch_results,
            })
    report["status"] = "exact" if len(report["rows"]) == len(selected_rows) and all(row["status"] == "exact" for row in report["rows"]) else "mismatch"
    report["exact_depths"] = [row["depth"] for row in report["rows"] if row["status"] == "exact"]
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "exact_depths": report["exact_depths"], "report": str(args.report)}))
    return 0 if report["status"] == "exact" else 1


if __name__ == "__main__":
    raise SystemExit(main())
