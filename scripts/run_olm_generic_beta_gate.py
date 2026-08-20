#!/usr/bin/env python3
"""Stdlib-only, fail-closed aggregate gate for the generic beta lanes."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
import subprocess
import sys
import time
import traceback
import types
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "refs/conformance/olm_generic_beta_gate.json"
DEFAULT_TIMEOUT = 300

# Deliberately explicit: adding a test to the tree does not silently broaden the gate.
MANIFEST = [
    ("ColorKeep", "tests/test_colorkeep_generic_beta_20260820.py", "mac/ColorKeep/ColorKeep.cpp"),
    ("ColorKeep-ROI", "tests/test_colorkeep_roi_tile_beta_20260820.py", "mac/ColorKeep/ColorKeep.cpp"),
    ("OLMBlur", "tests/test_olmblur_generic_beta_lane_20260820.py", "mac/OLMBlur/OLMBlur.cpp"),
    ("OLMBlur", "tests/test_olmblur_generic_beta_sanitizers_20260820.py", "tools/emulation/probe_olmblur_generic_beta_sanitized_20260820.cpp"),
    ("OLMBlur-ROI-policy", "tests/test_olmblur_roi_halo_contract_20260820.py", "mac/OLMBlur/OLMBlur.cpp"),
    ("OLMColorKey", "tests/test_olmcolorkey_generic_pixel_local_beta.py", "mac/OLMColorKey/OLMColorKey.cpp"),
    ("OLMColorKey", "tests/test_olmcolorkey_generic_pixel_local_pairwise.py", "mac/OLMColorKey/OLMColorKey.cpp"),
    ("OLMColorKey-ROI", "tests/test_olmcolorkey_generic_roi_tile.py", "mac/OLMColorKey/OLMColorKey.cpp"),
    ("OLMDirectionalBlur", "tools/emulation/test_dblur_generic_pf8_geometry_beta_20260820.py", "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"),
    ("OLMDirectionalBlur", "tools/emulation/test_dblur_generic_deep_geometry_beta_20260820.py", "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"),
    ("OLMDirectionalBlur-ROI-policy", "tools/emulation/test_dblur_generic_roi_policy_20260820.py", "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"),
    ("OLMDistanceGradation", "tests/test_olmdistancegradation_generic_production_beta_20260820.py", "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"),
    ("OLMDistanceGradation", "tests/test_olmdistancegradation_pf32_smart_unblurred_beta_20260820.py", "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"),
    ("OLMKiraKira", "tests/test_olmkirakira_generic_beta_lane_20260820.py", "mac/OLMKiraKira/OLMKiraKira.cpp"),
    ("OLMKiraKira", "tests/test_olmkirakira_generic_beta_sanitizers_20260820.py", "mac/OLMKiraKira/OLMKiraKira.cpp"),
    ("OLMKiraKira", "tests/test_olmkirakira_native_smoke_tuple_20260820.py", "mac/OLMKiraKira/OLMKiraKira.cpp"),
    ("OLMRadialBlur", "tests/test_olmradialblur_generic_baseline_20260820.py", "mac/OLMRadialBlur/OLMRadialBlur.cpp"),
    ("OLMRadialBlur", "tests/test_olmradialblur_generic_baseline_sanitizers_20260820.py", "mac/OLMRadialBlur/OLMRadialBlur.cpp"),
    ("OLMRadialBlur", "tests/test_olmradialblur_generic_type3_sanitizers_20260820.py", "mac/OLMRadialBlur/OLMRadialBlur.cpp"),
    ("OLMRadialBlur-ROI-policy", "tests/test_olmradialblur_global_polar_smart_contract_20260820.py", "mac/OLMRadialBlur/OLMRadialBlur.cpp"),
    ("OLMSmoother", "tests/test_olmsmoother_v1_generic_classic_beta_20260820.py", "mac/OLMSmoother/Mac/OLMSmoother_port.cpp"),
    ("OLMSmoother2", "tests/test_olmsmoother2_default_beta_lane_20260820.py", "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"),
    ("OLMSmoother2-ROI-policy", "tests/test_olmsmoother2_roi_fullframe_contract_20260820.py", "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"),
    ("OLMToonDilate", "tests/test_olmtoondilate_generic_beta.py", "mac/OLMToonDilate/OLMToonDilate.cpp"),
    ("OLMToonDilate-ROI-safety", "tests/test_olmtoondilate_roi_safety.py", "mac/OLMToonDilate/OLMToonDilate.cpp"),
    ("common-world", "tests/test_olm_world_safety.py", "tests/test_olm_world_safety.cpp"),
    ("common-world", "tests/test_olm_checked_allocation.py", "core/olm_checked_allocation.h"),
    ("common-ROI", "tests/test_olm_checked_rect.py", "core/olm_checked_rect.h"),
    ("common-ROI", "tests/test_olm_roi_contract.py", "core/olm_roi_contract.h"),
    ("property", "tests/test_olm_property_cases.py", "tests/test_olm_property_cases.py"),
    ("roi_tile_property", "tests/test_olm_roi_tile_property.py", "tests/test_olm_roi_tile_property.py"),
    ("oracle", "tests/test_generate_aexcompat_oracle_campaign.py", "scripts/generate_aexcompat_oracle_campaign.py"),
    ("oracle", "tests/test_run_aexcompat_reference_20260725.py", "scripts/run_aexcompat_reference.py"),
    ("windows-oracle-bundle", "tests/test_generic_beta_windows_oracle_handoff.py", "scripts/package_generic_beta_windows_oracle.py"),
    ("ae-smoke", "tests/test_ae_generalization_smoke.py", "scripts/run_ae_generalization_smoke.py"),
    ("documentation", "tests/test_beta_support_documentation.py", "docs/BETA_SUPPORT.md"),
    ("performance", "tests/test_generic_beta_perf_smoke_runner.py", "tools/perf/run_generic_beta_smoke.py"),
    ("package-hash", "tests/test_verify_mac_plugin_package_hash.py", "scripts/verify_mac_plugin_package.py"),
]


def sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _install_pytest_shim() -> None:
    if "pytest" in sys.modules:
        return
    shim = types.ModuleType("pytest")

    class Mark:
        @staticmethod
        def skipif(condition: bool, reason: str = ""):
            def decorate(function):
                if condition:
                    function.__unittest_skip__ = True
                    function.__unittest_skip_why__ = reason
                return function
            return decorate

    shim.mark = Mark()
    sys.modules["pytest"] = shim


def run_test_file(path: Path) -> int:
    """Run unittest cases and zero-argument pytest-style functions."""
    _install_pytest_shim()
    spec = importlib.util.spec_from_file_location(f"olm_gate_{path.stem}", path)
    if spec is None or spec.loader is None:
        print(json.dumps({"status": "FAIL", "error": "module spec unavailable"}))
        return 1
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        traceback.print_exc()
        return 1
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=1).run(suite)
    failures = len(result.failures) + len(result.errors) + len(result.unexpectedSuccesses)
    ran = result.testsRun
    skipped = len(result.skipped)
    for name, function in sorted(vars(module).items()):
        if not name.startswith("test_") or not inspect.isfunction(function) or inspect.signature(function).parameters:
            continue
        ran += 1
        if getattr(function, "__unittest_skip__", False):
            skipped += 1
            continue
        try:
            function()
        except unittest.SkipTest:
            skipped += 1
        except Exception:
            failures += 1
            traceback.print_exc()
    if ran == 0:
        print(json.dumps({"status": "FAIL", "error": "zero tests collected"}), file=sys.stderr)
        return 1
    if failures:
        return 1
    return 77 if ran > 0 and skipped == ran else 0


def execute_entry(plugin: str, test_rel: str, source_rel: str, timeout: int) -> dict[str, object]:
    test_path, source_path = ROOT / test_rel, ROOT / source_rel
    # Script-style probes under tools/ own their main() and must not pass merely
    # because importing them collected zero unittest/pytest tests.
    command = ([sys.executable, str(test_path)] if test_rel.startswith("tools/") else
               [sys.executable, str(Path(__file__).resolve()), "--run-test-file", str(test_path)])
    started = time.monotonic()
    row: dict[str, object] = {
        "plugin": plugin, "test": test_rel, "source": source_rel,
        "command": command, "test_sha256": sha256(test_path),
        "source_sha256": sha256(source_path),
    }
    if row["test_sha256"] is None or row["source_sha256"] is None:
        row.update(status="FAIL", duration_seconds=0.0, exit_code=None, stderr="missing test or source")
        return row
    try:
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=timeout, check=False)
        status = "PASS" if completed.returncode == 0 else "SKIP" if completed.returncode == 77 else "FAIL"
        row.update(status=status, exit_code=completed.returncode,
                   stdout=completed.stdout[-4000:], stderr=completed.stderr[-4000:])
    except subprocess.TimeoutExpired as exc:
        row.update(status="FAIL", exit_code=None, stderr=f"timeout after {timeout}s: {exc}")
    row["duration_seconds"] = round(time.monotonic() - started, 6)
    return row


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--allow-skip", action="store_true",
                        help="permit missing optional evidence; default is fail-closed INCOMPLETE")
    parser.add_argument("--run-test-file", type=Path)
    args = parser.parse_args(argv)
    if args.run_test_file:
        return run_test_file(args.run_test_file)
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    rows = [execute_entry(*entry, args.timeout) for entry in MANIFEST]
    plugin_summary: dict[str, str] = {}
    for plugin in dict.fromkeys(row["plugin"] for row in rows):
        states = {row["status"] for row in rows if row["plugin"] == plugin}
        plugin_summary[str(plugin)] = (
            "FAIL" if "FAIL" in states else
            "INCOMPLETE" if "SKIP" in states and not args.allow_skip else
            "PASS" if "PASS" in states else "SKIP"
        )
    has_failure = any(row["status"] == "FAIL" for row in rows)
    has_skip = any(row["status"] == "SKIP" for row in rows)
    overall = "FAIL" if has_failure else "INCOMPLETE" if has_skip and not args.allow_skip else "PASS"
    payload = {
        "schema": "olm.generic-beta-gate/1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": overall,
        "allow_skip": args.allow_skip,
        "counts": {state: sum(row["status"] == state for row in rows) for state in ("PASS", "FAIL", "SKIP")},
        "plugin_summary": plugin_summary,
        "entries": rows,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
