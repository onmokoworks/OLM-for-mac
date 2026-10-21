#!/usr/bin/env python3
"""Fail-closed preflight/fresh-AE runner. This script never installs a bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
SOURCE_SHA = "36063ae68027d97169679b4b234f83ec871cdfed4f936ce6464c7a49cbc71743"
BUILD_BINARY = ROOT / "handoff/mac_plugin_builds/olmradialblur_type3_20260812/OLMRadialBlur.plugin/Contents/MacOS/OLMRadialBlur"
BUILD_SHA = "7701c3cb864ec9a05c82de68d1ab3a57a18f9a9b4f97e3b8d7b1786a016818b3"
INSTALLED_BINARY = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMRadialBlur.plugin/Contents/MacOS/OLMRadialBlur"
AE_APP = Path("/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app")
AE_EXECUTABLE = AE_APP / "Contents/MacOS/After Effects"
PAYLOAD = ROOT / "tools/emulation/olmradialblur_type3_current_install_smoke_payload_20260812.jsx"
GO_TOKEN = "RADIAL_TYPE3_INSTALL_AE_GO_20260812"
PARAMETERS = {
    "OLM RadialBlur-0001": 1, "OLM RadialBlur-0002": [4, 3],
    "OLM RadialBlur-0004": 4, "OLM RadialBlur-0028": 1,
    "OLM RadialBlur-0029": 0, "OLM RadialBlur-0008": 0,
    "OLM RadialBlur-0026": True, "OLM RadialBlur-0012": 1,
    "OLM RadialBlur-0013": 0, "OLM RadialBlur-0015": 5,
    "OLM RadialBlur-0016": 1, "OLM RadialBlur-0017": 0,
    "OLM RadialBlur-0019": 25, "OLM RadialBlur-0020": 3,
    "OLM RadialBlur-0024": 3,
}

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def running_ae() -> list[str]:
    run = subprocess.run(["/usr/bin/pgrep", "-ifl", str(AE_EXECUTABLE)], capture_output=True, text=True)
    return [line for line in run.stdout.splitlines() if line.strip()]

def command_ok(command: list[str]) -> bool:
    return subprocess.run(command, capture_output=True).returncode == 0

def architectures(path: Path) -> list[str]:
    run = subprocess.run(["/usr/bin/lipo", "-archs", str(path)], capture_output=True, text=True)
    return run.stdout.split() if run.returncode == 0 else []

def installed_bundle_count() -> int:
    media_core = INSTALLED_BINARY.parents[3]
    return len(list(media_core.glob("OLMRadialBlur.plugin"))) if media_core.is_dir() else 0

def preflight() -> dict:
    build_exists = BUILD_BINARY.is_file()
    installed_exists = INSTALLED_BINARY.is_file()
    build_bundle = BUILD_BINARY.parents[2]
    installed_bundle = INSTALLED_BINARY.parents[2]
    return {
        "source_sha256": digest(SOURCE) if SOURCE.is_file() else None,
        "source_exact": SOURCE.is_file() and digest(SOURCE) == SOURCE_SHA,
        "build_binary": str(BUILD_BINARY),
        "build_sha256": digest(BUILD_BINARY) if build_exists else None,
        "build_exact": build_exists and digest(BUILD_BINARY) == BUILD_SHA,
        "build_architectures": architectures(BUILD_BINARY) if build_exists else [],
        "build_codesign_deep_strict": build_exists and command_ok(["/usr/bin/codesign", "--verify", "--deep", "--strict", str(build_bundle)]),
        "installed_binary": str(INSTALLED_BINARY),
        "installed_sha256": digest(INSTALLED_BINARY) if installed_exists else None,
        "installed_is_prepared_build": installed_exists and digest(INSTALLED_BINARY) == BUILD_SHA,
        "installed_bundle_count": installed_bundle_count(),
        "installed_architectures": architectures(INSTALLED_BINARY) if installed_exists else [],
        "installed_codesign_deep_strict": installed_exists and command_ok(["/usr/bin/codesign", "--verify", "--deep", "--strict", str(installed_bundle)]),
        "ae_executable": str(AE_EXECUTABLE), "ae_exists": AE_EXECUTABLE.is_file(),
        "running_ae": running_ae(),
    }

def validate_result(value: dict) -> None:
    required = {"status", "ae_version", "bits", "renderer_raw", "effect_match_name",
                "plumbing_output_path", "type3", "scope"}
    if set(value) != required or value["status"] != "ok":
        raise ValueError("result schema/status")
    if value["bits"] != 32 or value["renderer_raw"] != 1816 or value["effect_match_name"] != "OLM RadialBlur":
        raise ValueError("host contract")
    if value["type3"].get("pixel_exact") is not False:
        raise ValueError("Type3 pixel claim must remain false")
    if value["type3"].get("status") not in {"live_render_plumbing_pass", "live_type3_unavailable_fail_closed", "live_type3_timeout"}:
        raise ValueError("Type3 status")
    if "plumbing" not in value["scope"] or "non-exact" not in value["scope"]:
        raise ValueError("scope")

def execute(output: Path, token: str) -> dict:
    if token != GO_TOKEN:
        raise RuntimeError("explicit GO token required")
    state = preflight()
    if not all((state["source_exact"], state["build_exact"], state["installed_is_prepared_build"], state["ae_exists"],
                state["build_architectures"] == ["x86_64", "arm64"], state["build_codesign_deep_strict"],
                state["installed_bundle_count"] == 1, state["installed_architectures"] == ["x86_64", "arm64"],
                state["installed_codesign_deep_strict"])):
        raise RuntimeError("identity preflight failed")
    if state["running_ae"]:
        raise RuntimeError("fresh-process contract: AE already running")
    output.mkdir(parents=True, exist_ok=False)
    config = {
        "ready_path": str(output / "ready.json"), "continue_path": str(output / "continue.marker"),
        "result_path": str(output / "raw_result.json"), "plumbing_output": str(output / "default_plumbing.png"),
        "type3_output": str(output / "type3_layer.png"), "noise_layer_match_name": "OLM RadialBlur-0021",
        "type3_parameters": PARAMETERS, "attempt_type3": True,
    }
    config_path = output / "runtime_config.json"
    config_path.write_text(json.dumps(config, sort_keys=True), encoding="utf-8")
    payload = PAYLOAD.read_text(encoding="utf-8")
    if payload.count("__CONFIG_PATH_JSON__") != 1:
        raise RuntimeError("payload placeholder")
    runtime = output / "runtime.jsx"
    runtime.write_text(payload.replace("__CONFIG_PATH_JSON__", json.dumps(str(config_path))), encoding="utf-8")
    process = None; apple_process = None
    try:
        process = subprocess.Popen([str(AE_EXECUTABLE)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)
        apple = ('with timeout of 1200 seconds\n'
                 'tell application "Adobe After Effects 2026" to DoScriptFile POSIX file '
                 + json.dumps(str(runtime)) + ' with override\nend timeout\n')
        apple_process = subprocess.Popen(["/usr/bin/osascript", "-e", apple], stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL, text=True)
        ready = output / "ready.json"; result_path = output / "raw_result.json"
        deadline = time.time() + 240
        while not ready.exists() and not result_path.exists() and process.poll() is None and time.time() < deadline:
            time.sleep(.2)
        if not ready.exists():
            raise RuntimeError("AE did not reach ready handshake")
        vmmap = subprocess.run(["/usr/bin/vmmap", str(process.pid)], capture_output=True, text=True)
        vmmap_path = output / "vmmap.txt"
        vmmap_path.write_text(vmmap.stdout + vmmap.stderr, encoding="utf-8")
        if vmmap.stdout.count(str(INSTALLED_BINARY)) != 4:
            raise RuntimeError("installed module exact path segment count")
        (output / "continue.marker").write_text("continue\n", encoding="utf-8")
        deadline = time.time() + 120
        while not result_path.exists() and process.poll() is None and time.time() < deadline:
            time.sleep(.2)
        plumbing = output / "default_plumbing.png"
        if result_path.exists():
            raw = json.loads(result_path.read_text(encoding="utf-8"))
        elif plumbing.is_file() and process.poll() is None:
            handshake = json.loads(ready.read_text(encoding="utf-8"))
            raw = {"status": "ok", "ae_version": handshake["ae_version"], "bits": handshake["bits"],
                   "renderer_raw": handshake["renderer_raw"], "effect_match_name": handshake["effect_match_name"],
                   "plumbing_output_path": str(plumbing),
                   "type3": {"status": "live_type3_timeout", "pixel_exact": False},
                   "scope": "fresh AE load/add/default render plumbing; Type3 non-exact timeout"}
            result_path.write_text(json.dumps(raw, sort_keys=True) + "\n", encoding="utf-8")
        else:
            raise RuntimeError("AE result missing before default render")
        validate_result(raw)
        if not plumbing.is_file(): raise RuntimeError("plumbing output missing")
        return {"raw": raw, "ae_pid": process.pid, "vmmap_sha256": digest(vmmap_path),
                "plumbing_output_sha256": digest(plumbing), "installed_sha256": digest(INSTALLED_BINARY)}
    finally:
        try:
            if apple_process is not None and apple_process.poll() is None:
                try:
                    apple_process.kill(); apple_process.wait(timeout=10)
                except (ProcessLookupError, subprocess.TimeoutExpired):
                    pass
        finally:
            if process is not None and process.poll() is None:
                try:
                    process.terminate(); process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait(timeout=10)
                except ProcessLookupError:
                    pass
            residual = running_ae()
            if residual:
                raise RuntimeError("cleanup audit: AE remains running: " + " | ".join(residual))

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--execute", action="store_true"); parser.add_argument("--go-token", default="")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.execute:
        if args.preflight or args.output is None: parser.error("--execute requires --output only")
        print(json.dumps(execute(args.output.resolve(), args.go_token), indent=2, sort_keys=True)); return 0
    if not args.preflight: parser.error("choose --preflight or --execute")
    print(json.dumps(preflight(), indent=2, sort_keys=True)); return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except Exception as error:
        print(f"FAIL_CLOSED: {error}", file=sys.stderr); raise SystemExit(2)
