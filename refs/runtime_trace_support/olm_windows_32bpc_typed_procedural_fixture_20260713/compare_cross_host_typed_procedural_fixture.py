#!/usr/bin/env python3
"""Fail-closed compare for typed-procedural 32bpc render records."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "fixture"))

from compare_float_exr import compare  # noqa: E402
from verify_32bpc_float_return import VerificationError, inspect_float_rgba_exr  # noqa: E402


EXPECTED_KIND = "olm_32bpc_typed_procedural_render_record"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_zip(path: Path) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if path.is_dir():
        return path.resolve(), None
    if path.is_file() and path.suffix.lower() == ".zip":
        temp = tempfile.TemporaryDirectory(prefix="typed_proc_compare_")
        root = Path(temp.name)
        with zipfile.ZipFile(path) as archive:
            archive.extractall(root)
        children = [item for item in root.iterdir()]
        if len(children) == 1 and children[0].is_dir():
            return children[0], temp
        return root, temp
    if path.is_file() and path.suffix.lower() == ".json":
        return path.parent.resolve(), None
    raise VerificationError(f"unsupported compare input: {path}")


def load_record(locator: Path) -> tuple[dict[str, Any], Path, tempfile.TemporaryDirectory[str] | None]:
    root, temp = extract_zip(locator)
    candidates = []
    if locator.is_file() and locator.suffix.lower() == ".json":
        candidates.append(locator.resolve())
    candidates.extend(
        path
        for name in ("return_manifest.json", "reference_manifest.json", "render_record.json")
        for path in root.rglob(name)
    )
    if not candidates:
        raise VerificationError(f"{locator}: no render record found")
    record_path = sorted(candidates)[0]
    payload = json.loads(record_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict) or payload.get("kind") != EXPECTED_KIND:
        raise VerificationError(f"{record_path}: unexpected record kind")
    return payload, record_path.parent, temp


def require_case_map(record: dict[str, Any], root: Path) -> dict[str, dict[str, Any]]:
    if record.get("schema") != 1:
        raise VerificationError("render record schema must be 1")
    if record.get("required_ae_major_minor") != "26.3":
        raise VerificationError("render record must pin AE 26.3")
    if record.get("output_template") != "OLM EXR 32 Float":
        raise VerificationError("render record must pin OLM EXR 32 Float")
    platform = record.get("platform")
    if platform not in {"windows", "macos"}:
        raise VerificationError("render record platform must be windows or macos")
    if not isinstance(record.get("fixture_jsx_sha256"), str) or len(record["fixture_jsx_sha256"]) != 64:
        raise VerificationError("render record fixture_jsx_sha256 missing or invalid")
    cases = record.get("cases")
    if not isinstance(cases, list) or not cases:
        raise VerificationError("render record has no cases")
    output: dict[str, dict[str, Any]] = {}
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise VerificationError("case id is required")
        if not isinstance(case.get("effect"), str) or not case["effect"]:
            raise VerificationError(f"{case.get('id')}: effect is required")
        plugin = case.get("plugin")
        if not isinstance(plugin, dict) or not isinstance(plugin.get("name"), str):
            raise VerificationError(f"{case['id']}: plugin metadata is required")
        contract = case.get("fixture_contract")
        if not isinstance(contract, dict):
            raise VerificationError(f"{case['id']}: fixture_contract is required")
        required_pairs = {
            "manifest_kind": "olm_32bpc_typed_procedural_fixture",
            "project_bits_per_channel": 32,
            "working_space": "None",
            "linear_blending": False,
            "frame": 0,
            "source_policy": "AE-generated solids only; no footage imported",
            "render_policy": "same comp, only branch enabled state changes",
        }
        for key, expected in required_pairs.items():
            if contract.get(key) != expected:
                raise VerificationError(f"{case['id']}: fixture_contract.{key} mismatch")
        if contract.get("dimensions") != [64, 64]:
            raise VerificationError(f"{case['id']}: fixture dimensions must be [64, 64]")
        if contract.get("output_names") != {
            "no_effect": "effect_no_effect_00000.exr",
            "effect_on": "effect_effect_on_00000.exr",
        }:
            raise VerificationError(f"{case['id']}: fixture output names mismatch")
        layers = contract.get("source_layers")
        if not isinstance(layers, list) or len(layers) != 5:
            raise VerificationError(f"{case['id']}: fixture source_layers mismatch")
        outputs = case.get("outputs")
        if not isinstance(outputs, dict):
            raise VerificationError(f"{case['id']}: outputs object missing")
        normalized_outputs: dict[str, dict[str, Any]] = {}
        for name in ("no_effect", "effect_on"):
            row = outputs.get(name)
            if not isinstance(row, dict):
                raise VerificationError(f"{case['id']}: outputs.{name} missing")
            rel = row.get("path")
            stated_sha = row.get("sha256")
            if not isinstance(rel, str) or not rel:
                raise VerificationError(f"{case['id']}: outputs.{name}.path missing")
            if not isinstance(stated_sha, str) or len(stated_sha) != 64:
                raise VerificationError(f"{case['id']}: outputs.{name}.sha256 missing")
            path = (root / rel).resolve()
            if not path.is_file():
                raise VerificationError(f"{case['id']}: outputs.{name} file missing: {rel}")
            actual_sha = sha256(path)
            if actual_sha != stated_sha.lower():
                raise VerificationError(f"{case['id']}: outputs.{name} sha256 mismatch")
            inspected = inspect_float_rgba_exr(path, expected_dimensions=(64, 64))
            normalized_outputs[name] = {
                "path": path,
                "sha256": actual_sha,
                "inspection": inspected,
            }
        output[case["id"]] = {
            "id": case["id"],
            "effect": case["effect"],
            "plugin": plugin,
            "fixture_contract": contract,
            "outputs": normalized_outputs,
        }
    return output


def compare_records(left_record: dict[str, Any], left_root: Path, right_record: dict[str, Any], right_root: Path) -> dict[str, Any]:
    if left_record.get("platform") == right_record.get("platform"):
        raise VerificationError("compare requires two different platforms")
    if left_record.get("fixture_jsx_sha256") != right_record.get("fixture_jsx_sha256"):
        raise VerificationError("fixture_jsx_sha256 mismatch between hosts")
    left_cases = require_case_map(left_record, left_root)
    right_cases = require_case_map(right_record, right_root)
    if set(left_cases) != set(right_cases):
        raise VerificationError("case sets differ between records")
    results = []
    for case_id in sorted(left_cases):
        left_case = left_cases[case_id]
        right_case = right_cases[case_id]
        if left_case["effect"] != right_case["effect"]:
            raise VerificationError(f"{case_id}: effect name mismatch")
        if left_case["fixture_contract"] != right_case["fixture_contract"]:
            raise VerificationError(f"{case_id}: fixture contract mismatch")
        no_effect = compare(left_case["outputs"]["no_effect"]["path"], right_case["outputs"]["no_effect"]["path"])
        effect_on = compare(left_case["outputs"]["effect_on"]["path"], right_case["outputs"]["effect_on"]["path"])
        left_delta = compare(left_case["outputs"]["no_effect"]["path"], left_case["outputs"]["effect_on"]["path"])
        right_delta = compare(right_case["outputs"]["no_effect"]["path"], right_case["outputs"]["effect_on"]["path"])
        if no_effect["mismatched_values"] != 0:
            raise VerificationError(f"{case_id}: no_effect is not raw-float-bit exact across hosts")
        if effect_on["mismatched_values"] != 0:
            raise VerificationError(f"{case_id}: effect_on is not raw-float-bit exact across hosts")
        results.append(
            {
                "id": case_id,
                "effect": left_case["effect"],
                "platforms": [left_record["platform"], right_record["platform"]],
                "no_effect_cross_host": no_effect,
                "effect_on_cross_host": effect_on,
                "left_internal_delta": left_delta,
                "right_internal_delta": right_delta,
                "status": "raw-float-bits-exact",
            }
        )
    return {
        "status": "pass",
        "fixture_jsx_sha256": left_record["fixture_jsx_sha256"],
        "platforms": [left_record["platform"], right_record["platform"]],
        "cases": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    temp_objects: list[tempfile.TemporaryDirectory[str]] = []
    try:
        left_record, left_root, left_temp = load_record(args.left)
        right_record, right_root, right_temp = load_record(args.right)
        if left_temp is not None:
            temp_objects.append(left_temp)
        if right_temp is not None:
            temp_objects.append(right_temp)
        result = compare_records(left_record, left_root, right_record, right_root)
    except (OSError, ValueError, KeyError, VerificationError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1
    finally:
        for temp in temp_objects:
            temp.cleanup()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for case in result["cases"]:
            print(
                f"[PASS] {case['id']} no_effect={case['no_effect_cross_host']['mismatched_values']} "
                f"effect_on={case['effect_on_cross_host']['mismatched_values']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
