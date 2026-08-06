#!/usr/bin/env python3
"""Accept one stable, signed Universal ten-plugin install into the identity manifest.

This is intentionally a separate mutation command. Normal preflight never learns
new hashes. Acceptance requires AE to be stopped and every installed executable
to byte-match the corresponding current build product.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MEDIA_CORE = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore"
DEFAULT_MANIFEST = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
PLUGINS = (
    "OLMBlur", "ColorKeep", "OLMColorKey", "OLMDirectionalBlur",
    "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur",
    "OLMSmoother", "OLMSmoother2", "OLMToonDilate",
)


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ae_pids() -> list[int]:
    proc = run("pgrep", "-x", "After Effects")
    return [int(value) for value in proc.stdout.split() if value.isdigit()]


def collect(configuration: str, media_core: Path = MEDIA_CORE) -> list[dict[str, Any]]:
    failures: list[str] = []
    rows: list[dict[str, Any]] = []
    for name in PLUGINS:
        installed_matches = sorted(media_core.rglob(f"{name}.plugin"))
        installed_bundle = installed_matches[0] if len(installed_matches) == 1 else media_core / f"{name}.plugin"
        installed_binary = installed_bundle / "Contents/MacOS" / name
        source_bundle = ROOT / "mac" / name / "Mac/build" / configuration / f"{name}.plugin"
        source_binary = source_bundle / "Contents/MacOS" / name
        row: dict[str, Any] = {
            "plugin": name,
            "installed_bundle": str(installed_bundle),
            "installed_bundle_count": len(installed_matches),
            "source_bundle": source_bundle.relative_to(ROOT).as_posix(),
        }
        if len(installed_matches) != 1:
            failures.append(f"{name}:installed_bundle_count={len(installed_matches)}")
        if not installed_binary.is_file():
            failures.append(f"{name}:installed_binary_missing")
        if not source_binary.is_file():
            failures.append(f"{name}:source_binary_missing")
        if len(installed_matches) != 1 or not installed_binary.is_file() or not source_binary.is_file():
            rows.append(row)
            continue
        installed_hash = sha256(installed_binary)
        source_hash = sha256(source_binary)
        archs = run("lipo", "-archs", str(installed_binary)).stdout.split()
        signature = run("codesign", "--verify", "--deep", "--strict", str(installed_bundle))
        row.update({
            "sha256": installed_hash,
            "source_sha256": source_hash,
            "source_installed_exact": source_hash == installed_hash,
            "architectures": archs,
            "universal_exact": set(archs) == {"arm64", "x86_64"},
            "codesign_exact": signature.returncode == 0,
        })
        if source_hash != installed_hash:
            failures.append(f"{name}:source_installed_mismatch")
        if set(archs) != {"arm64", "x86_64"}:
            failures.append(f"{name}:not_universal")
        if signature.returncode != 0:
            failures.append(f"{name}:codesign_invalid")
        rows.append(row)
    if failures:
        raise ValueError(",".join(failures))
    return rows


def stable_collect(configuration: str, settle_seconds: float) -> list[dict[str, Any]]:
    first = collect(configuration)
    if settle_seconds:
        time.sleep(settle_seconds)
    second = collect(configuration)
    first_identity = [(row["plugin"], row["sha256"], row["source_sha256"]) for row in first]
    second_identity = [(row["plugin"], row["sha256"], row["source_sha256"]) for row in second]
    if first_identity != second_identity:
        raise ValueError("bundle_identity_changed_during_acceptance")
    return second


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--configuration", default="Debug")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--settle-seconds", type=float, default=2.0)
    args = parser.parse_args()
    pids = ae_pids()
    if pids:
        print(json.dumps({"status": "refused", "reason": "after_effects_running", "pids": pids}, sort_keys=True))
        return 2
    try:
        rows = stable_collect(args.configuration, max(0.0, args.settle_seconds))
    except ValueError as exc:
        print(json.dumps({"status": "refused", "reason": str(exc)}, sort_keys=True))
        return 3
    pids = ae_pids()
    if pids:
        print(json.dumps({"status": "refused", "reason": "after_effects_started_during_acceptance", "pids": pids}, sort_keys=True))
        return 2
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "schema": "olm.installed-identity-manifest/1",
        "accepted_at": now,
        "installed_after": now,
        "configuration": args.configuration,
        "claim_boundary": "Exact installed executable identity, arm64+x86_64 architectures, valid strict code signature, and byte identity with the named local build product. No AE load, UI, or render claim.",
        "acceptance_requirements": {
            "after_effects_processes": 0,
            "stable_consecutive_collections": 2,
            "source_installed_exact": True,
            "universal_exact": True,
            "codesign_exact": True
        },
        "plugins": rows,
    }
    output = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "accepted", "manifest": str(output), "plugins": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
