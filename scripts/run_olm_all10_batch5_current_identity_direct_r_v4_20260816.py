#!/usr/bin/env python3
"""Fail-closed Batch5 fresh-AE startup-script smoke for all ten OLM plug-ins.

The accepted installed-identity manifest is verified before launch.  One new
AE process loads, applies, and renders all ten effects.  It is launched once
as ``After Effects -r <nonce-bound-wrapper.jsx>``; this avoids the unreliable
AppleScript ``DoScriptFile`` dispatch that failed before the payload ran.
While the project is open, this runner persists one vmmap and binds every exact
installed executable path to that PID.  This is host-plumbing evidence only,
never a pixel-exact or Windows-equivalence claim.
"""

from __future__ import annotations

import argparse
import atexit
import errno
import hashlib
import json
import os
import plistlib
import re
import secrets
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNNER = Path(__file__).resolve()
PAYLOAD = ROOT / "scripts/ae_host_all10_batch5_current_identity_live_v3_20260815.jsx"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
APP = Path("/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app")
EXECUTABLE = APP / "Contents/MacOS/After Effects"
MEDIA_CORE = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore"
EXPECTED_PLUGINS = (
    "OLMBlur",
    "ColorKeep",
    "OLMColorKey",
    "OLMDirectionalBlur",
    "OLMDistanceGradation",
    "OLMKiraKira",
    "OLMRadialBlur",
    "OLMSmoother",
    "OLMSmoother2",
    "OLMToonDilate",
)
EXPECTED_AE_VERSION = "26.3x87"
EXPECTED_RENDERER_RAW = 1816
ENABLED_HOST_FRAME_PLUGINS = {"OLMBlur", "OLMDirectionalBlur"}
CLAIM_BOUNDARY = "Batch5 installed host load/add/enable-state and exact mapping for all ten; generic effect-enabled host-frame render only for OLMBlur and OLMDirectionalBlur. The other eight bounded effects are disabled before generic saveFrameToPng. Numerical behavior is not assessed. No pixel-exact, Windows-equivalence, typed-plane, padding, admission, or public-owner numerical-exact claim."
RAW = ROOT / "refs/conformance/olm_all10_batch5_current_identity_direct_r_v4_fresh_ae_smoke_raw_20260816.json"
SUMMARY = ROOT / "refs/conformance/olm_all10_batch5_current_identity_direct_r_v4_fresh_ae_smoke_20260816.json"
ARTIFACT_DIR = ROOT / "handoffs/olm_all10_batch5_current_identity_direct_r_v4_fresh_ae_smoke_20260816"
INVOCATION_RECEIPT = ARTIFACT_DIR.with_name(ARTIFACT_DIR.name + ".invocation-receipt.json")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_iso(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp is not a string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp is not timezone-aware")
    return parsed.astimezone(timezone.utc)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(command: list[str], *, timeout: int = 120, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout, env=env)


def ae_pids() -> list[int]:
    result = run(["pgrep", "-f", f"^{EXECUTABLE}( |$)"])
    if result.returncode not in (0, 1):
        raise RuntimeError(f"pgrep failed with return code {result.returncode}")
    return sorted(int(value) for value in result.stdout.split() if value.isdigit())


def process_sample(pid: int) -> dict[str, Any]:
    sampled_at = now_iso()
    result = run(["ps", "-p", str(pid), "-o", "pid=,ppid=,lstart=,command="])
    return {
        "sampled_at": sampled_at,
        "returncode": result.returncode,
        "stdout": result.stdout.rstrip("\n"),
        "stderr": result.stderr.rstrip("\n"),
    }


def process_started_at(pid: int) -> str:
    result = run(["ps", "-p", str(pid), "-o", "lstart="])
    if result.returncode != 0 or not result.stdout.strip():
        raise ValueError("could not read AE process start time")
    local = datetime.strptime(result.stdout.strip(), "%a %b %d %H:%M:%S %Y").astimezone()
    return local.astimezone(timezone.utc).isoformat()


def wait_for_single_new_pid(before: set[int], timeout: float = 240.0) -> tuple[int | None, list[dict[str, Any]]]:
    deadline = time.monotonic() + timeout
    samples: list[dict[str, Any]] = []
    while time.monotonic() < deadline:
        current = ae_pids()
        samples.append({"sampled_at": now_iso(), "pids": current})
        new = sorted(set(current).difference(before))
        if len(current) == 1 and len(new) == 1:
            return new[0], samples
        time.sleep(0.5)
    return None, samples


def wait_for_file(path: Path, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.is_file() and path.stat().st_size > 0:
            return True
        time.sleep(0.25)
    return path.is_file() and path.stat().st_size > 0


def wait_for_scriptable_ae(timeout: float = 300.0) -> list[dict[str, Any]]:
    deadline = time.monotonic() + timeout
    samples: list[dict[str, Any]] = []
    while time.monotonic() < deadline:
        check = run(
            ["osascript", "-e", 'tell application "Adobe After Effects 2026" to get version'],
            timeout=20,
        )
        samples.append({
            "sampled_at": now_iso(),
            "returncode": check.returncode,
            "stdout": check.stdout.strip(),
            "stderr": check.stderr.strip(),
        })
        if check.returncode == 0 and check.stdout.strip():
            return samples
        time.sleep(1.0)
    return samples


def stop_owned_ae(owned: set[int], timeout: float = 120.0) -> dict[str, Any]:
    actions: list[dict[str, Any]] = []
    current = ae_pids()
    unexpected = sorted(set(current).difference(owned))
    live_owned = sorted(owned.intersection(current))
    if live_owned and not unexpected:
        try:
            quit_result = run(
                ["osascript", "-e", 'tell application "Adobe After Effects 2026" to quit saving no'],
                timeout=30,
            )
            actions.append({
                "action": "application_quit",
                "returncode": quit_result.returncode,
                "stdout": quit_result.stdout,
                "stderr": quit_result.stderr,
            })
        except (subprocess.TimeoutExpired, OSError) as error:
            actions.append({"action": "application_quit", "error": type(error).__name__})
    elif unexpected:
        actions.append({
            "action": "application_quit_skipped",
            "reason": "unexpected AE PIDs are outside runner ownership",
            "unexpected_pids": unexpected,
        })

    deadline = time.monotonic() + timeout
    remaining = sorted(owned.intersection(ae_pids()))
    while remaining and time.monotonic() < deadline:
        time.sleep(0.5)
        remaining = sorted(owned.intersection(ae_pids()))

    for sig, label in ((signal.SIGTERM, "SIGTERM"), (signal.SIGKILL, "SIGKILL")):
        if not remaining:
            break
        signalled: list[int] = []
        for pid in remaining:
            try:
                os.kill(pid, sig)
                signalled.append(pid)
            except ProcessLookupError:
                pass
        actions.append({"action": label, "exact_pids": signalled})
        deadline = time.monotonic() + 10.0
        while remaining and time.monotonic() < deadline:
            time.sleep(0.25)
            remaining = sorted(owned.intersection(ae_pids()))

    final = ae_pids()
    return {
        "completed_at": now_iso(),
        "owned_pids": sorted(owned),
        "actions": actions,
        "remaining_owned_pids": sorted(owned.intersection(final)),
        "remaining_ae_pids": final,
    }


def executable_for(plugin: str, bundle: Path) -> Path:
    plist_path = bundle / "Contents/Info.plist"
    if not plist_path.is_file():
        raise ValueError(f"missing Info.plist for {plugin}")
    plist = plistlib.loads(plist_path.read_bytes())
    executable = plist.get("CFBundleExecutable")
    if not isinstance(executable, str) or not executable:
        raise ValueError(f"missing CFBundleExecutable for {plugin}")
    return (bundle / "Contents/MacOS" / executable).resolve()


def verify_identity() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not IDENTITY.is_file():
        raise ValueError("accepted identity manifest is absent")
    manifest = json.loads(IDENTITY.read_text(encoding="utf-8"))
    if manifest.get("schema") != "olm.installed-identity-manifest/1":
        raise ValueError("identity schema mismatch")
    accepted_at = manifest.get("accepted_at")
    if not isinstance(accepted_at, str):
        raise ValueError("identity accepted_at missing")
    parse_iso(accepted_at)
    rows = manifest.get("plugins")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED_PLUGINS):
        raise ValueError("identity does not contain exactly ten rows")
    by_name = {row.get("plugin"): row for row in rows if isinstance(row, dict)}
    if set(by_name) != set(EXPECTED_PLUGINS):
        raise ValueError("identity plug-in names mismatch")

    verified: list[dict[str, Any]] = []
    for plugin in EXPECTED_PLUGINS:
        row = by_name[plugin]
        bundle = Path(row.get("installed_bundle", "")).expanduser().resolve()
        expected_bundle = (MEDIA_CORE / f"{plugin}.plugin").resolve()
        if bundle != expected_bundle or not bundle.is_dir():
            raise ValueError(f"installed bundle identity mismatch for {plugin}")
        matching = sorted(path.resolve() for path in MEDIA_CORE.glob(f"{plugin}.plugin"))
        if matching != [expected_bundle]:
            raise ValueError(f"installed bundle cardinality mismatch for {plugin}")
        binary = executable_for(plugin, bundle)
        observed = sha256(binary)
        expected = row.get("sha256")
        if observed != expected or row.get("source_sha256") != expected:
            raise ValueError(f"installed hash mismatch for {plugin}")
        if row.get("source_installed_exact") is not True or row.get("universal_exact") is not True or row.get("codesign_exact") is not True:
            raise ValueError(f"accepted identity flags false for {plugin}")
        verified.append({
            "plugin": plugin,
            "bundle_path": str(bundle),
            "executable_path": str(binary),
            "accepted_executable_sha256": expected,
            "pre_launch_executable_sha256": observed,
            "matching_bundle_count": len(matching),
        })
    return manifest, verified


def capture_vmmap(pid: int, path: Path) -> dict[str, Any]:
    captured_at = now_iso()
    result = run(["vmmap", str(pid)], timeout=180)
    raw = result.stdout + ("\n[stderr]\n" + result.stderr if result.stderr else "")
    path.write_text(raw, encoding="utf-8", errors="strict")
    return {
        "captured_at": captured_at,
        "returncode": result.returncode,
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
        "size": path.stat().st_size,
    }


def parse_vmmap_identity(text: str, pid: int, executable: Path) -> dict[str, Any]:
    header_pid = None
    code_type = None
    for line in text.splitlines()[:80]:
        if line.startswith("Process:") and "[" in line and "]" in line:
            candidate = line.rsplit("[", 1)[1].split("]", 1)[0]
            if candidate.isdigit():
                header_pid = int(candidate)
        if line.startswith("Code Type:"):
            code_type = line.split(":", 1)[1].strip()
    suffix = "/Contents/MacOS/" + executable.name
    candidates: set[str] = set()
    matching_lines: list[str] = []
    for line in text.splitlines():
        # The protection column itself contains a slash (for example
        # ``r--/rwx``).  A vmmap pathname is instead separated from the fixed
        # columns by at least two spaces; anchor the match to the executable
        # suffix so competing same-name bundles are still collected.
        mapped = re.search(r"\s{2,}(/[^\n]*" + re.escape(suffix) + r")\s*$", line)
        if mapped is None:
            continue
        path_text = mapped.group(1)
        if path_text.endswith(suffix):
            candidates.add(path_text)
            if path_text == str(executable):
                matching_lines.append(line)
    return {
        "header_pid": header_pid,
        "code_type": code_type,
        "candidate_paths": sorted(candidates),
        "matching_lines": matching_lines,
        "exact": header_pid == pid and code_type == "ARM64" and sorted(candidates) == [str(executable)],
    }


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
        "size": path.stat().st_size,
    }


