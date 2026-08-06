#!/usr/bin/env python3
"""Fail-closed integration gate for the bounded ten-plugin Mac release.

Default operation reruns all fixed fixtures. ``--skip-regression`` is an audit
mode only and can never produce a releasable result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "refs/conformance/olm_release_gate_manifest_20260806.json"
PREFLIGHT = ROOT / "scripts/preflight_olm_all_universal_installs_20260805.py"
REGRESSION = ROOT / "scripts/run_olm_mac_fixed_fixture_regression_20260805.py"
PARAMETER_UI_GATE = ROOT / "scripts/run_olm_parameter_ui_gate_20260806.py"
DEFAULT_REPORT = ROOT / "refs/conformance/olm_release_gate_status_20260806.json"
WINDOWS_BOUNDARY_INTAKE = ROOT / "refs/conformance/olm_windows_ae_release_boundary_minimal_intake_20260806.json"


def windows_boundary_gate() -> dict[str, Any]:
    payload = json.loads(WINDOWS_BOUNDARY_INTAKE.read_text(encoding="utf-8"))
    rows = payload.get("rows", [])
    if payload.get("status") != "accepted" or len(rows) != 7:
        raise ValueError("Windows AE boundary intake is not accepted for exactly seven rows")
    if any(row.get("status") != "accepted" for row in rows):
        raise ValueError("Windows AE boundary intake contains an unaccepted row")
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


def validate_host_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for spec in manifest["plugins"]:
        path = ROOT / spec["evidence"]
        failures: list[str] = []
        if not path.is_file():
            failures.append("evidence_missing")
        elif path.suffix == ".json":
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                for dotted, expected in spec.get("assertions", {}).items():
                    try:
                        actual = lookup(payload, dotted)
                    except KeyError:
                        failures.append(f"missing:{dotted}")
                    else:
                        if actual != expected:
                            failures.append(f"mismatch:{dotted}")
            except (OSError, json.JSONDecodeError) as exc:
                failures.append(f"invalid_json:{exc}")
        else:
            text = path.read_text(encoding="utf-8")
            for needle in spec.get("contains", []):
                if needle not in text:
                    failures.append(f"missing_text:{needle}")
        declared = spec["state"]
        state = "invalid" if failures else declared
        rows.append({
            "plugin": spec["plugin"], "state": state,
            "declared_state": declared, "evidence": spec["evidence"],
            "boundary": spec["boundary"], "failures": failures,
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
    exact = len(bundles) == 10 and all(
        row.get("bundle_count") == 1
        and row.get("sha256_exact") is True
        and row.get("universal_exact") is True
        and row.get("codesign_exact") is True
        for row in bundles
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-regression", action="store_true", help="audit manifests/installs only; result stays pending")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    host_rows = validate_host_rows(manifest)
    install = installed_gate()
    regression = regression_gate(args.skip_regression)
    parameter_ui = parameter_ui_gate()
    windows_boundary = windows_boundary_gate()
    host_counts = {state: sum(row["state"] == state for row in host_rows) for state in ("proven", "pending", "invalid")}
    releasable = (
        install["state"] == "proven"
        and regression["state"] == "proven"
        and parameter_ui["state"] == "proven"
        and host_counts == {"proven": 10, "pending": 0, "invalid": 0}
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
    }
    report_path = args.report if args.report.is_absolute() else ROOT / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if releasable else 1


if __name__ == "__main__":
    raise SystemExit(main())
