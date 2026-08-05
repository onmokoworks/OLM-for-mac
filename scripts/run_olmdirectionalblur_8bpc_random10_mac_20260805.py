#!/usr/bin/env python3
"""Hash-bound Mac AE runner for the DirectionalBlur random-10 8-bpc set."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUEST_ID = "ae_pixel_olm_final_random10_olm_directionalblur_20260629"
REQUEST = ROOT / "handoff/ae_pixel_validation_20260618/requests" / REQUEST_ID
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMDirectionalBlur.plugin/Contents/MacOS/OLMDirectionalBlur"
EXPECTED_INSTALLED_SHA256 = "61dca84682741365643ba6d5dfbc457f586f8733e5a37203b122b2555a95206d"
RUNNER = ROOT / "scripts/run_ae_validation_batch.py"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ae_pids() -> list[int]:
    result = subprocess.run(["pgrep", "-x", "After Effects"],
                            capture_output=True, text=True, check=False)
    return [int(line) for line in result.stdout.splitlines() if line.strip().isdigit()]


def loaded_directionalblur(pid: int) -> list[str]:
    result = subprocess.run(["lsof", "-Fn", "-p", str(pid)],
                            capture_output=True, text=True, check=False)
    return [line[1:] for line in result.stdout.splitlines()
            if line.startswith("n/") and
            line.endswith("/Contents/MacOS/OLMDirectionalBlur")]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true",
                        help="run the AE batch after the module/hash preflight")
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()

    installed_hash = sha256(INSTALLED) if INSTALLED.is_file() else None
    pids = ae_pids()
    modules = {str(pid): loaded_directionalblur(pid) for pid in pids}
    installed_resolved = str(INSTALLED.resolve()) if INSTALLED.exists() else None
    bound = [
        {"pid": pid, "path": path}
        for pid in pids for path in modules[str(pid)]
        if installed_resolved and str(Path(path).resolve()) == installed_resolved
    ]
    checks = {
        "request_manifest_present": (REQUEST / "request_manifest.json").is_file(),
        "reference_manifest_present": (REQUEST / "reference_manifest.json").is_file(),
        "installed_hash": installed_hash,
        "installed_hash_matches": installed_hash == EXPECTED_INSTALLED_SHA256,
        "single_ae_process": len(pids) == 1,
        "loaded_module_paths": modules,
        "loaded_module_is_installed_bundle": len(bound) == 1,
    }
    ready = all((checks["request_manifest_present"],
                 checks["reference_manifest_present"],
                 checks["installed_hash_matches"],
                 checks["single_ae_process"],
                 checks["loaded_module_is_installed_bundle"]))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_root = (args.output_root or
                   ROOT / f"refs/reports/dblur_random10_mac_20260805_{timestamp}").resolve()
    report = {
        "schema": 1,
        "kind": "olmdirectionalblur_8bpc_random10_mac_runner_20260805",
        "status": "ready" if ready else "restart_required",
        "request_id": REQUEST_ID,
        "expected_installed_sha256": EXPECTED_INSTALLED_SHA256,
        "checks": checks,
        "run_requested": args.run,
        "run_executed": False,
        "claim_boundary": {"mac_ae_rendered": False,
                           "windows_ae_pixel_exact": False},
    }
    output_root.mkdir(parents=True, exist_ok=True)
    report_path = output_root / "runner_report.json"
    if not ready:
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "report": str(report_path),
                          "loaded": modules, "installed_hash": installed_hash}))
        return 2
    if not args.run:
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "ready", "report": str(report_path),
                          "bound": bound}))
        return 0

    results = output_root / "results"
    command = [
        sys.executable, str(RUNNER), "--request-id", REQUEST_ID,
        "--results-base", str(results), "--app-name", "Adobe After Effects 2026",
        "--timeout", "3600",
    ]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    report["run_executed"] = True
    report["command"] = command
    report["returncode"] = completed.returncode
    report["stdout"] = completed.stdout
    report["stderr"] = completed.stderr
    post_modules = {str(pid): loaded_directionalblur(pid) for pid in ae_pids()}
    report["post_run_loaded_module_paths"] = post_modules
    report["status"] = "rendered" if completed.returncode == 0 else "render_failed"
    report["claim_boundary"]["mac_ae_rendered"] = completed.returncode == 0
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="")
    print(json.dumps({"status": report["status"], "report": str(report_path)}))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
