#!/usr/bin/env python3
"""Fail-closed identity gate for the ten installed OLM Universal bundles.

Exit 0 means the installed bundle identities are exact and the running AE process
started after the installation campaign. Exit 2 means the bundles are exact but
AE is not running or still needs a user-managed restart. This does not claim any
render result.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MEDIA_CORE = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore"
IDENTITY_MANIFEST = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
PLUGIN_NAMES = {
    "OLMBlur", "ColorKeep", "OLMColorKey", "OLMDirectionalBlur",
    "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur",
    "OLMSmoother", "OLMSmoother2", "OLMToonDilate",
}


def load_identity_manifest() -> tuple[datetime, dict[str, str]]:
    payload = json.loads(IDENTITY_MANIFEST.read_text(encoding="utf-8"))
    if payload.get("schema") != "olm.installed-identity-manifest/1":
        raise ValueError("installed identity manifest schema mismatch")
    rows = payload.get("plugins")
    if not isinstance(rows, list) or len(rows) != 10:
        raise ValueError("installed identity manifest must contain ten plugins")
    expected = {row["plugin"]: row["sha256"] for row in rows}
    if set(expected) != PLUGIN_NAMES or any(
        not isinstance(value, str)
        or len(value) != 64
        or any(char not in "0123456789abcdef" for char in value)
        for value in expected.values()
    ):
        raise ValueError("installed identity manifest identities invalid")
    return datetime.fromisoformat(payload["installed_after"]), expected


INSTALLED_AFTER, EXPECTED = load_identity_manifest()


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True)


def ae_processes() -> list[dict[str, object]]:
    found: list[dict[str, object]] = []
    result = run("pgrep", "-x", "After Effects")
    for raw_pid in result.stdout.split():
        details = run("ps", "-p", raw_pid, "-o", "lstart=,command=")
        text = details.stdout.strip()
        if not text:
            continue
        start_text = text[:24]
        started = datetime.strptime(start_text, "%a %b %d %H:%M:%S %Y").astimezone()
        found.append({"pid": int(raw_pid), "started": started.isoformat(), "command": text[25:]})
    return found


def main() -> int:
    bundles: list[dict[str, object]] = []
    exact = True
    for name, expected_hash in EXPECTED.items():
        matches = list(MEDIA_CORE.rglob(f"{name}.plugin"))
        row: dict[str, object] = {"name": name, "bundle_count": len(matches)}
        if len(matches) != 1:
            exact = False
            bundles.append(row)
            continue
        bundle = matches[0]
        executables = list((bundle / "Contents/MacOS").iterdir())
        if len(executables) != 1:
            row["executable_count"] = len(executables)
            exact = False
            bundles.append(row)
            continue
        executable = executables[0]
        actual_hash = hashlib.sha256(executable.read_bytes()).hexdigest()
        archs = run("lipo", "-archs", str(executable)).stdout.split()
        signature = run("codesign", "--verify", "--deep", "--strict", str(bundle))
        row.update(
            path=str(bundle),
            sha256=actual_hash,
            sha256_exact=actual_hash == expected_hash,
            architectures=archs,
            universal_exact=set(archs) == {"arm64", "x86_64"},
            codesign_exact=signature.returncode == 0,
        )
        exact &= bool(row["sha256_exact"] and row["universal_exact"] and row["codesign_exact"])
        bundles.append(row)

    processes = ae_processes()
    restarted = bool(processes) and all(
        datetime.fromisoformat(str(process["started"])) > INSTALLED_AFTER for process in processes
    )
    if not exact:
        status = "installed_identity_mismatch"
    elif not processes:
        status = "ae_not_running"
    elif restarted:
        status = "ready_for_hash_bound_host_runners"
    else:
        status = "restart_required"
    report = {
        "status": status,
        "claim_boundary": "installed bundle identity and AE restart age only; no plugin load or render claim",
        "installed_after": INSTALLED_AFTER.isoformat(),
        "bundles": bundles,
        "after_effects": processes,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if not exact:
        return 1
    return 0 if restarted else 2


if __name__ == "__main__":
    raise SystemExit(main())
