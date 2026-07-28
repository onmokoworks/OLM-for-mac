#!/usr/bin/env python3
"""Fail-closed validator for Mac OLMDistanceGradation PF16 boundary evidence."""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from pathlib import Path
from typing import Any

SCHEMA_ID = "olmdistancegradation_pf16_boundary_capture_20260728/v1"
CANONICAL_CASE_MANIFEST_SHA256 = "7c4761b3b4de904c2a8baa8883c964f234943604414d2cd34bab107ccc43cf29"
CANONICAL_REFERENCE_MANIFEST_SHA256 = "c4378358c8b4db2b2d5d12d0bf0b4142f141963538ca5ec4d86a49eeb8b9e71e"
LAYER_CASES = {
    "olmdistancegradation_extended__case_0012",
    "olmdistancegradation_extended__case_0014",
}
FIELD_CASES = {
    "olmdistancegradation_extended__case_0024",
    "olmdistancegradation_extended__case_0025",
    "olmdistancegradation_extended__case_0026",
    "olmdistancegradation_extended__case_0027",
}
ALL_CASES = LAYER_CASES | FIELD_CASES
AUTHORITATIVE_COORDINATES = {
    "olmdistancegradation_extended__case_0012": (438, 0),
    "olmdistancegradation_extended__case_0014": (448, 0),
    "olmdistancegradation_extended__case_0024": (232, 328),
    "olmdistancegradation_extended__case_0025": (3, 0),
    "olmdistancegradation_extended__case_0026": (907, 222),
    "olmdistancegradation_extended__case_0027": (1234, 443),
}
FIELD_DERIVATION = "nearest_even_clamp_float32_times_32768_logging_only"
NO_DIRECT_FIELD_WORD = "unavailable_at_mac_float_field_boundary"
IDENTITY_KEYS = (
    "run_id",
    "platform",
    "case_manifest_sha256",
    "reference_manifest_sha256",
    "plugin_path",
    "plugin_sha256",
    "process_id",
    "process_start_token",
    "process_executable",
    "process_executable_sha256",
)
CHANNELS = ("a", "r", "g", "b")


class EvidenceError(ValueError):
    pass


def fail(path: str, message: str) -> None:
    raise EvidenceError(f"{path}: {message}")


def exact_keys(value: Any, path: str, required: set[str], optional: set[str] = set()) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(path, "must be an object")
    missing = required - value.keys()
    extra = value.keys() - required - optional
    if missing:
        fail(path, f"missing keys {sorted(missing)}")
    if extra:
        fail(path, f"unexpected keys {sorted(extra)}")
    return value


def check_sha(value: Any, path: str) -> None:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        fail(path, "must be a lowercase 64-hex SHA-256")


def check_identity(value: Any, path: str) -> dict[str, Any]:
    obj = exact_keys(value, path, set(IDENTITY_KEYS))
    for key in ("run_id", "process_start_token"):
        if not isinstance(obj[key], str) or not obj[key]:
            fail(f"{path}.{key}", "must be a non-empty string")
    if obj["platform"] != "macos":
        fail(f"{path}.platform", "must be macos")
    for key in ("case_manifest_sha256", "reference_manifest_sha256", "plugin_sha256", "process_executable_sha256"):
        check_sha(obj[key], f"{path}.{key}")
    if obj["case_manifest_sha256"] != CANONICAL_CASE_MANIFEST_SHA256:
        fail(f"{path}.case_manifest_sha256", "does not identify the authoritative canonical request manifest")
    if obj["reference_manifest_sha256"] != CANONICAL_REFERENCE_MANIFEST_SHA256:
        fail(f"{path}.reference_manifest_sha256", "does not identify the authoritative canonical reference manifest")
    for key in ("plugin_path", "process_executable"):
        if not isinstance(obj[key], str) or not obj[key].startswith("/"):
            fail(f"{path}.{key}", "must be an absolute path")
    if type(obj["process_id"]) is not int or obj["process_id"] < 1:
        fail(f"{path}.process_id", "must be a positive integer")
    return obj


def check_coordinate(value: Any, path: str) -> tuple[int, int]:
    obj = exact_keys(value, path, {"x", "y"})
    for key in ("x", "y"):
        if type(obj[key]) is not int or obj[key] < 0:
            fail(f"{path}.{key}", "must be a nonnegative integer")
    return obj["x"], obj["y"]


