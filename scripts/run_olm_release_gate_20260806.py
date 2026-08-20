#!/usr/bin/env python3
"""Fail-closed integration gate for the bounded ten-plugin Mac release.

Default operation reruns all fixed fixtures. ``--skip-regression`` is an audit
mode only and can never produce a releasable result.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "refs/conformance/olm_release_gate_manifest_20260806.json"
IDENTITY_MANIFEST = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
CURRENT_HOST_SMOKE = ROOT / "refs/conformance/olm_all10_post_colorkeep_count9_fresh_ae_smoke_20260813.json"
PREFLIGHT = ROOT / "scripts/preflight_olm_all_universal_installs_20260805.py"
REGRESSION = ROOT / "scripts/run_olm_mac_fixed_fixture_regression_20260805.py"
PARAMETER_UI_GATE = ROOT / "scripts/run_olm_parameter_ui_gate_20260806.py"
DEFAULT_REPORT = ROOT / "refs/conformance/olm_release_gate_status_20260806.json"
WINDOWS_BOUNDARY_INTAKE = ROOT / "refs/conformance/olm_windows_ae_release_boundary_minimal_intake_20260806.json"
CURRENT_HOST_SMOKE_RAW = ROOT / "refs/conformance/olm_all10_post_colorkeep_count9_fresh_ae_smoke_raw_20260813.json"
CURRENT_HOST_SMOKE_RUNNER = ROOT / "scripts/run_olm_all10_current_install_fresh_ae_smoke_20260812.py"
PLUGIN_NAMES = {
    "OLMBlur", "ColorKeep", "OLMColorKey", "OLMDirectionalBlur",
    "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur",
    "OLMSmoother", "OLMSmoother2", "OLMToonDilate",
}
WINDOWS_BOUNDARY_ROW_IDS = {
    f"colorkeep__discovery_3__colorkeep_opaque_cells_red_darkgray__{depth}bpc"
    for depth in (8, 16, 32)
} | {
    f"olmkirakira__controlled_ramps_off_10__kk_mapped_bm4_mm1_hi_r5_orange_opaque__{depth}bpc"
    for depth in (8, 16, 32)
} | {"olmsmoother_v1__canonical_3__case_0001__16bpc"}


def windows_boundary_gate() -> dict[str, Any]:
    payload = json.loads(WINDOWS_BOUNDARY_INTAKE.read_text(encoding="utf-8"))
    rows = payload.get("rows", [])
    if (
        payload.get("kind") != "olm_windows_ae_release_boundary_minimal_intake"
        or payload.get("status") != "accepted"
        or payload.get("after_effects") != "26.3x87"
        or payload.get("renderer_raw") != 1816
        or not isinstance(rows, list)
        or len(rows) != 7
    ):
        raise ValueError("Windows AE boundary intake is not accepted for exactly seven rows")
    row_ids = [row.get("row_id") for row in rows if isinstance(row, dict)]
    if len(set(row_ids)) != 7 or set(row_ids) != WINDOWS_BOUNDARY_ROW_IDS:
        raise ValueError("Windows AE boundary intake row set mismatch")
    if any(
        row.get("status") != "accepted"
        or not _hex_sha256(row.get("no_effect_sha256"))
        or not _hex_sha256(row.get("effect_on_sha256"))
        for row in rows
    ):
        raise ValueError("Windows AE boundary intake contains an unaccepted row")
    for field in ("contract_archive", "return_archive"):
        raw_path = payload.get(field)
        expected_sha = payload.get(f"{field}_sha256")
        if not isinstance(raw_path, str) or not _hex_sha256(expected_sha):
            raise ValueError(f"Windows AE boundary {field} binding invalid")
        path = ROOT / raw_path
        try:
            path.resolve().relative_to(ROOT.resolve())
        except ValueError as exc:
            raise ValueError(f"Windows AE boundary {field} outside repository") from exc
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha:
            raise ValueError(f"Windows AE boundary {field} digest mismatch")
    return {
        "state": "accepted_bounded_plugin_comparisons_complete",
        "accepted_rows": 7,
        "invalid_rows": 0,
        "after_effects": payload["after_effects"],
        "contract_archive_sha256": payload["contract_archive_sha256"],
        "return_archive_sha256": payload["return_archive_sha256"],
        "evidence": str(WINDOWS_BOUNDARY_INTAKE.relative_to(ROOT)),
        "boundary": (
            "The seven Windows AE process/module/parameter/EXR contracts are accepted. "
            "Bounded per-plugin comparisons are complete for ColorKeep PF8/PF16/PF32, "
            "OLMKiraKira Mode4 PF32 internals, and OLMSmoother v1 PF16 internals. This "
            "state does not claim blanket cross-host exported-pixel equality."
        ),
    }


def lookup(value: Any, dotted: str) -> Any:
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            raise KeyError(dotted)
        value = value[part]
    return value


def _hex_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def _file_sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _validate_artifact(binding: Any, label: str, failures: list[str]) -> None:
    if not isinstance(binding, dict):
        failures.append(f"{label}_binding_missing")
        return
    raw_path = binding.get("path")
    expected_sha = binding.get("sha256")
    if not isinstance(raw_path, str) or not _hex_sha256(expected_sha):
        failures.append(f"{label}_binding_invalid")
        return
    path = ROOT / raw_path
    try:
        path.resolve().relative_to(ROOT.resolve())
    except ValueError:
        failures.append(f"{label}_path_outside_repository")
        return
    if not path.is_file():
        failures.append(f"{label}_missing")
    elif hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha:
        failures.append(f"{label}_sha256_mismatch")


def _validate_smoke_raw(summary: dict[str, Any], failures: list[str]) -> None:
    raw_binding = summary.get("raw_report", {})
    runner_binding = summary.get("runner", {})
    expected_raw_path = CURRENT_HOST_SMOKE_RAW.relative_to(ROOT).as_posix()
    expected_runner_path = CURRENT_HOST_SMOKE_RUNNER.relative_to(ROOT).as_posix()
    if raw_binding.get("path") != expected_raw_path:
        failures.append("current_host_smoke_raw_path_mismatch")
    if runner_binding.get("path") != expected_runner_path:
        failures.append("current_host_smoke_runner_path_mismatch")
    if not CURRENT_HOST_SMOKE_RAW.is_file():
        return
    try:
        raw = json.loads(CURRENT_HOST_SMOKE_RAW.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"current_host_smoke_raw_invalid:{exc}")
        return
    if raw.get("schema") != "olm.all10-current-install-fresh-ae-smoke-raw/1":
        failures.append("current_host_smoke_raw_schema_mismatch")
    # The producer owns the complete raw/summary semantic contract (AE return,
    # vmmap, PNGs, payload and runner digests). Reuse that validator instead of
    # trusting a hand-edited green summary that merely cites a real raw file.
    try:
        spec = importlib.util.spec_from_file_location("olm_all10_current_smoke", CURRENT_HOST_SMOKE_RUNNER)
        if spec is None or spec.loader is None:
            raise ImportError("fresh smoke runner spec unavailable")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if module.validate_persisted_summary(summary, raw, CURRENT_HOST_SMOKE_RAW) is not True:
            failures.append("current_host_smoke_raw_semantic_validation_failed")
    except Exception as exc:
        failures.append(f"current_host_smoke_raw_validator_error:{exc}")


def validate_current_host_smoke(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Bind the host gate to the currently accepted ten-bundle identity set.

    Older per-plugin host records remain useful historical evidence, but cannot
    prove that the executables accepted by the current identity manifest loaded
    and rendered.  One fresh aggregate run must bind every row to the exact
    current executable hash and to the current manifest bytes/acceptance time.
    """
    common_failures: list[str] = []
    manifest_rows = manifest.get("plugins", [])
    if manifest.get("schema") != "olm.release-gate-manifest/2":
        common_failures.append("release_manifest_schema_mismatch")
    if manifest.get("current_identity_manifest") != IDENTITY_MANIFEST.relative_to(ROOT).as_posix():
        common_failures.append("release_manifest_identity_path_mismatch")
    if manifest.get("current_host_smoke") != CURRENT_HOST_SMOKE.relative_to(ROOT).as_posix():
        common_failures.append("release_manifest_host_smoke_path_mismatch")
    if not isinstance(manifest_rows, list) or len(manifest_rows) != 10:
        common_failures.append("release_manifest_plugin_cardinality_mismatch")
        manifest_rows = []
    expected_plugins = {
        spec.get("plugin"): spec for spec in manifest_rows if isinstance(spec, dict)
    }
    if len(expected_plugins) != 10 or set(expected_plugins) != PLUGIN_NAMES:
        common_failures.append("release_manifest_plugin_set_not_unique")
    if not IDENTITY_MANIFEST.is_file():
        identity: dict[str, Any] = {}
        common_failures.append("identity_manifest_missing")
    else:
        try:
            identity = json.loads(IDENTITY_MANIFEST.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            identity = {}
            common_failures.append(f"identity_manifest_invalid:{exc}")
    identity_sha = (
        hashlib.sha256(IDENTITY_MANIFEST.read_bytes()).hexdigest()
        if IDENTITY_MANIFEST.is_file()
        else None
    )
    identity_rows = identity.get("plugins", []) if isinstance(identity, dict) else []
    if not isinstance(identity_rows, list) or len(identity_rows) != 10:
        common_failures.append("identity_plugin_cardinality_mismatch")
        identity_rows = []
    accepted = {
        row.get("plugin"): row.get("sha256")
        for row in identity_rows
        if isinstance(row, dict)
    }
    if identity.get("schema") != "olm.installed-identity-manifest/1":
        common_failures.append("identity_schema_mismatch")
    if set(accepted) != set(expected_plugins) or any(not _hex_sha256(value) for value in accepted.values()):
        common_failures.append("identity_plugin_set_or_hash_invalid")
    if len(accepted) != len(identity_rows):
        common_failures.append("identity_plugin_set_not_unique")
    if not isinstance(identity.get("accepted_at"), str):
        common_failures.append("identity_accepted_at_missing")

    if not CURRENT_HOST_SMOKE.is_file():
        smoke: dict[str, Any] = {}
        common_failures.append("current_host_smoke_missing")
    else:
        try:
            smoke = json.loads(CURRENT_HOST_SMOKE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            smoke = {}
            common_failures.append(f"current_host_smoke_invalid:{exc}")

    if smoke.get("schema") != "olm.all10-current-install-fresh-ae-smoke/1":
        common_failures.append("current_host_smoke_schema_mismatch")
    if smoke.get("status") != "pass" or smoke.get("passed") is not True:
        common_failures.append("current_host_smoke_not_pass")
    binding = smoke.get("installed_identity_manifest", {})
    expected_identity_path = IDENTITY_MANIFEST.relative_to(ROOT).as_posix()
    if binding.get("path") != expected_identity_path:
        common_failures.append("current_host_smoke_identity_path_mismatch")
    if binding.get("sha256") != identity_sha:
        common_failures.append("current_host_smoke_identity_sha256_mismatch")
    if binding.get("accepted_at") != identity.get("accepted_at"):
        common_failures.append("current_host_smoke_identity_acceptance_mismatch")
    host = smoke.get("host", {})
    if host.get("process_count") != 1:
        common_failures.append("current_host_smoke_process_count_mismatch")
    if host.get("fresh_process") is not True:
        common_failures.append("current_host_smoke_process_not_fresh")
    if host.get("started_after_identity_acceptance") is not True:
        common_failures.append("current_host_smoke_process_too_old")
    if host.get("renderer") != "SOFTWARE":
        common_failures.append("current_host_smoke_renderer_mismatch")

    accepted_at = _parse_time(identity.get("accepted_at"))
    started_at = _parse_time(host.get("started_at"))
    captured_at = _parse_time(host.get("captured_at"))
    if accepted_at is None:
        common_failures.append("identity_accepted_at_invalid")
    if started_at is None or accepted_at is None or started_at <= accepted_at:
        common_failures.append("current_host_smoke_started_at_not_after_acceptance")
    if captured_at is None or started_at is None or captured_at < started_at:
        common_failures.append("current_host_smoke_captured_at_invalid")
    host_pid = host.get("pid")
    if not isinstance(host_pid, int) or host_pid <= 0:
        common_failures.append("current_host_smoke_pid_invalid")
    _validate_artifact(smoke.get("raw_report"), "current_host_smoke_raw", common_failures)
    _validate_artifact(smoke.get("runner"), "current_host_smoke_runner", common_failures)
    _validate_smoke_raw(smoke, common_failures)

    raw_smoke_rows = smoke.get("plugins", [])
    if not isinstance(raw_smoke_rows, list) or len(raw_smoke_rows) != 10:
        common_failures.append("current_host_smoke_plugin_cardinality_mismatch")
        raw_smoke_rows = []
    smoke_rows = {
        row.get("plugin"): row
        for row in raw_smoke_rows
        if isinstance(row, dict) and isinstance(row.get("plugin"), str)
    }
    if len(smoke_rows) != len(raw_smoke_rows):
        common_failures.append("current_host_smoke_plugin_set_not_unique")
    if set(smoke_rows) != set(expected_plugins):
        common_failures.append("current_host_smoke_plugin_set_mismatch")

    rows: list[dict[str, Any]] = []
    try:
        evidence = CURRENT_HOST_SMOKE.relative_to(ROOT).as_posix()
    except ValueError:
        evidence = str(CURRENT_HOST_SMOKE)
    for plugin, spec in expected_plugins.items():
        failures = list(common_failures)
        observed = smoke_rows.get(plugin, {})
        if observed.get("status") != "pass":
            failures.append("plugin_status_not_pass")
        for field in ("loaded", "applied", "host_frame_render_succeeded", "render_succeeded"):
            if observed.get(field) is not True:
                failures.append(f"plugin_{field}_not_true")
        expectation = spec.get("host_smoke_expectation")
        if observed.get("host_smoke_expectation") != expectation:
            failures.append("plugin_host_smoke_expectation_mismatch")
        if expectation == "enabled_host_frame_render":
            numerical_contract = {
                "effect_enabled_host_frame_attempted": True,
                "effect_enabled_host_frame_succeeded": True,
                "numerical_render_expected": False,
                "numerical_render_supported": False,
                "effect_enabled_numerical_render_attempted": False,
                "numerical_render_succeeded": None,
                "effect_disabled_during_host_frame": False,
            }
        elif expectation == "disabled_host_frame_render":
            numerical_contract = {
                "effect_enabled_host_frame_attempted": False,
                "effect_enabled_host_frame_succeeded": False,
                "numerical_render_expected": False,
                "numerical_render_supported": False,
                "effect_enabled_numerical_render_attempted": False,
                "numerical_render_succeeded": None,
                "effect_disabled_during_host_frame": True,
            }
        else:
            failures.append("plugin_host_smoke_expectation_invalid")
            numerical_contract = {}
        for field, expected in numerical_contract.items():
            if observed.get(field) is not expected:
                failures.append(f"plugin_{field}_mismatch")
        if observed.get("installed_executable_sha256") != accepted.get(plugin):
            failures.append("plugin_installed_identity_mismatch")
        identity_row = next(
            (row for row in identity_rows if isinstance(row, dict) and row.get("plugin") == plugin),
            {},
        )
        expected_path = str(Path(identity_row.get("installed_bundle", "")) / "Contents/MacOS" / plugin)
        if observed.get("loaded_module_path") != expected_path:
            failures.append("plugin_loaded_module_path_mismatch")
        if observed.get("loaded_module_count") != 1:
            failures.append("plugin_loaded_module_count_mismatch")
        if observed.get("ae_pid") != host_pid:
            failures.append("plugin_ae_pid_mismatch")
        if observed.get("post_render_mapping_exact") is not True:
            failures.append("plugin_post_render_mapping_not_exact")
        if observed.get("post_render_on_disk_sha256") != accepted.get(plugin):
            failures.append("plugin_post_render_identity_mismatch")
        rows.append({
            "plugin": plugin,
            "state": "invalid" if failures else "proven",
            "declared_state": "proven",
            "evidence": evidence,
            "boundary": spec["boundary"],
            "failures": failures,
        })
    return rows


def installed_gate() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(PREFLIGHT)], cwd=ROOT, capture_output=True, text=True
    )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"state": "invalid", "returncode": proc.returncode, "error": "preflight_non_json"}
    bundles = payload.get("bundles", [])
    identity = json.loads(IDENTITY_MANIFEST.read_text(encoding="utf-8"))
    expected_names = {row["plugin"] for row in identity.get("plugins", [])}
    observed_names = [row.get("name") for row in bundles]
    status_allowed = payload.get("status") in {
        "ae_not_running", "ready_for_hash_bound_host_runners", "restart_required"
    }
    exact = (
        proc.returncode in (0, 2)
        and status_allowed
        and len(bundles) == 10
        and len(set(observed_names)) == 10
        and set(observed_names) == expected_names
        and all(
        row.get("bundle_count") == 1
        and row.get("sha256_exact") is True
        and row.get("universal_exact") is True
        and row.get("codesign_exact") is True
        for row in bundles
        )
    )
    return {
        "state": "proven" if exact else "invalid",
        "returncode": proc.returncode,
        "preflight_status": payload.get("status"),
        "bundle_count": len(bundles),
        "bundles": [{k: row.get(k) for k in ("name", "sha256", "architectures", "sha256_exact", "universal_exact", "codesign_exact")} for row in bundles],
        "boundary": "Bundle identity/architectures/signature only; AE process state is reported but is not an install-identity failure.",
    }


