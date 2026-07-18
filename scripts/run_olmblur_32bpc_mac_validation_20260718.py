#!/usr/bin/env python3
"""Fail-closed launcher for the OLMBlur 32bpc Mac AE candidate lane.

The existing 20260715 runner owns the JSX/render contract. This dated wrapper
adds a current-plugin provenance record and refuses to render unless exactly
one After Effects process is already running.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY_RUNNER = ROOT / "scripts/run_olmblur_32bpc_mac_validation_20260715.py"
REQUEST = ROOT / "refs/mac_validation_requests/olmblur_32bpc_mac_validation_repeat1_20260718.json"
INPUT = ROOT / "refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMBlur/case_0001_before_effects.png"
DEFAULT_PLUGIN = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMBlur.plugin"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def process_ids() -> list[int]:
    result = subprocess.run(["pgrep", "-x", "After Effects"], text=True, capture_output=True, check=False)
    return [int(value) for value in result.stdout.split() if value.isdigit()]


def write_provenance(path: Path, plugin: Path, status: str, blocker: str | None = None) -> None:
    binary = plugin / "Contents/MacOS/OLMBlur"
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    data = {
        "kind": "olmblur_32bpc_mac_validation_provenance",
        "schema_version": 1,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": status,
        "ae_exact_claim": False,
        "blocker": blocker,
        "request": {"path": str(REQUEST.relative_to(ROOT)), "sha256": sha256(REQUEST)},
        "input": {"path": str(INPUT.relative_to(ROOT)), "sha256": sha256(INPUT)},
        "contract": request["ae_contract"],
        "plugin": {
            "bundle_path": str(plugin.resolve()),
            "binary_path": str(binary.resolve()),
            "binary_sha256": sha256(binary),
        },
        "source_build": {
            "project": "mac/OLMBlur/Mac/OLMBlur.xcodeproj",
            "configuration": "Debug",
            "command": "xcodebuild -project mac/OLMBlur/Mac/OLMBlur.xcodeproj -configuration Debug build CODE_SIGNING_ALLOWED=NO",
        },
        "runner": {
            "path": "scripts/run_olmblur_32bpc_mac_validation_20260718.py",
            "delegates_to": str(LEGACY_RUNNER.relative_to(ROOT)),
            "requires_exactly_one_preexisting_ae_process": True,
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin-path", type=Path, default=DEFAULT_PLUGIN)
    parser.add_argument("--support-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--result-json", type=Path, required=True)
    parser.add_argument("--provenance-json", type=Path, required=True)
    args = parser.parse_args()

    plugin = args.plugin_path.resolve()
    binary = plugin / "Contents/MacOS/OLMBlur"
    if plugin.name != "OLMBlur.plugin" or not plugin.is_dir() or not binary.is_file():
        print("[FAIL_CLOSED] current OLMBlur.plugin or Contents/MacOS/OLMBlur is missing")
        return 2
    if not REQUEST.is_file() or not INPUT.is_file():
        print("[FAIL_CLOSED] pinned request or input fixture is missing")
        return 2

    pids = process_ids()
    if len(pids) != 1:
        blocker = f"expected exactly one pre-existing After Effects process; found {pids!r}"
        write_provenance(args.provenance_json, plugin, "blocked_preflight", blocker)
        print(f"[FAIL_CLOSED] {blocker}")
        print(f"[PROVENANCE] {args.provenance_json}")
        return 3

    cmd = [
        sys.executable,
        str(LEGACY_RUNNER),
        "--plugin-path", str(plugin),
        "--request", str(REQUEST),
        "--support-dir", str(args.support_dir),
        "--output-dir", str(args.output_dir),
        "--result-json", str(args.result_json),
    ]
    result = subprocess.run(cmd, text=True, check=False)
    if result.returncode != 0:
        write_provenance(args.provenance_json, plugin, "blocked_or_failed_render", f"delegated runner exit {result.returncode}")
        return result.returncode
    write_provenance(args.provenance_json, plugin, "candidate_return_verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