def check_words(value: Any, path: str, maximum: int) -> None:
    obj = exact_keys(value, path, set(CHANNELS))
    for channel in CHANNELS:
        word = obj[channel]
        if type(word) is not int or not 0 <= word <= maximum:
            fail(f"{path}.{channel}", f"must be an integer in [0,{maximum}]")


def float_from_bits(bits_hex: Any, path: str) -> float:
    if not isinstance(bits_hex, str) or len(bits_hex) != 10 or not bits_hex.startswith("0x"):
        fail(path, "must be 0x plus eight hex digits")
    try:
        bits = int(bits_hex[2:], 16)
    except ValueError:
        fail(path, "must be 0x plus eight hex digits")
    return struct.unpack("<f", struct.pack("<I", bits))[0]


def check_typed_float(value: Any, path: str) -> None:
    obj = exact_keys(value, path, {"value", "bits_hex"})
    if type(obj["value"]) not in (int, float) or not math.isfinite(obj["value"]):
        fail(f"{path}.value", "must be finite")
    decoded = float_from_bits(obj["bits_hex"], f"{path}.bits_hex")
    if struct.pack("<f", float(obj["value"])) != struct.pack("<f", decoded):
        fail(path, "value does not match float32 bits")


def authoritative_float32(value: Any, path: str) -> float:
    check_typed_float(value, path)
    return float_from_bits(value["bits_hex"], f"{path}.bits_hex")


def truncating_clamp16(value: float) -> int:
    """Current binary/source-grounded normalized float -> PF16 store rule."""
    return int(min(1.0, max(0.0, value)) * 32768.0)


def check_stage_coordinate(stage: Any, path: str, coordinate: tuple[int, int]) -> dict[str, Any]:
    if not isinstance(stage, dict):
        fail(path, "must be an object")
    if check_coordinate(stage.get("coordinate"), f"{path}.coordinate") != coordinate:
        fail(f"{path}.coordinate", "does not match capture coordinate")
    return stage