def regression_gate(skip: bool) -> dict[str, Any]:
    if skip:
        return {"state": "pending", "reason": "skipped_by_audit_mode"}
    proc = subprocess.run(
        [sys.executable, str(REGRESSION)], cwd=ROOT, capture_output=True, text=True
    )
    output = proc.stdout + proc.stderr
    marker = "PASS_OLM_MAC_FIXED_FIXTURE_REGRESSION lanes=10"
    return {
        "state": "proven" if proc.returncode == 0 and marker in output else "invalid",
        "returncode": proc.returncode,
        "output_sha256": hashlib.sha256(output.encode()).hexdigest(),
        "summary": next((line for line in reversed(output.splitlines()) if "OLM_MAC_FIXED_FIXTURE_REGRESSION" in line), None),
        "tail": output.splitlines()[-20:],
        "boundary": "Only commands enumerated by the ten fixed-fixture lanes; slow RadialBlur full replay is excluded.",
    }


def parameter_ui_gate() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="olm_parameter_ui_release_gate_") as raw:
        report_path = Path(raw) / "report.json"
        try:
            proc = subprocess.run(
                [sys.executable, str(PARAMETER_UI_GATE), "--report", str(report_path)],
                cwd=ROOT, capture_output=True, text=True, timeout=600,
            )
        except subprocess.TimeoutExpired as exc:
            return {"state": "invalid", "error": "parameter_ui_gate_timeout", "detail": str(exc)}
        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return {
                "state": "invalid", "returncode": proc.returncode,
                "error": f"parameter_ui_report_invalid:{exc}",
                "tail": (proc.stdout + proc.stderr).splitlines()[-20:],
            }
    exact = (
        proc.returncode == 0
        and payload.get("passed") is True
        and payload.get("counts") == {"proven": 10, "pending": 0, "invalid": 0}
    )
    return {
        "state": "proven" if exact else "invalid",
        "returncode": proc.returncode,
        "status": payload.get("status"),
        "counts": payload.get("counts"),
        "bounded_count": payload.get("bounded_count"),
        "plugins": [
            {k: row.get(k) for k in ("plugin", "state", "classification", "boundary", "failures")}
            for row in payload.get("plugins", [])
        ],
        "boundary": payload.get("claim_boundary"),
    }


