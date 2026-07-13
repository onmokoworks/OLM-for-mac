#!/usr/bin/env python3
"""Render reproducible Mac AE 32bpc EXR candidates for focused request specs.

The resulting index is a Mac candidate record, not a Windows reference result
and not an AE-exact verdict. It exists so a valid Windows EXR return can be
compared immediately without rerendering the Mac side.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import struct
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from materialize_32bpc_mac_request import materialize
from verify_32bpc_float_return import (
    VerificationError,
    canonical_sha256,
    inspect_float_rgba_exr,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPECS = (
    ("refs/reference_requests/olm_bitdepth_32bpc_colorkey_float_20260710.json", "refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMbit-depthconformancebatch"),
    ("refs/reference_requests/olm_bitdepth_32bpc_toondilate_float_20260710.json", "refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMbit-depthconformancebatch"),
)
ARTIFACT_RUNS = (
    {
        "key": "effect_on",
        "label": "effect-on FLOAT EXR",
        "effect_disabled": False,
        "ae_env": {"OLM_AE_FORCE_NEW_PROJECT": "1"},
    },
    {
        "key": "no_effect",
        "label": "no-effect FLOAT EXR",
        "effect_disabled": True,
        "ae_env": {
            "OLM_AE_DISABLE_EFFECT": "1",
            "OLM_AE_FORCE_NEW_PROJECT": "1",
        },
    },
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, default=Path("/tmp/olm_ae_32bpc_mac_candidates"))
    parser.add_argument("--output-template", default="OLM EXR 32 Float")
    parser.add_argument("--app-name", default="Adobe After Effects 2026")
    parser.add_argument("--timeout", type=int, default=1200)
    parser.add_argument("--request-id", default="", help="Render only one focused request id.")
    parser.add_argument("--case-id", default="", help="Render only one exact focused case id.")
    parser.add_argument("--dry-run", action="store_true", help="Materialize bridges and write the planned index without starting AE.")
    parser.add_argument("--keep-open", action="store_true", help="Keep AE open after each case instead of quitting it.")
    parser.add_argument("--ae-exit-timeout", type=float, default=90.0, help="Seconds to wait for AE to fully exit between paired runs.")
    parser.add_argument("--runner-timeout", type=float, default=180.0, help="Fail one artifact when the AE single-case runner stops responding.")
    parser.add_argument(
        "--plugin-binary",
        action="append",
        default=[],
        metavar="MATCH_NAME=PATH",
        help="Explicit Mac .plugin binary binding for one exact effect match_name. Repeat per effect; required for actual Darwin runs.",
    )
    return parser.parse_args()


def bridge_dir(work_dir: Path, request_id: str, case_id: str) -> Path:
    return work_dir / "bridges" / request_id / case_id


def exr_summary(path: Path) -> dict[str, Any]:
    return inspect_float_rgba_exr(path)


def artifact_output_dir(output_dir: Path, key: str) -> Path:
    return output_dir / key


def runner_output_path(output_dir: Path) -> Path:
    return output_dir / "RUNNER_OUTPUT.txt"


def wait_for_ae_exit(timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        probe = subprocess.run(
            ["pgrep", "-x", "After Effects"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if probe.returncode != 0:
            return True
        time.sleep(0.25)
    return False


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def parse_plugin_binary_bindings(values: list[str]) -> dict[str, Path]:
    bindings: dict[str, Path] = {}
    for value in values:
        match_name, separator, raw_path = value.partition("=")
        match_name = match_name.strip()
        raw_path = raw_path.strip()
        if separator != "=" or not match_name or not raw_path:
            raise ValueError(f"invalid --plugin-binary {value!r}; expected MATCH_NAME=PATH")
        binary_path = Path(raw_path).expanduser().resolve(strict=False)
        existing = bindings.get(match_name)
        if existing is not None and existing != binary_path:
            raise ValueError(f"duplicate --plugin-binary for {match_name!r}")
        bindings[match_name] = binary_path
    return bindings


def case_effect_match_name(spec: dict[str, Any], case: dict[str, Any], *, request_id: str, case_id: str) -> str:
    effect = case.get("effect")
    if not isinstance(effect, dict):
        effect = spec.get("effect")
    if not isinstance(effect, dict):
        raise ValueError(f"{request_id} {case_id}: missing effect object for explicit Mac plugin binding")
    match_name = effect.get("match_name")
    if not isinstance(match_name, str) or not match_name.strip() or match_name == "mixed":
        raise ValueError(f"{request_id} {case_id}: exact effect.match_name is required for --plugin-binary binding")
    return match_name


def planned_plugin_binding(match_name: str, binary_path: Path | None) -> dict[str, Any]:
    record: dict[str, Any] = {
        "match_name": match_name,
        "state": "unbound" if binary_path is None else "planned",
        "required_for_actual_run": True,
    }
    if binary_path is not None:
        record["binary_path"] = str(binary_path)
    return record


def resolve_actual_plugin_binding(planned: dict[str, Any], *, request_id: str, case_id: str) -> dict[str, Any]:
    match_name = str(planned["match_name"])
    binary_value = planned.get("binary_path")
    if not isinstance(binary_value, str) or not binary_value:
        raise ValueError(f"{request_id} {case_id}: missing --plugin-binary for effect match_name {match_name!r}")
    binary_path = Path(binary_value)
    if not binary_path.is_file():
        raise ValueError(f"{request_id} {case_id}: bound Mac plugin binary is not a file: {binary_path}")
    resolved = binary_path.resolve(strict=True)
    return {
        "match_name": match_name,
        "state": "bound",
        "required_for_actual_run": True,
        "binary_path": str(resolved),
        "sha256": file_sha256(resolved),
    }


def artifact_record(run_spec: dict[str, Any], output_dir: Path, state: str) -> dict[str, Any]:
    return {
        "label": run_spec["label"],
        "state": state,
        "effect_disabled": run_spec["effect_disabled"],
        "ae_env": dict(run_spec["ae_env"]),
        "output_dir": str(output_dir),
        "runner_output": str(runner_output_path(output_dir)),
    }


def run_artifact(
    *,
    run_spec: dict[str, Any],
    bridge: Path,
    case_id: str,
    output_dir: Path,
    args: argparse.Namespace,
    mac_plugin_binding: dict[str, Any] | None,
) -> dict[str, Any]:
    record = artifact_record(run_spec, output_dir, "pending")
    if not wait_for_ae_exit(args.ae_exit_timeout):
        record.update({"state": "error", "error": "prior_ae_process_did_not_exit"})
        return record
    command = [
        sys.executable,
        str(ROOT / "scripts/run_ae_single_case.py"),
        "--request-dir",
        str(bridge),
        "--case-id",
        case_id,
        "--output-dir",
        str(output_dir),
        "--output-mode",
        "exr_render_queue",
        "--output-template",
        args.output_template,
        "--app-name",
        args.app_name,
        "--timeout",
        str(args.timeout),
    ]
    for key, value in sorted(run_spec["ae_env"].items()):
        command.extend(["--ae-env", f"{key}={value}"])
    if args.keep_open:
        command.append("--keep-open")
    try:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=args.runner_timeout,
        )
    except subprocess.TimeoutExpired as exc:
        output_dir.mkdir(parents=True, exist_ok=True)
        runner_output_path(output_dir).write_text(exc.stdout or "", encoding="utf-8")
        record.update({"state": "error", "error": "ae_single_case_runner_timeout"})
        return record
    output_dir.mkdir(parents=True, exist_ok=True)
    runner_output = runner_output_path(output_dir)
    runner_output.write_text(proc.stdout, encoding="utf-8")
    record["runner_exit"] = proc.returncode
    if not args.keep_open and not wait_for_ae_exit(args.ae_exit_timeout):
        record.update({"state": "error", "error": "ae_process_did_not_exit_after_run"})
        return record
    result_path = output_dir / "AE_SINGLE_CASE_RESULT.json"
    record["result_path"] = str(result_path)
    if proc.returncode != 0 or not result_path.is_file():
        record.update({"state": "error", "error": "runner_failed"})
        return record
    result = load_json(result_path)
    if run_spec["key"] == "effect_on" and mac_plugin_binding is not None:
        bound_plugin_sha256 = mac_plugin_binding.get("sha256")
        if not isinstance(bound_plugin_sha256, str) or len(bound_plugin_sha256) != 64:
            record.update({"state": "error", "error": "missing_bound_plugin_sha256"})
            return record
        # This binds the intended installed binary. It is not proof that AE
        # loaded that path; only a host/module observation may use "loaded".
        record["bound_plugin_sha256"] = bound_plugin_sha256
    record["result"] = result
    exr_value = result.get("output_exr")
    exr = Path(exr_value) if isinstance(exr_value, str) else None
    expected_effect_disabled = run_spec["effect_disabled"]
    if result.get("status") != "ok":
        record.update({"state": "error", "error": "runner_result_not_ok"})
        return record
    if result.get("effect_disabled") is not expected_effect_disabled:
        record.update({
            "state": "error",
            "error": "effect_disabled_mismatch",
            "expected_effect_disabled": expected_effect_disabled,
        })
        return record
    if exr is None or not exr.is_file():
        record.update({"state": "error", "error": "missing_output_exr"})
        return record
    try:
        summary = exr_summary(exr.resolve())
    except (OSError, ValueError, struct.error, VerificationError) as exc:
        record.update({"state": "error", "error": "invalid_output_exr", "validation_error": str(exc)})
        return record
    record.update({
        "state": "rendered",
        "sha256": summary["sha256"],
        "exr": summary,
    })
    return record


def main() -> int:
    try:
        args = parse_args()
        if args.keep_open and not args.dry_run:
            raise ValueError("--keep-open is incompatible with paired effect/control collection")
        plugin_binary_bindings = parse_plugin_binary_bindings(args.plugin_binary)
    except ValueError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1
    work_dir = args.work_dir.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    candidates_dir = work_dir / "candidates"
    candidates_dir.mkdir(exist_ok=True)
    rows: list[dict[str, Any]] = []
    selected_cases: list[dict[str, Any]] = []

    for spec_rel, source_rel in DEFAULT_SPECS:
        spec_path = ROOT / spec_rel
        source_reference = ROOT / source_rel
        spec = load_json(spec_path)
        request_id = str(spec["request_id"])
        if args.request_id and request_id != args.request_id:
            continue
        for case in spec["cases"]:
            case_id = str(case["id"])
            if args.case_id and case_id != args.case_id:
                continue
            try:
                match_name = case_effect_match_name(spec, case, request_id=request_id, case_id=case_id)
            except ValueError as exc:
                print(f"[FAIL] {exc}", file=sys.stderr)
                return 1
            selected_cases.append({
                "spec_path": spec_path,
                "source_reference": source_reference,
                "spec": spec,
                "request_id": request_id,
                "case": case,
                "case_id": case_id,
                "match_name": match_name,
            })

    actual_plugin_bindings: dict[str, dict[str, Any]] = {}
    if not args.dry_run and platform.system() == "Darwin":
        required_match_names = sorted({str(item["match_name"]) for item in selected_cases})
        try:
            for match_name in required_match_names:
                actual_plugin_bindings[match_name] = resolve_actual_plugin_binding(
                    planned_plugin_binding(match_name, plugin_binary_bindings.get(match_name)),
                    request_id="actual-run",
                    case_id=match_name,
                )
        except ValueError as exc:
            print(f"[FAIL] {exc}", file=sys.stderr)
            return 1

    for item in selected_cases:
        spec_path = Path(item["spec_path"])
        source_reference = Path(item["source_reference"])
        request_id = str(item["request_id"])
        case = dict(item["case"])
        case_id = str(item["case_id"])
        match_name = str(item["match_name"])
        bridge = bridge_dir(work_dir, request_id, case_id)
        if not bridge.exists():
            materialize(spec_path, source_reference, bridge, case_id)
        output_dir = candidates_dir / request_id / case_id
        mac_plugin_binding = planned_plugin_binding(match_name, plugin_binary_bindings.get(match_name))
        if not args.dry_run and platform.system() == "Darwin":
            mac_plugin_binding = dict(actual_plugin_bindings[match_name])
        artifacts = {
            run_spec["key"]: artifact_record(
                run_spec,
                artifact_output_dir(output_dir, run_spec["key"]),
                "planned" if args.dry_run else "pending",
            )
            for run_spec in ARTIFACT_RUNS
        }
        row: dict[str, Any] = {
            "request_id": request_id,
            "case_id": case_id,
            "bridge_dir": str(bridge),
            "output_dir": str(output_dir),
            "case": case,
            "bit_depth": "32bpc",
            "bits_per_channel": 32,
            "params_sha256": canonical_sha256(case.get("params_full")),
            "candidate_contract": "mac-float-rgba-exr-v1",
            "mac_plugin_binding": mac_plugin_binding,
            "artifacts": artifacts,
            "state": "planned" if args.dry_run else "pending",
            "readiness": {
                "bridge_materialized": True,
                "ae_gui_required": True,
                "executed": False,
                "validated": False,
                "artifact_keys": [run_spec["key"] for run_spec in ARTIFACT_RUNS],
                "host_platform": platform.system(),
                "plugin_binding_required": True,
            },
        }
        if not args.dry_run and platform.system() != "Darwin":
            row.update({
                "state": "not_run_host_platform",
                "artifacts": {
                    run_spec["key"]: artifact_record(
                        run_spec,
                        artifact_output_dir(output_dir, run_spec["key"]),
                        "not_run_host_platform",
                    )
                    for run_spec in ARTIFACT_RUNS
                },
                "readiness": {
                    **row["readiness"],
                    "reason": "AE GUI candidate execution is a Mac-only no-op on this host",
                },
            })
        elif not args.dry_run:
            rendered_artifacts: dict[str, Any] = {}
            for run_spec in ARTIFACT_RUNS:
                artifact = run_artifact(
                    run_spec=run_spec,
                    bridge=bridge,
                    case_id=case_id,
                    output_dir=artifact_output_dir(output_dir, run_spec["key"]),
                    args=args,
                    mac_plugin_binding=mac_plugin_binding,
                )
                rendered_artifacts[run_spec["key"]] = artifact
            row["artifacts"] = rendered_artifacts
            effect_on = rendered_artifacts["effect_on"]
            if "result" in effect_on:
                row["result"] = effect_on["result"]
            if "exr" in effect_on:
                row["exr"] = effect_on["exr"]
            if all(artifact["state"] == "rendered" for artifact in rendered_artifacts.values()):
                row.update({
                    "state": "rendered",
                    "readiness": {**row["readiness"], "executed": True, "validated": True},
                })
            else:
                row.update({
                    "state": "error",
                    "readiness": {**row["readiness"], "executed": True, "validated": False},
                    "artifact_errors": {
                        key: artifact.get("error", artifact["state"])
                        for key, artifact in rendered_artifacts.items()
                        if artifact["state"] != "rendered"
                    },
                })
        rows.append(row)
        print(f"[{row['state'].upper()}] {request_id} {case_id}")

    index = {
        "kind": "olm_mac_ae_32bpc_candidate_index",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output_template": args.output_template,
        "output_mode": "exr_render_queue",
        "host_platform": platform.system(),
        "ae_exact_claim": False,
        "execution": {
            "ae_gui_required": True,
            "status": "not_run" if args.dry_run or platform.system() != "Darwin" else "executed",
            "plugin_binary_bindings_required_for_actual_run": True,
            "note": "Mac candidate EXRs only; this index is never an AE exact verdict.",
        },
        "candidates": rows,
    }
    index_path = work_dir / "MAC_32BPC_CANDIDATE_INDEX.json"
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    rendered = sum(row["state"] == "rendered" for row in rows)
    errors = sum(row["state"] == "error" for row in rows)
    readiness_path = work_dir / "MAC_32BPC_READINESS.json"
    readiness_path.write_text(json.dumps({
        "kind": "olm_mac_ae_32bpc_candidate_readiness",
        "status": "ready_for_mac_ae_gui" if any(row["state"] in {"planned", "not_run_host_platform"} for row in rows) else "rendered_and_validated",
        "executed": any(row["readiness"].get("executed") for row in rows),
        "host_platform": platform.system(),
        "candidate_index": str(index_path),
        "note": "AE GUI execution is required for Mac candidates and is not performed by --dry-run or on non-Mac hosts.",
    }, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] candidate index: {index_path}")
    print(f"[OK] readiness package: {readiness_path}")
    print(f"[SUMMARY] planned={len(rows)} rendered={rendered} errors={errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
