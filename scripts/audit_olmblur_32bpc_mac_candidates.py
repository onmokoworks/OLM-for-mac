#!/usr/bin/env python3
"""Materialize a fail-closed OLMBlur 32bpc Mac/Windows EXR audit report.

The report compares exact FLOAT RGBA semantic planes.  There is deliberately
no tolerance, epsilon, or numeric normalization in this audit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from compare_float_exr import read_planes  # noqa: E402
from verify_32bpc_float_return import VerificationError  # noqa: E402


CHANNELS = ("A", "B", "G", "R")
CASE_TOKENS = ("id", "source_case_id")
NO_OP_TAILS = ("_before_effects", "__no_effect", "__no_op", "__noop")
EFFECT_TAILS = ("", "__effect_on", "__effect", "__effects")
BUILT_IN_PARAMS = {"ADBE Effect Mask Opacity", "ADBE Force CPU GPU"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def case_tokens(case: dict[str, Any]) -> set[str]:
    primary = case.get("id") or case.get("source_case_id")
    tokens = {str(primary)} if primary else set()
    tokens.update({token.replace("__", "_") for token in list(tokens)})
    return tokens


def artifact_kind(stem: str, tokens: set[str]) -> str | None:
    for token in sorted(tokens, key=len, reverse=True):
        match = re.search(r"(?:^|__)" + re.escape(token.lower()) + r"(?P<tail>.*)$", stem.lower())
        if not match:
            continue
        tail = match.group("tail")
        if tail in NO_OP_TAILS:
            return "no_op"
        if tail in EFFECT_TAILS:
            return "effect"
    return None


def find_artifact(root: Path, case: dict[str, Any], no_op: bool) -> Path:
    if not root.is_dir():
        raise VerificationError(f"artifact root does not exist or is not a directory: {root}")
    tokens = case_tokens(case)
    matches = []
    for path in sorted(root.rglob("*.exr")):
        kind = artifact_kind(path.stem, tokens)
        if kind == ("no_op" if no_op else "effect"):
            matches.append(path)
    if len(matches) != 1:
        label = "no-op" if no_op else "effect"
        raise VerificationError(f"{root}: expected exactly one {label} EXR for {sorted(tokens)!r}, found {len(matches)}")
    return matches[0]


def provenance_hash(root: Path) -> str | None:
    """Read only explicit AEX hash fields from JSON provenance sidecars."""
    keys = {"aex_sha256", "plugin_aex_sha256", "plugin_binary_sha256", "binary_sha256"}
    plugin_objects = {"loaded_plugin", "plugin_binary", "installed_plugin"}
    hashes: set[str] = set()
    for path in sorted(root.rglob("*.json")):
        try:
            value = load_json(path)
        except (OSError, ValueError):
            continue
        stack = [value]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                for key, candidate in item.items():
                    if key.lower() in plugin_objects and isinstance(candidate, dict):
                        sha = candidate.get("sha256")
                        if isinstance(sha, str) and re.fullmatch(r"[0-9a-fA-F]{64}", sha):
                            hashes.add(sha.lower())
                for key, candidate in item.items():
                    if key.lower() in keys and isinstance(candidate, str) and re.fullmatch(r"[0-9a-fA-F]{64}", candidate):
                        hashes.add(candidate.lower())
                    stack.append(candidate)
            elif isinstance(item, list):
                stack.extend(item)
    if len(hashes) > 1:
        raise VerificationError(f"{root}: conflicting explicit plug-in SHA-256 values: {sorted(hashes)!r}")
    return next(iter(hashes), None)


def inspect(path: Path) -> tuple[dict[str, bytes], int, int]:
    planes, width, height = read_planes(path)
    return planes, width, height


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact_label(root: Path, path: Path) -> str:
    """Keep reports portable by recording artifacts relative to their lane root."""
    return path.relative_to(root).as_posix()


def artifact_record(root: Path, path: Path) -> dict[str, Any]:
    return {"path": artifact_label(root, path), "sha256": file_digest(path), "size_bytes": path.stat().st_size}


def repo_label(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.name


def required_json(root: Path, filename: str) -> dict[str, Any]:
    path = root / filename
    value = load_json(path)
    if not isinstance(value, dict):
        raise VerificationError(f"{path}: expected a JSON object")
    return value


def mac_return(root: Path) -> dict[str, Any]:
    matches = []
    for path in sorted(root.rglob("*.json")):
        try:
            value = load_json(path)
        except (OSError, ValueError):
            continue
        if isinstance(value, dict) and value.get("kind") == "olmblur_32bpc_mac_validation_return":
            matches.append(value)
    if len(matches) != 1:
        raise VerificationError(f"{root}: expected one OLMBlur Mac validation return, found {len(matches)}")
    return matches[0]


def select_case(cases: Any, case_id: str, label: str) -> dict[str, Any]:
    matches = [case for case in cases if isinstance(case, dict) and case.get("id") == case_id] if isinstance(cases, list) else []
    if len(matches) != 1:
        raise VerificationError(f"{label}: expected one {case_id} case, found {len(matches)}")
    return matches[0]


def parameter_map(rows: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        key = row.get("match_name") or row.get("name")
        if isinstance(key, str) and key not in BUILT_IN_PARAMS and "value" in row:
            result[key] = row["value"]
    return result


def parameter_value_equal(left: Any, right: Any) -> bool:
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(parameter_value_equal(a, b) for a, b in zip(left, right))
    if isinstance(left, (int, float)) and not isinstance(left, bool) and isinstance(right, (int, float)) and not isinstance(right, bool):
        return struct.pack("<f", float(left)) == struct.pack("<f", float(right))
    return left == right


def compare_parameters(expected: dict[str, Any], actual: dict[str, Any]) -> list[dict[str, Any]]:
    differences = []
    for key, value in expected.items():
        if key not in actual:
            differences.append({"match_name": key, "expected": value, "actual": None, "reason": "missing"})
        elif not parameter_value_equal(value, actual[key]):
            differences.append({"match_name": key, "expected": value, "actual": actual[key], "reason": "value_mismatch"})
    return differences


def environment_contract(windows: dict[str, Any], mac: dict[str, Any], mac_case: dict[str, Any]) -> dict[str, bool]:
    windows_project = windows.get("project") if isinstance(windows.get("project"), dict) else {}
    windows_gpu = windows_project.get("project_gpu_accel_type") if isinstance(windows_project.get("project_gpu_accel_type"), dict) else {}
    windows_output = windows.get("output_capabilities") if isinstance(windows.get("output_capabilities"), dict) else {}
    mac_project = mac.get("project") if isinstance(mac.get("project"), dict) else {}
    mac_output = mac.get("output_module") if isinstance(mac.get("output_module"), dict) else {}
    mac_intent = mac_output.get("intent") if isinstance(mac_output.get("intent"), dict) else {}
    outputs = mac_case.get("outputs") if isinstance(mac_case.get("outputs"), dict) else {}
    no_op_settings = (outputs.get("no_effect") or {}).get("output_module_settings", {})
    effect_settings = (outputs.get("effect_on") or {}).get("output_module_settings", {})
    checks = {
        "ae_version": windows.get("ae_version") == "26.3x87" and mac.get("ae_version") == "26.3x87",
        "bit_depth": windows_project.get("bits_per_channel") == 32 and mac_project.get("bits_per_channel") == 32,
        "software_renderer": windows_gpu.get("current_name") == "SOFTWARE" and mac_project.get("renderer") == "SOFTWARE",
        "working_space_none": windows_project.get("working_space") in ("", "None") and mac_project.get("working_space") in ("", "None"),
        "linear_light_off": windows_project.get("linearize_working_space") is False and windows_project.get("blend_colors_using_1_0_gamma") is False and mac_project.get("linear_blending") is False,
        "float_exr_template": windows_output.get("output_format") == "exr" and windows_output.get("float_preserving") is True and windows_output.get("output_template") == "OLM EXR 32 Float" and mac_output.get("template_name") == "OLM EXR 32 Float",
        "windows_output_module_readback": windows_output.get("output_module_readback_verified") is True,
        "mac_float_intent": mac_intent == {"channels": ["A", "B", "G", "R"], "compression": "none", "sample_type": "FLOAT"},
        "mac_output_settings_pair": bool(no_op_settings.get("sha256")) and no_op_settings.get("serialization") == effect_settings.get("serialization") and no_op_settings.get("sha256") == effect_settings.get("sha256"),
    }
    return checks


def compare(left: Path, right: Path) -> dict[str, Any]:
    left_planes, left_w, left_h = inspect(left)
    right_planes, right_w, right_h = inspect(right)
    dimensions_match = (left_w, left_h) == (right_w, right_h)
    counts: dict[str, int] = {}
    max_delta: dict[str, int] = {}
    if dimensions_match:
        for channel in CHANNELS:
            count = 0
            delta = 0
            for offset in range(0, len(left_planes[channel]), 4):
                a = left_planes[channel][offset:offset + 4]
                b = right_planes[channel][offset:offset + 4]
                if a != b:
                    count += 1
                    delta = max(delta, abs(int.from_bytes(a, "little") - int.from_bytes(b, "little")))
            counts[channel] = count
            max_delta[channel] = delta
    else:
        counts = {channel: None for channel in CHANNELS}  # type: ignore[assignment]
        max_delta = {channel: None for channel in CHANNELS}  # type: ignore[assignment]
    mismatched_values = sum(counts.values()) if dimensions_match else None
    max_raw_u32_delta = max(max_delta.values()) if dimensions_match else None
    return {
        "match": dimensions_match and all(value == 0 for value in counts.values()),
        "dimensions": {"reference": [left_w, left_h], "candidate": [right_w, right_h], "match": dimensions_match},
        "mismatched_values": mismatched_values,
        "mismatched_values_by_channel": counts,
        "max_raw_u32_delta": max_raw_u32_delta,
        "max_raw_u32_delta_by_channel": max_delta,
        "alpha_mismatch": counts["A"],
    }


def audit(
    spec_path: Path,
    windows_root: Path,
    mac_effect_root: Path,
    mac_noop_root: Path,
    selected_case_ids: set[str] | None = None,
) -> dict[str, Any]:
    spec = load_json(spec_path)
    if spec.get("scope", {}).get("bit_depth") != "32bpc" or spec.get("effect", {}).get("match_name") != "OLM OLM Blur":
        raise VerificationError("focused spec is not the OLMBlur 32bpc spec")
    cases = spec.get("cases")
    if not isinstance(cases, list) or not cases:
        raise VerificationError("focused spec has no cases")
    if selected_case_ids:
        cases = [case for case in cases if case.get("id") in selected_case_ids]
        found = {str(case.get("id")) for case in cases}
        missing = selected_case_ids - found
        if missing:
            raise VerificationError(f"requested case IDs are absent from focused spec: {sorted(missing)!r}")
    windows_manifest = required_json(windows_root, "reference_manifest.json")
    mac_result = mac_return(mac_effect_root)
    windows_aex_hash = provenance_hash(windows_root)
    mac_aex_hash = provenance_hash(mac_effect_root)
    mac_noop_hash = provenance_hash(mac_noop_root)
    rows = []
    for case in cases:
        case_id = case.get("id")
        if not isinstance(case_id, str):
            raise VerificationError("every focused-spec case must have a string id")
        win_effect = find_artifact(windows_root, case, False)
        win_noop = find_artifact(windows_root, case, True)
        mac_effect = find_artifact(mac_effect_root, case, False)
        mac_noop = find_artifact(mac_noop_root, case, True)
        noop = compare(win_noop, mac_noop)
        effect = compare(win_effect, mac_effect)
        windows_case = select_case(windows_manifest.get("cases"), case_id, "Windows reference manifest")
        mac_case = select_case(mac_result.get("cases"), case_id, "Mac validation return")
        expected_params = parameter_map(case.get("params_full"))
        windows_params = parameter_map((windows_case.get("effects") or [{}])[0].get("params"))
        mac_params = parameter_map(mac_case.get("params"))
        windows_param_differences = compare_parameters(expected_params, windows_params)
        mac_param_differences = compare_parameters(expected_params, mac_params)
        parameter_identity = not windows_param_differences and not mac_param_differences
        rows.append({
            "case_id": case_id,
            "windows": {
                "effect": artifact_record(windows_root, win_effect),
                "no_op": artifact_record(windows_root, win_noop),
            },
            "mac": {
                "effect": artifact_record(mac_effect_root, mac_effect),
                "no_op": artifact_record(mac_noop_root, mac_noop),
            },
            "parameter_identity": {
                "match": parameter_identity,
                "requested": expected_params,
                "windows_readback": windows_params,
                "mac_readback": mac_params,
                "windows_differences": windows_param_differences,
                "mac_differences": mac_param_differences,
            },
            "no_op": noop,
            "effect": effect,
            "effect_comparison_valid": False,
            "effect_result_classification": "pending_global_evidence_gates",
            "effect_attributable": False,
        })
    no_op_exact = all(row["no_op"]["match"] for row in rows)
    effect_exact = all(row["effect"]["match"] for row in rows)
    parameter_identity = all(row["parameter_identity"]["match"] for row in rows)
    windows_hash_present = bool(windows_aex_hash)
    mac_effect_hash_present = bool(mac_aex_hash)
    mac_noop_hash_present = bool(mac_noop_hash)
    mac_identity_consistent = bool(mac_aex_hash and mac_noop_hash and mac_aex_hash == mac_noop_hash)
    loaded_proof = mac_result.get("loaded_plugin_proof", {})
    loaded_plugin = mac_result.get("loaded_plugin", {})
    mac_loaded_module_bound = (
        isinstance(loaded_proof, dict)
        and isinstance(loaded_plugin, dict)
        and loaded_proof.get("method") == "vmmap_exact_path"
        and loaded_proof.get("module_sha256") == mac_aex_hash
        and loaded_proof.get("module_path") == loaded_plugin.get("path")
        and isinstance(loaded_proof.get("pid"), int)
        and loaded_proof.get("pid") > 0
        and loaded_proof.get("binary_predates_process_start") is True
    )
    mac_case_for_environment = select_case(mac_result.get("cases"), rows[0]["case_id"], "Mac validation return environment")
    environment_checks = environment_contract(windows_manifest, mac_result, mac_case_for_environment)
    environment_identity = all(environment_checks.values())
    provenance_exact = windows_hash_present and mac_effect_hash_present and mac_noop_hash_present and mac_identity_consistent and mac_loaded_module_bound
    for row in rows:
        row_valid = row["no_op"]["match"] and row["parameter_identity"]["match"] and environment_identity and provenance_exact
        row["effect_comparison_valid"] = row_valid
        row["effect_attributable"] = row_valid
        if row_valid:
            row["effect_result_classification"] = "exact" if row["effect"]["match"] else "known_red"
        elif not row["parameter_identity"]["match"] or not row["no_op"]["match"]:
            row["effect_result_classification"] = "invalid_parameter_or_control_identity"
        else:
            row["effect_result_classification"] = "invalid_environment_or_provenance_identity"
    effect_comparison_valid = all(row["effect_comparison_valid"] for row in rows)
    ae_exact = effect_comparison_valid and effect_exact and provenance_exact and environment_identity
    return {
        "schema": "olmblur_32bpc_mac_candidate_audit.v1",
        "focused_spec": repo_label(spec_path),
        "plugin": "OLMBlur",
        "bit_depth": "32bpc",
        "comparison": {"mode": "exact_float_semantic_planes", "tolerance": None, "tolerance_used": False},
        "environment": {
            "windows": {
                "ae_version": windows_manifest.get("ae_version"),
                "project": windows_manifest.get("project"),
                "output_capabilities": windows_manifest.get("output_capabilities"),
            },
            "mac": {
                "ae_version": mac_result.get("ae_version"),
                "project": mac_result.get("project"),
                "output_module": mac_result.get("output_module"),
                "input_sha256": ((mac_result.get("cases") or [{}])[0].get("input") or {}).get("sha256"),
                "plugin_binding": {
                    "method": loaded_proof.get("method") if isinstance(loaded_proof, dict) else None,
                    "sha256": mac_aex_hash,
                    "pid": loaded_proof.get("pid") if isinstance(loaded_proof, dict) else None,
                    "module_path_matches_return": loaded_proof.get("module_path") == loaded_plugin.get("path") if isinstance(loaded_proof, dict) and isinstance(loaded_plugin, dict) else False,
                    "binary_predates_process_start": loaded_proof.get("binary_predates_process_start") if isinstance(loaded_proof, dict) else None,
                },
            },
            "contract_checks": environment_checks,
        },
        "provenance": {
            "windows_aex_sha256": windows_aex_hash,
            "mac_effect_aex_sha256": mac_aex_hash,
            "mac_no_op_aex_sha256": mac_noop_hash,
            "mac_effect_no_op_identity_consistent": mac_identity_consistent,
            "mac_loaded_module_bound": mac_loaded_module_bound,
            "aex_hashes_present": provenance_exact,
        },
        "gates": {
            "no_op_exact": no_op_exact,
            "effect_exact": effect_exact,
            "parameter_identity": parameter_identity,
            "effect_comparison_valid": effect_comparison_valid,
            "environment_identity": environment_identity,
            "windows_aex_hash_present": windows_hash_present,
            "mac_effect_aex_hash_present": mac_effect_hash_present,
            "mac_no_op_aex_hash_present": mac_noop_hash_present,
            "mac_effect_no_op_identity_consistent": mac_identity_consistent,
            "mac_loaded_module_bound": mac_loaded_module_bound,
            "aex_hashes_present": provenance_exact,
            "ae_exact": ae_exact,
            "ae_exact_refused": not ae_exact,
            "refusal_reasons": [
                reason for reason, failed in (
                    ("no-op mismatch", not no_op_exact),
                    ("Windows/Mac effect parameter identity mismatch", not parameter_identity),
                    ("AE/project/color/output environment mismatch", not environment_identity),
                    ("effect mismatch", effect_comparison_valid and not effect_exact),
                    ("Windows AEX hash missing from provenance", not windows_hash_present),
                    ("Mac effect plug-in hash missing from provenance", not mac_effect_hash_present),
                    ("Mac no-op plug-in hash missing from provenance", not mac_noop_hash_present),
                    ("Mac effect/no-op plug-in identity mismatch", not mac_identity_consistent),
                    ("Mac plug-in is not bound to the AE process mapping", not mac_loaded_module_bound),
                ) if failed
            ],
        },
        "cases": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--focused-spec", required=True, type=Path)
    parser.add_argument("--windows-reference-dir", required=True, type=Path)
    parser.add_argument("--mac-effect-result-root", required=True, type=Path)
    parser.add_argument("--mac-no-op-result-root", required=True, type=Path)
    parser.add_argument("--case-id", action="append", default=[], help="Limit the audit to one or more exact spec case IDs")
    parser.add_argument("--output", required=True, type=Path, help="JSON report path; a Markdown sibling is also written")
    args = parser.parse_args()
    try:
        report = audit(
            args.focused_spec,
            args.windows_reference_dir,
            args.mac_effect_result_root,
            args.mac_no_op_result_root,
            set(args.case_id) or None,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        md = args.output.with_suffix(".md")
        lines = [
            "# OLMBlur 32bpc Mac candidate audit",
            "",
            f"Verdict: `{('AE exact' if report['gates']['ae_exact'] else 'AE exact refused')}`",
            "",
            "| case | parameters identical | no-op exact | no-op mismatches | effect comparison valid | effect exact | effect mismatches | max raw-u32 delta |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for row in report["cases"]:
            lines.append(
                f"| `{row['case_id']}` | {row['parameter_identity']['match']} | {row['no_op']['match']} "
                f"| {row['no_op']['mismatched_values']} | {row['effect_comparison_valid']} "
                f"| {row['effect']['match']} | {row['effect']['mismatched_values']} "
                f"| {row['effect']['max_raw_u32_delta']} |"
            )
            for difference in row["parameter_identity"]["windows_differences"]:
                lines.append(
                    f"- Windows parameter mismatch `{difference['match_name']}`: requested "
                    f"`{difference['expected']}`, read back `{difference['actual']}`."
                )
            lines.append(f"- Effect result classification: `{row['effect_result_classification']}`.")
        lines.extend([
            "",
            f"Mac effect/no-op plug-in SHA-256: `{report['provenance']['mac_effect_aex_sha256'] or 'missing'}`.",
            f"Windows AEX SHA-256: `{report['provenance']['windows_aex_sha256'] or 'missing'}`.",
            "",
            "Refusal reasons: " + (", ".join(report["gates"]["refusal_reasons"]) or "none") + ".",
            "",
        ])
        md.write_text("\n".join(lines), encoding="utf-8")
        print(f"[OK] wrote {args.output}")
        print(f"[OK] wrote {md}")
        return 0 if report["gates"]["ae_exact"] else 1
    except (OSError, ValueError, KeyError, VerificationError) as exc:
        print(f"[FAIL] {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
