#!/usr/bin/env python3
"""Prepare or complete the identity-bound OLMBlur 16bpc case 0003/0004 gate.

This wrapper never launches After Effects. A later session may provide a
loaded-module proof and a returned candidate directory for the authoritative
true16 comparison.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUEST_ROOT = ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmblur_exact_20260625"
REQUEST_MANIFEST = REQUEST_ROOT / "request_manifest.json"
REFERENCE_MANIFEST = REQUEST_ROOT / "reference_manifest.json"
CONTRACT = ROOT / "refs/conformance/olmblur_16bpc_candidates_mac_validation_20260716.json"
SELECTED = ("olmblur__case_0003", "olmblur__case_0004")
SOURCE_FILES = ("mac/OLMBlur/OLMBlur.cpp", "core/olmblur_worker16_legacy.cpp")
REQUEST_SHA256 = "1ff908fca5b733a629ff6a72f107278f94a2510a3a6e192ae969bb90ca070047"
REFERENCE_SHA256 = "c4378358c8b4db2b2d5d12d0bf0b4142f141963538ca5ec4d86a49eeb8b9e71e"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_revision() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def committed_source_identity(revision: str) -> list[dict[str, str]]:
    identities = []
    for relative in SOURCE_FILES:
        path = ROOT / relative
        working = path.read_bytes()
        committed = subprocess.run(
            ["git", "show", f"{revision}:{relative}"], cwd=ROOT, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout
        if working != committed:
            raise ValueError(f"candidate source differs from {revision}: {relative}")
        identities.append({"path": relative, "sha256": hashlib.sha256(working).hexdigest()})
    return identities


def load_selected() -> tuple[dict, dict]:
    if sha256(REQUEST_MANIFEST) != REQUEST_SHA256:
        raise ValueError("request manifest hash drifted")
    if sha256(REFERENCE_MANIFEST) != REFERENCE_SHA256:
        raise ValueError("reference manifest hash drifted")
    request = json.loads(REQUEST_MANIFEST.read_text(encoding="utf-8"))
    reference = json.loads(REFERENCE_MANIFEST.read_text(encoding="utf-8"))
    cases = request.get("cases", [])
    ids = tuple(case.get("id") for case in cases)
    if set(SELECTED) - set(ids):
        raise ValueError("selected case is missing from the existing request")
    ref_ids = {case.get("id") for case in reference.get("cases", [])}
    if set(SELECTED) - ref_ids:
        raise ValueError("selected case is missing from the reference manifest")
    selected = [case for case in cases if case.get("id") in SELECTED]
    if {case["id"] for case in selected} != set(SELECTED):
        raise ValueError("request case selection is not exactly case_0003 and case_0004")
    return request, reference


def build_contract(source_revision: str, source_files: list[dict[str, str]],
                   binary_path: Path, binary_sha256: str) -> dict:
    request, reference = load_selected()
    reference_cases = {case["id"]: case for case in reference["cases"]}
    cases = []
    for case in request["cases"]:
        if case["id"] not in SELECTED:
            continue
        input_path = REQUEST_ROOT / "input" / case["before_effects_frame"]
        expected_path = REQUEST_ROOT / "expected" / case["frame"]
        if not input_path.is_file() or not expected_path.is_file():
            raise ValueError(f"missing selected input/reference for {case['id']}")
        cases.append({
            "id": case["id"],
            "input": {"path": str(input_path.relative_to(ROOT)), "sha256": sha256(input_path)},
            "reference": {"path": str(expected_path.relative_to(ROOT)), "sha256": sha256(expected_path)},
            "reference_manifest_case": reference_cases[case["id"]].get("frame"),
        })
    return {
        "kind": "olmblur_16bpc_candidates_mac_validation_contract",
        "schema": 1,
        "record_id": "olmblur_16bpc_candidates_mac_validation_20260716",
        "status": "pending_live_loaded_module_proof",
        "platform": "macOS-only",
        "ae_execution": "not_run_by_this_wrapper",
        "source_identity": {"git_revision_required": source_revision, "files": source_files},
        "binary_identity": {"path": str(binary_path.relative_to(ROOT)), "sha256": binary_sha256,
                            "hash_algorithm": "sha256"},
        "request_identity": {
            "request_manifest": str(REQUEST_MANIFEST.relative_to(ROOT)),
            "request_manifest_sha256": REQUEST_SHA256,
            "reference_manifest": str(REFERENCE_MANIFEST.relative_to(ROOT)),
            "reference_manifest_sha256": REFERENCE_SHA256,
            "selected_case_ids": list(SELECTED),
        },
        "cases": cases,
        "required_future_proof": {
            "loaded_module": "explicit runtime proof of the exact hashed binary, path, PID, AE session, and render nonce",
            "comparison": "authoritative true16 channel words for both selected outputs against the pinned references",
            "promotion": "exact is permitted only when loaded-module identity and raw true16 equality both pass",
        },
        "fail_closed": [
            "missing source git revision",
            "missing binary or binary hash mismatch",
            "missing, stale, or ambiguous loaded-module proof",
            "PNG-only, byte-view, or pre-store-only evidence",
            "any candidate/reference mismatch or missing selected case",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-revision", required=True, help="Git revision used for the candidate build")
    parser.add_argument("--binary-path", type=Path, required=True, help="Built OLMBlur binary to hash")
    parser.add_argument("--output", type=Path, default=CONTRACT, help="Pending contract output")
    parser.add_argument("--loaded-module-proof", type=Path, help="Future AE runtime proof JSON")
    parser.add_argument("--candidate-dir", type=Path, help="Future AE candidate output directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        actual_revision = git_revision()
        if args.source_revision != actual_revision:
            raise ValueError(f"source revision is not current HEAD: {args.source_revision} != {actual_revision}")
        binary_path = args.binary_path.expanduser().resolve()
        if not binary_path.is_file():
            raise ValueError(f"built binary is missing: {binary_path}")
        try:
            binary_path.relative_to(ROOT)
        except ValueError as error:
            raise ValueError("built binary must be inside the project tree") from error
        binary_hash = sha256(binary_path)
        source_files = committed_source_identity(actual_revision)
        contract = build_contract(actual_revision, source_files, binary_path, binary_hash)
        if args.loaded_module_proof or args.candidate_dir:
            raise ValueError("live loaded-module proof and true16 comparison are reserved for a future AE session")
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError) as error:
        print(f"FAIL-CLOSED: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"status": contract["status"], "cases": list(SELECTED), "contract": str(output)}, indent=2))
    print("PAUSED: live loaded-module proof and authoritative true16 comparison are required after AE.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
