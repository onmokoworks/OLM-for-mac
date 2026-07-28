#!/usr/bin/env python3
"""Synthetic accept/reject tests for the DG PF16 boundary evidence validator."""

from __future__ import annotations

import copy
import struct

from validate_olmdistancegradation_pf16_boundary_capture_20260728 import (
    ALL_CASES,
    AUTHORITATIVE_COORDINATES,
    CANONICAL_CASE_MANIFEST_SHA256,
    CANONICAL_REFERENCE_MANIFEST_SHA256,
    EvidenceError,
    FIELD_DERIVATION,
    NO_DIRECT_FIELD_WORD,
    SCHEMA_ID,
    validate,
)


def bits(value: float) -> str:
    return f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08x}"


def identity(run: str = "synthetic-run-a") -> dict:
    return {
        "run_id": run,
        "platform": "macos",
        "case_manifest_sha256": CANONICAL_CASE_MANIFEST_SHA256,
        "reference_manifest_sha256": CANONICAL_REFERENCE_MANIFEST_SHA256,
        "plugin_path": "/synthetic/OLMDistanceGradation.plugin/Contents/MacOS/OLMDistanceGradation",
        "plugin_sha256": "3" * 64,
        "process_id": 4242,
        "process_start_token": "synthetic-start-123",
        "process_executable": "/synthetic/After Effects",
        "process_executable_sha256": "4" * 64,
    }


def capture(case_number: str, root_identity: dict) -> dict:
    x, y = AUTHORITATIVE_COORDINATES[f"olmdistancegradation_extended__case_{case_number}"]
    coord = {"x": x, "y": y}
    record = {
        "case_id": f"olmdistancegradation_extended__case_{case_number}",
        "identity": copy.deepcopy(root_identity),
        "coordinate": coord,
        "source_pf16": {"coordinate": copy.deepcopy(coord), "argb": {"a": 32768, "r": 100, "g": 200, "b": 300}},
    }
    if case_number in {"0024", "0025", "0026", "0027"}:
        record["field"] = {
            "coordinate": copy.deepcopy(coord),
            "float_value": 0.25,
            "float_bits_hex": bits(0.25),
            "derived_pf16_word": 8192,
            "derivation": FIELD_DERIVATION,
            "direct_field_staging_word": NO_DIRECT_FIELD_WORD,
        }
    if case_number in {"0012", "0014"}:
        record["pre_store"] = {
            "coordinate": copy.deepcopy(coord),
            "argb": {channel: {"value": 0.5, "bits_hex": bits(0.5)} for channel in "argb"},
        }
        record["stored_pf16"] = {
            "coordinate": copy.deepcopy(coord),
            "argb": {"a": 16384, "r": 16384, "g": 16384, "b": 16384},
        }
        record["exported_true16"] = {
            "coordinate": copy.deepcopy(coord),
            "argb": {"a": 32767, "r": 32767, "g": 32767, "b": 32767},
            "artifact_path": "/synthetic/export.tiff",
            "artifact_sha256": "5" * 64,
            "relation_to_stored_pf16": "unverified_structural_only",
        }
    return record


def fixture() -> dict:
    root_identity = identity()
    case_numbers = ("0012", "0014", "0024", "0025", "0026", "0027")
    return {
        "schema_id": SCHEMA_ID,
        "identity": root_identity,
        "captures": [capture(number, root_identity) for number in case_numbers],
    }


def rejects(document: dict, needle: str) -> None:
    try:
        validate(document, require_all_cases=True)
    except EvidenceError as exc:
        assert needle in str(exc), (needle, str(exc))
    else:
        raise AssertionError(f"fixture unexpectedly accepted; wanted {needle!r}")