def build_summary(raw: dict[str, Any], raw_path: Path) -> dict[str, Any]:
    launch_wrapper = ROOT / raw["artifacts"]["launch_wrapper"]["path"]
    invocation_receipt = launch_wrapper.parent.with_name(
        launch_wrapper.parent.name + ".invocation-receipt.json"
    )
    summary = {
        "schema": "olm.all10-current-install-fresh-ae-smoke/1",
        "generated_at": now_iso(),
        "status": "fail_closed",
        "passed": False,
        "installed_identity_manifest": raw["installed_identity_manifest"],
        "host": {
            "initial_process_count": len(raw["host"]["initial_ae_pids"]),
            "process_count": 1 if raw["host"].get("pid") else 0,
            "fresh_process": False,
            "started_after_identity_acceptance": False,
            "pid": raw["host"].get("pid"),
            "started_at": raw["host"].get("started_at"),
            "captured_at": raw["host"].get("captured_at"),
            "renderer": raw.get("ae_return", {}).get("project", {}).get("renderer"),
            "renderer_raw": raw.get("ae_return", {}).get("project", {}).get("renderer_raw"),
            "quit_succeeded": raw.get("cleanup", {}).get("remaining_ae_pids") == [],
            "residual_process_count": len(raw.get("cleanup", {}).get("remaining_ae_pids", [])),
        },
        "plugins": [],
        "raw_report": {
            "path": str(raw_path.relative_to(ROOT)),
            "sha256": sha256(raw_path),
        },
        "runner": artifact(RUNNER),
        "producer_runner": raw["runner"],
        "validator_runner": artifact(RUNNER),
        "artifacts": {
            "raw_report": {
                "path": str(raw_path.relative_to(ROOT)),
                "sha256": sha256(raw_path),
            },
            "runner": artifact(RUNNER),
            "producer_runner": raw["runner"],
            "invocation_receipt": artifact(invocation_receipt),
            "payload": artifact(PAYLOAD),
        },
        "claim_boundary": raw["claim_boundary"],
    }
    if raw.get("vmmap"):
        summary["artifacts"]["vmmap"] = raw["vmmap"]
    if raw.get("artifacts", {}).get("ae_return"):
        summary["artifacts"]["ae_return"] = raw["artifacts"]["ae_return"]

    returned_by_name = {
        row.get("plugin"): row for row in raw.get("ae_return", {}).get("plugins", [])
        if isinstance(row, dict)
    }
    mapping_by_name = {
        row.get("plugin"): row for row in raw.get("plugins", []) if isinstance(row, dict)
    }
    for plugin in EXPECTED_PLUGINS:
        returned = returned_by_name.get(plugin, {})
        mapped = mapping_by_name.get(plugin, {})
        row_pass = all((
            returned.get("loaded") is True,
            returned.get("applied") is True,
            returned.get("effect_can_enable_after_add") is True,
            returned.get("effect_enabled_during_render") is (plugin in ENABLED_HOST_FRAME_PLUGINS),
            returned.get("host_smoke_expectation") == ("enabled_host_frame_render" if plugin in ENABLED_HOST_FRAME_PLUGINS else "disabled_host_frame_render"),
            returned.get("effect_enabled_host_frame_attempted") is (plugin in ENABLED_HOST_FRAME_PLUGINS),
            returned.get("effect_enabled_host_frame_succeeded") is (plugin in ENABLED_HOST_FRAME_PLUGINS),
            returned.get("numerical_render_attempted") is False,
            returned.get("numerical_render_expected") is False,
            returned.get("numerical_render_supported") is False,
            returned.get("effect_enabled_numerical_render_attempted") is False,
            returned.get("numerical_render_succeeded") is None,
            returned.get("effect_disabled_during_host_frame") is (plugin not in ENABLED_HOST_FRAME_PLUGINS),
            returned.get("host_frame_render_succeeded") is True,
            returned.get("render_succeeded") is True,
            mapped.get("loaded_module_count") == 1,
            mapped.get("post_render_mapping_exact") is True,
            mapped.get("post_render_on_disk_sha256") == mapped.get("accepted_executable_sha256"),
            mapped.get("installed_hash_unchanged") is True,
            isinstance(mapped.get("png", {}).get("sha256"), str),
        ))
        summary["plugins"].append({
            "plugin": plugin,
            "status": "pass" if row_pass else "fail_closed",
            "loaded": returned.get("loaded") is True,
            "applied": returned.get("applied") is True,
            "render_succeeded": returned.get("render_succeeded") is True,
            "host_frame_render_succeeded": returned.get("host_frame_render_succeeded") is True,
            "host_smoke_expectation": "enabled_host_frame_render" if plugin in ENABLED_HOST_FRAME_PLUGINS else "disabled_host_frame_render",
            "effect_enabled_host_frame_attempted": returned.get("effect_enabled_host_frame_attempted") is True,
            "effect_enabled_host_frame_succeeded": returned.get("effect_enabled_host_frame_succeeded") is True,
            "numerical_render_expected": False,
            "numerical_render_supported": False,
            "effect_enabled_numerical_render_attempted": False,
            "numerical_render_succeeded": returned.get("numerical_render_succeeded"),
            "effect_disabled_during_host_frame": returned.get("effect_disabled_during_host_frame") is True,
            "ae_pid": mapped.get("ae_pid"),
            "loaded_module_path": mapped.get("loaded_module_path"),
            "loaded_module_count": mapped.get("loaded_module_count", 0),
            "post_render_mapping_exact": mapped.get("post_render_mapping_exact") is True,
            "installed_executable_path": mapped.get("executable_path"),
            "installed_executable_sha256": mapped.get("post_render_on_disk_sha256"),
            "accepted_executable_sha256": mapped.get("accepted_executable_sha256"),
            "post_render_on_disk_sha256": mapped.get("post_render_on_disk_sha256"),
            "png": mapped.get("png"),
        })

    accepted_value = summary["installed_identity_manifest"].get("accepted_at")
    accepted_at = parse_iso(accepted_value) if isinstance(accepted_value, str) else None
    started_at = parse_iso(summary["host"]["started_at"]) if summary["host"]["started_at"] else None
    summary["host"]["fresh_process"] = summary["host"]["initial_process_count"] == 0 and summary["host"]["process_count"] == 1
    summary["host"]["started_after_identity_acceptance"] = (
        started_at is not None and accepted_at is not None and started_at > accepted_at
    )
    summary["passed"] = all((
        raw.get("status") == "pass",
        summary["host"]["fresh_process"],
        summary["host"]["started_after_identity_acceptance"],
        summary["host"]["renderer"] == "SOFTWARE",
        summary["host"]["renderer_raw"] == EXPECTED_RENDERER_RAW,
        summary["host"]["quit_succeeded"],
        summary["host"]["residual_process_count"] == 0,
        len(summary["plugins"]) == 10,
        all(row["status"] == "pass" for row in summary["plugins"]),
    ))
    summary["status"] = "pass" if summary["passed"] else "fail_closed"
    return summary


