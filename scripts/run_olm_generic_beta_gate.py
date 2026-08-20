#!/usr/bin/env python3
"""Stdlib-only, fail-closed aggregate gate for the generic beta lanes."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import traceback
import types
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "reports/olm_generic_beta_gate.json"
DEFAULT_TIMEOUT = 300
PROCESS_DRAIN_TIMEOUT = 1.0

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
    ("OLMDirectionalBlur", "tools/emulation/test_dblur_generic_backonly_beta_20260821.py", "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"),
    ("OLMDirectionalBlur", "tools/emulation/test_dblur_generic_backonly_effectmain_20260821.py", "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"),
    ("OLMDirectionalBlur", "tools/emulation/test_dblur_generic_admission_budget_20260821.py", "core/dblur_generic_budget.h"),
    ("OLMDirectionalBlur", "tools/emulation/test_olmdirectionalblur_smart_cleanup_atomic_20260813.py", "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"),
    ("OLMDirectionalBlur-ROI-policy", "tools/emulation/test_dblur_generic_roi_policy_20260820.py", "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"),
    ("OLMDistanceGradation", "tests/test_olmdistancegradation_generic_production_beta_20260820.py", "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"),
    ("OLMDistanceGradation", "tests/test_olmdistancegradation_pf32_smart_unblurred_beta_20260820.py", "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"),
    ("OLMKiraKira", "tests/test_olmkirakira_generic_beta_lane_20260820.py", "mac/OLMKiraKira/OLMKiraKira.cpp"),
    ("OLMKiraKira", "tests/test_olmkirakira_generic_beta_sanitizers_20260820.py", "mac/OLMKiraKira/OLMKiraKira.cpp"),
    ("OLMKiraKira", "tests/test_olmkirakira_native_smoke_tuple_20260820.py", "mac/OLMKiraKira/OLMKiraKira.cpp"),
    ("OLMKiraKira", "tests/test_olmkirakira_mode3_ui_length_beta_20260821.py", "mac/OLMKiraKira/OLMKiraKira.cpp"),
    ("OLMRadialBlur", "tests/test_olmradialblur_generic_baseline_20260820.py", "mac/OLMRadialBlur/OLMRadialBlur.cpp"),
    ("OLMRadialBlur", "tests/test_olmradialblur_generic_baseline_sanitizers_20260820.py", "mac/OLMRadialBlur/OLMRadialBlur.cpp"),
    ("OLMRadialBlur", "tests/test_olmradialblur_generic_type3_sanitizers_20260820.py", "mac/OLMRadialBlur/OLMRadialBlur.cpp"),
    ("OLMRadialBlur-ROI-policy", "tests/test_olmradialblur_global_polar_smart_contract_20260820.py", "mac/OLMRadialBlur/OLMRadialBlur.cpp"),
    ("OLMSmoother", "tests/test_olmsmoother_v1_generic_classic_beta_20260820.py", "mac/OLMSmoother/Mac/OLMSmoother_port.cpp"),
    ("OLMSmoother2", "tests/test_olmsmoother2_default_beta_lane_20260820.py", "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"),
    ("OLMSmoother2", "tests/test_olmsmoother2_gamma_colors_beta_20260820.py", "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"),
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
    ("ae-output-completion", "tests/test_ae_png_completion.py", "scripts/run_ae_single_case.py"),
    ("ae-batch-output-integrity", "tests/test_ae_batch_png_integrity.py", "scripts/run_ae_validation_batch.py"),
    ("gate-self", "tests/test_run_olm_generic_beta_gate.py", "scripts/run_olm_generic_beta_gate.py"),
    ("documentation", "tests/test_beta_support_documentation.py", "docs/BETA_SUPPORT.md"),
    ("performance", "tests/test_generic_beta_perf_smoke_runner.py", "tools/perf/run_generic_beta_smoke.py"),
    ("package-hash", "tests/test_verify_mac_plugin_package_hash.py", "scripts/verify_mac_plugin_package.py"),
]

# Report the identity of the important transitive inputs as well as the primary
# source.  The keys are manifest test paths so the closure stays explicit and
# reviewable instead of being inferred from imports or command strings.
PERFORMANCE_DRIVERS = (
    "tools/perf/run_colorkeep_generic_production_perf.py",
    "tools/perf/run_olmblur_generic_production_perf.py",
    "tests/test_olmcolorkey_generic_pixel_local_pairwise.py",
    "tools/emulation/test_dblur_generic_deep_geometry_beta_20260820.py",
    "tests/test_olmdistancegradation_generic_production_beta_20260820.py",
    "tools/perf/run_olmkirakira_generic_production_perf.py",
    "tools/perf/run_olmradialblur_generic_production_perf.py",
    "tests/run_olmsmoother_v1_generic_production_perf.py",
    "tests/test_olmsmoother2_default_beta_lane_20260820.py",
    "tools/perf/run_olmtoondilate_generic_production_perf.py",
)
DIRECTIONAL_BACKONLY_DEPENDENCIES = (
    "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp",
    "mac/OLMDirectionalBlur/OLMDirectionalBlur.h",
    "mac/OLMDirectionalBlur/OLMDirectionalBlur_Strings.h",
    "core/dblur_frontonly.cpp",
    "core/dblur_frontonly.h",
    "core/dblur_generic_budget.h",
    "core/dblur_rotate.cpp",
    "core/dblur_rotate.h",
    "core/dblur_rowdriver.cpp",
    "core/dblur_rowdriver.h",
    "core/dblur_field.cpp",
    "core/dblur_field.h",
    "core/dblur_gaussian.h",
    "core/dblur_noise.h",
    "core/olm_checked_allocation.h",
    "core/olm_sha256_rows.h",
    "refs/conformance/dblur_mode1_backonly_portable_20260805.json",
)
KIRAKIRA_MODE3_UI_DEPENDENCIES = (
    "mac/OLMKiraKira/OLMKiraKira.cpp",
    "mac/OLMKiraKira/OLMKiraKira.h",
    "mac/OLMKiraKira/OLMKiraKira_Strings.cpp",
    "mac/OLMKiraKira/OLMKiraKira_Strings.h",
    "core/kirakira_gaussian.h",
    "core/kirakira_highlight.h",
    "core/kirakira_mode4.h",
    "core/kirakira_warp.h",
    "core/kirakira_merge2.h",
    "tests/olmkirakira_generic_beta_sanitizer_harness.cpp",
    "tools/emulation/olmkirakira_public_smart_bounded_closure_harness_20260812.cpp",
    "tools/emulation/test_olmkirakira_mode3_geometry_generalization_actual_aex_20260810.py",
    "tools/emulation/test_kirakira_mode3_default50_canonical.cpp",
    "refs/conformance/olmkirakira_mode3_geometry_generalization_actual_aex_20260810.json",
)
DEPENDENCY_PATHS: dict[str, tuple[str, ...]] = {
    "tests/test_ae_generalization_smoke.py": (
        "scripts/run_ae_generalization_smoke.py",
        "scripts/run_ae_single_case.py",
        "scripts/ae_render_single_case.jsx",
    ),
    "tests/test_ae_png_completion.py": (
        "scripts/run_ae_single_case.py",
        "scripts/ae_render_single_case.jsx",
        "scripts/ae_pixel_validation_render.jsx",
    ),
    "tests/test_ae_batch_png_integrity.py": (
        "scripts/run_ae_validation_batch.py",
        "scripts/ae_pixel_validation_render.jsx",
        "scripts/run_ae_single_case.py",
    ),
    "tools/emulation/test_dblur_generic_backonly_beta_20260821.py": (
        *DIRECTIONAL_BACKONLY_DEPENDENCIES,
    ),
    "tools/emulation/test_dblur_generic_backonly_effectmain_20260821.py": (
        *DIRECTIONAL_BACKONLY_DEPENDENCIES,
        "mac/OLMDirectionalBlur/OLMDirectionalBlur_Strings.cpp",
        "Util/AEGP_SuiteHandler.cpp",
        "Util/MissingSuiteError.cpp",
    ),
    "tests/test_olmkirakira_mode3_ui_length_beta_20260821.py": (
        *KIRAKIRA_MODE3_UI_DEPENDENCIES,
    ),
    "tests/test_generic_beta_perf_smoke_runner.py": (
        "tools/perf/run_generic_beta_smoke.py",
        "reports/generic_beta_perf_smoke.json",
        *PERFORMANCE_DRIVERS,
    ),
    "tests/test_beta_support_documentation.py": (
        "docs/BETA_SUPPORT.md",
        "README.md",
        "reports/public_beta_completion_audit_20260820.json",
        "reports/public_beta_roi_v2_package_20260820.json",
        "refs/conformance/olm_all10_roi_v2_quick_ae_smoke_20260820.json",
        "refs/conformance/olm_all10_roi_v2_quick_ae_smoke_raw_20260820.json",
        "refs/conformance/olm_all10_generic_beta_quick_ae_smoke_20260820.json",
        "refs/conformance/olm_all10_generic_beta_quick_ae_smoke_raw_20260820.json",
        "reports/generic_beta_perf_smoke.json",
        "core/dblur_generic_budget.h",
        "tools/emulation/test_dblur_generic_backonly_beta_20260821.py",
        "tools/emulation/test_dblur_generic_backonly_effectmain_20260821.py",
        *DIRECTIONAL_BACKONLY_DEPENDENCIES,
        "tests/test_olmkirakira_mode3_ui_length_beta_20260821.py",
        *KIRAKIRA_MODE3_UI_DEPENDENCIES,
        "mac/ColorKeep/ColorKeep.cpp",
        "mac/OLMBlur/OLMBlur.cpp",
        "mac/OLMColorKey/OLMColorKey.cpp",
        "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp",
        "mac/OLMDistanceGradation/OLMDistanceGradation.cpp",
        "mac/OLMKiraKira/OLMKiraKira.cpp",
        "mac/OLMRadialBlur/OLMRadialBlur.cpp",
        "mac/OLMSmoother/Mac/OLMSmoother_port.cpp",
        "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp",
        "mac/OLMToonDilate/OLMToonDilate.cpp",
        "tests/test_olmsmoother2_gamma_colors_beta_20260820.py",
        "refs/conformance/colorkeep_generic_beta_sanitizer_20260820.json",
        "reports/generic_beta_perf_smoke_radial.json",
        "refs/conformance/olmsmoother2_geometry_classifier_matrix_actual_aex_20260811.md",
        "refs/conformance/generic_beta_aexcompat_nonhd_checkpoint_20260820.json",
        "refs/conformance/generic_beta_aexcompat_hd_checkpoint_20260820.json",
    ),
}


def sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def dependency_hashes(test_rel: str, source_rel: str) -> dict[str, str | None]:
    paths = tuple(dict.fromkeys((source_rel, *DEPENDENCY_PATHS.get(test_rel, ()))))
    return {rel: sha256(ROOT / rel) for rel in paths}


def manifest_sha256() -> str:
    encoded = json.dumps(
        {"entries": MANIFEST, "dependencies": DEPENDENCY_PATHS},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    """Durably replace one JSON document without exposing a partial file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        try:
            directory_fd = os.open(path.parent, os.O_RDONLY)
        except OSError:
            directory_fd = None
        if directory_fd is not None:
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        temporary.unlink(missing_ok=True)