def validate(document: Any, require_all_cases: bool = False) -> dict[str, Any]:
    root = exact_keys(document, "$", {"schema_id", "identity", "captures"})
    if root["schema_id"] != SCHEMA_ID:
        fail("$.schema_id", f"must equal {SCHEMA_ID}")
    identity = check_identity(root["identity"], "$.identity")
    if not isinstance(root["captures"], list) or not root["captures"]:
        fail("$.captures", "must be a non-empty array")

    seen: set[tuple[str, int, int]] = set()
    present_cases: set[str] = set()
    for index, raw_capture in enumerate(root["captures"]):
        path = f"$.captures[{index}]"
        capture = exact_keys(
            raw_capture,
            path,
            {"case_id", "identity", "coordinate", "source_pf16"},
            {"field", "pre_store", "stored_pf16", "exported_true16"},
        )
        case_id = capture["case_id"]
        if case_id not in ALL_CASES:
            fail(f"{path}.case_id", "is outside the six permitted boundary cases")
        capture_identity = check_identity(capture["identity"], f"{path}.identity")
        if capture_identity != identity:
            fail(f"{path}.identity", "mixed-run or mixed manifest/plugin/process identity")
        coordinate = check_coordinate(capture["coordinate"], f"{path}.coordinate")
        if coordinate != AUTHORITATIVE_COORDINATES[case_id]:
            fail(
                f"{path}.coordinate",
                f"must equal authoritative coordinate {AUTHORITATIVE_COORDINATES[case_id]} for {case_id}",
            )
        unique = (case_id, *coordinate)
        if unique in seen:
            fail(path, "duplicate case/coordinate record")
        seen.add(unique)
        present_cases.add(case_id)

        source = exact_keys(capture["source_pf16"], f"{path}.source_pf16", {"coordinate", "argb"})
        check_stage_coordinate(source, f"{path}.source_pf16", coordinate)
        check_words(source["argb"], f"{path}.source_pf16.argb", 32768)

        if "field" in capture:
            if case_id in LAYER_CASES:
                fail(f"{path}.field", "forbidden stage leakage into cases 0012/0014")
            field = exact_keys(
                capture["field"],
                f"{path}.field",
                {
                    "coordinate",
                    "float_value",
                    "float_bits_hex",
                    "derived_pf16_word",
                    "derivation",
                    "direct_field_staging_word",
                },
            )
            check_stage_coordinate(field, f"{path}.field", coordinate)
            check_typed_float(
                {"value": field["float_value"], "bits_hex": field["float_bits_hex"]},
                f"{path}.field",
            )
            authoritative_field = float_from_bits(field["float_bits_hex"], f"{path}.field.float_bits_hex")
            expected_derived = round(min(1.0, max(0.0, authoritative_field)) * 32768.0)
            if type(field["derived_pf16_word"]) is not int or field["derived_pf16_word"] != expected_derived:
                fail(f"{path}.field.derived_pf16_word", f"must equal logging-only nearest-even derivation {expected_derived}")
            if field["derivation"] != FIELD_DERIVATION:
                fail(f"{path}.field.derivation", "must identify the logging-only derivation")
            if field["direct_field_staging_word"] != NO_DIRECT_FIELD_WORD:
                fail(f"{path}.field.direct_field_staging_word", "must state that no direct field staging word exists")
        elif case_id in FIELD_CASES:
            fail(f"{path}.field", "mandatory for cases 0024..0027")

        paired = ("pre_store", "stored_pf16", "exported_true16")
        if case_id in FIELD_CASES and any(key in capture for key in paired):
            fail(path, "pre-store/store/export chain forbidden for field-only cases 0024..0027")
        if case_id in LAYER_CASES and any(key not in capture for key in paired):
            fail(path, "cases 0012/0014 require paired pre_store, stored_pf16, and exported_true16")
        if any(key in capture for key in paired) and not all(key in capture for key in paired):
            fail(path, "partial pre-store/store/export chain is forbidden")
        if all(key in capture for key in paired):
            pre = exact_keys(capture["pre_store"], f"{path}.pre_store", {"coordinate", "argb"})
            check_stage_coordinate(pre, f"{path}.pre_store", coordinate)
            floats = exact_keys(pre["argb"], f"{path}.pre_store.argb", set(CHANNELS))
            expected_stored: dict[str, int] = {}
            for channel in CHANNELS:
                raw_float = authoritative_float32(floats[channel], f"{path}.pre_store.argb.{channel}")
                expected_stored[channel] = truncating_clamp16(raw_float)
            stored = exact_keys(capture["stored_pf16"], f"{path}.stored_pf16", {"coordinate", "argb"})
            check_stage_coordinate(stored, f"{path}.stored_pf16", coordinate)
            check_words(stored["argb"], f"{path}.stored_pf16.argb", 32768)
            if stored["argb"] != expected_stored:
                fail(
                    f"{path}.stored_pf16.argb",
                    f"does not equal truncating clamp16 of authoritative pre-store float32 bits; expected {expected_stored}",
                )
            exported = exact_keys(
                capture["exported_true16"],
                f"{path}.exported_true16",
                {"coordinate", "argb", "artifact_path", "artifact_sha256", "relation_to_stored_pf16"},
            )
            check_stage_coordinate(exported, f"{path}.exported_true16", coordinate)
            check_words(exported["argb"], f"{path}.exported_true16.argb", 65535)
            if not isinstance(exported["artifact_path"], str) or not exported["artifact_path"].startswith("/"):
                fail(f"{path}.exported_true16.artifact_path", "must be an absolute path")
            check_sha(exported["artifact_sha256"], f"{path}.exported_true16.artifact_sha256")
            if exported["relation_to_stored_pf16"] != "unverified_structural_only":
                fail(
                    f"{path}.exported_true16.relation_to_stored_pf16",
                    "must remain unverified_structural_only without a grounded host mapping",
                )

    if require_all_cases and present_cases != ALL_CASES:
        fail("$.captures", f"missing required cases {sorted(ALL_CASES - present_cases)}")
    return {
        "status": "accepted_structural_evidence",
        "pf16_store_mapping": "validated_truncating_clamp16_for_0012_0014",
        "export_conversion": "unverified",
        "captures": len(seen),
        "cases": sorted(present_cases),
        "run_id": identity["run_id"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", type=Path)
    parser.add_argument("--require-all-cases", action="store_true")
    parser.add_argument("--allow-non-macos-host-for-fixture-test", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if sys.platform != "darwin" and not args.allow_non_macos_host_for_fixture_test:
        print("REJECTED: validator is Mac-only", file=sys.stderr)
        return 2
    try:
        result = validate(json.loads(args.capture.read_text()), args.require_all_cases)
    except (OSError, json.JSONDecodeError, EvidenceError) as exc:
        print(f"REJECTED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