def main() -> None:
    valid = fixture()
    result = validate(valid, require_all_cases=True)
    assert set(result["cases"]) == ALL_CASES
    assert result["export_conversion"] == "unverified"

    missing_field = copy.deepcopy(valid)
    del missing_field["captures"][2]["field"]
    rejects(missing_field, "mandatory for cases 0024..0027")

    partial_pair = copy.deepcopy(valid)
    del partial_pair["captures"][0]["exported_true16"]
    rejects(partial_pair, "require paired")

    mixed_run = copy.deepcopy(valid)
    mixed_run["captures"][1]["identity"]["run_id"] = "synthetic-run-b"
    rejects(mixed_run, "mixed-run")

    mixed_plugin = copy.deepcopy(valid)
    mixed_plugin["captures"][4]["identity"]["plugin_sha256"] = "6" * 64
    rejects(mixed_plugin, "mixed-run")

    mixed_manifest = copy.deepcopy(valid)
    mixed_manifest["captures"][5]["identity"]["case_manifest_sha256"] = "7" * 64
    rejects(mixed_manifest, "authoritative canonical request")

    wrong_coordinate = copy.deepcopy(valid)
    wrong_coordinate["captures"][0]["coordinate"]["x"] = 999
    wrong_coordinate["captures"][0]["source_pf16"]["coordinate"]["x"] = 999
    wrong_coordinate["captures"][0]["pre_store"]["coordinate"]["x"] = 999
    wrong_coordinate["captures"][0]["stored_pf16"]["coordinate"]["x"] = 999
    wrong_coordinate["captures"][0]["exported_true16"]["coordinate"]["x"] = 999
    rejects(wrong_coordinate, "authoritative coordinate")

    mismatched_bits = copy.deepcopy(valid)
    mismatched_bits["captures"][2]["field"]["float_bits_hex"] = bits(0.5)
    rejects(mismatched_bits, "does not match float32 bits")

    invented_raw_word = copy.deepcopy(valid)
    invented_raw_word["captures"][2]["field"]["raw_pf16_word"] = 8192
    rejects(invented_raw_word, "unexpected keys")

    invented_direct_claim = copy.deepcopy(valid)
    invented_direct_claim["captures"][2]["field"]["direct_field_staging_word"] = 8192
    rejects(invented_direct_claim, "must state that no direct field staging word exists")

    unrelated_stored = copy.deepcopy(valid)
    unrelated_stored["captures"][0]["stored_pf16"]["argb"]["r"] = 12345
    rejects(unrelated_stored, "does not equal truncating clamp16")

    round_nearest_stored = copy.deepcopy(valid)
    half_step = 100.75 / 32768.0
    round_nearest_stored["captures"][1]["pre_store"]["argb"]["b"] = {
        "value": half_step,
        "bits_hex": bits(half_step),
    }
    round_nearest_stored["captures"][1]["stored_pf16"]["argb"]["b"] = 101
    rejects(round_nearest_stored, "does not equal truncating clamp16")

    arbitrary_export_is_structural = copy.deepcopy(valid)
    arbitrary_export_is_structural["captures"][0]["exported_true16"]["argb"] = {
        "a": 1,
        "r": 65535,
        "g": 42,
        "b": 60000,
    }
    assert validate(arbitrary_export_is_structural, require_all_cases=True)["export_conversion"] == "unverified"

    invented_export_relation = copy.deepcopy(valid)
    invented_export_relation["captures"][0]["exported_true16"]["relation_to_stored_pf16"] = "exact"
    rejects(invented_export_relation, "must remain unverified_structural_only")

    field_leaks_into_layer = copy.deepcopy(valid)
    field_leaks_into_layer["captures"][0]["field"] = copy.deepcopy(valid["captures"][2]["field"])
    field_leaks_into_layer["captures"][0]["field"]["coordinate"] = copy.deepcopy(
        field_leaks_into_layer["captures"][0]["coordinate"]
    )
    rejects(field_leaks_into_layer, "forbidden stage leakage")

    chain_leaks_into_field = copy.deepcopy(valid)
    for key in ("pre_store", "stored_pf16", "exported_true16"):
        chain_leaks_into_field["captures"][2][key] = copy.deepcopy(valid["captures"][0][key])
        chain_leaks_into_field["captures"][2][key]["coordinate"] = copy.deepcopy(
            chain_leaks_into_field["captures"][2]["coordinate"]
        )
    rejects(chain_leaks_into_field, "chain forbidden for field-only")

    missing_case = copy.deepcopy(valid)
    missing_case["captures"].pop()
    rejects(missing_case, "missing required cases")

    print(
        "PASS: truncating PF16 mapping enforced; export remains structural; "
        "missing/mixed-run/unrelated/leaked evidence rejected"
    )


if __name__ == "__main__":
    main()
