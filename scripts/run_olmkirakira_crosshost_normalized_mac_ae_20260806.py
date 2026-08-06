#!/usr/bin/env python3
"""Replay Kira on Mac using each corrected Windows no-effect frame as input."""

from __future__ import annotations

import argparse
import hashlib
import json
import plistlib
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "handoffs/windows_batch/olm_windows_all_plugins_reference_campaign_20260731_r5/tools"
sys.path.insert(0, str(TOOLS)); sys.path.insert(0, str(ROOT / "scripts"))
from compare_float_exr import compare  # noqa: E402

PACKAGE = ROOT / "refs/reference_requests/olm_crosshost_linear_input_20260806.zip"
WINDOWS = ROOT / "refs/returns/windows/RETURN_OLM_CROSSHOST_LINEAR_INPUT_CORRECTED_20260806.zip"
REPORT = ROOT / "refs/conformance/olmkirakira_crosshost_normalized_mac_ae_20260806.json"
APP = Path("/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app")
AE = APP / "Contents/MacOS/After Effects"
PLUGIN = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMKiraKira.plugin/Contents/MacOS/OLMKiraKira"


def sha_bytes(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def sha(path: Path) -> str: return sha_bytes(path.read_bytes())


def members(path: Path) -> dict[str, bytes]:
    result, folded = {}, set()
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir(): continue
            name = info.filename.replace("\\", "/"); pure = PurePosixPath(name)
            if name.startswith("/") or any(part in ("", ".", "..") for part in pure.parts) or name.casefold() in folded:
                raise RuntimeError(f"unsafe/duplicate member {name}")
            folded.add(name.casefold()); result[name] = archive.read(info)
    return result


def write_tree(files: dict[str, bytes], root: Path) -> None:
    for name, data in files.items():
        path = root.joinpath(*PurePosixPath(name).parts); path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)


def pids() -> list[int]:
    result = subprocess.run(["pgrep", "-f", f"^{AE}$"], capture_output=True, text=True)
    return [int(value) for value in result.stdout.split() if value.isdigit()]


def wait(predicate, seconds: int, label: str):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = predicate()
        if value: return value
        time.sleep(.2)
    raise RuntimeError(f"timeout {label}")


def mapped(pid: int) -> bool:
    result = subprocess.run(["vmmap", str(pid)], capture_output=True, text=True, timeout=120)
    return result.returncode == 0 and str(PLUGIN.resolve()) in result.stdout