def validate_summary_data(summary: dict[str, Any], raw: dict[str, Any]) -> bool:
    """Independent semantic gate used by the runner and tamper tests."""
    try:
        if summary.get("schema") != "olm.all10-current-install-fresh-ae-smoke/1":
            return False
        if summary.get("status") != "pass" or summary.get("passed") is not True:
            return False
        identity = summary["installed_identity_manifest"]
        if identity != raw["installed_identity_manifest"]:
            return False
        if identity.get("path") != "refs/conformance/olm_installed_identity_manifest_20260806.json":
            return False
        accepted_at = parse_iso(identity["accepted_at"])
        host = summary["host"]
        returned_header = raw.get("ae_return", {})
        if not all((
            host.get("initial_process_count") == 0,
            host.get("process_count") == 1,
            host.get("fresh_process") is True,
            host.get("started_after_identity_acceptance") is True,
            isinstance(host.get("pid"), int),
            parse_iso(host["started_at"]) > accepted_at,
            parse_iso(host["captured_at"]) >= parse_iso(host["started_at"]),
            host.get("renderer") == "SOFTWARE",
            host.get("renderer_raw") == EXPECTED_RENDERER_RAW,
            host.get("quit_succeeded") is True,
            host.get("residual_process_count") == 0,
            raw.get("status") == "pass",
            raw.get("host", {}).get("pid") == host.get("pid"),
            raw.get("host", {}).get("started_at") == host.get("started_at"),
            raw.get("host", {}).get("captured_at") == host.get("captured_at"),
            raw.get("host", {}).get("initial_ae_pids") == [],
            raw.get("host", {}).get("initial_process_count") == host.get("initial_process_count") == 0,
            raw.get("vmmap", {}).get("captured_at") == host.get("captured_at"),
            raw.get("cleanup", {}).get("remaining_ae_pids") == [],
            raw.get("schema") == "olm.all10-current-install-fresh-ae-smoke-raw/1",
            returned_header.get("schema") == "olm.all10-fresh-ae-host-return/1",
            returned_header.get("status") == "ok",
            returned_header.get("ae_version") == EXPECTED_AE_VERSION,
            returned_header.get("project", {}).get("renderer") == "SOFTWARE",
            returned_header.get("project", {}).get("renderer_raw") == EXPECTED_RENDERER_RAW,
            raw.get("host", {}).get("process_exit_returncode") == 0,
            raw.get("host", {}).get("script_invocation", {}).get("returncode") == 0,
            raw.get("vmmap", {}).get("returncode") == 0,
            raw.get("claim_boundary") == CLAIM_BOUNDARY,
            summary.get("claim_boundary") == CLAIM_BOUNDARY,
            raw.get("cleanup", {}).get("owned_pids") == [host.get("pid")],
            raw.get("cleanup", {}).get("remaining_owned_pids") == [],
        )):
            return False

        summary_rows = summary.get("plugins")
        raw_rows = raw.get("plugins")
        returned_rows = raw.get("ae_return", {}).get("plugins")
        if not all(isinstance(rows, list) and len(rows) == 10 for rows in (summary_rows, raw_rows, returned_rows)):
            return False
        if {row.get("plugin") for row in summary_rows} != set(EXPECTED_PLUGINS):
            return False
        if len({row.get("plugin") for row in summary_rows}) != 10:
            return False
        raw_by_name = {row["plugin"]: row for row in raw_rows}
        summary_png_paths = [row.get("png", {}).get("path") for row in summary_rows]
        raw_png_paths = [row.get("png", {}).get("path") for row in raw_rows]
        if (len(set(summary_png_paths)) != 10 or None in summary_png_paths or
                len(set(raw_png_paths)) != 10 or None in raw_png_paths):
            return False
        returned_by_name = {row["plugin"]: row for row in returned_rows}
        for row in summary_rows:
            plugin = row["plugin"]
            observed = raw_by_name[plugin]
            returned = returned_by_name[plugin]
            if not all((
                row.get("status") == "pass",
                row.get("loaded") is returned.get("loaded") is True,
                row.get("applied") is returned.get("applied") is True,
                row.get("render_succeeded") is returned.get("render_succeeded") is True,
                row.get("host_frame_render_succeeded") is returned.get("host_frame_render_succeeded") is True,
                row.get("host_smoke_expectation") == ("enabled_host_frame_render" if plugin in ENABLED_HOST_FRAME_PLUGINS else "disabled_host_frame_render"),
                row.get("effect_enabled_host_frame_attempted") is (plugin in ENABLED_HOST_FRAME_PLUGINS),
                row.get("effect_enabled_host_frame_succeeded") is (plugin in ENABLED_HOST_FRAME_PLUGINS),
                row.get("numerical_render_expected") is False,
                row.get("numerical_render_supported") is False,
                row.get("effect_enabled_numerical_render_attempted") is False,
                row.get("numerical_render_succeeded") is None,
                row.get("effect_disabled_during_host_frame") is (plugin not in ENABLED_HOST_FRAME_PLUGINS),
                returned.get("effect_can_enable_after_add") is True,
                returned.get("effect_enabled_during_render") is (plugin in ENABLED_HOST_FRAME_PLUGINS),
                returned.get("host_smoke_expectation") == row.get("host_smoke_expectation"),
                returned.get("effect_enabled_host_frame_attempted") is row.get("effect_enabled_host_frame_attempted"),
                returned.get("effect_enabled_host_frame_succeeded") is row.get("effect_enabled_host_frame_succeeded"),
                returned.get("numerical_render_expected") is row.get("numerical_render_expected") is False,
                returned.get("numerical_render_supported") is row.get("numerical_render_supported") is False,
                returned.get("numerical_render_attempted") is False,
                returned.get("effect_enabled_numerical_render_attempted") is row.get("effect_enabled_numerical_render_attempted") is False,
                returned.get("numerical_render_succeeded") is row.get("numerical_render_succeeded") is None,
                returned.get("effect_disabled_during_host_frame") is row.get("effect_disabled_during_host_frame") is (plugin not in ENABLED_HOST_FRAME_PLUGINS),
                row.get("ae_pid") == host["pid"] == observed.get("ae_pid"),
                row.get("loaded_module_path") == observed.get("executable_path"),
                row.get("loaded_module_count") == observed.get("loaded_module_count") == 1,
                row.get("post_render_mapping_exact") is observed.get("post_render_mapping_exact") is True,
                row.get("accepted_executable_sha256") == observed.get("accepted_executable_sha256"),
                row.get("post_render_on_disk_sha256") == observed.get("post_render_on_disk_sha256"),
                row.get("post_render_on_disk_sha256") == row.get("accepted_executable_sha256"),
                observed.get("installed_hash_unchanged") is True,
                observed.get("pre_launch_executable_sha256") == observed.get("accepted_executable_sha256"),
                row.get("png") == observed.get("png"),
                isinstance(row.get("png", {}).get("sha256"), str),
                row.get("png", {}).get("fresh_after_launch") is True,
            )):
                return False
        return True
    except (KeyError, TypeError, ValueError):
        return False