def python_optimization_reason() -> str | None:
    if sys.flags.optimize:
        return f"interpreter optimization level is {sys.flags.optimize}"
    raw = os.environ.get("PYTHONOPTIMIZE")
    if raw:
        try:
            enabled = int(raw) != 0
        except ValueError:
            enabled = True
        if enabled:
            return f"PYTHONOPTIMIZE={raw!r} would remove assert-based evidence"
    return None


def run_captured_process_group(
    command: list[str], *, cwd: Path, timeout: int
) -> tuple[bool, bool, subprocess.CompletedProcess[str]]:
    """Capture a command and kill its whole POSIX process group on timeout."""
    popen_options: dict[str, object] = {}
    if os.name == "posix":
        popen_options["start_new_session"] = True
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        **popen_options,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        timed_out = False
        drain_timed_out = False
    except subprocess.TimeoutExpired:
        timed_out = True
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()
        try:
            stdout, stderr = process.communicate(timeout=PROCESS_DRAIN_TIMEOUT)
            drain_timed_out = False
        except subprocess.TimeoutExpired as drain_error:
            # A deliberately detached descendant can retain inherited pipes
            # after the original process group is gone.  Do not let that turn
            # a bounded gate timeout into an unbounded communicate().
            drain_timed_out = True
            stdout = drain_error.stdout or ""
            stderr = drain_error.stderr or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()
            try:
                process.wait(timeout=PROCESS_DRAIN_TIMEOUT)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=PROCESS_DRAIN_TIMEOUT)
    completed = subprocess.CompletedProcess(
        command, process.returncode, stdout or "", stderr or ""
    )
    return timed_out, drain_timed_out, completed


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
    optimization = python_optimization_reason()
    if optimization:
        print(json.dumps({
            "status": "FAIL",
            "error": "optimized Python cannot collect assert-based evidence",
            "detail": optimization,
        }), file=sys.stderr)
        return 1
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
        if not name.startswith("test_") or not inspect.isfunction(function):
            continue
        signature = inspect.signature(function)
        if signature.parameters:
            failures += 1
            print(json.dumps({
                "status": "FAIL",
                "error": "module test requires unsupported parameters",
                "test": name,
                "signature": str(signature),
            }), file=sys.stderr)
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
    # A partially skipped evidence file is still incomplete.  Returning 77
    # lets the outer aggregate gate reject it by default and admit it only
    # when the caller explicitly supplies --allow-skip.
    return 77 if skipped else 0


