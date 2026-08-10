#!/usr/bin/env python3
"""Fail-closed actual-AEX parameter registration gate for all ten OLM plugins."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "refs/conformance/olm_parameter_ui_gate_manifest_20260806.json"
DEFAULT_REPORT = ROOT / "refs/conformance/olm_parameter_ui_gate_status_20260806.json"
EXPECTED_PLUGINS = {
    "OLMBlur", "ColorKeep", "OLMColorKey", "OLMDirectionalBlur",
    "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur",
    "OLMSmoother", "OLMSmoother2", "OLMToonDilate",
}


def lookup(value: Any, dotted: str) -> Any:
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            raise KeyError(dotted)
        value = value[part]
    return value


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    rows = manifest.get("plugins")
    accepted = manifest.get("accepted_classes")
    if manifest.get("schema") != "olm.parameter-ui-gate-manifest/1":
        failures.append("manifest_schema")
    if not isinstance(manifest.get("claim_boundary"), str) or not manifest["claim_boundary"].strip():
        failures.append("claim_boundary")
    if not isinstance(accepted, list) or set(accepted) != {
        "exact_normalized_registration", "bounded_public_registration"
    }:
        failures.append("accepted_classes")
    if not isinstance(rows, list) or len(rows) != 10:
        failures.append("plugin_count")
        return failures
    names = [row.get("plugin") for row in rows if isinstance(row, dict)]
    if len(names) != 10 or set(names) != EXPECTED_PLUGINS or len(set(names)) != 10:
        failures.append("plugin_set")
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            failures.append(f"row_{index}:not_object")
            continue
        prefix = str(row.get("plugin", index))
        if row.get("classification") not in accepted:
            failures.append(f"{prefix}:classification")
        for key in ("runner", "evidence", "boundary"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                failures.append(f"{prefix}:{key}")
        if row.get("classification") == "bounded_public_registration" and len(row.get("boundary", "")) < 40:
            failures.append(f"{prefix}:bounded_without_explicit_boundary")
        for check_index, check in enumerate(row.get("dynamic_checks", [])):
            if not isinstance(check, dict):
                failures.append(f"{prefix}:dynamic_{check_index}:not_object")
                continue
            for key in ("runner", "evidence"):
                if not isinstance(check.get(key), str) or not check[key].strip():
                    failures.append(f"{prefix}:dynamic_{check_index}:{key}")
    return failures


def evaluate_row(spec: dict[str, Any], run_runner: bool) -> dict[str, Any]:
    failures: list[str] = []
    runner_result: dict[str, Any]
    runner = ROOT / spec["runner"]
    evidence = ROOT / spec["evidence"]
    # Focused comparators regenerate their durable report. Preserve the checked-in
    # witness bytes so an audit cannot dirty the worktree merely because a raw
    # capture contains process-local pointer residue outside its normalized claim.
    original_evidence = evidence.read_bytes() if evidence.is_file() else None
    if not runner.is_file():
        failures.append("runner_missing")
        runner_result = {"state": "invalid"}
    elif run_runner:
        try:
            proc = subprocess.run(
                [sys.executable, str(runner)], cwd=ROOT, capture_output=True,
                text=True, timeout=180,
            )
        except subprocess.TimeoutExpired as exc:
            failures.append("runner_timeout")
            runner_result = {"state": "invalid", "timeout_seconds": 180, "error": str(exc)}
        else:
            output = proc.stdout + proc.stderr
            runner_result = {
                "state": "proven" if proc.returncode == 0 else "invalid",
                "returncode": proc.returncode,
                "output_sha256": hashlib.sha256(output.encode()).hexdigest(),
                "tail": [line[-1000:] for line in output.splitlines()[-8:]],
            }
            if proc.returncode != 0:
                failures.append(f"runner_exit:{proc.returncode}")
    else:
        runner_result = {"state": "pending", "reason": "skipped_by_audit_mode"}

    payload: dict[str, Any] | None = None
    if not evidence.is_file():
        failures.append("evidence_missing")
    else:
        try:
            payload = json.loads(evidence.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"evidence_invalid_json:{exc}")
    if payload is not None:
        for dotted, expected in spec.get("assertions", {}).items():
            try:
                actual = lookup(payload, dotted)
            except KeyError:
                failures.append(f"missing:{dotted}")
            else:
                if actual != expected:
                    failures.append(f"mismatch:{dotted}")
        for dotted, expected in spec.get("list_lengths", {}).items():
            try:
                actual = lookup(payload, dotted)
            except KeyError:
                failures.append(f"missing:{dotted}")
            else:
                if not isinstance(actual, list) or len(actual) != expected:
                    failures.append(f"length_mismatch:{dotted}")
    if original_evidence is not None and evidence.is_file() and evidence.read_bytes() != original_evidence:
        evidence.write_bytes(original_evidence)

    dynamic_results: list[dict[str, Any]] = []
    for check_index, check in enumerate(spec.get("dynamic_checks", [])):
        check_failures: list[str] = []
        check_runner = ROOT / check["runner"]
        check_evidence = ROOT / check["evidence"]
        original_check_evidence = check_evidence.read_bytes() if check_evidence.is_file() else None
        if not check_runner.is_file():
            check_failures.append("runner_missing")
            check_result = {"state": "invalid"}
        elif run_runner:
            try:
                check_proc = subprocess.run(
                    [sys.executable, str(check_runner)], cwd=ROOT,
                    capture_output=True, text=True, timeout=180,
                )
            except subprocess.TimeoutExpired as exc:
                check_failures.append("runner_timeout")
                check_result = {"state": "invalid", "error": str(exc)}
            else:
                check_output = check_proc.stdout + check_proc.stderr
                check_result = {
                    "state": "proven" if check_proc.returncode == 0 else "invalid",
                    "returncode": check_proc.returncode,
                    "output_sha256": hashlib.sha256(check_output.encode()).hexdigest(),
                    "tail": [line[-1000:] for line in check_output.splitlines()[-8:]],
                }
                if check_proc.returncode != 0:
                    check_failures.append(f"runner_exit:{check_proc.returncode}")
        else:
            check_result = {"state": "pending", "reason": "skipped_by_audit_mode"}

        if not check_evidence.is_file():
            check_failures.append("evidence_missing")
        else:
            try:
                check_payload = json.loads(check_evidence.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                check_failures.append(f"evidence_invalid_json:{exc}")
            else:
                for dotted, expected in check.get("assertions", {}).items():
                    try:
                        actual = lookup(check_payload, dotted)
                    except KeyError:
                        check_failures.append(f"missing:{dotted}")
                    else:
                        if actual != expected:
                            check_failures.append(f"mismatch:{dotted}")
        if (original_check_evidence is not None and check_evidence.is_file()
                and check_evidence.read_bytes() != original_check_evidence):
            check_evidence.write_bytes(original_check_evidence)
        failures.extend(f"dynamic_{check_index}:{failure}" for failure in check_failures)
        dynamic_results.append({
            "runner": check["runner"], "evidence": check["evidence"],
            "runner_result": check_result, "failures": check_failures,
        })

    if failures:
        state = "invalid"
    elif not run_runner:
        state = "pending"
    else:
        state = "proven"
    return {
        "plugin": spec["plugin"],
        "state": state,
        "classification": spec["classification"],
        "runner": spec["runner"],
        "runner_result": runner_result,
        "dynamic_checks": dynamic_results,
        "evidence": spec["evidence"],
        "boundary": spec["boundary"],
        "failures": failures,
    }


def run_gate(manifest: dict[str, Any], run_runners: bool) -> dict[str, Any]:
    manifest_failures = validate_manifest(manifest)
    rows = [] if manifest_failures else [evaluate_row(spec, run_runners) for spec in manifest["plugins"]]
    counts = {state: sum(row["state"] == state for row in rows) for state in ("proven", "pending", "invalid")}
    bounded = sum(row.get("classification") == "bounded_public_registration" for row in rows)
    passed = not manifest_failures and counts == {"proven": 10, "pending": 0, "invalid": 0}
    return {
        "schema": "olm.parameter-ui-gate-report/1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "parameter_ui_gate_pass" if passed else "parameter_ui_gate_pending_or_invalid",
        "passed": passed,
        "claim_boundary": manifest.get("claim_boundary"),
        "manifest_failures": manifest_failures,
        "counts": counts,
        "bounded_count": bounded,
        "plugins": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-runners", action="store_true", help="manifest/evidence audit only; can never pass")
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    manifest_path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report = {
            "schema": "olm.parameter-ui-gate-report/1", "status": "parameter_ui_gate_pending_or_invalid",
            "passed": False, "manifest_failures": [f"manifest_invalid:{exc}"], "plugins": [],
        }
    else:
        report = run_gate(manifest, not args.skip_runners)
    report_path = args.report if args.report.is_absolute() else ROOT / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("passed") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