def validate_persisted_summary(summary: dict[str, Any], raw: dict[str, Any], raw_path: Path) -> bool:
    if not validate_summary_data(summary, raw):
        return False
    try:
        if summary["raw_report"] != {
            "path": str(raw_path.relative_to(ROOT)),
            "sha256": sha256(raw_path),
        }:
            return False
        if summary["runner"] != artifact(RUNNER):
            return False
        if summary.get("validator_runner") != artifact(RUNNER):
            return False
        if summary.get("producer_runner") != raw.get("runner"):
            return False
        if summary.get("artifacts", {}).get("producer_runner") != raw.get("runner"):
            return False
        if summary["artifacts"]["payload"] != artifact(PAYLOAD):
            return False
        launch_wrapper_path = (ROOT / raw["artifacts"]["launch_wrapper"]["path"]).resolve()
        receipt_path = launch_wrapper_path.parent.with_name(
            launch_wrapper_path.parent.name + ".invocation-receipt.json"
        )
        receipt_artifact = artifact(receipt_path)
        if summary["artifacts"].get("invocation_receipt") != receipt_artifact:
            return False
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if (receipt != {
                "schema": "olm.all10-fresh-ae-invocation-receipt/1",
                "created_at": receipt.get("created_at"),
            } or parse_iso(receipt["created_at"]) > parse_iso(raw["generated_at"])
                or parse_iso(receipt["created_at"]) > parse_iso(raw["host"]["launch_requested_at"])):
            return False
        if summary["installed_identity_manifest"]["sha256"] != sha256(IDENTITY):
            return False
        if summary["artifacts"]["vmmap"] != raw["vmmap"]:
            return False
        correction = raw.get("derivation_correction")
        if correction is not None and correction.get("source_vmmap_sha256") != raw["vmmap"]["sha256"]:
            return False
        identity_bytes = json.loads(IDENTITY.read_text(encoding="utf-8"))
        if identity_bytes.get("schema") != "olm.installed-identity-manifest/1":
            return False
        if summary["installed_identity_manifest"].get("accepted_at") != identity_bytes.get("accepted_at"):
            return False
        if summary["installed_identity_manifest"].get("accepted_manifest_status") != "verified_before_launch":
            return False
        accepted_rows = {row["plugin"]: row for row in identity_bytes.get("plugins", [])}
        if set(accepted_rows) != set(EXPECTED_PLUGINS):
            return False
        raw_rows = {row["plugin"]: row for row in raw["plugins"]}
        for plugin, accepted in accepted_rows.items():
            expected_executable = Path(accepted["installed_bundle"]) / "Contents/MacOS" / plugin
            observed = raw_rows[plugin]
            if observed.get("executable_path") != str(expected_executable):
                return False
            if not all(observed.get(key) == accepted.get("sha256") for key in (
                "accepted_executable_sha256", "pre_launch_executable_sha256", "post_render_on_disk_sha256"
            )):
                return False
        vmmap_path = (ROOT / summary["artifacts"]["vmmap"]["path"]).resolve()
        vmmap_path.relative_to(ROOT)
        if sha256(vmmap_path) != summary["artifacts"]["vmmap"]["sha256"]:
            return False
        vmmap_text = vmmap_path.read_text(encoding="utf-8")
        returned_by_name = {row["plugin"]: row for row in raw["ae_return"]["plugins"]}
        png_paths: set[Path] = set()
        started_ms = raw["ae_return"]["started_epoch_ms"]
        completed_ms = raw["ae_return"]["completed_epoch_ms"]
        for row in summary["plugins"]:
            parsed = parse_vmmap_identity(vmmap_text, summary["host"]["pid"], Path(row["loaded_module_path"]))
            if not parsed["exact"]:
                return False
            png = (ROOT / row["png"]["path"]).resolve()
            png.relative_to(ROOT)
            if png.name != f'{row["plugin"]}.png' or png in png_paths:
                return False
            png_paths.add(png)
            returned = returned_by_name[row["plugin"]]
            actual_mtime_ms = int(png.stat().st_mtime * 1000)
            if sha256(png) != row["png"]["sha256"] or png.stat().st_size != row["png"]["size"]:
                return False
            if row["png"]["modified_epoch_ms"] != actual_mtime_ms or row["png"]["fresh_after_launch"] is not True:
                return False
            if Path(returned["output_path"]).resolve() != png or returned["output_size"] != png.stat().st_size:
                return False
            # ExtendScript's File.modified is second-resolution on this host,
            # while stat preserves sub-second precision.  Bind both readings
            # to the same UTC second; path, size, SHA-256 and stat mtime remain
            # independently exact above.
            if returned["output_modified_epoch_ms"] // 1000 != actual_mtime_ms // 1000:
                return False
            if not (started_ms - 1000 <= actual_mtime_ms <= completed_ms + 1000):
                return False
        if len(png_paths) != 10:
            return False
        ae_return_path = (ROOT / summary["artifacts"]["ae_return"]["path"]).resolve()
        ae_return_path.relative_to(ROOT)
        if sha256(ae_return_path) != summary["artifacts"]["ae_return"]["sha256"]:
            return False
        if json.loads(ae_return_path.read_text(encoding="utf-8")) != raw["ae_return"]:
            return False
        nonce = raw["ae_return"]["run_nonce"]
        if not isinstance(nonce, str) or len(nonce) != 32:
            return False
        for key in ("launch_wrapper", "vmmap_ack"):
            observed_artifact = raw["artifacts"][key]
            observed_path = (ROOT / observed_artifact["path"]).resolve()
            observed_path.relative_to(ROOT)
            if artifact(observed_path) != observed_artifact:
                return False
        ack_path = (ROOT / raw["artifacts"]["vmmap_ack"]["path"]).resolve()
        wrapper_path = (ROOT / raw["artifacts"]["launch_wrapper"]["path"]).resolve()
        if ack_path.read_text(encoding="utf-8") != nonce + "\n":
            return False
        nonce_statement = '$.setenv("OLM_ALL10_AE_RUN_NONCE", ' + json.dumps(nonce) + ');'
        if nonce_statement not in wrapper_path.read_text(encoding="utf-8"):
            return False
        return True
    except (KeyError, OSError, TypeError, ValueError):
        return False


