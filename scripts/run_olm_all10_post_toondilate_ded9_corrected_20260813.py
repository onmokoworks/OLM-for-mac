#!/usr/bin/env python3
"""Read-only corrected-contract validator; ``--run`` performs one exclusive AE smoke."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
THIS = Path(__file__).resolve()
BASE_PATH = ROOT / "scripts/run_olm_all10_current_install_fresh_ae_smoke_20260812.py"
BASE_PAYLOAD = ROOT / "scripts/ae_host_all10_current_install_fresh_validation_20260812.jsx"
PAYLOAD = ROOT / "scripts/ae_host_all10_post_toondilate_ded9_corrected_20260813.jsx"
PAIRED = ROOT / "refs/conformance/olmtoondilate_same_source_public_paired_replay_20260813.json"
NEGATIVE = ROOT / "refs/conformance/olmtoondilate_public_admission_negative_closure_20260813.json"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
INSTALL_REPORT = ROOT / "refs/conformance/olmtoondilate_ded9_incremental_install_identity_20260813.json"
CONTRACT_REPORT = ROOT / "refs/conformance/olm_all10_post_toondilate_ded9_corrected_contract_20260813.json"
RAW = ROOT / "refs/conformance/olm_all10_post_toondilate_ded9_corrected_fresh_ae_smoke_raw_20260813.json"
SUMMARY = ROOT / "refs/conformance/olm_all10_post_toondilate_ded9_corrected_fresh_ae_smoke_20260813.json"
ARTIFACT_DIR = ROOT / "handoffs/olm_all10_post_toondilate_ded9_corrected_fresh_ae_smoke_20260813"
RECEIPT = ARTIFACT_DIR.with_name(ARTIFACT_DIR.name + ".invocation-receipt.json")
FAILED_RAW = ROOT / "refs/conformance/olm_all10_post_toondilate_ded9_fresh_ae_smoke_raw_20260813.json"
FAILED_SUMMARY = ROOT / "refs/conformance/olm_all10_post_toondilate_ded9_fresh_ae_smoke_20260813.json"
FAILED_RECEIPT = ROOT / "handoffs/olm_all10_post_toondilate_ded9_fresh_ae_smoke_20260813.invocation-receipt.json"
HISTORICAL_SMOKE = ROOT / "refs/conformance/olm_all10_post_colorkeep_count9_fresh_ae_smoke_20260813.json"
HISTORICAL_SMOKE_RAW = ROOT / "refs/conformance/olm_all10_post_colorkeep_count9_fresh_ae_smoke_raw_20260813.json"

BASE_SHA256 = "45997d4c756fb9d82afde2fbe8f3be503db5e66dff2b15eaaf9ba1e1219ce4b7"
BASE_PAYLOAD_SHA256 = "ef0477d30d30b1b5c587ebcc511864bd4692ae0ef9cc2d656975a209df4ad511"
PAIRED_SHA256 = "80b4e05d844a33687f0d282037fd360898f99a2cf1eca469e68bf8accafee5c2"
NEGATIVE_SHA256 = "eaacb30d172d5a467b059a5e5fcfa7baacec2ee3c62f885b274d5e9c8f72bb09"
IDENTITY_SHA256 = "426dce713a9595157fe4c9fa3731c464e4ef10afd5db269335a12fa4b38beccc"
INSTALL_REPORT_SHA256 = "39536c468aa358884984f5a22fca759aaa94958e0430b55776e42da50f0aef2d"
FAILED_RAW_SHA256 = "17a728f155c292a45b4c1ed83fcc9ba2e0f7d72785732c97eec8780a8f4d0e0e"
FAILED_SUMMARY_SHA256 = "055820bf760d8c31d627e352c0fb87d11ecf263804f1bc3f8dcbc51c33c1972b"
FAILED_RECEIPT_SHA256 = "ed52902307f2e098c46dfb1343ac4105d3067657ac4d8a5a8001b2f71abaae7b"
HISTORICAL_SMOKE_SHA256 = "f87dd1ae13574e56c3e0f428ad3f0b503e37c96dc03b637bfe1ed798161743bc"
HISTORICAL_SMOKE_RAW_SHA256 = "6f096f2b057025f7b6bcc1119de30f1e0bd5e7341ccaa05eb834a8f4d2e18855"
ENABLED_HOST_FRAME_PLUGINS = {"OLMBlur", "OLMDirectionalBlur"}
CLAIM_BOUNDARY = (
    "Fresh installed host load/add/enable-state and exact mapping for all ten; effect-enabled "
    "generic host-frame render only for OLMBlur and OLMDirectionalBlur; OLMToonDilate and the "
    "other seven are disabled before generic saveFrameToPng. Numerical behavior is not assessed "
    "by this AE smoke. No pixel-exact, Windows-equivalence, typed-plane, padding, admission, or "
    "public-owner numerical-exact claim."
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execution_dependencies() -> dict[str, Any]:
    return {
        "classification": "pinned_dynamic_execution_dependencies",
        "base_python_runner": {
            "path": str(BASE_PATH.relative_to(ROOT)), "sha256": BASE_SHA256,
        },
        "base_jsx_payload": {
            "path": str(BASE_PAYLOAD.relative_to(ROOT)), "sha256": BASE_PAYLOAD_SHA256,
        },
        "corrected_python_wrapper": {
            "path": str(THIS.relative_to(ROOT)), "sha256": _sha(THIS),
        },
        "corrected_jsx_wrapper": {
            "path": str(PAYLOAD.relative_to(ROOT)), "sha256": _sha(PAYLOAD),
        },
        "accepted_installed_identity": {
            "path": str(IDENTITY.relative_to(ROOT)), "sha256": IDENTITY_SHA256,
        },
        "toondilate_post_install_identity": {
            "path": str(INSTALL_REPORT.relative_to(ROOT)), "sha256": INSTALL_REPORT_SHA256,
        },
    }


def numerical_authorities() -> dict[str, Any]:
    return {
        "classification": "separate_hostless_numerical_authorities_not_ae_pixel_evidence",
        "same_source_paired_exact12": {
            "path": str(PAIRED.relative_to(ROOT)), "sha256": PAIRED_SHA256, "case_count": 12,
        },
        "public_admission_negative": {
            "path": str(NEGATIVE.relative_to(ROOT)), "sha256": NEGATIVE_SHA256, "row_count": 576,
        },
    }


def validate_dependencies(value: Any) -> bool:
    try:
        return (
            value == execution_dependencies()
            and _sha(BASE_PATH) == BASE_SHA256
            and _sha(BASE_PAYLOAD) == BASE_PAYLOAD_SHA256
            and _sha(IDENTITY) == IDENTITY_SHA256
            and _sha(INSTALL_REPORT) == INSTALL_REPORT_SHA256
            and PAYLOAD.is_file()
        )
    except (OSError, TypeError, ValueError):
        return False


def validate_authorities(value: Any) -> bool:
    try:
        return (
            value == numerical_authorities()
            and _sha(PAIRED) == PAIRED_SHA256
            and _sha(NEGATIVE) == NEGATIVE_SHA256
        )
    except (OSError, TypeError, ValueError):
        return False


def failed_attempt_evidence() -> dict[str, Any]:
    return {
        "classification": "immutable_fail_closed_superseded_attempt_never_reused",
        "raw": {"path": str(FAILED_RAW.relative_to(ROOT)), "sha256": FAILED_RAW_SHA256},
        "summary": {"path": str(FAILED_SUMMARY.relative_to(ROOT)), "sha256": FAILED_SUMMARY_SHA256},
        "receipt": {"path": str(FAILED_RECEIPT.relative_to(ROOT)), "sha256": FAILED_RECEIPT_SHA256},
    }


def validate_failed_attempt(value: Any) -> bool:
    try:
        return value == failed_attempt_evidence() and _sha(FAILED_RAW) == FAILED_RAW_SHA256 and _sha(FAILED_SUMMARY) == FAILED_SUMMARY_SHA256 and _sha(FAILED_RECEIPT) == FAILED_RECEIPT_SHA256
    except (OSError, TypeError, ValueError):
        return False


def superseded_host_authority() -> dict[str, Any]:
    return {
        "classification": "historical_pre_toon_install_smoke_not_current_identity_authority",
        "summary": {"path": str(HISTORICAL_SMOKE.relative_to(ROOT)), "sha256": HISTORICAL_SMOKE_SHA256},
        "raw": {"path": str(HISTORICAL_SMOKE_RAW.relative_to(ROOT)), "sha256": HISTORICAL_SMOKE_RAW_SHA256},
        "historical_identity_sha256": "869a5e88ab34b3b26cc4a3786edb6de93f0e10c88b69c33f6e8d7afb6f18da90",
        "current_identity_sha256": IDENTITY_SHA256,
        "formal_consumer_retarget_pending": True,
    }


def validate_superseded_host(value: Any) -> bool:
    try:
        return value == superseded_host_authority() and _sha(HISTORICAL_SMOKE) == HISTORICAL_SMOKE_SHA256 and _sha(HISTORICAL_SMOKE_RAW) == HISTORICAL_SMOKE_RAW_SHA256
    except (OSError, TypeError, ValueError):
        return False


def corrected_contract() -> dict[str, Any]:
    return {
        "schema": "olm.all10-post-toondilate-ded9-corrected-contract/1",
        "claim_boundary": CLAIM_BOUNDARY,
        "enabled_host_frame_plugins": sorted(ENABLED_HOST_FRAME_PLUGINS),
        "disabled_host_frame_plugins": [
            "ColorKeep", "OLMColorKey", "OLMDistanceGradation", "OLMKiraKira",
            "OLMRadialBlur", "OLMSmoother", "OLMSmoother2", "OLMToonDilate",
        ],
        "numerical_render_assessment": "not_assessed_by_ae_smoke",
        "raw_report": str(RAW.relative_to(ROOT)),
        "summary": str(SUMMARY.relative_to(ROOT)),
        "artifact_dir": str(ARTIFACT_DIR.relative_to(ROOT)),
        "invocation_receipt": str(RECEIPT.relative_to(ROOT)),
        "execution_dependencies": execution_dependencies(),
        "toondilate_numerical_authorities": numerical_authorities(),
        "superseded_failed_attempt": failed_attempt_evidence(),
        "superseded_host_authority": superseded_host_authority(),
    }


def validate_contract(value: Any) -> bool:
    return (
        value == corrected_contract()
        and validate_dependencies(value.get("execution_dependencies") if isinstance(value, dict) else None)
        and validate_authorities(value.get("toondilate_numerical_authorities") if isinstance(value, dict) else None)
        and validate_failed_attempt(value.get("superseded_failed_attempt") if isinstance(value, dict) else None)
        and validate_superseded_host(value.get("superseded_host_authority") if isinstance(value, dict) else None)
    )


def validate_contract_report() -> bool:
    try:
        return json.loads(CONTRACT_REPORT.read_text(encoding="utf-8")) == corrected_contract()
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return False


if not validate_dependencies(execution_dependencies()):
    raise RuntimeError("corrected smoke execution dependency identity drift")

spec = importlib.util.spec_from_file_location("olm_all10_smoke_base_corrected", BASE_PATH)
if spec is None or spec.loader is None:
    raise ImportError("base smoke runner unavailable")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
base.RUNNER = THIS
base.PAYLOAD = PAYLOAD
base.ENABLED_HOST_FRAME_PLUGINS = ENABLED_HOST_FRAME_PLUGINS
base.CLAIM_BOUNDARY = CLAIM_BOUNDARY

_normalize_raw = base.normalize_raw_contract
def normalize_raw_contract(raw: dict[str, Any]) -> None:
    _normalize_raw(raw)
    for row in raw.get("plugins", []):
        row["numerical_render_supported"] = None
        row["numerical_render_assessment"] = "not_assessed"
    for row in raw.get("ae_return", {}).get("plugins", []):
        row["numerical_render_supported"] = None
        row["numerical_render_assessment"] = "not_assessed"
    raw["corrected_contract"] = corrected_contract()


_build_summary = base.build_summary
def _base_compatible(summary: dict[str, Any] | None, raw: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    base_summary = copy.deepcopy(summary) if summary is not None else None
    base_raw = copy.deepcopy(raw)
    for row in base_raw.get("plugins", []):
        row["numerical_render_supported"] = False
        row.pop("numerical_render_assessment", None)
    for row in base_raw.get("ae_return", {}).get("plugins", []):
        row["numerical_render_supported"] = False
        row.pop("numerical_render_assessment", None)
    if base_summary is not None:
        for row in base_summary.get("plugins", []):
            row["numerical_render_supported"] = False
            row.pop("numerical_render_assessment", None)
    return base_summary, base_raw


def build_summary(raw: dict[str, Any], raw_path: Path) -> dict[str, Any]:
    _, base_raw = _base_compatible(None, raw)
    value = _build_summary(base_raw, raw_path)
    for row in value.get("plugins", []):
        row["numerical_render_supported"] = None
        row["numerical_render_assessment"] = "not_assessed"
    value["corrected_contract"] = corrected_contract()
    value["toondilate_numerical_authorities"] = numerical_authorities()
    return value


_validate_data = base.validate_summary_data
def validate_summary_data(summary: dict[str, Any], raw: dict[str, Any]) -> bool:
    base_summary, base_raw = _base_compatible(summary, raw)
    returned = raw.get("ae_return", {})
    all_rows = list(summary.get("plugins", [])) + list(raw.get("plugins", [])) + list(returned.get("plugins", []))
    return (
        _validate_data(base_summary, base_raw)
        and returned.get("claim_boundary") == CLAIM_BOUNDARY
        and len(all_rows) == 30
        and all(row.get("numerical_render_supported") is None for row in all_rows)
        and all(row.get("numerical_render_assessment") == "not_assessed" for row in all_rows)
        and validate_contract(raw.get("corrected_contract"))
        and validate_contract(summary.get("corrected_contract"))
        and validate_authorities(summary.get("toondilate_numerical_authorities"))
        and summary.get("claim_boundary") == CLAIM_BOUNDARY
        and raw.get("claim_boundary") == CLAIM_BOUNDARY
    )


_validate_persisted = base.validate_persisted_summary
def validate_persisted_summary(summary: dict[str, Any], raw: dict[str, Any], raw_path: Path) -> bool:
    saved = base.validate_summary_data
    try:
        def compatible_semantic(value_summary: dict[str, Any], value_raw: dict[str, Any]) -> bool:
            translated_summary, translated_raw = _base_compatible(value_summary, value_raw)
            return _validate_data(translated_summary, translated_raw)
        base.validate_summary_data = compatible_semantic
        # Pass the actual persisted dictionaries so the base validator still
        # byte-binds ae_return.json (whose corrected fields are null/not_assessed).
        base_ok = _validate_persisted(summary, raw, raw_path)
    finally:
        base.validate_summary_data = saved
    return base_ok and validate_summary_data(summary, raw) and raw_path.resolve() == RAW and summary.get("raw_report", {}).get("path") == str(RAW.relative_to(ROOT))


base.normalize_raw_contract = normalize_raw_contract
base.build_summary = build_summary
base.validate_summary_data = validate_summary_data
base.validate_persisted_summary = validate_persisted_summary


def outputs_absent() -> bool:
    return not any(path.exists() for path in (RAW, SUMMARY, ARTIFACT_DIR, RECEIPT))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="perform the one exclusive corrected AE smoke")
    parser.add_argument("--write-contract", action="store_true", help="write only the canonical read-only contract manifest")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    contract = corrected_contract()
    if not validate_contract(contract):
        raise SystemExit("corrected contract validation failed")
    if args.write_contract:
        CONTRACT_REPORT.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not validate_contract_report():
            raise SystemExit("corrected contract report validation failed")
        print("PASS_CORRECTED_CONTRACT_WRITE")
        return 0
    if not validate_contract_report():
        raise SystemExit("corrected contract report missing or drifted")
    if not args.run:
        print(json.dumps({
            "status": "ready_read_only" if outputs_absent() else "already_invoked_no_reuse",
            "outputs_absent": outputs_absent(),
            "contract": contract,
        }, indent=2, sort_keys=True))
        return 0
    if not outputs_absent():
        raise SystemExit("refusing corrected path reuse")
    sys.argv = [
        str(THIS), "--raw-report", str(RAW), "--summary", str(SUMMARY),
        "--artifact-dir", str(ARTIFACT_DIR), "--timeout", str(args.timeout),
    ]
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