def execute_entry(plugin: str, test_rel: str, source_rel: str, timeout: int) -> dict[str, object]:
    test_path, source_path = ROOT / test_rel, ROOT / source_rel
    # Script-style probes under tools/ own their main() and must not pass merely
    # because importing them collected zero unittest/pytest tests.
    command = ([sys.executable, str(test_path)] if test_rel.startswith("tools/") else
               [sys.executable, str(Path(__file__).resolve()), "--run-test-file", str(test_path)])
    started = time.monotonic()
    dependencies = dependency_hashes(test_rel, source_rel)
    row: dict[str, object] = {
        "plugin": plugin, "test": test_rel, "source": source_rel,
        "command": command, "test_sha256": sha256(test_path),
        "source_sha256": sha256(source_path),
        "dependency_sha256": dependencies,
        "timeout_seconds": timeout,
    }
    missing = [rel for rel, digest in dependencies.items() if digest is None]
    if row["test_sha256"] is None or missing:
        if row["test_sha256"] is None:
            missing.insert(0, test_rel)
        row.update(
            status="FAIL", duration_seconds=0.0, exit_code=None,
            timed_out=False, timeout_drain_incomplete=False,
            stderr="missing test or dependencies: " + ", ".join(dict.fromkeys(missing)),
        )
        return row
    try:
        timed_out, drain_timed_out, completed = run_captured_process_group(
            command, cwd=ROOT, timeout=timeout
        )
        if timed_out:
            row.update(
                status="FAIL", exit_code=None, timed_out=True,
                timeout_drain_incomplete=drain_timed_out,
                termination_returncode=completed.returncode,
                stdout=completed.stdout[-4000:],
                stderr=(f"timeout after {timeout}s\n" + completed.stderr)[-4000:],
            )
        else:
            status = (
                "PASS" if completed.returncode == 0 else
                "SKIP" if completed.returncode == 77 else "FAIL"
            )
            row.update(
                status=status, exit_code=completed.returncode, timed_out=False,
                timeout_drain_incomplete=False,
                stdout=completed.stdout[-4000:], stderr=completed.stderr[-4000:],
            )
    except OSError as exc:
        row.update(
            status="FAIL", exit_code=None, timed_out=False,
            timeout_drain_incomplete=False,
            stderr=f"process launch failed: {type(exc).__name__}: {exc}",
        )
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
    started_at = datetime.now(timezone.utc).isoformat()
    run_id = uuid.uuid4().hex
    identity = {
        "schema": "olm.generic-beta-gate/1",
        "run_id": run_id,
        "started_at": started_at,
        "gate_sha256": sha256(Path(__file__).resolve()),
        "manifest_sha256": manifest_sha256(),
        "allow_skip": args.allow_skip,
    }
    running_payload: dict[str, object] = {
        **identity,
        "generated_at": started_at,
        "status": "RUNNING",
        "counts": {state: 0 for state in ("PASS", "FAIL", "SKIP")},
        "plugin_summary": {},
        "entries": [],
    }
    atomic_write_json(args.report, running_payload)
    optimization = python_optimization_reason()
    if optimization:
        failed_payload = {
            **running_payload,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "FAIL",
            "error": "optimized Python cannot execute assert-based evidence",
            "detail": optimization,
        }
        atomic_write_json(args.report, failed_payload)
        print(json.dumps(failed_payload, indent=2, sort_keys=True))
        return 1
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
        **identity,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "status": overall,
        "counts": {state: sum(row["status"] == state for row in rows) for state in ("PASS", "FAIL", "SKIP")},
        "plugin_summary": plugin_summary,
        "entries": rows,
    }
    atomic_write_json(args.report, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