def wrapper(payload: Path, env: dict[str, str]) -> str:
    return "\n".join([f"$.setenv({json.dumps(k)},{json.dumps(v)});" for k, v in env.items()] + [f"$.evalFile(new File({json.dumps(str(payload))}));"]) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--depth", type=int, choices=(8, 16, 32), action="append")
    parser.add_argument("--keep-dir", type=Path)
    parser.add_argument("--report", type=Path, default=REPORT)
    parser.add_argument("--original-source", action="store_true", help="keep the package fixture as Mac input")
    args = parser.parse_args()
    if pids(): raise SystemExit(f"fresh AE required; close {pids()}")
    with (APP / "Contents/Info.plist").open("rb") as stream:
        if plistlib.load(stream).get("CFBundleShortVersionString") != "26.3.0": raise SystemExit("AE version")
    if not PLUGIN.is_file(): raise SystemExit("Kira plugin missing")
    package_files, windows_files = members(PACKAGE), members(WINDOWS)
    contract = json.loads(package_files["BATCH_CONTRACT.json"])
    rows = sorted((row for row in contract["acquire"] if row["plugin"] == "OLMKiraKira" and (not args.depth or row["depth"] in args.depth)), key=lambda row: row["depth"])
    report = {
        "kind": "olmkirakira_crosshost_normalized_mac_ae",
        "status": "error", "package_sha256": sha(PACKAGE), "windows_return_sha256": sha(WINDOWS),
        "plugin_sha256": sha(PLUGIN), "normalization": "package fixture remains Mac source" if args.original_source else "Windows corrected no_effect EXR becomes Mac source at the same project depth",
        "rows": [],
    }
    with tempfile.TemporaryDirectory(prefix="olm_kira_normalized_") as tmp:
        root = Path(tmp); package_root = root / "package"; write_tree(package_files, package_root)
        for row in rows:
            row_id, depth = row["row_id"], row["depth"]
            source_name = f"inputs/windows_no_effect_{depth}bpc.exr"
            if not args.original_source:
                source_data = windows_files[f"outputs/{row_id}/no_effect.exr"]
                (package_root / source_name).write_bytes(source_data)
                row["source_member"] = source_name; row["source_sha256"] = sha_bytes(source_data)
        (package_root / "BATCH_CONTRACT.json").write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
        jsx_path = package_root / "scripts/ae_render_olm_crosshost_linear_input_20260806.jsx"
        jsx = jsx_path.read_text(encoding="utf-8")
        poll = 'var marker=new File(go),deadline=(new Date()).getTime()+600000; while(!marker.exists&&(new Date()).getTime()<deadline) $.sleep(100); if(!marker.exists) die("continue timeout");'
        jsx = jsx.replace(poll, 'var marker=new File(go); if(!marker.exists) die("continue marker missing");')
        jsx = jsx.replace('var no=render(comp,effect,false,out+"/no_effect.exr"', 'app.beginSuppressDialogs(); var no=render(comp,effect,false,out+"/no_effect.exr"')
        jsx = jsx.replace('var after=snapshot(effect,row.parameter_writes);', 'app.endSuppressDialogs(false); var after=snapshot(effect,row.parameter_writes);')
        jsx = jsx.replace('try { app.quit(); } catch(_) {}', '/* orchestrator owns fresh host */')
        jsx_path.write_text(jsx, encoding="utf-8")
        subprocess.run(["open", "-na", str(APP)], check=True)
        pid = wait(lambda: pids()[0] if len(pids()) == 1 else None, 120, "fresh AE")
        try:
            for row in rows:
                row_id, depth = row["row_id"], row["depth"]
                out = root / f"row_{depth}"; out.mkdir(); result = out / "result.json"; ready = out / "ready.json"; marker = out / "continue.marker"; marker.touch()
                launch = out / "launch.jsx"; launch.write_text(wrapper(jsx_path, {
                    "OLM_BOUNDARY_ROOT": str(package_root), "OLM_BOUNDARY_ROW_ID": row_id,
                    "OLM_BOUNDARY_ROW_OUTPUT": str(out), "OLM_BOUNDARY_RESULT": str(result),
                    "OLM_BOUNDARY_READY": str(ready), "OLM_BOUNDARY_CONTINUE": str(marker),
                    "OLM_BOUNDARY_NONCE": f"kira-normalized-{depth}-{time.time_ns()}", "OLM_BOUNDARY_OUTPUT_TEMPLATE": "OLM EXR 32 Float",
                }), encoding="utf-8")
                apple = "with timeout of 1800 seconds\ntell application \"Adobe After Effects 2026\" to DoScriptFile POSIX file " + json.dumps(str(launch)) + " with override\nend timeout\n"
                call = subprocess.run(["osascript"], input=apple, text=True, capture_output=True, timeout=1800)
                payload = json.loads(result.read_text(encoding="utf-8")) if result.is_file() else None
                if call.returncode or not payload or payload.get("status") != "ok" or pids() != [pid] or not mapped(pid):
                    raise RuntimeError(f"row {depth} host/result gate: {call.stderr} {payload}")
                normalized = {}
                for branch in ("no_effect", "effect_on"):
                    mac_candidates = list(out.glob(f"{branch}_*.exr"));
                    if len(mac_candidates) != 1: raise RuntimeError(f"row {depth}/{branch} output cardinality")
                    win = root / f"win_{depth}_{branch}.exr"; win.write_bytes(windows_files[f"outputs/{row_id}/{branch}.exr"])
                    comparison = compare(win, mac_candidates[0])
                    normalized[branch] = {"mac_sha256": sha(mac_candidates[0]), "windows_sha256": sha(win), **comparison, "exact": comparison["mismatched_values"] == 0}
                    if args.keep_dir:
                        args.keep_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(mac_candidates[0], args.keep_dir / f"{depth}bpc_{branch}_mac.exr")
                        shutil.copy2(win, args.keep_dir / f"{depth}bpc_{branch}_windows.exr")
                report["rows"].append({"row_id": row_id, "depth": depth, "ae_pid": pid, "source_sha256": row["source_sha256"], "source_interpretation": payload["source_interpretation"], "branches": normalized, "status": "exact" if all(item["exact"] for item in normalized.values()) else "mismatch"})
        finally:
            subprocess.run(["osascript", "-e", 'tell application "Adobe After Effects 2026" to quit saving no'], capture_output=True, text=True, timeout=120)
            wait(lambda: True if not pids() else None, 120, "AE exit")
    report["status"] = "exact" if len(report["rows"]) == len(rows) and all(row["status"] == "exact" for row in report["rows"]) else "mismatch"
    report["claim_boundary"] = "Kira representative Mode4 PF8/PF16/PF32, same numeric input proven by Windows-control-to-Mac-control equality; raw effect equality only where exact."
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "rows": [{"depth": r["depth"], "status": r["status"], "branches": r["branches"]} for r in report["rows"]]}, indent=2))
    return 0 if report["status"] == "exact" else 1


if __name__ == "__main__": raise SystemExit(main())
