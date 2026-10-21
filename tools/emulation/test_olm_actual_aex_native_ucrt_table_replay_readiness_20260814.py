#!/usr/bin/env python3
"""Freeze the AE-free AEXCompat native-UCRT table replay patch boundary."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / "tools/emulation/aexcompat_native_ucrt_table_replay_20260814.patch"
AEX_REPO = Path("/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue851-smart-primary-checkout")
CALLBACKS = AEX_REPO / "guest/crates/aex-guest-worker/src/x64/callbacks.rs"
ANALYZER = ROOT / "scripts/analyze_olm_math_ucrt_batch_return_20260814.py"
DOWNSTREAM = ROOT / "tools/emulation/test_olm_math_ucrt_downstream_replay_20260814.py"
DIRECTIONAL_CONTROL_TOOL = ROOT / "tools/emulation/test_olmdirectionalblur_same_table_dual_owner_plumbing_20260814.py"
DIRECTIONAL_CONTROL = ROOT / "refs/conformance/olmdirectionalblur_same_table_dual_owner_plumbing_20260814.json"
DISTANCE_CONTROL_TOOL = ROOT / "tools/emulation/test_olmdistancegradation_same_table_dual_owner_plumbing_20260814.py"
DISTANCE_CONTROL = ROOT / "refs/conformance/olmdistancegradation_same_table_dual_owner_plumbing_20260814.json"
DIRECTIONAL_AEX = ROOT / "aex/OLMDirectionalBlur/Plugins/64/2025/OLMDirectionalBlur.aex"
DISTANCE_AEX = ROOT / "aex/OLMDistanceGradation/Plugins/64/2025/DistanceGradation.aex"
REPORT = ROOT / "refs/conformance/olm_actual_aex_native_ucrt_table_replay_readiness_20260814.json"
MARKDOWN = REPORT.with_suffix(".md")

EXPECTED = {
    "aexcompat_head": "28d535469f84f67236ef3425afe4291ea2fb0991",
    "callbacks_sha256": "b26755017884874a7721bc749325a54f97f517f750d97db181ca6df36a0d6e31",
    "patch_sha256": "6fee08e81a7d0901eb2bfa4914bf6cbec2c3161806988eb52b9392f4dfd94361",
    "patched_callbacks_sha256": "c6db8fea04e2db211943ff923bbfe8b22655859dcf07210e403516a80c4b9aca",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(args), cwd=cwd, text=True, capture_output=True)


def static_inputs() -> dict[str, Any]:
    head = command("git", "rev-parse", "HEAD", cwd=AEX_REPO)
    if head.returncode != 0:
        raise RuntimeError("AEXCompat HEAD unavailable")
    observed = {
        "aexcompat_head": head.stdout.strip(),
        "callbacks_sha256": sha256(CALLBACKS),
        "patch_sha256": sha256(PATCH),
    }
    if observed != {key: EXPECTED[key] for key in observed}:
        raise RuntimeError(f"AEX replay input drift: {observed}")
    check = command("git", "apply", "--check", str(PATCH), cwd=AEX_REPO)
    if check.returncode != 0:
        raise RuntimeError("AEX replay patch no longer applies cleanly: " + check.stderr)
    text = PATCH.read_text(encoding="utf-8")
    required = (
        'std::env::var_os("OLM_NATIVE_UCRT_TABLE")',
        'olm_native_ucrt_result("expf", bits as u32, None)',
        'olm_native_ucrt_result("powf", left as u32, Some(right as u32))',
        'olm_missing_native_ucrt_result(unicorn, name)',
        'unicorn.emu_stop()',
    )
    if any(token not in text for token in required):
        raise RuntimeError("AEX replay patch fail-close token drift")
    return {
        "aexcompat_repo": str(AEX_REPO),
        "aexcompat_head": observed["aexcompat_head"],
        "callbacks": {"path": str(CALLBACKS), "sha256": observed["callbacks_sha256"]},
        "patch": {"path": str(PATCH.relative_to(ROOT)), "sha256": observed["patch_sha256"]},
        "strict_return_analyzer": {"path": str(ANALYZER.relative_to(ROOT)), "sha256": sha256(ANALYZER)},
        "mac_downstream_replay": {"path": str(DOWNSTREAM.relative_to(ROOT)), "sha256": sha256(DOWNSTREAM)},
        "host_substitute_plumbing_controls": {
            "directional": {"tool_sha256": sha256(DIRECTIONAL_CONTROL_TOOL),
                            "report_sha256": sha256(DIRECTIONAL_CONTROL)},
            "distance": {"tool_sha256": sha256(DISTANCE_CONTROL_TOOL),
                         "report_sha256": sha256(DISTANCE_CONTROL)},
        },
        "aex": {
            "directional": {"path": str(DIRECTIONAL_AEX.relative_to(ROOT)), "sha256": sha256(DIRECTIONAL_AEX)},
            "distance": {"path": str(DISTANCE_AEX.relative_to(ROOT)), "sha256": sha256(DISTANCE_AEX)},
        },
    }


def build_patch() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="olm-aex-native-ucrt-replay-") as raw:
        clone = Path(raw) / "repo"
        run = command("git", "clone", "--quiet", "--no-hardlinks", str(AEX_REPO), str(clone), cwd=Path(raw))
        if run.returncode != 0:
            raise RuntimeError("temporary AEXCompat clone failed: " + run.stderr)
        run = command("git", "apply", str(PATCH), cwd=clone)
        if run.returncode != 0:
            raise RuntimeError("temporary AEX replay patch apply failed: " + run.stderr)
        patched = clone / "guest/crates/aex-guest-worker/src/x64/callbacks.rs"
        patched_sha = sha256(patched)
        if patched_sha != EXPECTED["patched_callbacks_sha256"]:
            raise RuntimeError(f"patched callback identity drift: {patched_sha}")
        run = command("cargo", "check", "-p", "aex-guest-worker", "--manifest-path",
                      str(clone / "guest/Cargo.toml"), cwd=clone)
        if run.returncode != 0:
            raise RuntimeError("patched AEX worker cargo check failed: " + run.stdout + run.stderr)
        return {
            "temporary_clean_clone": True,
            "patch_applied": True,
            "cargo_check_package": "aex-guest-worker",
            "cargo_check_passed": True,
            "patched_callbacks_sha256": patched_sha,
        }


def generate(*, run_build: bool) -> dict[str, Any]:
    if not run_build:
        raise RuntimeError("canonical generation requires --run-build")
    return {
        "schema": "olm.actual-aex-native-ucrt-table-replay-readiness/1",
        "status": "READY_NATIVE_TABLE_REPLAY_HOST_SUBSTITUTE_DUAL_OWNER_PLUMBING_PROVEN",
        "inputs": static_inputs(),
        "build": build_patch(),
        "table_contract": {
            "format": "e <argument_u32_hex> <result_u32_hex> or p <input_u32_hex> <exponent_u32_hex> <result_u32_hex>",
            "environment": "OLM_NATIVE_UCRT_TABLE",
            "expf_exact_key": True,
            "powf_exact_pair_key": True,
            "missing_key_fails_closed": True,
            "host_math_fallback_when_table_present": False,
        },
        "next_exact_proof": {
            "directional_exported_cells": 6,
            "distance_exported_cells": 8,
            "host_substitute_same_table_directional_proven": 6,
            "host_substitute_same_table_distance_proven": 8,
            "same_native_table_required_for_aex_and_mac": True,
            "compare_full_raw_and_public_storage_contract": True,
        },
        "scope": {
            "native_windows_return_received": False,
            "host_substitute_patched_worker_built": True,
            "host_substitute_actual_aex_replay_executed": True,
            "native_table_actual_aex_replay_executed": False,
            "production_changed": False,
            "after_effects_launched": False,
            "network_changed": False,
        },
    }


def validate(value: Any, *, live: bool = True) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "schema", "status", "inputs", "build", "table_contract", "next_exact_proof", "scope"
    }:
        return False
    if value["schema"] != "olm.actual-aex-native-ucrt-table-replay-readiness/1" or value["status"] != \
            "READY_NATIVE_TABLE_REPLAY_HOST_SUBSTITUTE_DUAL_OWNER_PLUMBING_PROVEN":
        return False
    if live:
        try:
            if value["inputs"] != static_inputs():
                return False
        except (OSError, RuntimeError, ValueError):
            return False
    if value["build"] != {
        "temporary_clean_clone": True, "patch_applied": True,
        "cargo_check_package": "aex-guest-worker", "cargo_check_passed": True,
        "patched_callbacks_sha256": EXPECTED["patched_callbacks_sha256"],
    }:
        return False
    if value["table_contract"] != {
        "format": "e <argument_u32_hex> <result_u32_hex> or p <input_u32_hex> <exponent_u32_hex> <result_u32_hex>",
        "environment": "OLM_NATIVE_UCRT_TABLE", "expf_exact_key": True,
        "powf_exact_pair_key": True, "missing_key_fails_closed": True,
        "host_math_fallback_when_table_present": False,
    }:
        return False
    if value["next_exact_proof"] != {
        "directional_exported_cells": 6, "distance_exported_cells": 8,
        "host_substitute_same_table_directional_proven": 6,
        "host_substitute_same_table_distance_proven": 8,
        "same_native_table_required_for_aex_and_mac": True,
        "compare_full_raw_and_public_storage_contract": True,
    }:
        return False
    return value["scope"] == {
        "native_windows_return_received": False, "host_substitute_patched_worker_built": True,
        "host_substitute_actual_aex_replay_executed": True,
        "native_table_actual_aex_replay_executed": False, "production_changed": False,
        "after_effects_launched": False, "network_changed": False,
    }


def markdown(value: dict[str, Any]) -> str:
    return (
        "# Actual-AEX native UCRT table replay readiness\n\n"
        f"Status: `{value['status']}`.\n\n"
        "The patch cleanly applies to the pinned AEXCompat source and the patched "
        "`aex-guest-worker` passes `cargo check` in a temporary clean clone. Separate "
        "clean release builds have also driven the same macOS-host substitute table "
        "through six Directional and eight Distance exported-AEX cells and their "
        "matching Mac replays, all full-RAW exact. With a "
        "table present, exact `expf`/`powf` keys are required and a missing key stops "
        "emulation; host math is not a fallback. Those controls prove plumbing only, "
        "not native UCRT results. After the native 1,344-row return arrives, its same table must "
        "drive six Directional and eight Distance exported-AEX cells and the matching "
        "Mac public replays before any production promotion. AE and network state were "
        "not changed.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-build", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        value = generate(run_build=args.run_build)
        if not validate(value):
            raise RuntimeError("generated AEX table replay readiness invalid")
        REPORT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        MARKDOWN.write_text(markdown(value), encoding="utf-8")
    else:
        value = json.loads(REPORT.read_text(encoding="utf-8"))
        if not validate(value) or MARKDOWN.read_text(encoding="utf-8") != markdown(value):
            raise RuntimeError("persisted AEX table replay readiness drift")
    print(value["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
