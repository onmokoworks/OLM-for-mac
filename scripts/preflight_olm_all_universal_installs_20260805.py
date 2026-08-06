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


MEDIA_CORE = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore"
INSTALLED_AFTER = datetime.fromisoformat("2026-08-05T19:55:00+09:00")
EXPECTED = {
    "OLMBlur": "dd64362e6071cfd93e92f3a4853782752aeb023c54671773bfedb0c496e8afc7",
    "ColorKeep": "ccc89781fa547450acc3053cb77bff8d6983cd8c6835866c87449e7a64117cce",
    "OLMColorKey": "34fd47cd04c6665f75a84ffb0d2bb01390823e50d2224059917043cd45350464",
    "OLMDirectionalBlur": "6a89dd4d9bca3f5b3c7af7782627d1b7b7bb6b0c45afe83945d056f1db7519f0",
    "OLMDistanceGradation": "656537d052f67a9e7eb4d4ba2c6f5c890fe34e3d2c47069bcfba01854d96055e",
    "OLMKiraKira": "cd97c6f328bf6a4adbe001662f35c12af405f89a2374046f185f68673df96719",
    "OLMRadialBlur": "2e079e3c168666c2f3509f8d4c90ab107301880bce43f538cf4e16bcb8047732",
    "OLMSmoother": "44b199789d086b4f52354dd76fb3a3b107180323221718938d8d8580884028c0",
    "OLMSmoother2": "fe782f344dcaf8865b778198b0faeb8cecd525062a83f38aca8dc1db74442c34",
    "OLMToonDilate": "7d2c24d8ad0f7436ee7035e0d926a2abaac1a74bc9305a4223f76230c1fc5537",
}


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
        matches = list(MEDIA_CORE.glob(f"{name}.plugin"))
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