def normalize_raw_contract(report: dict[str, Any]) -> None:
    """Expose summary-comparable fields without discarding raw observations."""
    returned = report.get("ae_return", {})
    returned_by_name = {
        row.get("plugin"): row for row in returned.get("plugins", []) if isinstance(row, dict)
    }
    for row in report.get("plugins", []):
        host_row = returned_by_name.get(row.get("plugin"), {})
        row["status"] = "pass" if all((
            host_row.get("loaded") is True,
            host_row.get("applied") is True,
            host_row.get("effect_can_enable_after_add") is True,
            host_row.get("effect_enabled_during_render") is (row.get("plugin") in ENABLED_HOST_FRAME_PLUGINS),
            host_row.get("numerical_render_attempted") is False,
            host_row.get("host_frame_render_succeeded") is True,
            host_row.get("render_succeeded") is True,
            row.get("loaded_module_count") == 1,
            row.get("post_render_mapping_exact") is True,
            row.get("installed_hash_unchanged") is True,
            row.get("png", {}).get("fresh_after_launch") is True,
        )) else "fail_closed"
        row["loaded"] = host_row.get("loaded") is True
        row["applied"] = host_row.get("applied") is True
        row["render_succeeded"] = host_row.get("render_succeeded") is True
        row["host_frame_render_succeeded"] = host_row.get("host_frame_render_succeeded") is True
        row["host_smoke_expectation"] = "enabled_host_frame_render" if row.get("plugin") in ENABLED_HOST_FRAME_PLUGINS else "disabled_host_frame_render"
        row["effect_enabled_host_frame_attempted"] = host_row.get("effect_enabled_host_frame_attempted") is True
        row["effect_enabled_host_frame_succeeded"] = host_row.get("effect_enabled_host_frame_succeeded") is True
        row["numerical_render_expected"] = False
        row["numerical_render_supported"] = False
        row["effect_enabled_numerical_render_attempted"] = False
        row["numerical_render_succeeded"] = host_row.get("numerical_render_succeeded")
        row["effect_disabled_during_host_frame"] = host_row.get("effect_disabled_during_host_frame") is True
        row["installed_executable_sha256"] = row.get("post_render_on_disk_sha256")

    accepted_value = report.get("installed_identity_manifest", {}).get("accepted_at")
    started_value = report.get("host", {}).get("started_at")
    try:
        started_after = parse_iso(started_value) > parse_iso(accepted_value)
    except (TypeError, ValueError):
        started_after = False
    host = report["host"]
    host.update({
        "initial_process_count": len(host.get("initial_ae_pids", [])),
        "process_count": 1 if isinstance(host.get("pid"), int) else 0,
        "fresh_process": host.get("initial_ae_pids") == [] and isinstance(host.get("pid"), int),
        "started_after_identity_acceptance": started_after,
        "renderer": returned.get("project", {}).get("renderer"),
        "renderer_raw": returned.get("project", {}).get("renderer_raw"),
        "quit_succeeded": report.get("cleanup", {}).get("remaining_ae_pids") == [],
        "residual_process_count": len(report.get("cleanup", {}).get("remaining_ae_pids", [])),
    })
    report["passed"] = all((
        report.get("status") == "pass",
        host["initial_process_count"] == 0,
        host["process_count"] == 1,
        host["fresh_process"],
        host["started_after_identity_acceptance"],
        host["renderer"] == "SOFTWARE",
        host["renderer_raw"] == EXPECTED_RENDERER_RAW,
        host["quit_succeeded"],
        host["residual_process_count"] == 0,
        len(report.get("plugins", [])) == 10,
        all(row.get("status") == "pass" for row in report.get("plugins", [])),
    ))
    if not report["passed"]:
        report["status"] = "fail_closed"
    report["runner"] = artifact(RUNNER)
    report.setdefault("artifacts", {})["payload"] = artifact(PAYLOAD)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    raw_path = RAW.resolve()
    summary_path = SUMMARY.resolve()
    artifact_dir = ARTIFACT_DIR.resolve()
    if args.timeout <= 0:
        raise SystemExit("--timeout must be positive")
    if not args.run:
        manifest, identities = verify_identity()
        reserved = (RAW, SUMMARY, ARTIFACT_DIR, INVOCATION_RECEIPT)
        ready = not ae_pids() and all(not path.exists() for path in reserved)
        print(json.dumps({
            "status": "ready_no_ae" if ready else "blocked",
            "launch_mode": "direct_executable_dash_r",
            "identity_sha256": sha256(IDENTITY),
            "accepted_at": manifest["accepted_at"],
            "plugin_count": len(identities),
            "reserved_outputs_absent": all(not path.exists() for path in reserved),
            "ae_pids": ae_pids(),
            "exact_run_command": f"python3 {RUNNER.relative_to(ROOT)} --run",
        }, indent=2, sort_keys=True))
        return 0 if ready else 1
    for label, path in (("--raw-report", raw_path), ("--summary", summary_path), ("--artifact-dir", artifact_dir)):
        try:
            path.relative_to(ROOT)
        except ValueError as error:
            raise SystemExit(f"{label} must stay inside the repository") from error
    if raw_path == summary_path or raw_path.is_relative_to(artifact_dir) or summary_path.is_relative_to(artifact_dir):
        raise SystemExit("raw, summary, and artifact paths must not overlap")
    invocation_receipt = artifact_dir.with_name(artifact_dir.name + ".invocation-receipt.json")
    try:
        receipt_fd = os.open(invocation_receipt, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as error:
        if error.errno == errno.EEXIST:
            raise SystemExit(f"refusing repeated invocation: {invocation_receipt}") from error
        raise
    with os.fdopen(receipt_fd, "w", encoding="utf-8") as receipt:
        json.dump({"schema": "olm.all10-fresh-ae-invocation-receipt/1", "created_at": now_iso()}, receipt, sort_keys=True)
        receipt.write("\n")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    png_dir = artifact_dir / "png"
    if png_dir.exists() and any(png_dir.iterdir()):
        raise SystemExit("refusing to reuse a non-empty PNG artifact directory")
    png_dir.mkdir(exist_ok=True)
    result_path = artifact_dir / "ae_return.json"
    vmmap_path = artifact_dir / "ae_vmmap.txt"
    ack_path = artifact_dir / "vmmap_captured.ack"
    launch_wrapper = artifact_dir / "launch.jsx"
    for stale in (result_path, vmmap_path, ack_path):
        if stale.exists():
            stale.unlink()

    started_at = now_iso()
    initial = ae_pids()
    identity_digest = sha256(IDENTITY) if IDENTITY.is_file() else None
    report: dict[str, Any] = {
        "schema": "olm.all10-current-install-fresh-ae-smoke-raw/1",
        "generated_at": started_at,
        "status": "fail_closed",
        "installed_identity_manifest": {
            "path": str(IDENTITY.relative_to(ROOT)),
            "sha256": identity_digest,
            "accepted_at": None,
        },
        "host": {
            "initial_ae_pids": initial,
            "launch_requested_at": None,
            "pid": None,
            "started_at": None,
            "captured_at": None,
            "process_samples": [],
        },
        "plugins": [],
        "claim_boundary": CLAIM_BOUNDARY,
    }
    owned: set[int] = set()
    script_process: subprocess.Popen[str] | None = None

    def emergency_cleanup() -> None:
        if owned:
            stop_owned_ae(owned, timeout=15)

    atexit.register(emergency_cleanup)
    try:
        if initial:
            raise ValueError("AE process exists before launch")
        if not APP.is_dir() or not EXECUTABLE.is_file() or not PAYLOAD.is_file():
            raise ValueError("AE application or payload is absent")
        manifest, identities = verify_identity()
        report["installed_identity_manifest"]["accepted_at"] = manifest["accepted_at"]
        report["installed_identity_manifest"]["accepted_manifest_status"] = "verified_before_launch"
        if datetime.now(timezone.utc) <= parse_iso(manifest["accepted_at"]):
            raise ValueError("local clock is not after identity acceptance")

        nonce = secrets.token_hex(16)
        child_env = os.environ.copy()
        child_env.update({
            "OLM_ALL10_AE_RESULT": str(result_path),
            "OLM_ALL10_AE_PNG_DIR": str(png_dir),
            "OLM_ALL10_AE_VMMAP_ACK": str(ack_path),
            "OLM_ALL10_AE_RUN_NONCE": nonce,
        })
        launch_wrapper.write_text(
            "(function(){\n"
            + "$.setenv(\"OLM_ALL10_AE_RESULT\", " + json.dumps(str(result_path)) + ");\n"
            + "$.setenv(\"OLM_ALL10_AE_PNG_DIR\", " + json.dumps(str(png_dir)) + ");\n"
            + "$.setenv(\"OLM_ALL10_AE_VMMAP_ACK\", " + json.dumps(str(ack_path)) + ");\n"
            + "$.setenv(\"OLM_ALL10_AE_RUN_NONCE\", " + json.dumps(nonce) + ");\n"
            + "$.evalFile(new File(" + json.dumps(str(PAYLOAD)) + "));\n"
            + "}());\n",
            encoding="utf-8",
        )
        report.setdefault("artifacts", {})["launch_wrapper"] = artifact(launch_wrapper)
        report["host"]["launch_requested_at"] = now_iso()
        script_process = subprocess.Popen(
            [str(EXECUTABLE), "-r", str(launch_wrapper)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=child_env,
        )
        report["host"]["startup_script_launch"] = {
            "mode": "direct_executable_dash_r",
            "executable": str(EXECUTABLE),
            "wrapper": str(launch_wrapper.relative_to(ROOT)),
            "launcher_pid": script_process.pid,
        }
        pid, samples = wait_for_single_new_pid(set(initial))
        report["host"]["process_samples"] = samples
        if pid is None:
            raise ValueError("fresh singleton AE PID was not observed")
        owned.add(pid)
        report["host"]["pid"] = pid
        report["host"]["started_at"] = process_started_at(pid)
        report["host"]["launch_process_pid"] = pid
        report["host"]["process_identity"] = process_sample(pid)

        report["host"]["script_invocation_pid"] = script_process.pid

        deadline = time.monotonic() + args.timeout
        while time.monotonic() < deadline and not (result_path.is_file() and result_path.stat().st_size > 0):
            if script_process.poll() is not None:
                stdout, stderr = script_process.communicate()
                raise ValueError(f"After Effects -r exited before AE return: rc={script_process.returncode} stderr={stderr!r} stdout={stdout!r}")
            time.sleep(0.25)
        if not (result_path.is_file() and result_path.stat().st_size > 0):
            raise ValueError("AE return did not appear")
        returned = json.loads(result_path.read_text(encoding="utf-8"))
        report["ae_return"] = returned
        report.setdefault("artifacts", {})["ae_return"] = artifact(result_path)
        if returned.get("schema") != "olm.all10-fresh-ae-host-return/1" or returned.get("run_nonce") != nonce:
            raise ValueError("AE return identity mismatch")
        if returned.get("status") != "ok" or returned.get("ae_version") != EXPECTED_AE_VERSION:
            raise ValueError("AE return status/version mismatch")
        returned_rows = returned.get("plugins")
        if not isinstance(returned_rows, list) or len(returned_rows) != 10:
            raise ValueError("AE return does not contain exactly ten rows")
        if {row.get("plugin") for row in returned_rows} != set(EXPECTED_PLUGINS):
            raise ValueError("AE returned plug-in names mismatch")
        if ae_pids() != [pid]:
            raise ValueError("AE PID set changed before vmmap")

        vmmap = capture_vmmap(pid, vmmap_path)
        report["vmmap"] = vmmap
        report["host"]["captured_at"] = vmmap["captured_at"]
        if vmmap["returncode"] != 0 or vmmap["size"] == 0:
            raise ValueError("vmmap capture failed")
        vmmap_text = vmmap_path.read_text(encoding="utf-8", errors="strict")
        returned_by_name = {row["plugin"]: row for row in returned_rows}
        launch_epoch = parse_iso(report["host"]["launch_requested_at"]).timestamp()
        for identity in identities:
            plugin = identity["plugin"]
            executable = Path(identity["executable_path"])
            parsed_map = parse_vmmap_identity(vmmap_text, pid, executable)
            exact_lines = parsed_map["matching_lines"]
            mapped_paths = parsed_map["candidate_paths"]
            post_hash = sha256(executable) if executable.is_file() else None
            returned_row = returned_by_name[plugin]
            expected_png = (png_dir / f"{plugin}.png").resolve()
            png_path = Path(returned_row.get("output_path", "")).resolve()
            png_record = None
            if png_path == expected_png and png_path.is_file() and png_path.parent == png_dir:
                fresh_after_launch = png_path.stat().st_mtime + 1.0 >= launch_epoch
                png_record = {
                    "path": str(png_path.relative_to(ROOT)),
                    "sha256": sha256(png_path),
                    "size": png_path.stat().st_size,
                    "modified_epoch_ms": int(png_path.stat().st_mtime * 1000),
                    "fresh_after_launch": fresh_after_launch,
                }
            report["plugins"].append({
                **identity,
                "ae_pid": pid,
                "loaded_module_path": str(executable) if mapped_paths else None,
                "loaded_module_count": len(mapped_paths),
                "vmmap_matching_lines": exact_lines,
                "vmmap_same_executable_name_paths": mapped_paths,
                "vmmap_header_pid": parsed_map["header_pid"],
                "vmmap_code_type": parsed_map["code_type"],
                "post_render_mapping_exact": parsed_map["exact"],
                "post_render_on_disk_sha256": post_hash,
                "installed_hash_unchanged": post_hash == identity["pre_launch_executable_sha256"] == identity["accepted_executable_sha256"],
                "png": png_record,
            })

        ack_path.write_text(nonce + "\n", encoding="utf-8")
        report["artifacts"]["vmmap_ack"] = artifact(ack_path)
        deadline = time.monotonic() + 180.0
        while pid in ae_pids() and time.monotonic() < deadline:
            time.sleep(0.5)
        returncode = 0 if pid not in ae_pids() else None
        script_stdout = ""
        script_stderr = ""
        script_returncode = script_process.poll() if script_process else None
        if script_process:
            try:
                script_stdout, script_stderr = script_process.communicate(timeout=30)
            except subprocess.TimeoutExpired:
                script_process.terminate()
                script_stdout, script_stderr = script_process.communicate(timeout=10)
            script_returncode = script_process.returncode
        report["host"]["script_invocation"] = {
            "returncode": script_returncode,
            "stdout": script_stdout,
            "stderr": script_stderr,
        }
        report["host"]["process_exit_returncode"] = returncode
        report["host"]["post_script_ae_pids"] = ae_pids()
        report["status"] = "pass" if all((
            returncode == 0,
            script_returncode == 0,
            report["host"]["post_script_ae_pids"] == [],
            returned.get("project", {}).get("renderer") == "SOFTWARE",
            returned.get("project", {}).get("renderer_raw") == EXPECTED_RENDERER_RAW,
            all(row.get("loaded") is True and row.get("applied") is True and row.get("effect_can_enable_after_add") is True and row.get("effect_enabled_during_render") is (row.get("plugin") in ENABLED_HOST_FRAME_PLUGINS) and row.get("host_frame_render_succeeded") is True and row.get("render_succeeded") is True and row.get("numerical_render_attempted") is False and row.get("numerical_render_succeeded") is None for row in returned_rows),
            sorted(path.name for path in png_dir.iterdir()) == sorted(f"{name}.png" for name in EXPECTED_PLUGINS),
            all(row["post_render_mapping_exact"] and row["installed_hash_unchanged"] and row["png"] is not None and row["png"]["fresh_after_launch"] for row in report["plugins"]),
            sha256(IDENTITY) == identity_digest,
        )) else "fail_closed"
    except Exception as error:  # Always emit durable fail-closed evidence.
        report["error"] = {"type": type(error).__name__, "message": str(error)}
    finally:
        if script_process is not None and script_process.poll() is None:
            script_process.terminate()
        cleanup = stop_owned_ae(owned) if owned else {
            "completed_at": now_iso(),
            "owned_pids": [],
            "actions": [],
            "remaining_owned_pids": [],
            "remaining_ae_pids": ae_pids(),
        }
        report["cleanup"] = cleanup
        if cleanup["remaining_ae_pids"]:
            report["status"] = "fail_closed"
        report["completed_at"] = now_iso()
        normalize_raw_contract(report)
        write_json(raw_path, report)
        summary = build_summary(report, raw_path)
        if summary.get("passed") and not validate_persisted_summary(summary, report, raw_path):
            summary["passed"] = False
            summary["status"] = "fail_closed"
            summary["validation_error"] = "persisted summary self-check failed"
        write_json(summary_path, summary)
        atexit.unregister(emergency_cleanup)

    print(json.dumps({"status": summary["status"], "raw_report": str(raw_path), "summary": str(summary_path)}))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
