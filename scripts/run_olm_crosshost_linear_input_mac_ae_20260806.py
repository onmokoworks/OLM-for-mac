#!/usr/bin/env python3
"""Run the six-row cross-host linear-input contract in one already-open Mac AE."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "refs/reference_requests/olm_crosshost_linear_input_20260806.zip"
DEFAULT_RETURN = ROOT / "refs/returns/mac/RETURN_OLM_CROSSHOST_LINEAR_INPUT_MAC_20260806.zip"
APP = Path("/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app")
AE = APP / "Contents/MacOS/After Effects"
PLUGINS = {
    "ColorKeep": Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/ColorKeep.plugin/Contents/MacOS/ColorKeep",
    "OLMKiraKira": Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMKiraKira.plugin/Contents/MacOS/OLMKiraKira",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_extract(package: Path, target: Path) -> None:
    with zipfile.ZipFile(package) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = info.filename.replace("\\", "/")
            pure = PurePosixPath(name)
            if name.startswith("/") or any(part in ("", ".", "..") for part in pure.parts):
                raise RuntimeError(f"unsafe ZIP member: {name}")
            path = target.joinpath(*pure.parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(archive.read(info))


def ae_pids() -> list[int]:
    result = subprocess.run(["pgrep", "-f", f"^{AE}$"], capture_output=True, text=True)
    return [int(value) for value in result.stdout.split() if value.isdigit()]


def loaded(pid: int, binary: Path) -> bool:
    result = subprocess.run(["vmmap", str(pid)], capture_output=True, text=True, timeout=120)
    return result.returncode == 0 and str(binary.resolve()) in result.stdout


def wrapper(path: Path, env: dict[str, str]) -> str:
    return "\n".join(
        [f"$.setenv({json.dumps(key)},{json.dumps(value)});" for key, value in env.items()]
        + [f"$.evalFile(new File({json.dumps(str(path))}));"]
    ) + "\n"


def run(output: Path) -> dict:
    pids = ae_pids()
    if len(pids) != 1:
        raise RuntimeError(f"exactly one already-open AE process required; got {pids}")
    pid = pids[0]
    with (APP / "Contents/Info.plist").open("rb") as stream:
        if plistlib.load(stream).get("CFBundleShortVersionString") != "26.3.0":
            raise RuntimeError("AE version drift")
    for binary in PLUGINS.values():
        if not binary.is_file():
            raise RuntimeError(f"missing plugin binary: {binary}")

    with tempfile.TemporaryDirectory(prefix="olm_crosshost_linear_mac_") as tmp:
        work = Path(tmp)
        package_root = work / "package"
        safe_extract(PACKAGE, package_root)
        contract = json.loads((package_root / "BATCH_CONTRACT.json").read_text(encoding="utf-8"))
        jsx_path = package_root / "scripts/ae_render_olm_crosshost_linear_input_20260806.jsx"
        jsx = jsx_path.read_text(encoding="utf-8")
        old_poll = 'var marker=new File(go),deadline=(new Date()).getTime()+600000; while(!marker.exists&&(new Date()).getTime()<deadline) $.sleep(100); if(!marker.exists) die("continue timeout");'
        if jsx.count(old_poll) != 1:
            raise RuntimeError("JSX marker anchor drift")
        jsx = jsx.replace(old_poll, 'var marker=new File(go); if(!marker.exists) die("continue marker missing");')
        if jsx.count('try { app.quit(); } catch(_) {}') != 1:
            raise RuntimeError("JSX quit anchor drift")
        jsx = jsx.replace('try { app.quit(); } catch(_) {}', '/* shared Mac AE remains open */')
        jsx_path.write_text(jsx, encoding="utf-8")
        outputs = work / "outputs"
        rows = []
        for row in contract["acquire"]:
            binary = PLUGINS[row["plugin"]]
            row_out = outputs / row["row_id"]
            row_out.mkdir(parents=True)
            result, ready, marker = row_out / "ae_result.json", row_out / "ready.json", row_out / "continue.marker"
            marker.touch()
            launch = row_out / "wrapper.jsx"
            launch.write_text(wrapper(jsx_path, {
                "OLM_BOUNDARY_ROOT": str(package_root),
                "OLM_BOUNDARY_ROW_ID": row["row_id"],
                "OLM_BOUNDARY_ROW_OUTPUT": str(row_out),
                "OLM_BOUNDARY_RESULT": str(result),
                "OLM_BOUNDARY_READY": str(ready),
                "OLM_BOUNDARY_CONTINUE": str(marker),
                "OLM_BOUNDARY_NONCE": hashlib.sha256(f"{row['row_id']}:{time.time_ns()}".encode()).hexdigest(),
                "OLM_BOUNDARY_OUTPUT_TEMPLATE": "OLM EXR 32 Float",
            }), encoding="utf-8")
            apple = "with timeout of 1800 seconds\ntell application \"Adobe After Effects 2026\" to DoScriptFile POSIX file " + json.dumps(str(launch)) + " with override\nend timeout\n"
            call = subprocess.run(["osascript"], input=apple, text=True, capture_output=True, timeout=1800)
            if call.returncode or not result.is_file():
                raise RuntimeError(f"{row['row_id']}: AE call failed: {call.stderr}")
            ae_result = json.loads(result.read_text(encoding="utf-8"))
            if ae_result.get("status") != "ok" or ae_pids() != [pid] or not loaded(pid, binary):
                raise RuntimeError(f"{row['row_id']}: result/process/module gate")
            rendered = {}
            for branch in ("no_effect", "effect_on"):
                candidates = list(row_out.glob(f"{branch}_*.exr"))
                if len(candidates) != 1:
                    raise RuntimeError(f"{row['row_id']}/{branch}: rendered cardinality {len(candidates)}")
                target = row_out / f"{branch}.exr"
                candidates[0].replace(target)
                rendered[branch] = sha(target)
            attestation = {
                "row_id": row["row_id"], "execution_row_sha256": row["execution_row_sha256"],
                "ae_version": ae_result["ae_version"], "ae_executable_path": str(AE), "ae_executable_sha256": sha(AE),
                "ae_pid": pid, "ae_process_start_utc": None, "renderer_raw": ae_result["renderer_raw"],
                "bits_per_channel": ae_result["bits_per_channel"], "working_space_raw": None,
                "linear_blending": ae_result["linear_blending"], "plugin_path": str(binary.resolve()),
                "plugin_sha256": sha(binary), "source_sha256": row["source_sha256"],
                "source_interpretation": ae_result["source_interpretation"],
                "parameters_before": ae_result["parameters_before"], "parameters_after": ae_result["parameters_after"],
                "no_effect_sha256": rendered["no_effect"], "effect_on_sha256": rendered["effect_on"],
            }
            (row_out / "attestation.json").write_text(json.dumps(attestation, indent=2) + "\n", encoding="utf-8")
            rows.append({"row_id": row["row_id"], "status": "rendered"})
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            output.unlink()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(outputs.rglob("*")):
                if path.is_file() and path.name in ("no_effect.exr", "effect_on.exr", "attestation.json"):
                    archive.write(path, path.relative_to(work).as_posix())
    return {"status": "rendered_candidate", "return": str(output), "sha256": sha(output), "rows": rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_RETURN)
    args = parser.parse_args()
    if not args.run:
        report = {"status": "preflight_ready" if PACKAGE.is_file() and APP.is_dir() and all(p.is_file() for p in PLUGINS.values()) else "blocked", "package": str(PACKAGE), "package_sha256": sha(PACKAGE) if PACKAGE.is_file() else None, "ae_pids": ae_pids()}
    else:
        report = run(args.output.resolve())
    print(json.dumps(report, indent=2))
    return 0 if report["status"] != "blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