def release_predicate(
    install: dict[str, Any], regression: dict[str, Any],
    parameter_ui: dict[str, Any], windows_boundary: dict[str, Any],
    host_counts: dict[str, int],
) -> bool:
    """One auditable top-level GO predicate for every independent boundary."""
    return (
        install.get("state") == "proven"
        and regression.get("state") == "proven"
        and parameter_ui.get("state") == "proven"
        and windows_boundary.get("state") == "accepted_bounded_plugin_comparisons_complete"
        and windows_boundary.get("accepted_rows") == 7
        and host_counts == {"proven": 10, "pending": 0, "invalid": 0}
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-regression", action="store_true", help="audit manifests/installs only; result stays pending")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    host_rows = validate_current_host_smoke(manifest)
    install = installed_gate()
    regression = regression_gate(args.skip_regression)
    parameter_ui = parameter_ui_gate()
    windows_boundary = windows_boundary_gate()
    host_counts = {state: sum(row["state"] == state for row in host_rows) for state in ("proven", "pending", "invalid")}
    releasable = release_predicate(
        install, regression, parameter_ui, windows_boundary, host_counts
    )
    report = {
        "schema": "olm.release-gate-report/1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "release_gate_pass" if releasable else "release_gate_pending_or_invalid",
        "releasable": releasable,
        "claim_boundary": (
            manifest["claim_boundary"]
            + " Seven Windows AE release-boundary observations are accepted; "
            "cross-host exactness remains a per-plugin claim."
        ),
        "windows_ae_release_boundary": windows_boundary,
        "fixed_fixture_regression": regression,
        "parameter_ui_registration": parameter_ui,
        "universal_installs": install,
        "mac_ae_representative": {"counts": host_counts, "plugins": host_rows},
        "valid_for": {
            "release_manifest_path": MANIFEST.relative_to(ROOT).as_posix(),
            "release_manifest_sha256": _file_sha256(MANIFEST),
            "installed_identity_manifest_path": IDENTITY_MANIFEST.relative_to(ROOT).as_posix(),
            "installed_identity_manifest_sha256": _file_sha256(IDENTITY_MANIFEST),
            "current_host_smoke_path": CURRENT_HOST_SMOKE.relative_to(ROOT).as_posix(),
            "current_host_smoke_sha256": _file_sha256(CURRENT_HOST_SMOKE),
            "current_host_smoke_raw_path": CURRENT_HOST_SMOKE_RAW.relative_to(ROOT).as_posix(),
            "current_host_smoke_raw_sha256": _file_sha256(CURRENT_HOST_SMOKE_RAW),
            "current_host_smoke_runner_path": CURRENT_HOST_SMOKE_RUNNER.relative_to(ROOT).as_posix(),
            "current_host_smoke_runner_sha256": _file_sha256(CURRENT_HOST_SMOKE_RUNNER),
            "release_gate_runner_path": Path(__file__).resolve().relative_to(ROOT).as_posix(),
            "release_gate_runner_sha256": _file_sha256(Path(__file__).resolve()),
            "windows_boundary_intake_path": WINDOWS_BOUNDARY_INTAKE.relative_to(ROOT).as_posix(),
            "windows_boundary_intake_sha256": _file_sha256(WINDOWS_BOUNDARY_INTAKE),
        },
    }
    report_path = args.report if args.report.is_absolute() else ROOT / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if releasable else 1


if __name__ == "__main__":
    raise SystemExit(main())
