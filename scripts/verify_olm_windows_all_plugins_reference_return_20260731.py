#!/usr/bin/env python3
"""Fail-closed verifier for the consolidated 2026-07-31 Windows reference return."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import ntpath
import os
import re
import stat
import struct
import sys
import unicodedata
import zlib
from datetime import datetime
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

from compare_float_exr import (
    compare as compare_float_exr,
    read_planes_with_layout,
)
from verify_32bpc_float_return import (
    VerificationError as ExrVerificationError,
    inspect_float_rgba_exr,
)


R4_CAMPAIGN_ID = "olm_windows_all_plugins_reference_campaign_20260731_r4"
R5_CAMPAIGN_ID = "olm_windows_all_plugins_reference_campaign_20260731_r5"
CAMPAIGN_ID = R4_CAMPAIGN_ID
R4_EXPECTED_LANE_ROWS = {
    "OLMDistanceGradation": 99,
    "OLMDirectionalBlur": 54,
    "OLMRadialBlur": 18,
    "OLMKiraKira": 30,
    "OLMSmoother v1": 19,
    "ColorKeep": 9,
}
R5_EXPECTED_LANE_ROWS = {**R4_EXPECTED_LANE_ROWS, "OLMKiraKira": 60}
EXPECTED_LANE_ROWS = R4_EXPECTED_LANE_ROWS
EXPECTED_TOTAL_ROWS = sum(EXPECTED_LANE_ROWS.values())
R4_EXPECTED_SCHEMA_FILES = {
    "BATCH_MANIFEST.schema.json",
    "EVIDENCE_BINDING.schema.json",
    "RETURN_STATUS.schema.json",
    "OLMKIRAKIRA_CROSS_ROW.schema.json",
    "OLMRADIALBLUR_WITNESS.schema.json",
    "OLMKIRAKIRA_WRITER_TRACE.schema.json",
    "OLMKIRAKIRA_PF32_TRACE.schema.json",
    "OLMKIRAKIRA_GAUSSIAN_KERNEL.schema.json",
}
R5_EXPECTED_SCHEMA_FILES = R4_EXPECTED_SCHEMA_FILES | {
    "EXECUTION_ROW.schema.json",
}
EXPECTED_SCHEMA_FILES = R4_EXPECTED_SCHEMA_FILES
R4_EXPECTED_SCHEMA_SHA256 = {
    "BATCH_MANIFEST.schema.json": "e1c1c0da472de21687db303ce8aa17b7c4382754e276e95f771955b8f71c4e50",
    "EVIDENCE_BINDING.schema.json": "8d74613b654ba22d764ef0bd19ee0364559e0ba86aeaf7f14516f3a41436a1ed",
    "OLMKIRAKIRA_CROSS_ROW.schema.json": "23853809ad2075cceb7bf81f1a72c481b8ccab9815da6f71cddc9466edc96595",
    "OLMKIRAKIRA_GAUSSIAN_KERNEL.schema.json": "37b1a6628f7a3b594d588d36fa3c48a6c2c775a8ed97cb838d2f98bf806979e0",
    "OLMKIRAKIRA_PF32_TRACE.schema.json": "f68aa194232473dc1561bab11f40a5d651d81aa2af19f9cfb301d053ed12427b",
    "OLMKIRAKIRA_WRITER_TRACE.schema.json": "1768bdc167b40949bce93d6ec2dcded3978334bfffe5eb5fa7fee8ec1816eb20",
    "OLMRADIALBLUR_WITNESS.schema.json": "2687d2054e9dabf77f3a2066129505d2ffb514c8a6845089da1fc039996ee4aa",
    "RETURN_STATUS.schema.json": "a51f97277ccf2792b9b86e03f7cdfd87de78f46c34f2632097890f9b967de57d",
}
R5_EXPECTED_SCHEMA_SHA256 = {
    "BATCH_MANIFEST.schema.json": "eb1bcf4f2b53b560d4c8df4cef050001c216b6190ed8f7097c5f3de1db94de1c",
    "EVIDENCE_BINDING.schema.json": "d5b1e45fb49b797121d3ac41f7e7b67d87f038fde262cf380cb2510e6ca74647",
    "EXECUTION_ROW.schema.json": "c4af0c6f7e81d0cfdc458aabb8a0d7cda58b4746cb10fcc7de7b7c9ce6be3076",
    "OLMKIRAKIRA_CROSS_ROW.schema.json": "f4113d407860dda3fea761a99ab62d2e1b5e2cb8f4ed6506f05c773be69dbb2a",
    "OLMKIRAKIRA_GAUSSIAN_KERNEL.schema.json": "bc47e09be5271aafd8d24e130cb3f09af24b04a350022072d056a842734ad19b",
    "OLMKIRAKIRA_PF32_TRACE.schema.json": "5180fb27b39886b7d3475f00bbec9fb49cf8f7d3819b35731b898772db46cda2",
    "OLMKIRAKIRA_WRITER_TRACE.schema.json": "a57a0c5cd566754fbb137f50b56caea5740bb8d7a60fb552ea4ff2d28ec03e49",
    "OLMRADIALBLUR_WITNESS.schema.json": "7280205dcc05df63376825c1171c229c406ae27765009ad940ba86c7e7508532",
    "RETURN_STATUS.schema.json": "b5b2183c33bc70049cc686b90b1afbdc89410b969a5090f497cf98932d397d27",
}
EXPECTED_SCHEMA_SHA256 = R4_EXPECTED_SCHEMA_SHA256
COMMON_STANDARD_OPTIONS = [
    {
        "match_name": "ADBE Effect Mask Opacity",
        "property_type": 6417,
        "scope": "effect_compositing_option",
        "value": 100,
        "action": "set",
        "write": True,
        "value_type": "integer",
        "comparison_mode": "exact_integer",
    },
    {
        "match_name": "ADBE Force CPU GPU",
        "property_type": 6417,
        "scope": "effect_compositing_option",
        "value": 1,
        "action": "set",
        "write": True,
        "value_type": "integer",
        "comparison_mode": "exact_integer",
    },
]
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_CHECKSUM_BYTES = 16 * 1024 * 1024
MAX_RETURN_MEMBER_BYTES = 256 * 1024 * 1024
MAX_EXR_BYTES = 64 * 1024 * 1024
MAX_TOTAL_RETURN_BYTES = 64 * 1024 * 1024 * 1024
MAX_DECODED_PNG_BYTES = 64 * 1024 * 1024
MAX_PNG_CHUNKS = 10_000
PASS_JSON_FILES = {
    "params_expected.json": "params_expected",
    "params_setup.json": "params_setup",
    "params_before.json": "params_before",
    "params_after.json": "params_after",
    "project_before.json": "project_before",
    "project_after.json": "project_after",
    "output_module_before.json": "output_module_before",
    "output_module_after.json": "output_module_after",
    "exr_header_no_effect.json": "exr_header_no_effect",
    "exr_header_effect_on.json": "exr_header_effect_on",
    "raw_off_on_comparison.json": "raw_off_on_comparison",
    "process.json": "process",
}
PASS_OTHER_FILES = ("etw.etl", "etw.csv", "aerender_stdout.txt")
PF32_DIAGNOSTICS = {
    "approximated_input_trace.json": {
        "kind": "olmkirakira_pf32_approximated_input_trace_v1",
        "event": "approximated_input_stage_sample",
        "case_ids": (
            "kk_mapped_bm2_mm1_ray_f0_a0_alpha",
            "kk_mapped_bm2_mm1_ray_f0_a1_alpha",
        ),
    },
    "highlight_layer_trace.json": {
        "kind": "olmkirakira_pf32_highlight_radius_trace_v1",
        "event": "highlight_radius_stage_sample",
        "case_ids": (
            "kk_mapped_bm3_mm1_hi_r0_orange_opaque",
            "kk_mapped_bm3_mm1_hi_r5_orange_opaque",
        ),
    },
    "highlight_color_trace.json": {
        "kind": "olmkirakira_pf32_highlight_color_trace_v1",
        "event": "highlight_color_stage_sample",
        "case_ids": (
            "kk_mapped_bm3_mm1_hi_r5_white_opaque",
            "kk_mapped_bm3_mm1_hi_r5_orange_opaque",
        ),
    },
    "mode4_trace.json": {
        "kind": "olmkirakira_pf32_mode4_trace_v1",
        "event": "mode4_recurrence_stage_sample",
        "case_ids": (
            "kk_mapped_bm3_mm1_hi_r5_orange_opaque",
            "kk_mapped_bm4_mm1_hi_r5_orange_opaque",
        ),
    },
}

KIRA_AUTHORITATIVE_GROUP = "final_random_authoritative_10"
KIRA_AUTHORITATIVE_DEFINITION = (
    "case_definitions/olmkirakira_final_random_all30.json"
)
KIRA_PROPERTY_READBACK_FILE = "kirakira_property_readback.json"
KIRA_LINEAGE_FILE = "kirakira_lineage.json"
KIRA_MODE4_FILE = "kirakira_mode4.json"
KIRA_AEX_SHA256 = (
    "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7"
)
KIRA_DEFAULT_RAMP_SHA256 = (
    "80030de202298d2f868e07b027eab0fe647a411c4f050b9b95f91b32902c1ea3"
)
KIRA_RICH42_CAPTURE_TOOL = "tools/capture_olmkirakira_rich42.jsx"
KIRA_RICH42_CAPTURE_TOOL_SHA256 = (
    "a8b75a848ee988fda31dd4d56c94ae69ca750d9e6126b830122408c2768b9370"
)
KIRA_RICH42_SOURCE_MANIFEST = (
    "refs/win_references/20260710_190500__ae26_3_32bpc_recap/"
    "OLMKiraKira/reference_manifest.json"
)
KIRA_RICH42_SOURCE_MANIFEST_SHA256 = (
    "638cb66a60a52f4f9877f0f74937a891d447dc85673c8cca48c0780acf3ec9e7"
)
KIRA_RICH42_CAPTURE_PHASE = (
    "after_parameter_and_standard_option_writes_after_params_before_snapshot_"
    "before_render"
)
KIRA_LAYER_NAMES = (
    "vertical",
    "horizontal",
    "diagonal",
    "diagonal2",
    "highlight",
)
KIRA_RAMP_LAYERS_BY_CASE = {
    "final_random10_olm_kira_kira_01": ("diagonal2", "highlight"),
    "final_random10_olm_kira_kira_02": ("vertical", "diagonal", "highlight"),
    "final_random10_olm_kira_kira_03": (),
    "final_random10_olm_kira_kira_04": ("vertical", "diagonal2"),
    "final_random10_olm_kira_kira_05": ("diagonal",),
    "final_random10_olm_kira_kira_06": ("vertical",),
    "final_random10_olm_kira_kira_07": ("diagonal2",),
    "final_random10_olm_kira_kira_08": ("vertical", "diagonal", "diagonal2"),
    "final_random10_olm_kira_kira_09": (),
    "final_random10_olm_kira_kira_10": ("vertical", "diagonal"),
}
KIRA_MODE4_CASES = {
    "final_random10_olm_kira_kira_01",
    "final_random10_olm_kira_kira_04",
}
KIRA_MODE_METADATA = {
    "final_random10_olm_kira_kira_01": (4, 2, 0),
    "final_random10_olm_kira_kira_02": (1, 1, 0),
    "final_random10_olm_kira_kira_03": (3, 1, 0),
    "final_random10_olm_kira_kira_04": (4, 2, 1),
    "final_random10_olm_kira_kira_05": (1, 2, 1),
    "final_random10_olm_kira_kira_06": (2, 1, 0),
    "final_random10_olm_kira_kira_07": (3, 2, 0),
    "final_random10_olm_kira_kira_08": (1, 2, 1),
    "final_random10_olm_kira_kira_09": (2, 1, 1),
    "final_random10_olm_kira_kira_10": (3, 1, 1),
}
KIRA_AUTHORITATIVE_HASHES = {
    "final_random10_olm_kira_kira_01": (
        "8c1d418c7b853cc6f79087215ee86ab0b9eac423953c1a3409af3e120891a7f0",
        "9baabc16de003ac9b8e1d407d812d2651e527d237b1da54cf5091577129dc440",
    ),
    "final_random10_olm_kira_kira_02": (
        "e100cd998a5e6f093cf7233821a0ba67d866117ca2f1b300023d6672457e6954",
        "be3664b249e030f2ce45337f2c6f1fcdc712797d35c5144267a1f8e36cd3e83c",
    ),
    "final_random10_olm_kira_kira_03": (
        "8bdac36ca9a84569ce568781810283eb1bbcb326934c123d2daf38b16c80bc91",
        "95bd69def5027340fde2520d8541490ee0996a1f26459734f370676f5ff92cb5",
    ),
    "final_random10_olm_kira_kira_04": (
        "f004f56651793a586e94dfabd467eb0e0df9fcf5f8500db5d54e215e070bc267",
        "22a2d8eb5b4eddf88c78bb676ac6a7e76eccd30da2bb62cad10354836e897e88",
    ),
    "final_random10_olm_kira_kira_05": (
        "24b0782b49de384af3f46d613c0c69dd01a6bb02d38226a54a413950d58155d6",
        "c261bf4deb3fc8d17dd1a8b85c6c386d7d4f7d37fd10228bfea8914e674669fa",
    ),
    "final_random10_olm_kira_kira_06": (
        "27e55775eb4b6b038ac04f10b56e5800904efb658864ff4c1c64ed0728ae2676",
        "cf30acd083b7a8836b54a7a7a0d3bee51ce4d181c94ee5b22d1cb82fdd982d5b",
    ),
    "final_random10_olm_kira_kira_07": (
        "20962bb08aa7c5a5cdaa549fbff0356d240b91bed6c67b5ca4c6b6d325c9a356",
        "244d2121750c31dd7b4c06577f2d89c942f8835c1b95a50ce796955cc54075c2",
    ),
    "final_random10_olm_kira_kira_08": (
        "d9bfadc91935239a44deec0872d2dd24b15b26eeb8488cd34b06cde3121e20fc",
        "452cd9b7c1d0246b42eebbaeb94a92c1e95f6b3a1c7dbee8aea323113d43432a",
    ),
    "final_random10_olm_kira_kira_09": (
        "d32e20f429da453910c6fa2038bf133b29fae0df793acb9444c3af399fbc3729",
        "ace4fd4afec942562600730e73cab1cb8bd0318d06407fe370c29fa52f21ff84",
    ),
    "final_random10_olm_kira_kira_10": (
        "2cbad9f4d6afb88e285191728a4120c9e0b7691d64b52cfa4a77ce8127029d88",
        "433d05f5135c31329a2f2f88dbd7acca4851a80c7ec71ec79274ca7a69e7dc91",
    ),
}
KIRA_TYPED_ENTRIES = {
    8: {
        "owner": "FUN_18114d220",
        "outer": "FUN_18114e110",
        "writer": "FUN_181230b90",
        "pixel_bytes": 4,
        "stored_unit": "u8",
        "scale": 255,
    },
    16: {
        "owner": "FUN_18114cc50",
        "outer": "FUN_18114ddc0",
        "writer": "FUN_181230bd0",
        "pixel_bytes": 8,
        "stored_unit": "u16",
        "scale": 32768,
    },
    32: {
        "owner": "FUN_18114d7f0",
        "outer": "FUN_18114e460",
        "writer": "FUN_181230c20",
        "pixel_bytes": 16,
        "stored_unit": "f32_u32",
        "scale": None,
    },
}


def configure_campaign_contract(campaign_id: object) -> None:
    global CAMPAIGN_ID, EXPECTED_LANE_ROWS, EXPECTED_TOTAL_ROWS
    global EXPECTED_SCHEMA_FILES, EXPECTED_SCHEMA_SHA256
    if campaign_id == R4_CAMPAIGN_ID:
        CAMPAIGN_ID = R4_CAMPAIGN_ID
        EXPECTED_LANE_ROWS = R4_EXPECTED_LANE_ROWS
        EXPECTED_SCHEMA_FILES = R4_EXPECTED_SCHEMA_FILES
        EXPECTED_SCHEMA_SHA256 = R4_EXPECTED_SCHEMA_SHA256
    elif campaign_id == R5_CAMPAIGN_ID:
        CAMPAIGN_ID = R5_CAMPAIGN_ID
        EXPECTED_LANE_ROWS = R5_EXPECTED_LANE_ROWS
        EXPECTED_SCHEMA_FILES = R5_EXPECTED_SCHEMA_FILES
        EXPECTED_SCHEMA_SHA256 = R5_EXPECTED_SCHEMA_SHA256
    else:
        fail(f"unsupported campaign_id: {campaign_id!r}")
    EXPECTED_TOTAL_ROWS = sum(EXPECTED_LANE_ROWS.values())


def is_kira_authoritative_row(row: dict[str, Any]) -> bool:
    return (
        CAMPAIGN_ID == R5_CAMPAIGN_ID
        and row.get("plugin") == "OLMKiraKira"
        and row.get("group_id") == KIRA_AUTHORITATIVE_GROUP
    )


def verify_kira_rich42_preimage(
    case: dict[str, Any],
    label: str,
) -> list[object]:
    case_id = case.get("case_id")
    hashes = KIRA_AUTHORITATIVE_HASHES.get(case_id)
    if hashes is None:
        fail(f"{label}: unknown authoritative KiraKira case")
    expected_sha = hashes[1]
    preimage = case.get("full_42_property_readback_preimage")
    contract = case.get("full_42_property_readback_preimage_contract")
    if (
        not isinstance(preimage, list)
        or len(preimage) != 42
        or canonical_json_sha256(preimage) != expected_sha
        or case.get("full_42_property_readback_sha256") != expected_sha
        or not strict_equal(
            contract,
            {
                "ordered_row_count": 42,
                "canonical_json": {
                    "encoding": "UTF-8",
                    "ensure_ascii": True,
                    "sort_keys": True,
                    "separators": [",", ":"],
                    "allow_nan": False,
                    "bom": False,
                    "trailing_newline": False,
                },
                "source_manifest_repository_path": KIRA_RICH42_SOURCE_MANIFEST,
                "source_manifest_sha256": KIRA_RICH42_SOURCE_MANIFEST_SHA256,
                "capture_tool_member": KIRA_RICH42_CAPTURE_TOOL,
                "capture_tool_sha256": KIRA_RICH42_CAPTURE_TOOL_SHA256,
                "capture_phase_id": KIRA_RICH42_CAPTURE_PHASE,
                "evidence_capture_phase": {
                    "after_parameter_and_standard_option_writes": True,
                    "after_params_before_snapshot": True,
                    "before_first_render": True,
                    "params_before_values_sha256": (
                        "<exact bound params_before.values_sha256>"
                    ),
                },
                "capture_sequence": [
                    "apply and read back all case parameter actions",
                    "apply and read back both standard options",
                    "write params_before.json from those live readbacks",
                    "capture the ordered rich 42-property rows",
                    "only then begin either render branch",
                ],
                "value_binding": {
                    "writable_plugin_rows": (
                        "must equal the same live values encoded in "
                        "params_before.parameter_actions and row.parameter_writes"
                    ),
                    "standard_option_rows": (
                        "must equal the same live values encoded in "
                        "params_before.standard_options and row.standard_options"
                    ),
                    "params_before_values_sha256_required": True,
                },
                "params_setup_observed_surface_role": (
                    "fresh pre-write surface identity/default gate only; never "
                    "reuse it for case-specific rich-42 value equality"
                ),
                "required_ae_locale": "en_US",
                "error_policy": (
                    "retain exact English AE Error.toString() text; no "
                    "translation, punctuation normalization, or projection"
                ),
            },
        )
    ):
        fail(f"{label}: rich-42 preimage/capture contract mismatch")
    return preimage


def verify_kira_capture_phase(
    capture_phase: object,
    params_before_values_sha256: object,
    label: str,
) -> None:
    expected_sha = require_sha(
        params_before_values_sha256,
        f"{label}.params_before_values_sha256",
    )
    if not strict_equal(
        capture_phase,
        {
            "after_parameter_and_standard_option_writes": True,
            "after_params_before_snapshot": True,
            "before_first_render": True,
            "params_before_values_sha256": expected_sha,
        },
    ):
        fail(f"{label}: rich-42 capture phase/params-before binding mismatch")


def verify_kira_rich42_writable_values(
    properties: object,
    parameter_actions: object,
    standard_options: object,
    label: str,
) -> None:
    if (
        not isinstance(properties, list)
        or not isinstance(parameter_actions, list)
        or not isinstance(standard_options, list)
    ):
        fail(f"{label}: rich-42 writable binding inputs are malformed")
    actions = {
        action.get("match_name"): action
        for action in parameter_actions
        if isinstance(action, dict) and isinstance(action.get("match_name"), str)
    }
    options = {
        option.get("match_name"): option
        for option in standard_options
        if isinstance(option, dict) and isinstance(option.get("match_name"), str)
    }
    observed_actions: set[str] = set()
    observed_options: set[str] = set()
    for index, record in enumerate(properties):
        if not isinstance(record, dict):
            fail(f"{label}: rich-42 row {index} is not an object")
        match_name = record.get("match_name")
        expected = actions.get(match_name)
        if expected is not None:
            observed_actions.add(match_name)
        else:
            expected = options.get(match_name)
            if expected is not None:
                observed_options.add(match_name)
        if expected is not None:
            comparison_mode = expected.get("comparison_mode")
            if isinstance(comparison_mode, str) and comparison_mode.startswith(
                "float32_u32_"
            ):
                values_match = strict_equal(
                    float32_words(
                        record.get("value"),
                        f"{label}.rich42[{index}].value",
                    ),
                    float32_words(
                        expected.get("value"),
                        f"{label}.parameter_action[{index}].value",
                    ),
                )
            else:
                values_match = json_number_equal(
                    record.get("value"), expected.get("value")
                )
            if not values_match:
                fail(f"{label}: rich-42 writable value mismatch at row {index}")
    if observed_actions != set(actions) or observed_options != set(options):
        fail(f"{label}: rich-42 writable identity coverage mismatch")


def targeted_png_member(row: dict[str, Any]) -> str | None:
    if (
        row.get("plugin") == "OLMRadialBlur"
        and row.get("case_id")
        == "olmradialblur__canonical_20260604_case_0010_tiny_rotation"
        and row.get("depth") == 8
    ):
        return (
            "diagnostics/OLMRadialBlur/8bpc/"
            "canonical_20260604_case0010/effect_on.png"
        )
    if (
        row.get("plugin") == "OLMKiraKira"
        and row.get("case_id")
        in {
            "kk_mapped_bm2_mm1_ray_f0_a0_opaque",
            "kk_mapped_bm2_mm2_ray_f0_a0_opaque",
        }
        and row.get("depth") == 8
    ):
        return f"diagnostics/OLMKiraKira/8bpc/{row['case_id']}/effect_on.png"
    return None


class VerificationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise VerificationError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def strict_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return set(left) == set(right) and all(
            strict_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            strict_equal(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    if isinstance(left, float):
        return math.isfinite(left) and math.isfinite(right) and left == right
    return left == right


def json_number_equal(left: object, right: object) -> bool:
    if (
        isinstance(left, (int, float))
        and not isinstance(left, bool)
        and isinstance(right, (int, float))
        and not isinstance(right, bool)
    ):
        return (
            (not isinstance(left, float) or math.isfinite(left))
            and (not isinstance(right, float) or math.isfinite(right))
            and left == right
        )
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return set(left) == set(right) and all(
            json_number_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            json_number_equal(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    return left == right


def float32_scalar_and_u32(value: object, label: str) -> tuple[float, int]:
    if not is_finite_float32_json(value):
        fail(f"{label}: expected finite float32-compatible JSON number")
    try:
        payload = struct.pack("<f", value)
    except (OverflowError, struct.error) as exc:
        fail(f"{label}: cannot canonicalize float32: {exc}")
    return struct.unpack("<f", payload)[0], struct.unpack("<I", payload)[0]


def float32_value_and_u32(
    value: object,
    label: str,
) -> tuple[object, object]:
    if isinstance(value, list):
        canonical: list[float] = []
        words: list[int] = []
        for index, component in enumerate(value):
            scalar, word = float32_scalar_and_u32(
                component,
                f"{label}[{index}]",
            )
            canonical.append(scalar)
            words.append(word)
        return canonical, words
    return float32_scalar_and_u32(value, label)


def float32_words(value: object, label: str) -> object:
    return float32_value_and_u32(value, label)[1]


def f32_round(value: float) -> float:
    try:
        return struct.unpack("<f", struct.pack("<f", value))[0]
    except (OverflowError, struct.error):
        return math.copysign(math.inf, value)


def f32_clamp_unit(value: float) -> float:
    return f32_round(min(1.0, max(0.0, f32_round(value))))


def expected_kira_pf8_xmm(
    source: list[object],
    glow: list[object],
    mode: int,
) -> list[float]:
    source_f32 = [float32_scalar_and_u32(value, "PF8 source")[0] for value in source]
    glow_f32 = [float32_scalar_and_u32(value, "PF8 glow")[0] for value in glow]
    if f32_round(source_f32[3] + glow_f32[3]) == 0.0:
        return [0.0, 0.0, 0.0, 0.0]
    source_weight = f32_clamp_unit(source_f32[3])
    glow_weight = f32_clamp_unit(glow_f32[3])
    denominator = f32_round(source_weight + glow_weight)
    alpha = f32_clamp_unit(denominator)
    if denominator == 0.0:
        return [0.0, 0.0, 0.0, 0.0]
    rgb: list[float] = []
    inverse = f32_round(1.0 / denominator) if mode == 1 else 1.0
    for channel in range(3):
        source_term = f32_round(source_weight * source_f32[channel])
        glow_term = f32_round(glow_weight * glow_f32[channel])
        combined = f32_round(source_term + glow_term)
        if mode == 1:
            combined = f32_round(combined * inverse)
        rgb.append(f32_clamp_unit(combined))
    return [*rgb, alpha]


def require_unique_nonempty_strings(value: object, label: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
        or len(value) != len(set(value))
    ):
        fail(f"{label}: expected unique nonempty strings")
    return value


def is_finite_float32_json(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and (not isinstance(value, float) or math.isfinite(value))
        and abs(value) <= 3.4028234663852886e38
    )


def is_exact_int(value: object, expected: int) -> bool:
    return type(value) is int and value == expected


def is_pointer_json(value: object) -> bool:
    if type(value) is int:
        return 0 <= value <= 0xFFFFFFFFFFFFFFFF
    return (
        isinstance(value, str)
        and re.fullmatch(
            r"0x(?:[0-9a-fA-F]{1,16}|[0-9a-fA-F]{1,8}`[0-9a-fA-F]{1,8})",
            value,
        )
        is not None
    )


def pointer_json_value(value: object) -> int | None:
    if not is_pointer_json(value):
        return None
    if type(value) is int:
        return value
    return int(value[2:].replace("`", ""), 16)


def normalized_parameter_actions(
    writes: object,
    surface: dict[str, Any],
    label: str,
) -> list[dict[str, Any]]:
    if not isinstance(writes, list):
        fail(f"{label}: case writes are not an array")
    exact_rows = surface.get("exact_rows")
    if not isinstance(exact_rows, list):
        fail(f"{label}: surface exact_rows missing")
    surface_rows = {
        item.get("match_name"): item
        for item in exact_rows
        if isinstance(item, dict) and isinstance(item.get("match_name"), str)
    }
    actions: list[dict[str, Any]] = []
    for index, write in enumerate(writes):
        if not isinstance(write, dict):
            fail(f"{label}: write {index} is not an object")
        action = dict(write)
        if action.get("write") is False:
            action["action"] = "verify_fresh_default"
            action["write"] = False
            if (
                "expected_fresh_default" not in action
                or not strict_equal(
                    action.get("value"),
                    action["expected_fresh_default"],
                )
            ):
                fail(f"{label}: verify-default action {index} is incomplete")
        else:
            action["action"] = "set"
            action["write"] = True
            if "value" not in action:
                fail(f"{label}: set action {index} has no value")
        property_type = action.get("property_type")
        value = action.get("value")
        surface_row = surface_rows.get(action.get("match_name"), {})
        default_value = surface_row.get("default")
        if property_type in (6415, 6418):
            action["value_type"] = "point" if property_type == 6415 else "color"
            action["comparison_mode"] = "float32_u32_vector"
        elif property_type == 6421:
            action["value_type"] = "layer_index"
            action["comparison_mode"] = "exact_integer"
        elif isinstance(value, float) or isinstance(default_value, float):
            action["value_type"] = "scalar_float"
            action["comparison_mode"] = "float32_u32_scalar"
        else:
            action["value_type"] = "integer_or_popup"
            action["comparison_mode"] = "exact_integer"
        if action["comparison_mode"].startswith("float32_u32_"):
            canonical_value, raw_words = float32_value_and_u32(
                action["value"],
                f"{label}.write[{index}].value",
            )
            action["value"] = canonical_value
            action["value_raw_f32_u32"] = raw_words
            if action["action"] == "verify_fresh_default":
                action["expected_fresh_default"] = canonical_value
        actions.append(action)
    return actions


def verify_observed_surface(
    expected_contract: dict[str, Any],
    observed_surface: object,
    label: str,
) -> None:
    expected_rows = expected_contract.get("exact_rows")
    expected_count = expected_contract.get("plugin_only_leaf_count")
    if (
        not isinstance(expected_rows, list)
        or not isinstance(expected_count, int)
        or expected_count != len(expected_rows)
        or not isinstance(observed_surface, list)
        or len(observed_surface) != expected_count
    ):
        fail(f"{label}: surface cardinality mismatch")
    observed_keys = {
        "property_index",
        "match_name",
        "display_name",
        "property_type",
        "enabled",
        "active",
        "value_available",
        "value",
    }
    indices: set[int] = set()
    match_names: set[str] = set()
    for index, (expected, observed) in enumerate(
        zip(expected_rows, observed_surface, strict=True)
    ):
        if (
            not isinstance(expected, dict)
            or not isinstance(observed, dict)
            or set(observed) != observed_keys
        ):
            fail(f"{label}: malformed surface row {index}")
        for field in (
            "property_index",
            "match_name",
            "display_name",
            "property_type",
            "enabled",
            "active",
        ):
            if field not in expected or not strict_equal(
                observed[field], expected[field]
            ):
                fail(f"{label}: surface field mismatch row={index} field={field}")
        property_index = observed["property_index"]
        match_name = observed["match_name"]
        if (
            not isinstance(property_index, int)
            or isinstance(property_index, bool)
            or property_index in indices
            or not isinstance(match_name, str)
            or not match_name
            or match_name in match_names
        ):
            fail(f"{label}: duplicate/invalid surface identity row={index}")
        indices.add(property_index)
        match_names.add(match_name)
        value_available = observed["value_available"]
        if not isinstance(value_available, bool):
            fail(f"{label}: value_available must be boolean row={index}")
        if expected["property_type"] in (6412, 6419):
            if value_available is not False or observed["value"] is not None:
                fail(f"{label}: NO_VALUE/custom row exposed a value row={index}")
        elif value_available is not True:
            fail(f"{label}: writable value unavailable row={index}")
        if "default" in expected:
            expected_default = expected["default"]
            float32_default = (
                expected["property_type"] in (6415, 6418)
                or isinstance(expected_default, float)
                or isinstance(expected_default, list)
                and any(isinstance(component, float) for component in expected_default)
            )
            if value_available is not True:
                fail(f"{label}: untouched default unavailable row={index}")
            if float32_default:
                _, expected_words = float32_value_and_u32(
                    expected_default,
                    f"{label}.expected_default[{index}]",
                )
                _, observed_words = float32_value_and_u32(
                    observed["value"],
                    f"{label}.observed_default[{index}]",
                )
                if not strict_equal(observed_words, expected_words):
                    fail(f"{label}: untouched float32 default mismatch row={index}")
            elif not strict_equal(observed["value"], expected_default):
                fail(f"{label}: untouched default mismatch row={index}")


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_json_constant(value: str) -> None:
    fail(f"non-finite JSON constant rejected: {value}")


def load_json(path: Path) -> dict[str, Any]:
    if path.stat().st_size > 64 * 1024 * 1024:
        fail(f"JSON exceeds 64 MiB: {path}")
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_json_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"invalid JSON {path}: {exc}")
    if not isinstance(value, dict):
        fail(f"JSON root must be an object: {path}")
    stack: list[tuple[object, int]] = [(value, 0)]
    node_count = 0
    while stack:
        item, depth = stack.pop()
        node_count += 1
        if depth > 64 or node_count > 2_000_000:
            fail(f"JSON structural limit exceeded: {path}")
        if isinstance(item, dict):
            stack.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            stack.extend((child, depth + 1) for child in item)
    return value


def require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        fail(
            f"{label}: key mismatch missing={sorted(expected - actual)} "
            f"extra={sorted(actual - expected)}"
        )


def require_sha(value: object, label: str) -> str:
    if not isinstance(value, str) or SHA_RE.fullmatch(value) is None:
        fail(f"{label}: expected lowercase SHA-256")
    return value


def is_link_or_reparse(path: Path) -> bool:
    info = path.lstat()
    is_junction = getattr(path, "is_junction", None)
    return (
        stat.S_ISLNK(info.st_mode)
        or bool(getattr(info, "st_file_attributes", 0) & 0x400)
        or (callable(is_junction) and is_junction())
    )


def require_safe_relative_path(relative: str, label: str) -> str:
    parts = Path(relative).parts
    reserved = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{index}" for index in range(1, 10)),
        *(f"LPT{index}" for index in range(1, 10)),
    }
    if (
        not relative
        or len(relative) > 1024
        or relative.startswith("/")
        or "\\" in relative
        or ".." in parts
        or re.match(r"^[A-Za-z]:", relative)
    ):
        fail(f"{label}: unsafe relative path: {relative}")
    for part in parts:
        if (
            not part
            or len(part) > 255
            or any(ord(character) < 32 for character in part)
            or ":" in part
            or part.endswith((".", " "))
            or part.split(".", 1)[0].upper() in reserved
        ):
            fail(f"{label}: Windows-unsafe path component: {relative}")
    return unicodedata.normalize("NFC", relative).casefold()


def windows_runtime_path_key(value: str) -> str:
    windows_path = value.replace("/", "\\")
    folded = windows_path.casefold()
    if folded.startswith(("\\\\?\\", "\\\\.\\")):
        fail(f"extended/device runtime path rejected: {value}")
    if re.match(r"^[A-Za-z]:\\", windows_path):
        path_tail = windows_path[3:]
    elif windows_path.startswith("\\\\"):
        path_tail = windows_path[2:]
    else:
        fail(f"runtime path is not absolute Windows syntax: {value}")
    components = path_tail.split("\\")
    if (
        ":" in path_tail
        or any(
            component in {".", ".."}
            or component.endswith((".", " "))
            or not component
            for component in components
        )
    ):
        fail(f"noncanonical/aliasing runtime path rejected: {value}")
    return ntpath.normcase(ntpath.normpath(windows_path))


def regular_files(root: Path) -> dict[str, Path]:
    if not root.is_dir() or is_link_or_reparse(root):
        fail(f"root is missing, not a directory, or a symlink: {root}")
    result: dict[str, Path] = {}
    total_bytes = 0
    folded_paths: set[str] = set()
    folded_directories: set[str] = set()
    def walk_error(error: OSError) -> None:
        fail(f"directory traversal failed under {root}: {error}")

    for directory, names, files in os.walk(
        root,
        followlinks=False,
        onerror=walk_error,
    ):
        directory_path = Path(directory)
        if is_link_or_reparse(directory_path):
            fail(f"symlink directory rejected: {directory_path}")
        if directory_path != root and not names and not files:
            fail(f"unexpected empty directory rejected: {directory_path}")
        for name in names:
            if len(folded_directories) >= 10_000:
                fail(f"directory-count ceiling exceeded under {root}")
            path = directory_path / name
            if is_link_or_reparse(path):
                fail(f"symlink directory rejected: {path}")
            relative_directory = path.relative_to(root).as_posix()
            folded_directory = require_safe_relative_path(
                relative_directory,
                "return directory",
            )
            if folded_directory in folded_directories:
                fail(f"case-folding directory collision: {relative_directory}")
            folded_directories.add(folded_directory)
        for name in files:
            if len(result) >= 10_000:
                fail(f"file-count ceiling exceeded under {root}")
            path = directory_path / name
            info = path.lstat()
            if is_link_or_reparse(path) or not stat.S_ISREG(info.st_mode):
                fail(f"non-regular return member rejected: {path}")
            relative = path.relative_to(root).as_posix()
            size_ceiling = (
                MAX_CHECKSUM_BYTES
                if relative == "CHECKSUMS.sha256"
                else MAX_EXR_BYTES
                if relative.casefold().endswith(".exr")
                else MAX_RETURN_MEMBER_BYTES
            )
            if info.st_size > size_ceiling:
                fail(
                    f"return member exceeds {size_ceiling} byte ceiling: "
                    f"{relative}"
                )
            total_bytes += info.st_size
            if total_bytes > MAX_TOTAL_RETURN_BYTES:
                fail(
                    f"return tree exceeds {MAX_TOTAL_RETURN_BYTES} byte ceiling "
                    f"under {root}"
                )
            folded = require_safe_relative_path(relative, "return member")
            if folded in folded_paths:
                fail(f"case-folding path collision: {relative}")
            folded_paths.add(folded)
            result[relative] = path
    return result


def parse_checksums(path: Path) -> dict[str, str]:
    if path.stat().st_size > MAX_CHECKSUM_BYTES:
        fail(f"{path}: checksum manifest exceeds {MAX_CHECKSUM_BYTES} bytes")
    rows: dict[str, str] = {}
    with path.open("r", encoding="utf-8", newline="") as stream:
        for line_number, raw_line in enumerate(stream, 1):
            if line_number > 10_000:
                fail(f"{path}: checksum row-count ceiling exceeded")
            if len(raw_line) > 1100:
                fail(f"{path}:{line_number}: checksum row exceeds length ceiling")
            line = raw_line.removesuffix("\n").removesuffix("\r")
            match = re.fullmatch(r"([0-9a-f]{64})  ([^\x00-\x1f]+)", line)
            if match is None:
                fail(f"{path}:{line_number}: malformed checksum row")
            digest, relative = match.groups()
            require_safe_relative_path(relative, f"{path}:{line_number}")
            if relative in rows:
                fail(f"{path}:{line_number}: duplicate checksum path")
            rows[relative] = digest
    return rows


def read_text_evidence(path: Path, label: str) -> str:
    if path.stat().st_size > 64 * 1024 * 1024:
        fail(f"{label}: text evidence exceeds 64 MiB")
    payload = path.read_bytes()
    if payload.startswith((b"\xff\xfe", b"\xfe\xff")):
        encodings = ("utf-16",)
    elif b"\x00" in payload[:256]:
        even_nuls = payload[:256:2].count(0)
        odd_nuls = payload[1:256:2].count(0)
        encodings = (
            ("utf-16-le", "utf-16-be")
            if odd_nuls >= even_nuls
            else ("utf-16-be", "utf-16-le")
        )
    else:
        encodings = ("utf-8-sig",)
    for encoding in encodings:
        try:
            text = payload.decode(encoding)
        except UnicodeError:
            continue
        if "\x00" not in text and text.strip():
            return text
    fail(f"{label}: expected nonempty UTF-8/UTF-16 text evidence")


def parse_utc_timestamp(value: object, label: str) -> datetime:
    if (
        not isinstance(value, str)
        or re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z",
            value,
        )
        is None
    ):
        fail(f"{label}: expected ISO-8601 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        fail(f"{label}: invalid timestamp: {exc}")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        fail(f"{label}: timestamp is not timezone-aware")
    return parsed


def verify_etw_csv(
    text: str,
    process: dict[str, Any],
    row: dict[str, Any],
    label: str,
) -> None:
    reader = csv.DictReader(io.StringIO(text))
    expected_fields = [
        "event_type",
        "pid",
        "parent_pid",
        "image_path",
        "timestamp_utc",
    ]
    if reader.fieldnames != expected_fields:
        fail(f"{label}: normalized ETW CSV header mismatch")
    records: list[dict[str, str]] = []
    for record in reader:
        records.append(record)
        if len(records) > 5:
            fail(f"{label}: normalized ETW CSV has extra records")
    expected_records = [
        {
            "event_type": "aerender_start",
            "pid": str(process["aerender"]["pid"]),
            "parent_pid": "0",
            "image_path": process["aerender"]["path"],
            "timestamp_utc": process["aerender"]["start_time_utc"],
        },
        {
            "event_type": "afterfx_child_start",
            "pid": str(process["real_afterfx_child"]["pid"]),
            "parent_pid": str(process["aerender"]["pid"]),
            "image_path": process["real_afterfx_child"]["path"],
            "timestamp_utc": process["real_afterfx_child"]["start_time_utc"],
        },
        {
            "event_type": "aex_image_load",
            "pid": str(process["real_afterfx_child"]["pid"]),
            "parent_pid": str(process["aerender"]["pid"]),
            "image_path": process["module"]["path"],
            "timestamp_utc": process["module"]["load_time_utc"],
        },
        {
            "event_type": "aex_image_unload",
            "pid": str(process["real_afterfx_child"]["pid"]),
            "parent_pid": str(process["aerender"]["pid"]),
            "image_path": process["module"]["path"],
            "timestamp_utc": process["module"]["unload_time_utc"],
        },
        {
            "event_type": "afterfx_child_stop",
            "pid": str(process["real_afterfx_child"]["pid"]),
            "parent_pid": str(process["aerender"]["pid"]),
            "image_path": process["real_afterfx_child"]["path"],
            "timestamp_utc": process["real_afterfx_child"]["stop_time_utc"],
        },
    ]
    if not strict_equal(records, expected_records):
        fail(f"{label}: normalized ETW process/module projection mismatch")
    for index, record in enumerate(records):
        parse_utc_timestamp(
            record["timestamp_utc"],
            f"{label}.rows[{index}].timestamp_utc",
        )


def verify_png_container(path: Path, label: str) -> tuple[int, int]:
    if path.stat().st_size > 64 * 1024 * 1024:
        fail(f"{label}: PNG exceeds 64 MiB")
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        fail(f"{label}: not a PNG")
    cursor = 8
    chunks: list[tuple[bytes, bytes]] = []
    while cursor < len(data):
        if cursor + 12 > len(data):
            fail(f"{label}: truncated PNG chunk")
        length = struct.unpack_from(">I", data, cursor)[0]
        chunk_type = data[cursor + 4 : cursor + 8]
        payload_start = cursor + 8
        payload_end = payload_start + length
        chunk_end = payload_end + 4
        if chunk_end > len(data):
            fail(f"{label}: PNG chunk exceeds file")
        payload = data[payload_start:payload_end]
        stored_crc = struct.unpack_from(">I", data, payload_end)[0]
        if zlib.crc32(chunk_type + payload) & 0xFFFFFFFF != stored_crc:
            fail(f"{label}: PNG CRC mismatch")
        chunks.append((chunk_type, payload))
        if len(chunks) > MAX_PNG_CHUNKS:
            fail(f"{label}: PNG chunk-count ceiling exceeded")
        cursor = chunk_end
        if chunk_type == b"IEND":
            break
    if cursor != len(data) or not chunks or chunks[-1][0] != b"IEND":
        fail(f"{label}: PNG has no exact terminal IEND")
    if (
        sum(kind == b"IHDR" for kind, _ in chunks) != 1
        or sum(kind == b"IEND" for kind, _ in chunks) != 1
        or chunks[-1][1] != b""
    ):
        fail(f"{label}: PNG critical-chunk structure mismatch")
    chunk_type, ihdr = chunks[0]
    if chunk_type != b"IHDR" or len(ihdr) != 13:
        fail(f"{label}: PNG IHDR missing or malformed")
    width, height, depth, color_type, compression, filtering, interlace = (
        struct.unpack(">IIBBBBB", ihdr)
    )
    if (
        not 1 <= width <= 16384
        or not 1 <= height <= 16384
        or depth not in (1, 2, 4, 8, 16)
        or color_type not in (0, 2, 3, 4, 6)
        or compression != 0
        or filtering != 0
        or interlace not in (0, 1)
        or not any(kind == b"IDAT" and payload for kind, payload in chunks)
    ):
        fail(f"{label}: PNG header/data contract mismatch")
    return width, height


def read_rgba8_png(
    path: Path,
    expected_dimensions: tuple[int, int],
) -> tuple[int, int, bytes]:
    if path.stat().st_size > 64 * 1024 * 1024:
        fail(f"{path}: PNG exceeds 64 MiB")
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        fail(f"{path}: not a PNG")
    cursor = 8
    chunks: list[tuple[bytes, bytes]] = []
    while cursor < len(data):
        if cursor + 12 > len(data):
            fail(f"{path}: truncated PNG chunk")
        length = struct.unpack_from(">I", data, cursor)[0]
        chunk_type = data[cursor + 4 : cursor + 8]
        payload_start = cursor + 8
        payload_end = payload_start + length
        chunk_end = payload_end + 4
        if chunk_end > len(data):
            fail(f"{path}: PNG chunk exceeds file")
        payload = data[payload_start:payload_end]
        stored_crc = struct.unpack_from(">I", data, payload_end)[0]
        if zlib.crc32(chunk_type + payload) & 0xFFFFFFFF != stored_crc:
            fail(f"{path}: PNG CRC mismatch")
        chunks.append((chunk_type, payload))
        if len(chunks) > MAX_PNG_CHUNKS:
            fail(f"{path}: PNG chunk-count ceiling exceeded")
        cursor = chunk_end
        if chunk_type == b"IEND":
            break
    if cursor != len(data) or not chunks or chunks[-1][0] != b"IEND":
        fail(f"{path}: PNG has no exact terminal IEND")
    if (
        sum(kind == b"IHDR" for kind, _ in chunks) != 1
        or sum(kind == b"IEND" for kind, _ in chunks) != 1
        or chunks[-1][1] != b""
    ):
        fail(f"{path}: PNG critical-chunk structure mismatch")
    chunk_type, ihdr = chunks[0]
    if chunk_type != b"IHDR" or len(ihdr) != 13:
        fail(f"{path}: PNG IHDR missing or malformed")
    width, height, depth, color_type, compression, filtering, interlace = (
        struct.unpack(">IIBBBBB", ihdr)
    )
    if (
        (width, height) != expected_dimensions
        or depth != 8
        or color_type != 6
        or compression != 0
        or filtering != 0
        or interlace != 0
    ):
        fail(f"{path}: expected noninterlaced RGBA8 PNG at {expected_dimensions}")
    decoded_bytes = width * height * 4
    if decoded_bytes > MAX_DECODED_PNG_BYTES:
        fail(
            f"{path}: decoded RGBA8 payload exceeds "
            f"{MAX_DECODED_PNG_BYTES} bytes"
        )
    compressed = b"".join(payload for kind, payload in chunks if kind == b"IDAT")
    if not compressed:
        fail(f"{path}: PNG has no IDAT payload")
    row_bytes = width * 4
    expected_filtered_bytes = height * (row_bytes + 1)
    try:
        decompressor = zlib.decompressobj()
        filtered = decompressor.decompress(
            compressed,
            expected_filtered_bytes + 1,
        )
    except zlib.error as exc:
        fail(f"{path}: PNG zlib decode failed: {exc}")
    if (
        len(filtered) != expected_filtered_bytes
        or decompressor.unconsumed_tail
        or decompressor.unused_data
        or not decompressor.eof
    ):
        fail(f"{path}: PNG decoded byte count mismatch")
    decoded = bytearray(decoded_bytes)
    previous = bytearray(row_bytes)
    source_offset = 0
    for y in range(height):
        filter_type = filtered[source_offset]
        source_offset += 1
        source = filtered[source_offset : source_offset + row_bytes]
        source_offset += row_bytes
        current = bytearray(row_bytes)
        for index, value in enumerate(source):
            left = current[index - 4] if index >= 4 else 0
            up = previous[index]
            upper_left = previous[index - 4] if index >= 4 else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = up
            elif filter_type == 3:
                predictor = (left + up) // 2
            elif filter_type == 4:
                estimate = left + up - upper_left
                left_distance = abs(estimate - left)
                up_distance = abs(estimate - up)
                upper_left_distance = abs(estimate - upper_left)
                predictor = (
                    left
                    if left_distance <= up_distance
                    and left_distance <= upper_left_distance
                    else up
                    if up_distance <= upper_left_distance
                    else upper_left
                )
            else:
                fail(f"{path}: unsupported PNG filter type {filter_type}")
            current[index] = (value + predictor) & 0xFF
        decoded[y * row_bytes : (y + 1) * row_bytes] = current
        previous = current
    return width, height, bytes(decoded)


def verify_checksums(root: Path, files: dict[str, Path]) -> dict[str, str]:
    checksum_path = files.get("CHECKSUMS.sha256")
    if checksum_path is None:
        fail(f"{root}: CHECKSUMS.sha256 missing")
    expected = parse_checksums(checksum_path)
    actual_names = set(files) - {"CHECKSUMS.sha256"}
    if set(expected) != actual_names:
        fail(
            f"{root}: checksum coverage mismatch "
            f"missing={sorted(actual_names - set(expected))[:5]} "
            f"extra={sorted(set(expected) - actual_names)[:5]}"
        )
    for relative, digest in expected.items():
        if sha256(files[relative]) != digest:
            fail(f"{root}: checksum mismatch: {relative}")
    return expected


def request_contract(request_root: Path) -> tuple[
    dict[str, Path],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    files = regular_files(request_root)
    verify_checksums(request_root, files)
    for required in (
        "CAMPAIGN_MANIFEST.json",
        "EXECUTION_ROWS.json",
        "ROW_INVENTORY.json",
        "RETURN_CONTRACT.json",
    ):
        if required not in files:
            fail(f"request missing {required}")
    campaign = load_json(files["CAMPAIGN_MANIFEST.json"])
    configure_campaign_contract(campaign.get("campaign_id"))
    inventory = load_json(files["ROW_INVENTORY.json"])
    execution = load_json(files["EXECUTION_ROWS.json"])
    return_contract = load_json(files["RETURN_CONTRACT.json"])
    schema_index = load_json(files["schemas/SCHEMA_INDEX.json"])
    require_exact_keys(
        schema_index,
        {
            "schema_version",
            "campaign_id",
            "files",
            "schemas_are_normative",
            "validation",
        },
        "schemas/SCHEMA_INDEX.json",
    )
    require_exact_keys(
        inventory,
        {
            "schema_version",
            "campaign_id",
            "claim_boundary",
            "row_count",
            "lane_counts",
            "groups",
            "rows",
        },
        "ROW_INVENTORY.json",
    )
    require_exact_keys(
        execution,
        {
            "schema_version",
            "campaign_id",
            "claim_boundary",
            "row_count",
            "rows",
        },
        "EXECUTION_ROWS.json",
    )
    require_exact_keys(
        return_contract,
        {
            "schema_version",
            "campaign_id",
            "single_consolidated_return_only",
            "raw_outcome_predicates",
            "parameter_predicates",
            "cross_row_predicates",
            "image_policy",
            "required_tree",
            "reject_if",
            "claim_boundary",
            "row_contract",
        },
        "RETURN_CONTRACT.json",
    )
    if (
        campaign.get("campaign_id") != CAMPAIGN_ID
        or not is_exact_int(
            campaign.get("expected_row_count"),
            EXPECTED_TOTAL_ROWS,
        )
        or not is_exact_int(
            campaign.get("expected_render_count"),
            EXPECTED_TOTAL_ROWS * 2,
        )
        or inventory.get("campaign_id") != CAMPAIGN_ID
        or execution.get("campaign_id") != CAMPAIGN_ID
        or not is_exact_int(return_contract.get("schema_version"), 3)
        or return_contract.get("campaign_id") != CAMPAIGN_ID
        or return_contract.get("single_consolidated_return_only") is not True
        or return_contract.get("row_contract", {}).get("partial_return_allowed")
        is not False
        or not is_exact_int(
            return_contract.get("row_contract", {}).get("expected_total_rows"),
            EXPECTED_TOTAL_ROWS,
        )
        or not strict_equal(
            return_contract.get("row_contract", {}).get("expected_lane_rows"),
            EXPECTED_LANE_ROWS,
        )
        or not is_exact_int(inventory.get("schema_version"), 1)
        or not is_exact_int(execution.get("schema_version"), 1)
        or not strict_equal(inventory.get("lane_counts"), EXPECTED_LANE_ROWS)
        or not is_exact_int(schema_index.get("schema_version"), 1)
        or schema_index.get("campaign_id") != CAMPAIGN_ID
        or schema_index.get("schemas_are_normative") is not True
        or not isinstance(schema_index.get("validation"), str)
        or not schema_index["validation"]
        or not isinstance(schema_index.get("files"), list)
        or set(schema_index["files"]) != EXPECTED_SCHEMA_FILES
    ):
        fail("request campaign/return/schema contract mismatch")
    if len(schema_index["files"]) != len(set(schema_index["files"])):
        fail("request schema index contains duplicate files")
    for schema_name in schema_index["files"]:
        if (
            not isinstance(schema_name, str)
            or f"schemas/{schema_name}" not in files
            or sha256(files[f"schemas/{schema_name}"])
            != EXPECTED_SCHEMA_SHA256.get(schema_name)
            or not load_json(files[f"schemas/{schema_name}"]).get("$schema")
        ):
            fail(f"request schema index mismatch: {schema_name!r}")
    rows = execution.get("rows")
    compact_rows = inventory.get("rows")
    expected_count = campaign.get("expected_row_count")
    if (
        type(expected_count) is not int
        or not isinstance(rows, list)
        or not isinstance(compact_rows, list)
        or len(rows) != expected_count
        or len(compact_rows) != expected_count
        or not is_exact_int(execution.get("row_count"), expected_count)
        or not is_exact_int(inventory.get("row_count"), expected_count)
    ):
        fail("request row cardinality mismatch")
    row_ids: list[str] = []
    lane_counts: dict[str, int] = {}
    definition_cache: dict[str, dict[str, Any]] = {}
    inventory_row_keys = {
        "row_id",
        "plugin",
        "group_id",
        "case_id",
        "depth",
        "source_member",
        "source_sha256",
        "aex_member",
        "aex_sha256",
        "comp",
        "case_definition_file",
        "case_definition_sha256",
        "case_contract_sha256",
        "intentional_noop",
        "expected_raw_off_on_relation",
    }
    execution_extra_keys = {
        "effect",
        "parameter_surface",
        "parameter_writes",
        "parameter_action_semantics",
        "standard_options",
        "project_contract",
        "fresh_identity_contract",
        "execution_row_sha256",
    }
    if CAMPAIGN_ID == R5_CAMPAIGN_ID:
        execution_extra_keys.add("plugin_deployment_contract")
    expected_action_semantics = {
        "set": (
            "Resolve exactly one recursive leaf by exact match_name, set "
            "value, then read back before and after render."
        ),
        "verify_fresh_default": (
            "Do not call setValue. Before any render, require the fresh "
            "effect value to equal expected_fresh_default, then read back "
            "the same value after render."
        ),
    }
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            fail(f"execution row {index} is not an object")
        if set(row) != inventory_row_keys | execution_extra_keys:
            fail(f"execution row {index} has an unexpected shape")
        row_id = row.get("row_id")
        if not isinstance(row_id, str) or not row_id:
            fail(f"execution row {index} has no row_id")
        if row_id in row_ids:
            fail(f"duplicate execution row_id: {row_id}")
        stored_hash = require_sha(row.get("execution_row_sha256"), f"{row_id}.execution")
        unhashed = dict(row)
        del unhashed["execution_row_sha256"]
        if canonical_json_sha256(unhashed) != stored_hash:
            fail(f"execution_row_sha256 mismatch: {row_id}")
        compact = compact_rows[index]
        if (
            not isinstance(compact, dict)
            or set(compact) != inventory_row_keys
            or compact.get("row_id") != row_id
        ):
            fail(f"compact/execution row order mismatch: {row_id}")
        for key in inventory_row_keys:
            if not strict_equal(row[key], compact[key]):
                fail(f"compact/execution semantic mismatch: {row_id}.{key}")
        source = files.get(str(row.get("source_member")))
        aex = files.get(str(row.get("aex_member")))
        if source is None or sha256(source) != row.get("source_sha256"):
            fail(f"source binding mismatch: {row_id}")
        if aex is None or sha256(aex) != row.get("aex_sha256"):
            fail(f"AEX binding mismatch: {row_id}")
        definition = files.get(str(row.get("case_definition_file")))
        if definition is None or sha256(definition) != row.get("case_definition_sha256"):
            fail(f"case-definition binding mismatch: {row_id}")
        definition_member = str(row["case_definition_file"])
        definition_value = definition_cache.get(definition_member)
        if definition_value is None:
            definition_value = load_json(definition)
            definition_cache[definition_member] = definition_value
        cases = definition_value.get("cases")
        if not isinstance(cases, list):
            fail(f"case definition has no cases: {definition_member}")
        matching_cases = [
            case
            for case in cases
            if isinstance(case, dict) and case.get("case_id") == row.get("case_id")
        ]
        if len(matching_cases) != 1:
            fail(f"case definition resolution is not unique: {row_id}")
        case = matching_cases[0]
        surface = definition_value.get("surface")
        if surface is None:
            surface = definition_value.get("surface_contract")
        writes = case.get("writes")
        if writes is None:
            writes = case.get("parameter_writes")
        effect = {
            "display_name": definition_value.get("effect_display_name"),
            "match_name": definition_value.get("effect_match_name"),
        }
        if (
            canonical_json_sha256(case) != row.get("case_contract_sha256")
            or case.get("intentional_noop") is not row.get("intentional_noop")
            or type(row.get("intentional_noop")) is not bool
            or not isinstance(row.get("parameter_writes"), list)
            or not isinstance(row.get("parameter_surface"), dict)
            or not isinstance(surface, dict)
            or not strict_equal(row["parameter_surface"], surface)
            or not strict_equal(
                row["parameter_writes"],
                normalized_parameter_actions(writes, surface, row_id),
            )
            or not strict_equal(row.get("effect"), effect)
            or not strict_equal(
                row.get("parameter_action_semantics"),
                expected_action_semantics,
            )
            or not isinstance(row["parameter_surface"].get("exact_rows"), list)
            or row["parameter_surface"].get("plugin_only_leaf_count")
            != len(row["parameter_surface"]["exact_rows"])
            or not strict_equal(row.get("standard_options"), COMMON_STANDARD_OPTIONS)
        ):
            fail(f"materialized execution semantics mismatch: {row_id}")
        surface_rows = row["parameter_surface"]["exact_rows"]
        surface_indices: set[int] = set()
        surface_names: set[str] = set()
        surface_by_name: dict[str, dict[str, Any]] = {}
        for surface_index, surface_row in enumerate(surface_rows):
            if (
                not isinstance(surface_row, dict)
                or any(
                    field not in surface_row
                    for field in (
                        "property_index",
                        "match_name",
                        "display_name",
                        "property_type",
                        "enabled",
                        "active",
                    )
                )
                or type(surface_row["property_index"]) is not int
                or surface_row["property_index"] <= 0
                or not isinstance(surface_row["match_name"], str)
                or not surface_row["match_name"]
                or not isinstance(surface_row["display_name"], str)
                or type(surface_row["property_type"]) is not int
                or type(surface_row["enabled"]) is not bool
                or type(surface_row["active"]) is not bool
                or surface_row["property_index"] in surface_indices
                or surface_row["match_name"] in surface_names
            ):
                fail(f"surface identity row is malformed: {row_id}/{surface_index}")
            surface_indices.add(surface_row["property_index"])
            surface_names.add(surface_row["match_name"])
            surface_by_name[surface_row["match_name"]] = surface_row
        action_names: set[str] = set()
        for action in row["parameter_writes"]:
            if not isinstance(action, dict):
                fail(f"parameter action is not an object: {row_id}")
            match_name = action.get("match_name")
            if (
                not isinstance(match_name, str)
                or not match_name
                or match_name in action_names
                or action.get("action") not in ("set", "verify_fresh_default")
                or not isinstance(action.get("write"), bool)
                or not isinstance(action.get("comparison_mode"), str)
                or not isinstance(action.get("value_type"), str)
            ):
                fail(f"parameter action is ambiguous: {row_id}")
            if (
                action["action"] == "set"
                and action["write"] is not True
            ) or (
                action["action"] == "verify_fresh_default"
                and (
                    action["write"] is not False
                    or "expected_fresh_default" not in action
                    or not strict_equal(
                        action.get("value"),
                        action["expected_fresh_default"],
                    )
                )
            ):
                fail(f"parameter action discriminator mismatch: {row_id}")
            surface_row = surface_by_name.get(match_name)
            if (
                surface_row is None
                or action.get("property_type") != surface_row["property_type"]
                or (
                    action["action"] == "set"
                    and surface_row.get("write") is False
                )
            ):
                fail(f"parameter action/surface identity mismatch: {row_id}")
            action_names.add(match_name)
        project_contract = row.get("project_contract")
        comp = row.get("comp")
        if (
            not isinstance(project_contract, dict)
            or not isinstance(comp, dict)
            or project_contract.get("ae_version") != "26.3x87"
            or project_contract.get("renderer") != "SOFTWARE"
            or project_contract.get("renderer_raw") != 1816
            or project_contract.get("bits_per_channel") != row.get("depth")
            or project_contract.get("working_space_normalized") is not None
            or not strict_equal(
                project_contract.get("working_space_raw_accepted"),
                [None, ""],
            )
            or project_contract.get("linear_blending") is not False
            or project_contract.get("blend_colors_using_1_0_gamma") is not False
            or not strict_equal(project_contract.get("comp"), comp)
            or not strict_equal(
                project_contract.get("primary_output"),
                {
                    "format": "OpenEXR",
                    "storage": "scanline",
                    "compression": "none",
                    "physical_channels": ["A", "B", "G", "R"],
                    "sample_type": "FLOAT32",
                    "channel_type": 2,
                },
            )
        ):
            fail(f"project contract is under-bound: {row_id}")
        expected_project_contract_keys = {
            "ae_version",
            "renderer",
            "renderer_raw",
            "bits_per_channel",
            "working_space_normalized",
            "working_space_raw_accepted",
            "linear_blending",
            "blend_colors_using_1_0_gamma",
            "comp",
            "input_interpretation",
            "primary_output",
        }
        if CAMPAIGN_ID == R5_CAMPAIGN_ID:
            expected_project_contract_keys.add("render_queue_observation_contract")
        require_exact_keys(
            project_contract,
            expected_project_contract_keys,
            f"{row_id}.project_contract",
        )
        expected_comp_keys = {
            "width",
            "height",
            "pixel_aspect",
            "frame_rate",
            "frame",
            "time_seconds",
            "duration_seconds",
            "render_time_span_start_seconds",
            "render_time_span_duration_seconds",
            "resolution_factor",
            "source_layer_scale",
            "source_layer_centered",
            "source_layer_index",
            "num_layers",
        }
        if CAMPAIGN_ID == R5_CAMPAIGN_ID:
            expected_comp_keys.add("source_layer_timing")
        require_exact_keys(
            comp,
            expected_comp_keys,
            f"{row_id}.comp",
        )
        if CAMPAIGN_ID == R5_CAMPAIGN_ID:
            global_contract = campaign.get("global_contract")
            if not isinstance(global_contract, dict):
                fail("r5 campaign global_contract missing")
            default_frame = global_contract.get("default_frame")
            default_time_seconds = global_contract.get("default_time_seconds")
            if (
                not is_exact_int(default_frame, 24)
                or type(default_time_seconds) is not float
                or default_time_seconds != 1.0
            ):
                fail("r5 campaign default frame/time contract drift")
            expected_frame = definition_value.get("frame", default_frame)
            expected_time_seconds = definition_value.get(
                "time_seconds", default_time_seconds
            )
        else:
            expected_frame = 24
            expected_time_seconds = 1.0
        if (
            type(comp["width"]) is not int
            or comp["width"] <= 0
            or type(comp["height"]) is not int
            or comp["height"] <= 0
            or type(comp["pixel_aspect"]) is not float
            or comp["pixel_aspect"] != 1.0
            or type(comp["frame_rate"]) is not int
            or comp["frame_rate"] != 24
            or type(comp["frame"]) is not int
            or comp["frame"] != expected_frame
            or type(comp["time_seconds"]) is not float
            or comp["time_seconds"] != expected_time_seconds
            or type(comp["duration_seconds"]) is not float
            or comp["duration_seconds"] != 2.0
            or type(comp["render_time_span_start_seconds"]) is not float
            or comp["render_time_span_start_seconds"] != expected_time_seconds
            or type(comp["render_time_span_duration_seconds"]) is not float
            or comp["render_time_span_duration_seconds"] != 1.0 / 24.0
            or not strict_equal(comp["resolution_factor"], [1, 1])
            or not strict_equal(comp["source_layer_scale"], [100.0, 100.0])
            or comp["source_layer_centered"] is not True
            or type(comp["source_layer_index"]) is not int
            or comp["source_layer_index"] != 1
            or type(comp["num_layers"]) is not int
            or comp["num_layers"] != 1
            or CAMPAIGN_ID == R5_CAMPAIGN_ID
            and (
                not is_exact_int(expected_frame, comp["frame"])
                or type(expected_time_seconds) is not float
                or expected_time_seconds != comp["time_seconds"]
                or expected_time_seconds != expected_frame / 24.0
                or not strict_equal(
                    comp["source_layer_timing"],
                    {
                        "startTime": 0.0,
                        "inPoint": 0.0,
                        "outPoint": 2.0,
                        "stretch": 100.0,
                        "timeRemapEnabled": False,
                    },
                )
            )
        ):
            fail(f"exact comp/timing contract drift: {row_id}")
        interpretation = project_contract.get("input_interpretation")
        if (
            not isinstance(interpretation, dict)
            or interpretation.get("method")
            != "hash_bound_aep_template_footage_replace"
            or interpretation.get("replace_method") != "FootageItem.replace(File)"
            or interpretation.get("preserve_rgb") is not True
            or interpretation.get("alpha_mode") != "straight"
            or interpretation.get("premultiplied") is not False
            or interpretation.get("template_member")
            != "inputs/preserve_rgb_template.aep"
            or interpretation.get("template_sha256")
            != "51fd5403b0a43825f0f6d189c49154ad756f4c565498f733c1fb725377583679"
            or interpretation.get("footage_item_name") != "OLM_COLOR_PROBE_INPUT"
            or interpretation.get("comp_item_name") != "OLM_COLOR_PROBE_COMP"
            or interpretation.get("comp_layer_index") != 1
            or interpretation.get("expected_num_layers") != 1
            or interpretation.get("effect_parade_must_be_empty_before_add")
            is not True
        ):
            fail(f"input interpretation contract is under-bound: {row_id}")
        expected_interpretation_keys = {
            "method",
            "replace_method",
            "preserve_rgb",
            "alpha_mode",
            "premultiplied",
            "template_member",
            "template_sha256",
            "footage_item_name",
            "comp_item_name",
            "comp_layer_index",
            "expected_num_layers",
            "source_identity_gate",
            "effect_parade_must_be_empty_before_add",
        }
        if CAMPAIGN_ID == R5_CAMPAIGN_ID:
            expected_interpretation_keys.add("project_item_name_type_cardinality")
        require_exact_keys(
            interpretation,
            expected_interpretation_keys,
            f"{row_id}.input_interpretation",
        )
        if CAMPAIGN_ID == R5_CAMPAIGN_ID:
            if not strict_equal(
                interpretation["project_item_name_type_cardinality"],
                {
                    "OLM_COLOR_PROBE_INPUT": {
                        "item_type": "FootageItem",
                        "exact_count": 1,
                    },
                    "OLM_COLOR_PROBE_COMP": {
                        "item_type": "CompItem",
                        "exact_count": 1,
                    },
                },
            ):
                fail(f"project item cardinality contract drift: {row_id}")
            rq_contract = project_contract["render_queue_observation_contract"]
            if not strict_equal(
                rq_contract,
                {
                    "branch_names": ["no_effect", "effect_on"],
                    "required_live_fields": ["timeSpanStart", "timeSpanDuration"],
                    "timeSpanStart": comp["render_time_span_start_seconds"],
                    "timeSpanDuration": comp["render_time_span_duration_seconds"],
                    "comparison_mode": "exact_live_numeric_readback",
                },
            ):
                fail(f"render queue observation contract drift: {row_id}")
            deployment = row["plugin_deployment_contract"]
            expected_basename = str(row["aex_member"]).rsplit("/", 1)[-1]
            deployment_campaign_root = (
                "%APPDATA%\\Adobe\\Common\\Plug-ins\\7.0\\MediaCore\\"
                f"OLM_Codex_Isolated\\{CAMPAIGN_ID}"
            )
            deployed_runtime_expression = (
                f"{deployment_campaign_root}\\{row['plugin']}\\{expected_basename}"
            )
            staging_campaign_root = (
                f"%LOCALAPPDATA%\\OLM_Codex_Staging\\{CAMPAIGN_ID}"
            )
            isolated_staging_expression = (
                f"{staging_campaign_root}\\{row['plugin']}\\{expected_basename}"
            )
            if not strict_equal(
                deployment,
                {
                    "preflight_only_until_explicit_user_start": True,
                    "declared_ae_26_3_plugin_root_ids": [
                        "ae_application_plugins",
                        "adobe_common_mediacore_machine",
                        "adobe_common_mediacore_user",
                    ],
                    "target": {
                        "aex_basename": expected_basename,
                        "effect_display_name": row["effect"]["display_name"],
                        "effect_match_name": row["effect"]["match_name"],
                        "sha256": row["aex_sha256"],
                    },
                    "staging_campaign_root_path_expression": staging_campaign_root,
                    "isolated_staging_path_expression": isolated_staging_expression,
                    "deployment_campaign_root_path_expression": (
                        deployment_campaign_root
                    ),
                    "deployed_runtime_path_expression": (
                        deployed_runtime_expression
                    ),
                    "deployment_copy_contract": {
                        "directory_method": "System.IO.Directory.CreateDirectory",
                        "copy_method": (
                            "System.IO.File.Copy(source, destination, false)"
                        ),
                        "source_sha256": row["aex_sha256"],
                        "staging_sha256": row["aex_sha256"],
                        "deployed_sha256": row["aex_sha256"],
                        "overwrite_allowed": False,
                        "copy_count_for_plugin": 1,
                        "row_specific_copies_forbidden": True,
                    },
                    "campaign_root_cleanup_gate": {
                        "scope_path_expression": deployment_campaign_root,
                        "inventory_all_declared_roots_before_cleanup": True,
                        "remove_only_exact_campaign_root": True,
                        "reject_reparse_points_or_scope_escape": True,
                        "require_nonexistent_or_empty_before_copy": True,
                        "require_only_expected_per_plugin_files_after_copy": True,
                        "begin_only_after_explicit_user_start": True,
                        "complete_before_ae_project_or_aerender_start": True,
                    },
                    "staging_root_cleanup_gate": {
                        "scope_path_expression": staging_campaign_root,
                        "begin_only_after_explicit_user_start": True,
                        "remove_only_exact_staging_campaign_root": True,
                        "reject_reparse_points_or_scope_escape": True,
                        "require_nonexistent_or_empty_before_copy": True,
                        "post_deployment_remove_exact_staging_campaign_root": True,
                        "post_cleanup_require_nonexistent": True,
                        "complete_before_ae_project_or_aerender_start": True,
                    },
                    "deployed_runtime_path_binding": {
                        "field": "deployed_runtime_path",
                        "expected_path_expression": deployed_runtime_expression,
                        "must_be_absolute_after_environment_expansion": True,
                        "must_be_recorded_before_project_creation": True,
                        "must_match_process_and_aex_load_evidence": True,
                    },
                    "effective_target_gate": {
                        "external_same_basename_count_before_copy": 0,
                        "external_same_effect_display_name_count_before_copy": 0,
                        "external_same_effect_match_name_count_before_copy": 0,
                        "effective_matching_basename_effect_hash_count_after_copy": 1,
                        "same_basename_other_hash_count": 0,
                        "same_effect_display_name_other_hash_count": 0,
                        "same_effect_match_name_other_hash_count": 0,
                    },
                    "sequencing_contract": [
                        "read-only verification and collision inventory before explicit user start",
                        "external staging and MediaCore campaign cleanup after explicit user start",
                        "copy and SHA-256 verification after cleanup",
                        "external staging campaign cleanup after deployment",
                        "AE project creation and aerender only after verified deployment",
                    ],
                    "request_tree_write_count": 0,
                    "evidence_observation_contract": {
                        "member": "evidence/<row_id>/process.json",
                        "data_field": "plugin_deployment",
                        "required_fields": [
                            "localappdata_path",
                            "declared_root_inventory",
                            "external_collision_counts",
                            "staging_campaign_root",
                            "staging_precleanup_inventory",
                            "staging_cleanup_performed",
                            "staging_empty_before_copy",
                            "isolated_staging_path",
                            "isolated_staging_sha256",
                            "deployment_campaign_root",
                            "deployment_precleanup_inventory",
                            "deployment_cleanup_performed",
                            "deployment_empty_before_copy",
                            "deployed_runtime_path",
                            "deployed_runtime_sha256",
                            "copy_count_for_plugin",
                            "staging_postcleanup_nonexistent",
                            "request_tree_write_count",
                            "read_only_preflight_completed_before_explicit_user_start",
                            "deployment_began_after_explicit_user_start",
                            "ae_started_after_verified_deployment_and_staging_cleanup",
                        ],
                    },
                },
            ):
                fail(f"plugin deployment contract drift: {row_id}")
        if (
            interpretation["source_identity_gate"]
            != "comp.layer(1).source.id == footage_item.id after replace"
            or not strict_equal(
                row.get("fresh_identity_contract"),
                {
                    "fresh_project": True,
                    "fresh_effect": True,
                    "fresh_nonce": True,
                    "fresh_aerender_process": True,
                    "render_queue_items": ["no_effect", "effect_on"],
                },
            )
        ):
            fail(f"fresh project/RQ identity contract drift: {row_id}")
        plugin = row.get("plugin")
        if plugin not in EXPECTED_LANE_ROWS:
            fail(f"unexpected requested plugin: {plugin!r}")
        lane_counts[plugin] = lane_counts.get(plugin, 0) + 1
        row_ids.append(row_id)
    if lane_counts != EXPECTED_LANE_ROWS:
        fail(f"request lane cardinality mismatch: {lane_counts}")
    kira_definition_path = files.get(
        "case_definitions/olmkirakira_controlled_ramps_off_matrix.json"
    )
    if kira_definition_path is None:
        fail("request lacks the materialized KiraKira controlled matrix")
    kira_definition = load_json(kira_definition_path)
    kira_cases = {
        case["case_id"]: case
        for case in kira_definition.get("cases", [])
        if isinstance(case, dict) and isinstance(case.get("case_id"), str)
    }
    pairs = kira_definition.get("pair_invariants")
    if not isinstance(pairs, list) or len(pairs) != 7:
        fail("KiraKira pair-invariant cardinality mismatch")
    for pair in pairs:
        if not isinstance(pair, dict):
            fail("KiraKira pair invariant must be an object")
        left = kira_cases.get(pair.get("left_case_id"))
        right = kira_cases.get(pair.get("right_case_id"))
        match_name = pair.get("only_different_match_name")
        if left is None or right is None or not isinstance(match_name, str):
            fail("KiraKira pair invariant has an unresolved case/match-name")
        left_writes = {
            write.get("match_name"): write.get("value")
            for write in left.get("writes", [])
            if isinstance(write, dict)
        }
        right_writes = {
            write.get("match_name"): write.get("value")
            for write in right.get("writes", [])
            if isinstance(write, dict)
        }
        differing = {
            name
            for name in set(left_writes) | set(right_writes)
            if left_writes.get(name) != right_writes.get(name)
        }
        if (
            differing != {match_name}
            or left_writes.get(match_name) != pair.get("left_value")
            or right_writes.get(match_name) != pair.get("right_value")
        ):
            fail(
                "KiraKira pair invariant is not a one-control delta: "
                f"{pair.get('pair_id')}"
            )
    if CAMPAIGN_ID == R5_CAMPAIGN_ID:
        authoritative_path = files.get(KIRA_AUTHORITATIVE_DEFINITION)
        if authoritative_path is None:
            fail("r5 request lacks the authoritative KiraKira all-30 definition")
        authoritative = load_json(authoritative_path)
        cases = authoritative.get("cases")
        if not isinstance(cases, list) or len(cases) != 10:
            fail("authoritative KiraKira definition must contain exactly ten cases")
        case_ids = [
            case.get("case_id") for case in cases if isinstance(case, dict)
        ]
        if (
            len(case_ids) != 10
            or len(set(case_ids)) != 10
            or set(case_ids) != set(KIRA_RAMP_LAYERS_BY_CASE)
        ):
            fail("authoritative KiraKira case identity set mismatch")
        authoritative_rows = [
            row for row in rows if is_kira_authoritative_row(row)
        ]
        expected_authoritative_rows = {
            (case_id, depth)
            for case_id in KIRA_RAMP_LAYERS_BY_CASE
            for depth in (8, 16, 32)
        }
        actual_authoritative_rows = {
            (row.get("case_id"), row.get("depth"))
            for row in authoritative_rows
        }
        if (
            len(authoritative_rows) != 30
            or actual_authoritative_rows != expected_authoritative_rows
        ):
            fail("authoritative KiraKira all-30 row matrix mismatch")
        for case in cases:
            if not isinstance(case, dict):
                fail("authoritative KiraKira case is not an object")
            expected_source_sha, expected_property_sha = (
                KIRA_AUTHORITATIVE_HASHES[case["case_id"]]
            )
            verify_kira_rich42_preimage(
                case,
                f"authoritative KiraKira case {case.get('case_id')}",
            )
            case_number = int(case["case_id"][-2:])
            if (
                case.get("intentional_noop") is not False
                or case.get("depths") != [8, 16, 32]
                or type(case.get("mode")) is not int
                or case["mode"] not in (1, 2, 3, 4)
                or type(case.get("merge_mode")) is not int
                or case["merge_mode"] not in (1, 2)
                or type(case.get("approximated_input")) is not int
                or case["approximated_input"] not in (0, 1)
                or (
                    case["mode"],
                    case["merge_mode"],
                    case["approximated_input"],
                )
                != KIRA_MODE_METADATA[case["case_id"]]
                or not strict_equal(
                    case.get("source"),
                    {
                        "member": (
                            f"inputs/kirakira_final_random_{case_number:02d}.exr"
                        ),
                        "sha256": expected_source_sha,
                    },
                )
                or case.get("full_42_property_readback_sha256")
                != expected_property_sha
            ):
                fail(
                    "authoritative KiraKira case mode/depth/no-op contract mismatch: "
                    f"{case.get('case_id')}"
                )
            require_sha(
                case.get("full_42_property_readback_sha256"),
                f"{case.get('case_id')}.full_42_property_readback_sha256",
            )
        capture_tool = files.get(KIRA_RICH42_CAPTURE_TOOL)
        if (
            capture_tool is None
            or sha256(capture_tool) != KIRA_RICH42_CAPTURE_TOOL_SHA256
        ):
            fail("authoritative KiraKira rich-42 capture tool binding mismatch")
        authoritative_case_by_id = {case["case_id"]: case for case in cases}
        for row in authoritative_rows:
            expected_source_sha, _ = KIRA_AUTHORITATIVE_HASHES[row["case_id"]]
            case_number = int(row["case_id"][-2:])
            verify_kira_rich42_writable_values(
                authoritative_case_by_id[row["case_id"]][
                    "full_42_property_readback_preimage"
                ],
                row["parameter_writes"],
                row["standard_options"],
                row["row_id"],
            )
            if (
                row["source_member"]
                != f"inputs/kirakira_final_random_{case_number:02d}.exr"
                or row["source_sha256"] != expected_source_sha
                or row["aex_sha256"] != KIRA_AEX_SHA256
            ):
                fail(f"authoritative KiraKira row hash/member drift: {row['row_id']}")
    return files, campaign, inventory, execution


def require_binding(
    path: Path,
    value: dict[str, Any],
    kind: str,
    row: dict[str, Any],
    batch_sha: str,
) -> dict[str, Any]:
    require_exact_keys(value, {"schema_version", "kind", "binding", "data"}, str(path))
    if not is_exact_int(value["schema_version"], 1) or value["kind"] != kind:
        fail(f"{path}: evidence schema/kind mismatch")
    binding = value["binding"]
    if not isinstance(binding, dict):
        fail(f"{path}: binding must be an object")
    expected = {
        "campaign_id": CAMPAIGN_ID,
        "row_id": row["row_id"],
        "batch_manifest_sha256": batch_sha,
        "execution_row_sha256": row["execution_row_sha256"],
        "case_contract_sha256": row["case_contract_sha256"],
    }
    if binding != expected:
        fail(f"{path}: binding mismatch")
    data = value["data"]
    if not isinstance(data, dict):
        fail(f"{path}: data must be an object")
    return data


def verify_project_data(
    data: dict[str, Any],
    row: dict[str, Any],
    label: str,
    project_relative: str,
    project_sha256: str,
) -> dict[str, Any]:
    require_exact_keys(
        data,
        {
            "expected_project_contract",
            "expected_project_contract_sha256",
            "observed_project",
            "observed_project_sha256",
        },
        label,
    )
    observed = data["observed_project"]
    if (
        not json_number_equal(
            data["expected_project_contract"],
            row["project_contract"],
        )
        or data["expected_project_contract_sha256"]
        != canonical_json_sha256(row["project_contract"])
        or not isinstance(observed, dict)
        or data["observed_project_sha256"] != canonical_json_sha256(observed)
    ):
        fail(f"{label}: expected/observed project hash mismatch")
    expected_observed_keys = {
        "project_return_member",
        "project_sha256",
        "run_nonce",
        "source",
        "comp",
        "source_layer",
        "effect",
        "render_queue_items",
    }
    if CAMPAIGN_ID == R5_CAMPAIGN_ID:
        expected_observed_keys.add("project_item_inventory")
    require_exact_keys(
        observed,
        expected_observed_keys,
        f"{label}.observed_project",
    )
    source = observed["source"]
    comp = observed["comp"]
    source_layer = observed["source_layer"]
    effect = observed["effect"]
    render_queue = observed["render_queue_items"]
    if not all(
        isinstance(item, dict)
        for item in (source, comp, source_layer, effect, render_queue)
    ):
        fail(f"{label}: observed project subrecord is not an object")
    require_exact_keys(
        source,
        {
            "member",
            "runtime_path",
            "sha256",
            "footage_item_name",
            "footage_item_id",
            "preserve_rgb",
            "alpha_mode",
            "premultiplied",
        },
        f"{label}.source",
    )
    require_exact_keys(
        comp,
        {"item_name", "item_id", "contract", "num_layers"},
        f"{label}.comp",
    )
    expected_source_layer_keys = {
        "index",
        "source_item_id",
        "scale",
        "centered",
        "effect_parade_count_before_add",
        "effect_parade_count_after_add",
    }
    if CAMPAIGN_ID == R5_CAMPAIGN_ID:
        expected_source_layer_keys.update(
            {"startTime", "inPoint", "outPoint", "stretch", "timeRemapEnabled"}
        )
    require_exact_keys(
        source_layer,
        expected_source_layer_keys,
        f"{label}.source_layer",
    )
    require_exact_keys(
        effect,
        {"display_name", "match_name", "property_index"},
        f"{label}.effect",
    )
    if set(render_queue) != {"no_effect", "effect_on"}:
        fail(f"{label}: render-queue branch set mismatch")
    material_settings_sha256_by_branch: dict[str, str] = {}
    for branch, enabled, output_member, effects_modes, queue_index in (
        (
            "no_effect",
            False,
            f"outputs/{row['row_id']}/no_effect.exr",
            {"all off"},
            1,
        ),
        (
            "effect_on",
            True,
            f"outputs/{row['row_id']}/effect_on.exr",
            {"all on", "current settings"},
            2,
        ),
    ):
        record = render_queue[branch]
        if not isinstance(record, dict):
            fail(f"{label}: {branch} render-queue record is not an object")
        expected_rq_keys = {
            "id",
            "queue_index",
            "comp_item_id",
            "effect_enabled",
            "output_member",
            "output_runtime_path",
            "output_module_index",
            "render_settings_capture_method",
            "render_settings_serialization",
            "render_settings_serialization_sha256",
        }
        if CAMPAIGN_ID == R5_CAMPAIGN_ID:
            expected_rq_keys.update({"timeSpanStart", "timeSpanDuration"})
        require_exact_keys(
            record,
            expected_rq_keys,
            f"{label}.{branch}",
        )
        render_settings = parse_render_settings_serialization(
            record["render_settings_serialization"],
            f"{label}.{branch}.render_settings",
            row["depth"],
        )
        material_settings_sha256_by_branch[branch] = render_settings[
            "material_settings_sha256"
        ]
        if (
            record["id"] != f"{observed['run_nonce']}:rq:{queue_index}"
            or not is_exact_int(record["queue_index"], queue_index)
            or record["comp_item_id"] != comp["item_id"]
            or record["effect_enabled"] is not enabled
            or record["output_member"] != output_member
            or not isinstance(record["output_runtime_path"], str)
            or re.match(
                r"^(?:[A-Za-z]:[\\/]|\\\\)",
                record["output_runtime_path"],
            )
            is None
            or not is_exact_int(record["output_module_index"], 1)
            or record["render_settings_capture_method"]
            != "RenderQueueItem.getSettings(GetSettingsFormat.STRING)"
            or render_settings["effects_mode"] not in effects_modes
            or record["render_settings_serialization_sha256"]
            != hashlib.sha256(
                record["render_settings_serialization"].encode("utf-8")
            ).hexdigest()
            or CAMPAIGN_ID == R5_CAMPAIGN_ID
            and (
                type(record["timeSpanStart"]) is not float
                or record["timeSpanStart"]
                != row["comp"]["render_time_span_start_seconds"]
                or type(record["timeSpanDuration"]) is not float
                or record["timeSpanDuration"]
                != row["comp"]["render_time_span_duration_seconds"]
            )
        ):
            fail(f"{label}: {branch} render-queue observation mismatch")
    if (
        material_settings_sha256_by_branch["no_effect"]
        != material_settings_sha256_by_branch["effect_on"]
    ):
        fail(f"{label}: RQ material settings differ beyond Effects mode")
    interpretation = row["project_contract"]["input_interpretation"]
    if CAMPAIGN_ID == R5_CAMPAIGN_ID:
        project_items = observed["project_item_inventory"]
        if (
            not isinstance(project_items, list)
            or len(project_items) != 2
            or any(not isinstance(item, dict) for item in project_items)
        ):
            fail(f"{label}: project item inventory must contain exactly two items")
        for item in project_items:
            require_exact_keys(
                item,
                {"name", "item_type", "item_id"},
                f"{label}.project_item_inventory",
            )
        expected_project_items = [
            {
                "name": interpretation["footage_item_name"],
                "item_type": "FootageItem",
                "item_id": source["footage_item_id"],
            },
            {
                "name": interpretation["comp_item_name"],
                "item_type": "CompItem",
                "item_id": comp["item_id"],
            },
        ]
        if not strict_equal(project_items, expected_project_items):
            fail(f"{label}: named project item type/cardinality mismatch")
    if (
        observed["project_return_member"] != project_relative
        or observed["project_sha256"] != project_sha256
        or not isinstance(observed["run_nonce"], str)
        or not observed["run_nonce"]
        or source["member"] != row["source_member"]
        or not isinstance(source["runtime_path"], str)
        or re.match(r"^(?:[A-Za-z]:[\\/]|\\\\)", source["runtime_path"])
        is None
        or source["runtime_path"].replace("\\", "/").rsplit("/", 1)[-1]
        != str(row["source_member"]).rsplit("/", 1)[-1]
        or source["sha256"] != row["source_sha256"]
        or source["footage_item_name"] != interpretation["footage_item_name"]
        or type(source["footage_item_id"]) is not int
        or source["footage_item_id"] <= 0
        or source["preserve_rgb"] is not True
        or source["alpha_mode"] != "straight"
        or source["premultiplied"] is not False
        or comp["item_name"] != interpretation["comp_item_name"]
        or type(comp["item_id"]) is not int
        or comp["item_id"] <= 0
        or not json_number_equal(comp["contract"], row["comp"])
        or type(comp["num_layers"]) is not int
        or comp["num_layers"] != 1
        or type(source_layer["index"]) is not int
        or source_layer["index"] != 1
        or source_layer["source_item_id"] != source["footage_item_id"]
        or not json_number_equal(
            source_layer["scale"],
            row["comp"]["source_layer_scale"],
        )
        or source_layer["centered"] is not True
        or type(source_layer["effect_parade_count_before_add"]) is not int
        or source_layer["effect_parade_count_before_add"] != 0
        or type(source_layer["effect_parade_count_after_add"]) is not int
        or source_layer["effect_parade_count_after_add"] != 1
        or CAMPAIGN_ID == R5_CAMPAIGN_ID
        and not strict_equal(
            {
                "startTime": source_layer["startTime"],
                "inPoint": source_layer["inPoint"],
                "outPoint": source_layer["outPoint"],
                "stretch": source_layer["stretch"],
                "timeRemapEnabled": source_layer["timeRemapEnabled"],
            },
            row["comp"]["source_layer_timing"],
        )
        or not strict_equal(
            {
                "display_name": effect["display_name"],
                "match_name": effect["match_name"],
            },
            row["effect"],
        )
        or type(effect["property_index"]) is not int
        or effect["property_index"] != 1
        or render_queue["no_effect"]["id"] == render_queue["effect_on"]["id"]
    ):
        fail(f"{label}: live project/source/effect observation mismatch")
    return observed


def normalized_setting_text(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


def parse_render_settings_serialization(
    serialization: object,
    label: str,
    expected_depth: int,
) -> dict[str, str]:
    if not isinstance(serialization, str) or not serialization:
        fail(f"{label}: render-settings serialization is empty")
    try:
        captured = json.loads(
            serialization,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_json_constant,
        )
    except json.JSONDecodeError as exc:
        fail(f"{label}: render-settings serialization is invalid JSON: {exc}")
    if not isinstance(captured, dict):
        fail(f"{label}: render-settings serialization is not an object")
    require_exact_keys(
        captured,
        {
            "get_settings_format",
            "path_dependent_fields_excluded",
            "raw_settings",
        },
        label,
    )
    raw_settings = captured["raw_settings"]
    if not isinstance(raw_settings, dict) or not raw_settings:
        fail(f"{label}: render settings are empty")
    effects_values: list[object] = []
    color_depth_values: list[object] = []
    stack: list[object] = [raw_settings]
    node_count = 0
    while stack:
        item = stack.pop()
        node_count += 1
        if node_count > 100_000:
            fail(f"{label}: render-settings structural limit exceeded")
        if isinstance(item, dict):
            for key, value in item.items():
                if str(key).casefold() == "effects":
                    effects_values.append(value)
                if str(key).casefold() == "color depth":
                    color_depth_values.append(value)
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    if (
        serialization
        != json.dumps(
            captured,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        or captured["get_settings_format"] != "STRING"
        or captured["path_dependent_fields_excluded"] is not True
        or len(effects_values) != 1
        or len(color_depth_values) != 1
        or not isinstance(effects_values[0], str)
        or not isinstance(color_depth_values[0], str)
    ):
        fail(f"{label}: render-settings normalization contract mismatch")
    exact_effects_modes = {
        "All Off": "all off",
        "All On": "all on",
        "Current Settings": "current settings",
    }
    if effects_values[0] not in exact_effects_modes:
        fail(f"{label}: unsupported Effects render setting")
    effects_mode = exact_effects_modes[effects_values[0]]
    color_depth = normalized_setting_text(color_depth_values[0])
    allowed_depth_values = {
        8: {
            "current settings",
            "8 bit",
            "8 bits per channel",
            "8 bpc",
        },
        16: {
            "current settings",
            "16 bit",
            "16 bits per channel",
            "16 bpc",
        },
        32: {
            "current settings",
            "32 bit",
            "32 bits per channel",
            "32 bpc",
        },
    }
    if color_depth not in allowed_depth_values.get(expected_depth, set()):
        fail(f"{label}: Color Depth does not match the row depth")

    def normalize_effects(item: object) -> object:
        if isinstance(item, dict):
            return {
                key: (
                    "__EFFECTS_MODE__"
                    if str(key).casefold() == "effects"
                    else normalize_effects(value)
                )
                for key, value in item.items()
            }
        if isinstance(item, list):
            return [normalize_effects(value) for value in item]
        return item

    material_settings_sha256 = canonical_json_sha256(
        normalize_effects(captured)
    )
    return {
        "effects_mode": effects_mode,
        "color_depth": color_depth,
        "material_settings_sha256": material_settings_sha256,
    }


def setting_value_matches(
    key: str,
    value: str,
    required_tokens: tuple[str, ...],
) -> bool:
    normalized = normalized_setting_text(value)
    requirement = (key.casefold(), tuple(token.casefold() for token in required_tokens))
    allowed: dict[tuple[str, tuple[str, ...]], set[str]] = {
        ("format", ("openexr",)): {
            "openexr",
            "open exr",
            "openexr sequence",
            "open exr sequence",
        },
        ("format", ("png",)): {"png", "png sequence"},
        ("channels", ("rgb", "alpha")): {
            "rgb alpha",
            "rgb a",
            "rgb plus alpha",
        },
        ("depth", ("float",)): {
            "float",
            "floating point",
            "32 bit float",
            "32 bpc float",
        },
        ("depth", ("million",)): {
            "million colors",
            "million colors plus",
            "millions of colors",
            "millions of colors plus",
        },
        ("color", ("straight",)): {
            "straight",
            "straight alpha",
            "straight unmatted",
            "unmatted",
        },
        ("compression", ("none",)): {
            "none",
            "no compression",
            "uncompressed",
        },
    }
    return normalized in allowed.get(requirement, set())


def parse_settings_serialization(
    serialization: object,
    label: str,
    required_settings: dict[str, tuple[str, ...]],
    optional_settings: dict[str, tuple[str, ...]] | None = None,
) -> dict[str, Any]:
    if not isinstance(serialization, str) or not serialization:
        fail(f"{label}: settings serialization is empty")
    try:
        serialized_settings = json.loads(
            serialization,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_json_constant,
        )
    except json.JSONDecodeError as exc:
        fail(f"{label}: settings serialization is invalid JSON: {exc}")
    if not isinstance(serialized_settings, dict):
        fail(f"{label}: settings serialization is not an object")
    require_exact_keys(
        serialized_settings,
        {
            "get_settings_format",
            "path_dependent_fields_excluded",
            "raw_settings",
        },
        label,
    )
    raw_settings = serialized_settings["raw_settings"]
    if not isinstance(raw_settings, dict) or not raw_settings:
        fail(f"{label}: raw settings are empty")
    optional_settings = optional_settings or {}
    all_settings = {**required_settings, **optional_settings}
    setting_values: dict[str, list[object]] = {
        key.casefold(): [] for key in all_settings
    }
    stack = [raw_settings]
    node_count = 0
    while stack:
        item = stack.pop()
        node_count += 1
        if node_count > 100_000:
            fail(f"{label}: settings structural limit exceeded")
        if isinstance(item, dict):
            for key, value in item.items():
                folded_key = str(key).casefold()
                if folded_key in setting_values:
                    setting_values[folded_key].append(value)
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    if (
        serialization
        != json.dumps(
            serialized_settings,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        or serialized_settings["get_settings_format"] != "STRING"
        or serialized_settings["path_dependent_fields_excluded"] is not True
        or any(
            len(values) != 1
            or not isinstance(values[0], str)
            or not setting_value_matches(key, values[0], tokens)
            for key, tokens in required_settings.items()
            for values in (setting_values[key.casefold()],)
        )
        or any(
            len(values) > 1
            or (
                len(values) == 1
                and (
                    not isinstance(values[0], str)
                    or not setting_value_matches(key, values[0], tokens)
                )
            )
            for key, tokens in optional_settings.items()
            for values in (setting_values[key.casefold()],)
        )
    ):
        fail(f"{label}: settings normalization/value contract mismatch")
    return serialized_settings


def verify_output_module_data(
    data: dict[str, Any],
    row: dict[str, Any],
    label: str,
) -> dict[str, Any]:
    require_exact_keys(data, {"branches"}, label)
    branches = data["branches"]
    if not isinstance(branches, dict) or set(branches) != {"no_effect", "effect_on"}:
        fail(f"{label}: output-module branch set mismatch")
    serializations: list[str] = []
    for branch in ("no_effect", "effect_on"):
        record = branches[branch]
        if not isinstance(record, dict):
            fail(f"{label}: {branch} output-module record is not an object")
        require_exact_keys(
            record,
            {
                "render_queue_item_id",
                "output_module_index",
                "output_member",
                "normalized_output_contract",
                "settings_serialization",
                "settings_serialization_sha256",
            },
            f"{label}.{branch}",
        )
        serialization = record["settings_serialization"]
        parse_settings_serialization(
            serialization,
            f"{label}.{branch}.settings_serialization",
            {
                "Format": ("openexr",),
                "Channels": ("rgb", "alpha"),
                "Depth": ("float",),
                "Color": ("straight",),
            },
            {"Compression": ("none",)},
        )
        if (
            not isinstance(record["render_queue_item_id"], str)
            or not record["render_queue_item_id"]
            or type(record["output_module_index"]) is not int
            or record["output_module_index"] != 1
            or record["output_member"]
            != f"outputs/{row['row_id']}/{branch}.exr"
            or not strict_equal(
                record["normalized_output_contract"],
                row["project_contract"]["primary_output"],
            )
            or row["row_id"].casefold() in serialization.casefold()
            or record["settings_serialization_sha256"]
            != hashlib.sha256(serialization.encode("utf-8")).hexdigest()
        ):
            fail(f"{label}: {branch} output-module binding mismatch")
        serializations.append(serialization)
    if (
        branches["no_effect"]["render_queue_item_id"]
        == branches["effect_on"]["render_queue_item_id"]
        or serializations[0] != serializations[1]
    ):
        fail(f"{label}: output-module branches are not identical/fresh")
    return branches


def verify_parameter_snapshot(
    actual: object,
    expected: dict[str, Any],
    label: str,
) -> None:
    if not isinstance(actual, dict):
        fail(f"{label}: parameter snapshot is not an object")
    require_exact_keys(
        actual,
        {"parameter_actions", "standard_options"},
        label,
    )
    if not strict_equal(actual["standard_options"], expected["standard_options"]):
        fail(f"{label}: standard compositing options differ")
    actual_actions = actual["parameter_actions"]
    expected_actions = expected["parameter_actions"]
    if (
        not isinstance(actual_actions, list)
        or len(actual_actions) != len(expected_actions)
    ):
        fail(f"{label}: parameter-action cardinality mismatch")
    for index, (actual_action, expected_action) in enumerate(
        zip(actual_actions, expected_actions, strict=True)
    ):
        if (
            not isinstance(actual_action, dict)
            or set(actual_action) != set(expected_action)
        ):
            fail(f"{label}: parameter-action shape mismatch at {index}")
        comparison_mode = expected_action["comparison_mode"]
        ignored = {"value"}
        if comparison_mode.startswith("float32_u32_"):
            ignored.add("value_raw_f32_u32")
            if expected_action["action"] == "verify_fresh_default":
                ignored.add("expected_fresh_default")
        actual_metadata = {
            key: value for key, value in actual_action.items() if key not in ignored
        }
        expected_metadata = {
            key: value
            for key, value in expected_action.items()
            if key not in ignored
        }
        if not strict_equal(actual_metadata, expected_metadata):
            fail(f"{label}: parameter-action metadata mismatch at {index}")
        if comparison_mode.startswith("float32_u32_"):
            _, actual_words = float32_value_and_u32(
                actual_action["value"],
                f"{label}.action[{index}].value",
            )
            if (
                not strict_equal(
                    actual_action["value_raw_f32_u32"],
                    expected_action["value_raw_f32_u32"],
                )
                or not strict_equal(
                    actual_words,
                    expected_action["value_raw_f32_u32"],
                )
            ):
                fail(f"{label}: float32 readback mismatch at {index}")
            if expected_action["action"] == "verify_fresh_default":
                _, actual_default_words = float32_value_and_u32(
                    actual_action["expected_fresh_default"],
                    f"{label}.action[{index}].expected_fresh_default",
                )
                if not strict_equal(
                    actual_default_words,
                    expected_action["value_raw_f32_u32"],
                ):
                    fail(f"{label}: float32 fresh default mismatch at {index}")
        elif (
            comparison_mode != "exact_integer"
            or type(actual_action["value"]) is not int
            or not strict_equal(actual_action["value"], expected_action["value"])
        ):
            fail(f"{label}: exact integer readback mismatch at {index}")


def parameter_action_values_equal(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    if left.get("comparison_mode") != right.get("comparison_mode"):
        return False
    if str(left.get("comparison_mode", "")).startswith("float32_u32_"):
        return strict_equal(
            left.get("value_raw_f32_u32"),
            right.get("value_raw_f32_u32"),
        )
    return strict_equal(left.get("value"), right.get("value"))


def trace_control_value_matches(
    value: object,
    action: dict[str, Any],
    label: str,
) -> bool:
    if str(action.get("comparison_mode", "")).startswith("float32_u32_"):
        return strict_equal(
            float32_words(value, label),
            action.get("value_raw_f32_u32"),
        )
    return type(value) is int and strict_equal(value, action.get("value"))


def verify_plugin_deployment(
    deployment: object,
    row: dict[str, Any],
    label: str,
) -> str:
    if not isinstance(deployment, dict):
        fail(f"{label}: plugin_deployment must be an object")
    require_exact_keys(
        deployment,
        {
            "localappdata_path",
            "declared_root_inventory",
            "external_collision_counts",
            "staging_campaign_root",
            "staging_precleanup_inventory",
            "staging_cleanup_performed",
            "staging_empty_before_copy",
            "isolated_staging_path",
            "isolated_staging_sha256",
            "deployment_campaign_root",
            "deployment_precleanup_inventory",
            "deployment_cleanup_performed",
            "deployment_empty_before_copy",
            "deployed_runtime_path",
            "deployed_runtime_sha256",
            "copy_count_for_plugin",
            "staging_postcleanup_nonexistent",
            "request_tree_write_count",
            "read_only_preflight_completed_before_explicit_user_start",
            "deployment_began_after_explicit_user_start",
            "ae_started_after_verified_deployment_and_staging_cleanup",
        },
        f"{label}.plugin_deployment",
    )
    inventory = deployment["declared_root_inventory"]
    root_ids = row["plugin_deployment_contract"][
        "declared_ae_26_3_plugin_root_ids"
    ]
    if (
        not isinstance(inventory, list)
        or len(inventory) < len(root_ids)
        or any(not isinstance(record, dict) for record in inventory)
    ):
        fail(f"{label}: declared-root inventory cardinality mismatch")
    observed_root_ids = [record.get("root_id") for record in inventory]
    if set(observed_root_ids) != set(root_ids):
        fail(f"{label}: declared-root inventory coverage mismatch")
    target = row["plugin_deployment_contract"]["target"]
    external_basename = 0
    external_display = 0
    external_match = 0
    for index, record in enumerate(inventory):
        require_exact_keys(
            record,
            {
                "root_id",
                "declared_path_expression",
                "resolved_absolute_path",
                "exists",
                "aex_basename",
                "aex_absolute_path",
                "sha256",
                "effect_display_name",
                "effect_match_name",
            },
            f"{label}.plugin_deployment.declared_root_inventory[{index}]",
        )
        if (
            record["root_id"] not in root_ids
            or not isinstance(record["declared_path_expression"], str)
            or not record["declared_path_expression"]
            or not isinstance(record["resolved_absolute_path"], str)
            or re.match(
                r"^(?:[A-Za-z]:[\\/]|\\\\)", record["resolved_absolute_path"]
            )
            is None
            or type(record["exists"]) is not bool
        ):
            fail(f"{label}: malformed declared-root inventory row {index}")
        candidate_fields = (
            "aex_basename",
            "aex_absolute_path",
            "sha256",
            "effect_display_name",
            "effect_match_name",
        )
        values = [record[field] for field in candidate_fields]
        if all(value is None for value in values):
            continue
        if (
            any(not isinstance(value, str) or not value for value in values)
            or re.match(r"^(?:[A-Za-z]:[\\/]|\\\\)", record["aex_absolute_path"])
            is None
        ):
            fail(f"{label}: partial/malformed AEX inventory candidate {index}")
        require_sha(record["sha256"], f"{label}.plugin_deployment.inventory[{index}]")
        same_basename = record["aex_basename"].casefold() == target[
            "aex_basename"
        ].casefold()
        same_display = record["effect_display_name"] == target["effect_display_name"]
        same_match = record["effect_match_name"] == target["effect_match_name"]
        external_basename += int(same_basename)
        external_display += int(same_display)
        external_match += int(same_match)
    collision_counts = deployment["external_collision_counts"]
    expected_gate = row["plugin_deployment_contract"]["effective_target_gate"]
    if not isinstance(collision_counts, dict):
        fail(f"{label}: external_collision_counts must be an object")
    require_exact_keys(
        collision_counts,
        set(expected_gate),
        f"{label}.plugin_deployment.external_collision_counts",
    )
    for field, observed in (
        ("external_same_basename_count_before_copy", external_basename),
        ("external_same_effect_display_name_count_before_copy", external_display),
        ("external_same_effect_match_name_count_before_copy", external_match),
    ):
        if not is_exact_int(collision_counts[field], observed) or observed != 0:
            fail(f"{label}: external pre-copy collision gate failed: {field}")
    precleanup = deployment["deployment_precleanup_inventory"]
    if not isinstance(precleanup, list):
        fail(f"{label}: precleanup campaign-root inventory must be an array")
    for index, record in enumerate(precleanup):
        if not isinstance(record, dict):
            fail(f"{label}: malformed precleanup inventory row {index}")
        require_exact_keys(
            record,
            {"absolute_path", "sha256", "is_reparse_point"},
            f"{label}.plugin_deployment.precleanup[{index}]",
        )
        if (
            not isinstance(record["absolute_path"], str)
            or re.match(r"^(?:[A-Za-z]:[\\/]|\\\\)", record["absolute_path"])
            is None
            or record["is_reparse_point"] is not False
        ):
            fail(f"{label}: unsafe precleanup campaign-root member")
        require_sha(record["sha256"], f"{label}.plugin_deployment.precleanup[{index}]")
    staging_precleanup = deployment["staging_precleanup_inventory"]
    if not isinstance(staging_precleanup, list):
        fail(f"{label}: staging_precleanup_inventory must be an array")
    for index, record in enumerate(staging_precleanup):
        if not isinstance(record, dict):
            fail(f"{label}: malformed staging precleanup row {index}")
        require_exact_keys(
            record,
            {"absolute_path", "sha256", "is_reparse_point"},
            f"{label}.plugin_deployment.staging_precleanup[{index}]",
        )
        if (
            not isinstance(record["absolute_path"], str)
            or re.match(r"^(?:[A-Za-z]:[\/]|\\\\)", record["absolute_path"])
            is None
            or record["is_reparse_point"] is not False
        ):
            fail(f"{label}: unsafe staging precleanup member")
        require_sha(
            record["sha256"],
            f"{label}.plugin_deployment.staging_precleanup[{index}]",
        )
    if (
        deployment["deployment_cleanup_performed"] is not True
        or deployment["deployment_empty_before_copy"] is not True
        or deployment["staging_cleanup_performed"] is not True
        or deployment["staging_empty_before_copy"] is not True
        or deployment["staging_postcleanup_nonexistent"] is not True
        or not is_exact_int(deployment["request_tree_write_count"], 0)
        or deployment["read_only_preflight_completed_before_explicit_user_start"]
        is not True
        or deployment["deployment_began_after_explicit_user_start"] is not True
        or deployment[
            "ae_started_after_verified_deployment_and_staging_cleanup"
        ]
        is not True
    ):
        fail(f"{label}: cleanup/sequencing/request-read-only gate failed")
    staging_path = deployment["isolated_staging_path"]
    deployed_path = deployment["deployed_runtime_path"]
    localappdata_path = deployment["localappdata_path"]
    staging_root = deployment["staging_campaign_root"]
    deployment_root = deployment["deployment_campaign_root"]
    for field, value in (
        ("isolated_staging_path", staging_path),
        ("deployed_runtime_path", deployed_path),
        ("localappdata_path", localappdata_path),
        ("staging_campaign_root", staging_root),
        ("deployment_campaign_root", deployment_root),
    ):
        if (
            not isinstance(value, str)
            or re.match(r"^(?:[A-Za-z]:[\\/]|\\\\)", value) is None
        ):
            fail(f"{label}: {field} must be an absolute Windows path")
    if (
        staging_root
        != ntpath.join(
            localappdata_path,
            "OLM_Codex_Staging",
            CAMPAIGN_ID,
        )
        or staging_path
        != ntpath.join(staging_root, row["plugin"], target["aex_basename"])
        or not deployment_root.replace("\\", "/").casefold().endswith(
            (
                "/adobe/common/plug-ins/7.0/mediacore/"
                f"olm_codex_isolated/{CAMPAIGN_ID}"
            ).casefold()
        )
        or deployed_path
        != ntpath.join(deployment_root, row["plugin"], target["aex_basename"])
        or deployment["isolated_staging_sha256"] != target["sha256"]
        or deployment["deployed_runtime_sha256"] != target["sha256"]
        or not is_exact_int(deployment["copy_count_for_plugin"], 1)
    ):
        fail(f"{label}: isolated plugin deployment path binding mismatch")
    if not strict_equal(collision_counts, expected_gate):
        fail(f"{label}: effective deployed target/collision counts mismatch")
    return deployed_path


def verify_process_data(data: dict[str, Any], row: dict[str, Any], label: str) -> None:
    required = {
        "ae_version",
        "renderer",
        "renderer_raw",
        "working_space_normalized",
        "working_space_raw",
        "bits_per_channel",
        "comp",
        "source_member",
        "source_runtime_path",
        "source_sha256",
        "loaded_aex_member",
        "loaded_aex_sha256",
        "aerender",
        "real_afterfx_child",
        "module",
        "run_nonce",
        "project",
        "outputs",
        "diagnostic_outputs",
        "logs",
        "etw_export",
        "process_start_unix_ns",
        "process_end_unix_ns",
    }
    if CAMPAIGN_ID == R5_CAMPAIGN_ID:
        required.add("plugin_deployment")
    require_exact_keys(data, required, f"{label}.process")
    if (
        data["ae_version"] != "26.3x87"
        or data["renderer"] != "SOFTWARE"
        or data["renderer_raw"] != 1816
        or data["working_space_normalized"] is not None
        or data["working_space_raw"] not in (None, "")
        or data["bits_per_channel"] != row["depth"]
        or not json_number_equal(data["comp"], row["comp"])
        or data["source_member"] != row["source_member"]
        or not isinstance(data["source_runtime_path"], str)
        or re.match(r"^(?:[A-Za-z]:[\\/]|\\\\)", data["source_runtime_path"])
        is None
        or data["source_runtime_path"].replace("\\", "/").rsplit("/", 1)[-1]
        != str(row["source_member"]).rsplit("/", 1)[-1]
        or data["source_sha256"] != row["source_sha256"]
        or data["loaded_aex_member"] != row["aex_member"]
        or data["loaded_aex_sha256"] != row["aex_sha256"]
    ):
        fail(f"{label}: process/project/source/AEX contract mismatch")
    if not isinstance(data["run_nonce"], str) or not data["run_nonce"]:
        fail(f"{label}: run_nonce missing")
    aerender = data["aerender"]
    child = data["real_afterfx_child"]
    module = data["module"]
    deployed_runtime_path = None
    if CAMPAIGN_ID == R5_CAMPAIGN_ID:
        deployed_runtime_path = verify_plugin_deployment(
            data["plugin_deployment"], row, label
        )
    project = data["project"]
    outputs = data["outputs"]
    diagnostic_outputs = data["diagnostic_outputs"]
    logs = data["logs"]
    etw_export = data["etw_export"]
    if not all(
        isinstance(item, dict)
        for item in (
            aerender,
            child,
            module,
            project,
            outputs,
            diagnostic_outputs,
            logs,
            etw_export,
        )
    ):
        fail(f"{label}: process subrecords must be objects")
    for record, fields, record_label in (
        (
            aerender,
            {
                "path",
                "sha256",
                "version",
                "pid",
                "start_time_utc",
                "command",
                "command_argv",
            },
            "aerender",
        ),
        (
            child,
            {
                "pid",
                "parent_pid",
                "mapping_method",
                "path",
                "sha256",
                "start_time_utc",
                "stop_time_utc",
            },
            "real_afterfx_child",
        ),
        (
            module,
            {"path", "sha256", "pid", "load_time_utc", "unload_time_utc"},
            "module",
        ),
    ):
        require_exact_keys(record, fields, f"{label}.{record_label}")
    require_sha(aerender["sha256"], f"{label}.aerender.sha256")
    for field in ("path", "version", "start_time_utc", "command"):
        if not isinstance(aerender[field], str) or not aerender[field]:
            fail(f"{label}: aerender {field} missing")
    command_argv = aerender["command_argv"]
    if (
        not isinstance(command_argv, list)
        or not command_argv
        or any(not isinstance(argument, str) or not argument for argument in command_argv)
    ):
        fail(f"{label}: aerender command_argv invalid")
    if module["sha256"] != row["aex_sha256"]:
        fail(f"{label}: module SHA-256 mismatch")
    if (
        type(aerender["pid"]) is not int
        or aerender["pid"] <= 0
        or str(aerender["path"]).replace("\\", "/").rsplit("/", 1)[-1].lower()
        != "aerender.exe"
        or re.match(r"^(?:[A-Za-z]:[\\/]|\\\\)", aerender["path"]) is None
    ):
        fail(f"{label}: aerender PID invalid")
    if (
        type(child["pid"]) is not int
        or child["pid"] <= 0
        or not isinstance(child["mapping_method"], str)
        or not child["mapping_method"]
        or not isinstance(child["path"], str)
        or re.match(r"^(?:[A-Za-z]:[\\/]|\\\\)", child["path"]) is None
        or child["path"].replace("\\", "/").rsplit("/", 1)[-1].lower()
        != "afterfx.exe"
        or not isinstance(child["start_time_utc"], str)
        or not child["start_time_utc"]
        or not isinstance(child["stop_time_utc"], str)
        or not child["stop_time_utc"]
    ):
        fail(f"{label}: child PID invalid")
    require_sha(child["sha256"], f"{label}.real_afterfx_child.sha256")
    if (
        module.get("pid") != child["pid"]
        or str(module.get("path", "")).replace("\\", "/").rsplit("/", 1)[-1]
        != str(row["aex_member"]).rsplit("/", 1)[-1]
        or re.match(r"^(?:[A-Za-z]:[\\/]|\\\\)", str(module.get("path", "")))
        is None
        or not isinstance(module.get("load_time_utc"), str)
        or not module["load_time_utc"]
        or not isinstance(module.get("unload_time_utc"), str)
        or not module["unload_time_utc"]
        or CAMPAIGN_ID == R5_CAMPAIGN_ID
        and module.get("path") != deployed_runtime_path
    ):
        fail(f"{label}: loaded module is not bound to the real AfterFX child")
    if child.get("parent_pid") != aerender["pid"]:
        fail(f"{label}: real AfterFX child is not bound to aerender PID")
    aerender_start = parse_utc_timestamp(
        aerender["start_time_utc"],
        f"{label}.aerender.start_time_utc",
    )
    child_start = parse_utc_timestamp(
        child["start_time_utc"],
        f"{label}.real_afterfx_child.start_time_utc",
    )
    module_load = parse_utc_timestamp(
        module["load_time_utc"],
        f"{label}.module.load_time_utc",
    )
    module_unload = parse_utc_timestamp(
        module["unload_time_utc"],
        f"{label}.module.unload_time_utc",
    )
    child_stop = parse_utc_timestamp(
        child["stop_time_utc"],
        f"{label}.real_afterfx_child.stop_time_utc",
    )
    if not (
        aerender_start <= child_start <= module_load < module_unload <= child_stop
    ):
        fail(f"{label}: process/module UTC event ordering mismatch")
    start_ns = data["process_start_unix_ns"]
    end_ns = data["process_end_unix_ns"]
    if (
        type(start_ns) is not int
        or type(end_ns) is not int
        or start_ns <= 0
        or end_ns <= start_ns
    ):
        fail(f"{label}: process time barrier invalid")
    event_ns = [
        int(event.timestamp() * 1_000_000_000)
        for event in (
            aerender_start,
            child_start,
            module_load,
            module_unload,
            child_stop,
        )
    ]
    if not start_ns <= event_ns[0] <= event_ns[-1] <= end_ns:
        fail(f"{label}: Unix-ns barrier is disconnected from UTC ETW events")
    if set(project) != {"return_path", "runtime_path", "sha256"}:
        fail(f"{label}: project process record shape mismatch")
    require_sha(project.get("sha256"), f"{label}.project.sha256")
    if (
        project["return_path"] != f"projects/{row['row_id']}.aep"
        or not isinstance(project["runtime_path"], str)
        or not project["runtime_path"]
        or re.match(r"^(?:[A-Za-z]:[\\/]|\\\\)", project["runtime_path"])
        is None
        or project["runtime_path"] not in command_argv
        or project["runtime_path"] not in aerender["command"]
        or not any(
            argument.lower() == "-project"
            and index + 1 < len(command_argv)
            and command_argv[index + 1] == project["runtime_path"]
            for index, argument in enumerate(command_argv)
        )
    ):
        fail(f"{label}: aerender command is not bound to the runtime project")
    if set(outputs) != {"no_effect", "effect_on"}:
        fail(f"{label}: output process record shape mismatch")
    required_output_fields = {
        "return_path",
        "runtime_path",
        "sha256",
        "preexisting",
        "finalized",
        "mtime_unix_ns",
        "render_duration_ms",
        "render_start_unix_ns",
        "render_end_unix_ns",
        "render_queue_item_id",
    }
    for branch in ("no_effect", "effect_on"):
        record = outputs[branch]
        if not isinstance(record, dict) or set(record) != required_output_fields:
            fail(f"{label}: {branch} output process record shape mismatch")
        if (
            record["return_path"] != f"outputs/{row['row_id']}/{branch}.exr"
            or not isinstance(record["runtime_path"], str)
            or not record["runtime_path"]
            or re.match(r"^(?:[A-Za-z]:[\\/]|\\\\)", record["runtime_path"])
            is None
            or record["preexisting"] is not False
            or record["finalized"] is not True
            or type(record["mtime_unix_ns"]) is not int
            or type(record["render_start_unix_ns"]) is not int
            or type(record["render_end_unix_ns"]) is not int
            or not (
                event_ns[2]
                <= record["render_start_unix_ns"]
                <= record["mtime_unix_ns"]
                <= record["render_end_unix_ns"]
                <= event_ns[3]
            )
            or record["render_start_unix_ns"] >= record["render_end_unix_ns"]
            or type(record["render_duration_ms"]) is not int
            or record["render_duration_ms"] <= 0
            or record["render_duration_ms"]
            != max(
                1,
                (
                    record["render_end_unix_ns"]
                    - record["render_start_unix_ns"]
                    + 999_999
                )
                // 1_000_000,
            )
            or not isinstance(record["render_queue_item_id"], str)
            or not record["render_queue_item_id"]
        ):
            fail(f"{label}: {branch} cache/output barrier invalid")
        require_sha(record["sha256"], f"{label}.{branch}.sha256")
    if (
        outputs["no_effect"]["render_queue_item_id"]
        == outputs["effect_on"]["render_queue_item_id"]
        or windows_runtime_path_key(outputs["no_effect"]["runtime_path"])
        == windows_runtime_path_key(outputs["effect_on"]["runtime_path"])
        or outputs["no_effect"]["render_end_unix_ns"]
        > outputs["effect_on"]["render_start_unix_ns"]
    ):
        fail(f"{label}: off/on render-queue identities must be distinct")
    diagnostic_png = targeted_png_member(row)
    if diagnostic_png is None:
        if diagnostic_outputs:
            fail(f"{label}: unexpected diagnostic output record")
    else:
        if set(diagnostic_outputs) != {"effect_on_png"}:
            fail(f"{label}: targeted PNG process record missing")
        diagnostic = diagnostic_outputs["effect_on_png"]
        diagnostic_fields = {
            "return_path",
            "runtime_path",
            "sha256",
            "preexisting",
            "finalized",
            "mtime_unix_ns",
            "render_duration_ms",
            "render_start_unix_ns",
            "render_end_unix_ns",
            "render_queue_item_id",
            "output_module_index",
            "settings_serialization",
            "settings_serialization_sha256",
        }
        if not isinstance(diagnostic, dict) or set(diagnostic) != diagnostic_fields:
            fail(f"{label}: targeted PNG process record shape mismatch")
        parse_settings_serialization(
            diagnostic["settings_serialization"],
            f"{label}.diagnostic_outputs.effect_on_png.settings",
            {
                "Format": ("png",),
                "Channels": ("rgb", "alpha"),
                "Depth": ("million",),
                "Color": ("straight",),
            },
        )
        if (
            diagnostic["return_path"] != diagnostic_png
            or not isinstance(diagnostic["runtime_path"], str)
            or re.match(
                r"^(?:[A-Za-z]:[\\/]|\\\\)",
                diagnostic["runtime_path"],
            )
            is None
            or diagnostic["preexisting"] is not False
            or diagnostic["finalized"] is not True
            or type(diagnostic["mtime_unix_ns"]) is not int
            or not (
                diagnostic["render_start_unix_ns"]
                <= diagnostic["mtime_unix_ns"]
                <= diagnostic["render_end_unix_ns"]
            )
            or diagnostic["render_duration_ms"]
            != outputs["effect_on"]["render_duration_ms"]
            or diagnostic["render_start_unix_ns"]
            != outputs["effect_on"]["render_start_unix_ns"]
            or diagnostic["render_end_unix_ns"]
            != outputs["effect_on"]["render_end_unix_ns"]
            or diagnostic["render_queue_item_id"]
            != outputs["effect_on"]["render_queue_item_id"]
            or diagnostic["output_module_index"] != 2
            or diagnostic["settings_serialization_sha256"]
            != hashlib.sha256(
                diagnostic["settings_serialization"].encode("utf-8")
            ).hexdigest()
        ):
            fail(f"{label}: targeted PNG same-render binding mismatch")
        if windows_runtime_path_key(diagnostic["runtime_path"]) in {
            windows_runtime_path_key(outputs["no_effect"]["runtime_path"]),
            windows_runtime_path_key(outputs["effect_on"]["runtime_path"]),
        }:
            fail(f"{label}: targeted PNG runtime path aliases an EXR output")
        require_sha(diagnostic["sha256"], f"{label}.diagnostic_png.sha256")
    expected_logs = {
        "etw_etl": f"evidence/{row['row_id']}/etw.etl",
        "etw_csv": f"evidence/{row['row_id']}/etw.csv",
        "aerender_stdout": f"evidence/{row['row_id']}/aerender_stdout.txt",
    }
    if set(logs) != set(expected_logs):
        fail(f"{label}: process log set mismatch")
    for log_name, return_path in expected_logs.items():
        record = logs[log_name]
        if not isinstance(record, dict):
            fail(f"{label}: {log_name} log record is not an object")
        require_exact_keys(
            record,
            {"return_path", "runtime_path", "sha256"},
            f"{label}.{log_name}",
        )
        if (
            record["return_path"] != return_path
            or not isinstance(record["runtime_path"], str)
            or not record["runtime_path"]
            or re.match(r"^(?:[A-Za-z]:[\\/]|\\\\)", record["runtime_path"])
            is None
        ):
            fail(f"{label}: {log_name} runtime/return path mismatch")
        require_sha(record["sha256"], f"{label}.{log_name}.sha256")
    runtime_paths = [
        data["source_runtime_path"],
        project["runtime_path"],
        outputs["no_effect"]["runtime_path"],
        outputs["effect_on"]["runtime_path"],
        *(record["runtime_path"] for record in logs.values()),
    ]
    if diagnostic_outputs:
        runtime_paths.append(diagnostic_outputs["effect_on_png"]["runtime_path"])
    folded_runtime_paths = [windows_runtime_path_key(path) for path in runtime_paths]
    if len(folded_runtime_paths) != len(set(folded_runtime_paths)):
        fail(f"{label}: source/project/output/log runtime paths must be distinct")
    require_exact_keys(
        etw_export,
        {
            "tool_path",
            "tool_sha256",
            "tool_version",
            "command_argv",
            "source_etl_runtime_path",
            "source_etl_sha256",
            "normalized_csv_runtime_path",
            "normalized_csv_sha256",
        },
        f"{label}.etw_export",
    )
    export_argv = etw_export["command_argv"]
    if (
        not isinstance(etw_export["tool_path"], str)
        or re.match(r"^(?:[A-Za-z]:[\\/]|\\\\)", etw_export["tool_path"])
        is None
        or not isinstance(etw_export["tool_version"], str)
        or not etw_export["tool_version"]
        or not isinstance(export_argv, list)
        or any(not isinstance(argument, str) or not argument for argument in export_argv)
        or etw_export["source_etl_runtime_path"]
        != logs["etw_etl"]["runtime_path"]
        or etw_export["source_etl_runtime_path"] not in export_argv
        or etw_export["source_etl_sha256"] != logs["etw_etl"]["sha256"]
        or etw_export["normalized_csv_runtime_path"]
        != logs["etw_csv"]["runtime_path"]
        or etw_export["normalized_csv_runtime_path"] not in export_argv
        or etw_export["normalized_csv_sha256"] != logs["etw_csv"]["sha256"]
    ):
        fail(f"{label}: ETL-to-normalized-CSV export binding mismatch")
    require_sha(etw_export["tool_sha256"], f"{label}.etw_export.tool_sha256")


def require_hex_word(value: object, label: str) -> int:
    if (
        not isinstance(value, str)
        or re.fullmatch(r"0x[0-9a-f]{8}", value) is None
    ):
        fail(f"{label}: expected lowercase 0x-prefixed u32")
    return int(value, 16)


def require_pointer(value: object, label: str) -> int:
    if (
        not isinstance(value, str)
        or re.fullmatch(r"0x[0-9a-f]{1,16}", value) is None
        or int(value, 16) == 0
    ):
        fail(f"{label}: expected nonzero lowercase pointer")
    return int(value, 16)


def f32_from_word(word: int) -> float:
    return struct.unpack("<f", struct.pack("<I", word))[0]


def word_from_f32(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def authoritative_kira_case(
    files: dict[str, Path],
    row: dict[str, Any],
) -> dict[str, Any]:
    definition_path = files.get(KIRA_AUTHORITATIVE_DEFINITION)
    if definition_path is None:
        fail(f"{row['row_id']}: authoritative KiraKira definition missing")
    definition = load_json(definition_path)
    matches = [
        case
        for case in definition.get("cases", [])
        if isinstance(case, dict) and case.get("case_id") == row["case_id"]
    ]
    if len(matches) != 1:
        fail(f"{row['row_id']}: authoritative KiraKira case is not unique")
    return matches[0]


def verify_kira_property_readback(
    files: dict[str, Path],
    row: dict[str, Any],
    batch_sha: str,
    params_before: dict[str, Any],
) -> None:
    row_id = row["row_id"]
    relative = f"evidence/{row_id}/{KIRA_PROPERTY_READBACK_FILE}"
    path = files.get(relative)
    if path is None:
        fail(f"{row_id}: authoritative 42-property readback missing")
    data = require_binding(
        path,
        load_json(path),
        "kirakira_property_readback",
        row,
        batch_sha,
    )
    require_exact_keys(
        data,
        {"properties", "canonical_sha256", "capture_phase"},
        f"{row_id}.kirakira_property_readback.data",
    )
    params_before_values = params_before["values"]
    params_before_sha = params_before["values_sha256"]
    verify_kira_capture_phase(data["capture_phase"], params_before_sha, row_id)
    properties = data["properties"]
    case = authoritative_kira_case(files, row)
    expected_sha = require_sha(
        case.get("full_42_property_readback_sha256"),
        f"{row_id}.full_42_property_readback_sha256",
    )
    expected_preimage = verify_kira_rich42_preimage(case, row_id)
    verify_kira_rich42_writable_values(
        properties,
        params_before_values["parameter_actions"],
        params_before_values["standard_options"],
        row_id,
    )
    if (
        not isinstance(properties, list)
        or len(properties) != 42
        or not strict_equal(properties, expected_preimage)
        or data["canonical_sha256"] != canonical_json_sha256(properties)
        or data["canonical_sha256"] != expected_sha
    ):
        fail(f"{row_id}: authoritative 42-property canonical hash/count mismatch")
    required_fields = {
        "path",
        "path_full",
        "name",
        "match_name",
        "property_index",
        "property_type",
        "property_value_type",
        "is_time_varying",
        "num_keys",
        "can_set_expression",
        "expression_enabled",
        "enabled",
        "active",
        "value",
        "value_read_method",
        "range_metadata",
    }
    surface_rows = row["parameter_surface"]["exact_rows"]
    plugin_surface = {
        item["match_name"]: item
        for item in surface_rows
        if isinstance(item, dict) and isinstance(item.get("match_name"), str)
    }
    params_before_actions = {
        action["match_name"]: action
        for action in params_before_values["parameter_actions"]
    }
    params_before_options = {
        option["match_name"]: option
        for option in params_before_values["standard_options"]
    }
    expected_names = set(plugin_surface) | {
        option["match_name"] for option in COMMON_STANDARD_OPTIONS
    }
    expected_order = [
        item["match_name"] for item in surface_rows
    ] + [option["match_name"] for option in COMMON_STANDARD_OPTIONS]
    if [record.get("match_name") for record in properties] != expected_order:
        fail(f"{row_id}: full 42-property order mismatch")
    observed_names: set[str] = set()
    for index, record in enumerate(properties):
        if (
            not isinstance(record, dict)
            or not required_fields <= set(record)
        ):
            fail(f"{row_id}: malformed 42-property row {index}")
        match_name = record["match_name"]
        try:
            ae_property_type = int(record["property_type"])
            property_value_type = int(record["property_value_type"])
        except (TypeError, ValueError):
            fail(f"{row_id}: nonnumeric property type row {index}")
        unreadable = property_value_type in (6412, 6419)
        if (
            not isinstance(record["path"], list)
            or any(not isinstance(part, str) for part in record["path"])
            or not isinstance(record["path_full"], list)
            or any(not isinstance(part, str) for part in record["path_full"])
            or not isinstance(record["name"], str)
            or not isinstance(match_name, str)
            or not match_name
            or match_name in observed_names
            or type(record["property_index"]) is not int
            or record["property_index"] <= 0
            or type(record["enabled"]) is not bool
            or type(record["active"]) is not bool
            or type(record["is_time_varying"]) is not bool
            or type(record["num_keys"]) is not int
            or record["num_keys"] < 0
            or type(record["can_set_expression"]) is not bool
            or type(record["expression_enabled"]) is not bool
            or not isinstance(record["range_metadata"], dict)
            or unreadable
            and (
                record["value"] is not None
                or record["value_read_method"] is not None
                or not isinstance(record.get("error"), str)
                or not record["error"]
            )
            or not unreadable
            and (
                record["value_read_method"] != "value"
                or "error" in record
            )
        ):
            fail(f"{row_id}: invalid/duplicate 42-property row {index}")
        observed_names.add(match_name)
        surface = plugin_surface.get(match_name)
        if surface is not None:
            expected_action = params_before_actions.get(match_name)
            if (
                record["name"] != surface["display_name"]
                or record["property_index"] != surface["property_index"]
                or ae_property_type != 6212
                or property_value_type != surface["property_type"]
                or record["enabled"] is not surface["enabled"]
                or record["active"] is not surface["active"]
                or expected_action is not None
                and not json_number_equal(
                    record["value"], expected_action["value"]
                )
            ):
                fail(f"{row_id}: plugin readback/surface mismatch row {index}")
        else:
            option = next(
                (
                    candidate
                    for candidate in COMMON_STANDARD_OPTIONS
                    if candidate["match_name"] == match_name
                ),
                None,
            )
            if (
                option is None
                or match_name not in params_before_options
                or ae_property_type != 6212
                or property_value_type != option["property_type"]
                or not json_number_equal(
                    record["value"],
                    params_before_options[match_name]["value"],
                )
            ):
                fail(f"{row_id}: standard-option readback mismatch row {index}")
    if observed_names != expected_names:
        fail(f"{row_id}: full 42-property identity set mismatch")


def require_world(
    value: object,
    width: int,
    height: int,
    label: str,
) -> tuple[int, int]:
    if not isinstance(value, dict):
        fail(f"{label}: world is not an object")
    require_exact_keys(value, {"data", "rowbytes", "width", "height"}, label)
    base = require_pointer(value["data"], f"{label}.data")
    rowbytes = value["rowbytes"]
    if (
        type(rowbytes) is not int
        or rowbytes <= 0
        or value["width"] != width
        or value["height"] != height
    ):
        fail(f"{label}: world geometry mismatch")
    return base, rowbytes


def verify_kira_writer(
    writer: object,
    row: dict[str, Any],
    output_base: int,
    output_rowbytes: int,
    x: int,
    y: int,
    exported_words: list[int],
    label: str,
) -> None:
    if not isinstance(writer, dict):
        fail(f"{label}: writer is not an object")
    require_exact_keys(
        writer,
        {
            "entry",
            "callsite_rva",
            "return_seen",
            "destination",
            "pixel_bytes",
            "xmm_f32_u32",
            "stack_arg5_at_call",
            "stack_arg5_at_entry",
            "stored_argb",
        },
        label,
    )
    contract = KIRA_TYPED_ENTRIES[row["depth"]]
    destination = require_pointer(writer["destination"], f"{label}.destination")
    if (
        writer["entry"] != contract["writer"]
        or not isinstance(writer["callsite_rva"], str)
        or re.fullmatch(r"0x[0-9a-f]+", writer["callsite_rva"]) is None
        or writer["return_seen"] is not True
        or writer["pixel_bytes"] != contract["pixel_bytes"]
        or require_pointer(
            writer["stack_arg5_at_call"],
            f"{label}.stack_arg5_at_call",
        )
        != destination
        or require_pointer(
            writer["stack_arg5_at_entry"],
            f"{label}.stack_arg5_at_entry",
        )
        != destination
        or destination
        != output_base + y * output_rowbytes + x * contract["pixel_bytes"]
    ):
        fail(f"{label}: typed writer identity/destination mismatch")
    xmm = writer["xmm_f32_u32"]
    if not isinstance(xmm, dict):
        fail(f"{label}: XMM record is not an object")
    require_exact_keys(
        xmm,
        {"xmm0_r", "xmm1_g", "xmm2_b", "xmm3_a"},
        f"{label}.xmm_f32_u32",
    )
    rgba_words = [
        require_hex_word(xmm[name], f"{label}.{name}")
        for name in ("xmm0_r", "xmm1_g", "xmm2_b", "xmm3_a")
    ]
    rgba = [f32_from_word(word) for word in rgba_words]
    if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in rgba):
        fail(f"{label}: writer XMM value is not finite unit float32")
    stored = writer["stored_argb"]
    if not isinstance(stored, dict):
        fail(f"{label}: stored_argb is not an object")
    require_exact_keys(stored, {"unit", "values", "raw_hex"}, f"{label}.stored_argb")
    if (
        stored["unit"] != contract["stored_unit"]
        or not isinstance(stored["values"], list)
        or len(stored["values"]) != 4
        or not isinstance(stored["raw_hex"], str)
    ):
        fail(f"{label}: stored ARGB shape mismatch")
    argb_words = [rgba_words[3], rgba_words[0], rgba_words[1], rgba_words[2]]
    if row["depth"] == 32:
        expected_values: list[object] = [
            f"0x{word:08x}" for word in argb_words
        ]
        expected_raw = struct.pack("<4I", *argb_words).hex()
        expected_exported = rgba_words
    else:
        scale = int(contract["scale"])
        expected_units = [math.trunc(f32_from_word(word) * scale) for word in argb_words]
        expected_values = expected_units
        if row["depth"] == 8:
            if any(not 0 <= value <= 0xFF for value in expected_units):
                fail(f"{label}: PF8 conversion is out of range")
            expected_raw = bytes(expected_units).hex()
        else:
            if any(not 0 <= value <= 0xFFFF for value in expected_units):
                fail(f"{label}: PF16 conversion is out of range")
            expected_raw = struct.pack("<4H", *expected_units).hex()
        expected_exported = [
            word_from_f32(expected_units[channel] / scale)
            for channel in (1, 2, 3, 0)
        ]
    if (
        not strict_equal(stored["values"], expected_values)
        or stored["raw_hex"] != expected_raw
        or exported_words != expected_exported
    ):
        fail(f"{label}: typed writer store/export conversion mismatch")


def verify_kira_ramp_record(
    record: object,
    expected_layer: str,
    witness_id: str,
    x: int,
    y: int,
    ray_word_by_layer: dict[str, int],
    label: str,
) -> None:
    if not isinstance(record, dict):
        fail(f"{label}: ramp record is not an object")
    require_exact_keys(
        record,
        {
            "layer_index",
            "layer",
            "use_ramp",
            "block_pointer",
            "raw_0x144_hex",
            "raw_sha256",
            "stop_count",
            "stops",
            "helper",
        },
        label,
    )
    layer_index = KIRA_LAYER_NAMES.index(expected_layer)
    require_pointer(record["block_pointer"], f"{label}.block_pointer")
    raw_hex = record["raw_0x144_hex"]
    if (
        record["layer_index"] != layer_index
        or record["layer"] != expected_layer
        or record["use_ramp"] is not True
        or not isinstance(raw_hex, str)
        or re.fullmatch(r"[0-9a-f]{648}", raw_hex) is None
    ):
        fail(f"{label}: ramp identity/raw block shape mismatch")
    raw = bytes.fromhex(raw_hex)
    if (
        require_sha(record["raw_sha256"], f"{label}.raw_sha256")
        != hashlib.sha256(raw).hexdigest()
        or record["raw_sha256"] != KIRA_DEFAULT_RAMP_SHA256
    ):
        fail(f"{label}: ramp raw hash mismatch")
    stop_count = struct.unpack_from("<i", raw, 0)[0]
    stops = record["stops"]
    if (
        record["stop_count"] != stop_count
        or not 0 <= stop_count <= 16
        or not isinstance(stops, list)
        or len(stops) != stop_count
    ):
        fail(f"{label}: ramp stop count mismatch")
    stop_words: list[list[int]] = []
    stop_keys = ("position_u32", "a_u32", "r_u32", "g_u32", "b_u32")
    for index, stop in enumerate(stops):
        if not isinstance(stop, dict):
            fail(f"{label}: ramp stop {index} is not an object")
        require_exact_keys(stop, set(stop_keys), f"{label}.stops[{index}]")
        words = [
            require_hex_word(stop[key], f"{label}.stops[{index}].{key}")
            for key in stop_keys
        ]
        if words != list(struct.unpack_from("<5I", raw, 4 + index * 20)):
            fail(f"{label}: decoded ramp stop {index} differs from raw block")
        stop_words.append(words)
    helper = record["helper"]
    if not isinstance(helper, dict):
        fail(f"{label}: ramp helper is not an object")
    require_exact_keys(
        helper,
        {
            "entry",
            "entry_seen",
            "return_seen",
            "witness_id",
            "xy",
            "layer_index",
            "block_pointer",
            "raw_ray_input_u32",
            "returned_argb_f32_u32",
        },
        f"{label}.helper",
    )
    xy = helper["xy"]
    returned = helper["returned_argb_f32_u32"]
    if (
        helper["entry"] != "FUN_181232080"
        or helper["entry_seen"] is not True
        or helper["return_seen"] is not True
        or helper["witness_id"] != witness_id
        or not strict_equal(xy, {"x": x, "y": y})
        or helper["layer_index"] != layer_index
        or helper["block_pointer"] != record["block_pointer"]
        or require_hex_word(
            helper["raw_ray_input_u32"],
            f"{label}.helper.raw_ray_input_u32",
        )
        != ray_word_by_layer[expected_layer]
        or not isinstance(returned, list)
        or len(returned) != 4
        or any(
            not isinstance(word, str)
            or re.fullmatch(r"0x[0-9a-f]{8}", word) is None
            for word in returned
        )
    ):
        fail(f"{label}: ramp helper binding mismatch")
    input_value = f32_from_word(ray_word_by_layer[expected_layer])
    if not math.isfinite(input_value) or not stop_words:
        fail(f"{label}: ramp helper input/stops cannot be evaluated")
    decoded = [
        [f32_from_word(word) for word in words]
        for words in stop_words
    ]
    lower = None
    upper = None
    for stop in decoded:
        if stop[0] <= input_value and (
            lower is None or stop[0] >= lower[0]
        ):
            lower = stop
        if stop[0] > input_value and (
            upper is None or stop[0] < upper[0]
        ):
            upper = stop
    if lower is None:
        selected = upper
        expected_return_words = [
            word_from_f32(value) for value in selected[1:]
        ]
    elif upper is None:
        expected_return_words = [
            word_from_f32(value) for value in lower[1:]
        ]
    else:
        span = f32_round(upper[0] - lower[0])
        fraction = (
            0.0
            if abs(span) < f32_round(0.0001)
            else f32_round(f32_round(input_value - lower[0]) / span)
        )
        expected_return_words = [
            word_from_f32(
                f32_round(
                    lower[channel]
                    + f32_round(
                        fraction
                        * f32_round(upper[channel] - lower[channel])
                    )
                )
            )
            for channel in range(1, 5)
        ]
    actual_return_words = [
        require_hex_word(word, f"{label}.helper.returned_argb_f32_u32")
        for word in returned
    ]
    if actual_return_words != expected_return_words:
        fail(f"{label}: ramp helper result differs from decoded ramp interpolation")


def verify_kira_lineage(
    files: dict[str, Path],
    row: dict[str, Any],
    batch_sha: str,
    process: dict[str, Any],
) -> tuple[str, int, int, list[int]]:
    row_id = row["row_id"]
    relative = f"evidence/{row_id}/{KIRA_LINEAGE_FILE}"
    path = files.get(relative)
    if path is None:
        fail(f"{row_id}: authoritative KiraKira lineage missing")
    data = require_binding(
        path,
        load_json(path),
        "kirakira_lineage",
        row,
        batch_sha,
    )
    require_exact_keys(
        data,
        {"identity", "witness", "ramp_records"},
        f"{row_id}.kirakira_lineage.data",
    )
    case = authoritative_kira_case(files, row)
    identity = data["identity"]
    if not isinstance(identity, dict):
        fail(f"{row_id}: lineage identity is not an object")
    require_exact_keys(
        identity,
        {
            "campaign_id",
            "row_id",
            "case_id",
            "bits_per_channel",
            "aerender_pid",
            "afterfx_com_pid",
            "module_base",
            "aex_sha256",
        },
        f"{row_id}.lineage.identity",
    )
    if (
        identity["campaign_id"] != CAMPAIGN_ID
        or identity["row_id"] != row_id
        or identity["case_id"] != row["case_id"]
        or identity["bits_per_channel"] != row["depth"]
        or identity["aerender_pid"] != process["aerender"]["pid"]
        or identity["afterfx_com_pid"] != process["real_afterfx_child"]["pid"]
        or require_pointer(identity["module_base"], f"{row_id}.module_base") <= 0
        or identity["aex_sha256"] != KIRA_AEX_SHA256
        or identity["aex_sha256"] != row["aex_sha256"]
    ):
        fail(f"{row_id}: lineage/process/module identity mismatch")
    witness = data["witness"]
    if not isinstance(witness, dict):
        fail(f"{row_id}: lineage witness is not an object")
    require_exact_keys(
        witness,
        {
            "witness_id",
            "output_xy",
            "work_xy",
            "owner",
            "rays",
            "inner",
            "resize_bridge",
            "owner_staging",
            "outer",
            "writer",
            "exported_effect_on",
        },
        f"{row_id}.lineage.witness",
    )
    witness_id = witness["witness_id"]
    output_xy = witness["output_xy"]
    work_xy = witness["work_xy"]
    if (
        not isinstance(witness_id, str)
        or not witness_id
        or not isinstance(output_xy, dict)
        or set(output_xy) != {"x", "y"}
        or not isinstance(work_xy, dict)
        or set(work_xy) != {"x", "y", "linear_index"}
    ):
        fail(f"{row_id}: witness ID/XY shape mismatch")
    x = output_xy["x"]
    y = output_xy["y"]
    work_x = work_xy["x"]
    work_y = work_xy["y"]
    work_index = work_xy["linear_index"]
    width = row["comp"]["width"]
    height = row["comp"]["height"]
    approximated = case["approximated_input"] == 1
    work_width = int(width * 0.5) if approximated else width
    work_height = int(height * 0.5) if approximated else height
    if (
        type(x) is not int
        or type(y) is not int
        or not 0 <= x < width
        or not 0 <= y < height
        or type(work_x) is not int
        or type(work_y) is not int
        or type(work_index) is not int
        or not 0 <= work_x < work_width
        or not 0 <= work_y < work_height
        or work_index != work_y * work_width + work_x
        or approximated
        and (work_x != int(x * 0.5) or work_y != int(y * 0.5))
        or not approximated
        and (work_x != x or work_y != y)
    ):
        fail(f"{row_id}: witness XY is out of bounds")
    owner = witness["owner"]
    if not isinstance(owner, dict):
        fail(f"{row_id}: owner is not an object")
    require_exact_keys(
        owner,
        {
            "entry",
            "mode",
            "merge_mode",
            "approximated_input",
            "source_world",
            "output_world",
        },
        f"{row_id}.lineage.owner",
    )
    typed = KIRA_TYPED_ENTRIES[row["depth"]]
    if (
        owner["entry"] != typed["owner"]
        or owner["mode"] != case["mode"]
        or owner["merge_mode"] != case["merge_mode"]
        or owner["approximated_input"] != case["approximated_input"]
    ):
        fail(f"{row_id}: owner mode/depth identity mismatch")
    require_world(
        owner["source_world"], width, height, f"{row_id}.owner.source_world"
    )
    output_base, output_rowbytes = require_world(
        owner["output_world"], width, height, f"{row_id}.owner.output_world"
    )
    rays = witness["rays"]
    if not isinstance(rays, list) or len(rays) != 5:
        fail(f"{row_id}: lineage must contain exactly five ray records")
    ray_word_by_layer: dict[str, int] = {}
    for index, ray in enumerate(rays):
        if not isinstance(ray, dict):
            fail(f"{row_id}: ray {index} is not an object")
        require_exact_keys(
            ray,
            {
                "layer_index",
                "layer",
                "base",
                "byte_offset",
                "address",
                "raw_f32_u32",
            },
            f"{row_id}.rays[{index}]",
        )
        base = require_pointer(ray["base"], f"{row_id}.rays[{index}].base")
        address = require_pointer(
            ray["address"], f"{row_id}.rays[{index}].address"
        )
        word = require_hex_word(
            ray["raw_f32_u32"], f"{row_id}.rays[{index}].raw_f32_u32"
        )
        if (
            ray["layer_index"] != index
            or ray["layer"] != KIRA_LAYER_NAMES[index]
            or ray["byte_offset"] != work_index * 4
            or address != base + ray["byte_offset"]
            or not math.isfinite(f32_from_word(word))
        ):
            fail(f"{row_id}: ray {index} pointer/value lineage mismatch")
        ray_word_by_layer[ray["layer"]] = word
    inner = witness["inner"]
    if not isinstance(inner, dict):
        fail(f"{row_id}: inner record is not an object")
    require_exact_keys(
        inner,
        {
            "slot",
            "target",
            "entry_seen",
            "return_seen",
            "output_base",
            "byte_offset",
            "address",
            "rgba_f32_u32",
        },
        f"{row_id}.lineage.inner",
    )
    inner_base = require_pointer(inner["output_base"], f"{row_id}.inner.output_base")
    inner_address = require_pointer(inner["address"], f"{row_id}.inner.address")
    expected_slot = "+0x08" if case["merge_mode"] == 1 else "+0x10"
    expected_target = (
        "FUN_18114fd90" if case["merge_mode"] == 1 else "FUN_18114ffd0"
    )
    inner_words = inner["rgba_f32_u32"]
    if (
        inner["slot"] != expected_slot
        or inner["target"] != expected_target
        or inner["entry_seen"] is not True
        or inner["return_seen"] is not True
        or inner["byte_offset"] != work_index * 16
        or inner_address != inner_base + inner["byte_offset"]
        or not isinstance(inner_words, list)
        or len(inner_words) != 4
        or any(
            not math.isfinite(
                f32_from_word(require_hex_word(word, f"{row_id}.inner.rgba"))
            )
            for word in inner_words
        )
    ):
        fail(f"{row_id}: inner aggregator pointer/return mismatch")
    staging = witness["owner_staging"]
    if not isinstance(staging, dict) or set(staging) != {"before", "after"}:
        fail(f"{row_id}: owner staging shape mismatch")
    before = staging["before"]
    after = staging["after"]
    if not isinstance(before, dict) or not isinstance(after, dict):
        fail(f"{row_id}: owner staging records are not objects")
    require_exact_keys(before, {"plus_0x78", "plus_0x140"}, f"{row_id}.staging.before")
    require_exact_keys(after, {"plus_0x128", "plus_0x190"}, f"{row_id}.staging.after")
    before_78 = require_pointer(before["plus_0x78"], f"{row_id}.staging.+78")
    before_140 = require_pointer(before["plus_0x140"], f"{row_id}.staging.+140")
    after_128 = require_pointer(after["plus_0x128"], f"{row_id}.staging.+128")
    after_190 = require_pointer(after["plus_0x190"], f"{row_id}.staging.+190")
    if before_78 != after_128 or before_140 != after_190:
        fail(f"{row_id}: owner +0x128/+0x190 staging copy mismatch")
    bridge = witness["resize_bridge"]
    if case["approximated_input"] == 1:
        if not isinstance(bridge, dict):
            fail(f"{row_id}: approximated-input resize bridge missing")
        require_exact_keys(
            bridge,
            {
                "mapping",
                "work_output_base",
                "full_glow_base",
                "work_xy",
                "output_xy",
            },
            f"{row_id}.resize_bridge",
        )
        if (
            bridge["mapping"] != "nearest"
            or require_pointer(
                bridge["work_output_base"], f"{row_id}.bridge.work_output_base"
            )
            != inner_base
            or require_pointer(
                bridge["full_glow_base"], f"{row_id}.bridge.full_glow_base"
            )
            != after_190
            or not strict_equal(
                bridge["work_xy"], {"x": work_x, "y": work_y}
            )
            or not strict_equal(bridge["output_xy"], {"x": x, "y": y})
        ):
            fail(f"{row_id}: approximated-input resize bridge mismatch")
    elif bridge is not None or inner_base != after_190:
        fail(f"{row_id}: unexpected/missing direct inner-to-staging pointer")
    outer = witness["outer"]
    if not isinstance(outer, dict):
        fail(f"{row_id}: outer record is not an object")
    require_exact_keys(
        outer,
        {
            "entry",
            "source_base",
            "source_rowbytes",
            "source_address",
            "glow_base",
            "glow_rowbytes",
            "glow_address",
        },
        f"{row_id}.lineage.outer",
    )
    outer_source = require_pointer(outer["source_base"], f"{row_id}.outer.source_base")
    outer_glow = require_pointer(outer["glow_base"], f"{row_id}.outer.glow_base")
    if (
        outer["entry"] != typed["outer"]
        or outer_source != after_128
        or outer_glow != after_190
        or type(outer["source_rowbytes"]) is not int
        or outer["source_rowbytes"] < width * 16
        or type(outer["glow_rowbytes"]) is not int
        or outer["glow_rowbytes"] < width * 16
        or require_pointer(
            outer["source_address"], f"{row_id}.outer.source_address"
        )
        != outer_source + y * outer["source_rowbytes"] + x * 16
        or require_pointer(
            outer["glow_address"], f"{row_id}.outer.glow_address"
        )
        != outer_glow + y * outer["glow_rowbytes"] + x * 16
    ):
        fail(f"{row_id}: outer source/glow XY lineage mismatch")
    exported = witness["exported_effect_on"]
    if not isinstance(exported, dict):
        fail(f"{row_id}: exported pixel record is not an object")
    require_exact_keys(
        exported,
        {"member", "xy", "semantic_rgba_f32_u32"},
        f"{row_id}.exported_effect_on",
    )
    exported_words_raw = exported["semantic_rgba_f32_u32"]
    if (
        exported["member"] != f"outputs/{row_id}/effect_on.exr"
        or not strict_equal(exported["xy"], {"x": x, "y": y})
        or not isinstance(exported_words_raw, list)
        or len(exported_words_raw) != 4
    ):
        fail(f"{row_id}: exported effect-on pixel binding mismatch")
    exported_words = [
        require_hex_word(word, f"{row_id}.exported_effect_on.rgba")
        for word in exported_words_raw
    ]
    verify_kira_writer(
        witness["writer"],
        row,
        output_base,
        output_rowbytes,
        x,
        y,
        exported_words,
        f"{row_id}.writer",
    )
    ramp_records = data["ramp_records"]
    expected_layers = KIRA_RAMP_LAYERS_BY_CASE[row["case_id"]]
    if not isinstance(ramp_records, list) or len(ramp_records) != len(expected_layers):
        fail(f"{row_id}: enabled-ramp record cardinality mismatch")
    for index, (record, layer) in enumerate(
        zip(ramp_records, expected_layers, strict=True)
    ):
        verify_kira_ramp_record(
            record,
            layer,
            witness_id,
            x,
            y,
            ray_word_by_layer,
            f"{row_id}.ramp_records[{index}]",
        )
    return witness_id, x, y, exported_words


def verify_kira_mode4(
    files: dict[str, Path],
    row: dict[str, Any],
    batch_sha: str,
    witness_id: str,
    witness_x: int,
    witness_y: int,
) -> None:
    row_id = row["row_id"]
    relative = f"evidence/{row_id}/{KIRA_MODE4_FILE}"
    path = files.get(relative)
    if path is None:
        fail(f"{row_id}: Mode4 full-caller trace missing")
    data = require_binding(
        path,
        load_json(path),
        "kirakira_mode4",
        row,
        batch_sha,
    )
    require_exact_keys(
        data,
        {
            "witness_id",
            "output_xy",
            "layer_index",
            "inline_entry",
            "filter_calls",
            "shared_tail",
            "neighborhoods",
            "full_caller_continuation",
        },
        f"{row_id}.kirakira_mode4.data",
    )
    calls = data["filter_calls"]
    if (
        data["witness_id"] != witness_id
        or not strict_equal(
            data["output_xy"],
            {"x": witness_x, "y": witness_y},
        )
        or data["layer_index"] != 4
        or data["inline_entry"] != "0x181150979"
        or data["shared_tail"] != "0x181150f3d"
        or data["full_caller_continuation"] is not True
        or not isinstance(calls, list)
        or len(calls) != 3
    ):
        fail(f"{row_id}: Mode4 entry/tail/call cardinality mismatch")
    for index, call in enumerate(calls):
        if not isinstance(call, dict):
            fail(f"{row_id}: Mode4 call {index} is not an object")
        require_exact_keys(
            call,
            {
                "call_index",
                "target",
                "source_mat",
                "destination_mat",
                "gain_u32",
            },
            f"{row_id}.mode4.filter_calls[{index}]",
        )
        if (
            call["call_index"] != index
            or call["target"] != "FUN_181280bc0"
            or require_pointer(
                call["source_mat"], f"{row_id}.mode4.call[{index}].source"
            )
            <= 0
            or require_pointer(
                call["destination_mat"],
                f"{row_id}.mode4.call[{index}].destination",
            )
            <= 0
            or not math.isfinite(
                f32_from_word(
                    require_hex_word(
                        call["gain_u32"],
                        f"{row_id}.mode4.call[{index}].gain_u32",
                    )
                )
            )
        ):
            fail(f"{row_id}: Mode4 filter call mismatch")
    neighborhoods = data["neighborhoods"]
    required_stages = {
        "highlight_source",
        "mode4_tail_r14",
        "mode4_tail_r12",
        "mode4_destination",
    }
    if not isinstance(neighborhoods, dict):
        fail(f"{row_id}: Mode4 neighborhoods are not an object")
    require_exact_keys(neighborhoods, required_stages, f"{row_id}.mode4.neighborhoods")
    for stage in sorted(required_stages):
        record = neighborhoods[stage]
        if not isinstance(record, dict):
            fail(f"{row_id}: Mode4 {stage} neighborhood is not an object")
        require_exact_keys(
            record,
            {"shape", "unit", "words_u32", "packed_sha256"},
            f"{row_id}.mode4.{stage}",
        )
        words = record["words_u32"]
        if (
            record["shape"] != [7, 9]
            or record["unit"] != "le_f32_u32"
            or not isinstance(words, list)
            or len(words) != 63
        ):
            fail(f"{row_id}: Mode4 {stage} shape/word count mismatch")
        packed = struct.pack(
            "<63I",
            *[
                require_hex_word(
                    word,
                    f"{row_id}.mode4.{stage}.words_u32[{index}]",
                )
                for index, word in enumerate(words)
            ],
        )
        if (
            require_sha(
                record["packed_sha256"],
                f"{row_id}.mode4.{stage}.packed_sha256",
            )
            != hashlib.sha256(packed).hexdigest()
        ):
            fail(f"{row_id}: Mode4 {stage} packed hash mismatch")


def verify_pass_row(
    files: dict[str, Path],
    row: dict[str, Any],
    batch_sha: str,
) -> dict[str, Any]:
    row_id = row["row_id"]
    project_relative = f"projects/{row_id}.aep"
    no_effect_relative = f"outputs/{row_id}/no_effect.exr"
    effect_on_relative = f"outputs/{row_id}/effect_on.exr"
    for relative in (project_relative, no_effect_relative, effect_on_relative):
        path = files.get(relative)
        if path is None or path.stat().st_size <= 0:
            fail(f"{row_id}: required pass artifact missing/empty: {relative}")
    evidence_root = f"evidence/{row_id}"
    evidence_data: dict[str, dict[str, Any]] = {}
    for filename, kind in PASS_JSON_FILES.items():
        relative = f"{evidence_root}/{filename}"
        path = files.get(relative)
        if path is None:
            fail(f"{row_id}: pass evidence missing: {relative}")
        evidence_data[kind] = require_binding(
            path,
            load_json(path),
            kind,
            row,
            batch_sha,
        )
    minimum_other_sizes = {
        "etw.etl": 1024,
        "etw.csv": 128,
        "aerender_stdout.txt": 1,
    }
    for filename in PASS_OTHER_FILES:
        relative = f"{evidence_root}/{filename}"
        path = files.get(relative)
        if (
            path is None
            or path.stat().st_size < minimum_other_sizes[filename]
        ):
            fail(f"{row_id}: pass evidence missing/empty: {relative}")
    for kind in ("params_expected", "params_before", "params_after"):
        require_exact_keys(
            evidence_data[kind],
            {"values", "values_sha256"},
            f"{row_id}.{kind}.data",
        )
    expected_values = {
        "parameter_actions": row["parameter_writes"],
        "standard_options": row["standard_options"],
    }
    for kind in ("params_expected", "params_before", "params_after"):
        verify_parameter_snapshot(
            evidence_data[kind]["values"],
            expected_values,
            f"{row_id}.{kind}.values",
        )
        if evidence_data[kind].get("values_sha256") != canonical_json_sha256(
            evidence_data[kind]["values"]
        ):
            fail(f"{row_id}: {kind} canonical values SHA-256 mismatch")
    setup = evidence_data["params_setup"]
    require_exact_keys(
        setup,
        {
            "expected_surface_contract",
            "expected_surface_contract_sha256",
            "observed_surface",
            "observed_surface_sha256",
            "surface_gate_passed",
            "surface_gate_failures",
        },
        f"{row_id}.params_setup.data",
    )
    if (
        not json_number_equal(
            setup["expected_surface_contract"],
            row["parameter_surface"],
        )
        or setup["expected_surface_contract_sha256"]
        != canonical_json_sha256(row["parameter_surface"])
        or not isinstance(setup["observed_surface"], list)
        or not setup["observed_surface"]
        or setup["observed_surface_sha256"]
        != canonical_json_sha256(setup["observed_surface"])
        or setup["surface_gate_passed"] is not True
        or setup["surface_gate_failures"] != []
    ):
        fail(f"{row_id}: parameter-surface gate mismatch")
    verify_observed_surface(
        row["parameter_surface"],
        setup["observed_surface"],
        f"{row_id}.params_setup",
    )
    project_sha = sha256(files[project_relative])
    project_observations = [
        verify_project_data(
            evidence_data[kind],
            row,
            f"{row_id}.{kind}.data",
            project_relative,
            project_sha,
        )
        for kind in ("project_before", "project_after")
    ]
    if not json_number_equal(project_observations[0], project_observations[1]):
        fail(f"{row_id}: live project observation changed across render")
    output_module_branches = [
        verify_output_module_data(
            evidence_data[kind],
            row,
            f"{row_id}.{kind}.data",
        )
        for kind in ("output_module_before", "output_module_after")
    ]
    if not strict_equal(output_module_branches[0], output_module_branches[1]):
        fail(f"{row_id}: output-module observation changed across render")
    verify_process_data(evidence_data["process"], row, row_id)
    process = evidence_data["process"]
    kira_exported_witness: tuple[str, int, int, list[int]] | None = None
    if is_kira_authoritative_row(row):
        verify_kira_property_readback(
            files,
            row,
            batch_sha,
            evidence_data["params_before"],
        )
        kira_exported_witness = verify_kira_lineage(
            files,
            row,
            batch_sha,
            process,
        )
        case = authoritative_kira_case(files, row)
        if case["mode"] == 4:
            verify_kira_mode4(
                files,
                row,
                batch_sha,
                kira_exported_witness[0],
                kira_exported_witness[1],
                kira_exported_witness[2],
            )
    process_outputs = process["outputs"]
    for filename, log_name in (
        ("etw.etl", "etw_etl"),
        ("etw.csv", "etw_csv"),
        ("aerender_stdout.txt", "aerender_stdout"),
    ):
        if process["logs"][log_name]["sha256"] != sha256(
            files[f"{evidence_root}/{filename}"]
        ):
            fail(f"{row_id}: process log hash mismatch: {filename}")
    etw_csv_text = read_text_evidence(
        files[f"{evidence_root}/etw.csv"],
        f"{row_id}.etw.csv",
    )
    stdout_text = read_text_evidence(
        files[f"{evidence_root}/aerender_stdout.txt"],
        f"{row_id}.aerender_stdout.txt",
    ).casefold()
    verify_etw_csv(
        etw_csv_text,
        process,
        row,
        f"{row_id}.etw.csv",
    )
    stdout_tokens = [
        f"{row_id}.aep",
        process_outputs["no_effect"]["runtime_path"],
        process_outputs["effect_on"]["runtime_path"],
        process_outputs["no_effect"]["render_queue_item_id"],
        process_outputs["effect_on"]["render_queue_item_id"],
    ]
    diagnostic_png = targeted_png_member(row)
    if diagnostic_png is not None:
        diagnostic_process = process["diagnostic_outputs"]["effect_on_png"]
        if (
            diagnostic_process["sha256"] != sha256(files[diagnostic_png])
            or diagnostic_process["return_path"] != diagnostic_png
        ):
            fail(f"{row_id}: targeted PNG process hash/path mismatch")
        stdout_tokens.extend(
            [
                diagnostic_process["runtime_path"],
                diagnostic_process["render_queue_item_id"],
            ]
        )
    if any(token.casefold() not in stdout_text for token in stdout_tokens):
        fail(f"{row_id}: aerender stdout lacks project/output/RQ identity")
    observed_project = project_observations[0]
    observed_rq = observed_project["render_queue_items"]
    observed_output_module = output_module_branches[0]
    if (
        process["run_nonce"] != observed_project["run_nonce"]
        or process["source_runtime_path"]
        != observed_project["source"]["runtime_path"]
        or process["project"]["return_path"] != project_relative
        or process["project"]["sha256"] != project_sha
    ):
        fail(f"{row_id}: process/project observation binding mismatch")
    for branch in ("no_effect", "effect_on"):
        if (
            process_outputs[branch]["return_path"]
            != f"outputs/{row_id}/{branch}.exr"
            or process_outputs[branch]["render_queue_item_id"]
            != observed_rq[branch]["id"]
            or process_outputs[branch]["runtime_path"]
            != observed_rq[branch]["output_runtime_path"]
            or process_outputs[branch]["render_queue_item_id"]
            != observed_output_module[branch]["render_queue_item_id"]
        ):
            fail(f"{row_id}: {branch} process/RQ/output-module binding mismatch")
    no_effect_path = files[no_effect_relative]
    effect_on_path = files[effect_on_relative]
    no_effect_info = inspect_float_rgba_exr(
        no_effect_path, (row["comp"]["width"], row["comp"]["height"])
    )
    effect_on_info = inspect_float_rgba_exr(
        effect_on_path, (row["comp"]["width"], row["comp"]["height"])
    )
    if kira_exported_witness is not None:
        _, witness_x, witness_y, witness_words = kira_exported_witness
        planes, exr_width, exr_height, _ = read_planes_with_layout(effect_on_path)
        if (
            exr_width != row["comp"]["width"]
            or exr_height != row["comp"]["height"]
        ):
            fail(f"{row_id}: lineage effect-on EXR dimensions drifted")
        offset = (witness_y * exr_width + witness_x) * 4
        actual_rgba_words = [
            struct.unpack(
                "<I",
                planes[channel][offset : offset + 4],
            )[0]
            for channel in ("R", "G", "B", "A")
        ]
        if actual_rgba_words != witness_words:
            fail(f"{row_id}: lineage writer pixel differs from effect-on EXR")
    for kind, info in (
        ("exr_header_no_effect", no_effect_info),
        ("exr_header_effect_on", effect_on_info),
    ):
        independently_inspected = dict(info)
        independently_inspected.pop("path", None)
        if not strict_equal(evidence_data[kind], independently_inspected):
            fail(f"{row_id}: {kind} differs from independent EXR inspection")
    for label, info in (("no_effect", no_effect_info), ("effect_on", effect_on_info)):
        counts = info["sample_counts"]
        expected_window = [
            0,
            0,
            row["comp"]["width"] - 1,
            row["comp"]["height"] - 1,
        ]
        if (
            info.get("channel_order") != ["A", "B", "G", "R"]
            or info.get("data_window") != expected_window
            or info.get("display_window") != expected_window
            or counts["nan"]
            or counts["+inf"]
            or counts["-inf"]
        ):
            fail(f"{row_id}: {label} physical EXR contract mismatch")
    if (
        row["depth"] == 32
        and str(row["source_member"]).casefold().endswith(".exr")
    ):
        source_roundtrip = compare_float_exr(
            files[row["source_member"]],
            no_effect_path,
        )
        if source_roundtrip["mismatched_values"] != 0:
            fail(
                f"{row_id}: EXR source/no-effect raw FLOAT32 round-trip mismatch"
            )
    comparison = compare_float_exr(no_effect_path, effect_on_path)
    comparison_data = evidence_data["raw_off_on_comparison"]
    expected_comparison = {
        "no_effect_sha256": sha256(no_effect_path),
        "effect_on_sha256": sha256(effect_on_path),
        "decoded_word_count": (
            row["comp"]["width"] * row["comp"]["height"] * 4
        ),
        "mismatched_words": comparison["mismatched_values"],
        "max_raw_u32_delta": comparison["max_raw_u32_delta"],
    }
    if not strict_equal(comparison_data, expected_comparison):
        fail(f"{row_id}: reported raw comparison differs from independent decode")
    if (
        process_outputs["no_effect"]["sha256"] != sha256(no_effect_path)
        or process_outputs["effect_on"]["sha256"] != sha256(effect_on_path)
    ):
        fail(f"{row_id}: process project/output hashes do not bind artifacts")
    if row["intentional_noop"]:
        if comparison["mismatched_values"] != 0:
            fail(f"{row_id}: intentional no-op changed raw FLOAT32 words")
    elif comparison["mismatched_values"] == 0:
        fail(f"{row_id}: positive-effect row is an unmarked no-op")
    return evidence_data["process"]


def verify_fail_row(
    files: dict[str, Path],
    row: dict[str, Any],
    batch_sha: str,
    status_record: dict[str, Any],
) -> list[str]:
    row_id = row["row_id"]
    relative = f"evidence/{row_id}/failure.json"
    path = files.get(relative)
    if path is None:
        fail(f"{row_id}: terminal fail row lacks {relative}")
    data = require_binding(path, load_json(path), "failure", row, batch_sha)
    require_exact_keys(
        data,
        {"failure_codes", "stage", "message", "diagnostic_paths"},
        f"{row_id}.failure.data",
    )
    codes = require_unique_nonempty_strings(
        data.get("failure_codes"),
        f"{row_id}.failure_codes",
    )
    diagnostic_paths = data.get("diagnostic_paths")
    permitted_diagnostic = f"diagnostics/{row_id}/failure.png"
    if (
        not strict_equal(codes, status_record["failure_codes"])
        or not isinstance(data["stage"], str)
        or not data["stage"]
        or not isinstance(data["message"], str)
        or not data["message"]
        or diagnostic_paths not in ([], [permitted_diagnostic])
    ):
        fail(f"{row_id}: failure record is incomplete or status-inconsistent")
    for relative_path in diagnostic_paths:
        diagnostic_path = files.get(relative_path)
        if diagnostic_path is None:
            fail(f"{row_id}: declared failure diagnostic is missing: {relative_path}")
        dimensions = verify_png_container(
            diagnostic_path,
            f"{row_id}.failure.png",
        )
        read_rgba8_png(diagnostic_path, dimensions)
    return diagnostic_paths


def verify_cross_row(
    files: dict[str, Path],
    rows_by_id: dict[str, dict[str, Any]],
    status_by_id: dict[str, dict[str, Any]],
    batch_sha: str,
) -> None:
    relative = "cross_row/olmkirakira_controlled_matrix.json"
    path = files.get(relative)
    if path is None:
        fail(f"cross-row report missing: {relative}")
    report = load_json(path)
    require_exact_keys(
        report,
        {
            "schema_version",
            "campaign_id",
            "batch_manifest_sha256",
            "comparison_count",
            "comparisons",
        },
        relative,
    )
    if (
        not is_exact_int(report["schema_version"], 1)
        or report["campaign_id"] != CAMPAIGN_ID
        or report["batch_manifest_sha256"] != batch_sha
        or not is_exact_int(report["comparison_count"], 21)
        or not isinstance(report["comparisons"], list)
        or len(report["comparisons"]) != 21
    ):
        fail("cross-row report header/cardinality mismatch")
    definition = load_json(
        files["case_definitions/olmkirakira_controlled_ramps_off_matrix.json"]
    )
    expected = {
        (pair["pair_id"], depth): pair
        for pair in definition["pair_invariants"]
        for depth in (8, 16, 32)
    }
    seen: set[tuple[str, int]] = set()
    for record in report["comparisons"]:
        if not isinstance(record, dict):
            fail("cross-row comparison must be an object")
        pair_id, depth = record.get("pair_id"), record.get("depth")
        if (
            not isinstance(pair_id, str)
            or not pair_id
            or type(depth) is not int
            or depth not in (8, 16, 32)
        ):
            fail("cross-row pair_id/depth has the wrong type")
        key = (pair_id, depth)
        pair = expected.get(key)
        if pair is None or key in seen:
            fail(f"unexpected or duplicate cross-row comparison: {key}")
        seen.add(key)
        left_matches = [
            row_id
            for row_id, row in rows_by_id.items()
            if row["plugin"] == "OLMKiraKira"
            and row["case_id"] == pair["left_case_id"]
            and row["depth"] == depth
        ]
        right_matches = [
            row_id
            for row_id, row in rows_by_id.items()
            if row["plugin"] == "OLMKiraKira"
            and row["case_id"] == pair["right_case_id"]
            and row["depth"] == depth
        ]
        if len(left_matches) != 1 or len(right_matches) != 1:
            fail(f"cross-row semantic row resolution is not unique: {key}")
        left_id, right_id = left_matches[0], right_matches[0]
        if (
            record.get("left_row_id") != left_id
            or record.get("right_row_id") != right_id
        ):
            fail(f"cross-row row binding mismatch: {key}")
        both_pass = (
            status_by_id[left_id]["terminal_status"] == "pass"
            and status_by_id[right_id]["terminal_status"] == "pass"
        )
        if not both_pass:
            if (
                set(record)
                != {
                    "pair_id",
                    "depth",
                    "left_row_id",
                    "right_row_id",
                    "terminal_status",
                    "failure_codes",
                }
                or record.get("terminal_status") != "fail"
            ):
                fail(f"cross-row comparison must fail when a member row failed: {key}")
            require_unique_nonempty_strings(
                record.get("failure_codes"),
                f"cross-row {pair_id}/{depth} failure_codes",
            )
            continue
        pass_keys = {
            "pair_id",
            "depth",
            "left_row_id",
            "right_row_id",
            "terminal_status",
            "failure_codes",
            "left_source_sha256",
            "right_source_sha256",
            "left_parameter_sha256",
            "right_parameter_sha256",
            "left_effect_on_sha256",
            "right_effect_on_sha256",
            "decoded_word_count",
            "mismatched_words",
            "max_raw_u32_delta",
        }
        if (
            set(record) != pass_keys
            or record.get("terminal_status") != "pass"
            or not strict_equal(record.get("failure_codes"), [])
            or any(
                type(record.get(field)) is not int
                for field in (
                    "decoded_word_count",
                    "mismatched_words",
                    "max_raw_u32_delta",
                )
            )
        ):
            fail(f"cross-row comparison unexpectedly failed: {key}")
        left_path = files[f"outputs/{left_id}/effect_on.exr"]
        right_path = files[f"outputs/{right_id}/effect_on.exr"]
        left_params = require_binding(
            files[f"evidence/{left_id}/params_expected.json"],
            load_json(files[f"evidence/{left_id}/params_expected.json"]),
            "params_expected",
            rows_by_id[left_id],
            batch_sha,
        )
        right_params = require_binding(
            files[f"evidence/{right_id}/params_expected.json"],
            load_json(files[f"evidence/{right_id}/params_expected.json"]),
            "params_expected",
            rows_by_id[right_id],
            batch_sha,
        )
        comparison = compare_float_exr(left_path, right_path)
        if (
            record.get("left_source_sha256") != rows_by_id[left_id]["source_sha256"]
            or record.get("right_source_sha256")
            != rows_by_id[right_id]["source_sha256"]
            or record.get("left_parameter_sha256")
            != canonical_json_sha256(left_params["values"])
            or record.get("right_parameter_sha256")
            != canonical_json_sha256(right_params["values"])
            or record.get("left_effect_on_sha256") != sha256(left_path)
            or record.get("right_effect_on_sha256") != sha256(right_path)
            or record.get("decoded_word_count")
            != rows_by_id[left_id]["comp"]["width"]
            * rows_by_id[left_id]["comp"]["height"]
            * 4
            or record.get("mismatched_words") != comparison["mismatched_values"]
            or record.get("max_raw_u32_delta") != comparison["max_raw_u32_delta"]
            or comparison["mismatched_values"] <= 0
        ):
            fail(f"cross-row raw differential mismatch: {key}")
    if seen != set(expected):
        fail("cross-row comparison set is incomplete")


def resolve_unique_row(
    rows_by_id: dict[str, dict[str, Any]],
    plugin: str,
    case_id: str,
    depth: int,
    label: str,
) -> dict[str, Any]:
    matches = [
        row
        for row in rows_by_id.values()
        if row.get("plugin") == plugin
        and row.get("case_id") == case_id
        and row.get("depth") == depth
    ]
    if len(matches) != 1:
        fail(f"{label}: semantic row resolution is not unique")
    return matches[0]


def diagnostic_row_binding(
    files: dict[str, Path],
    row: dict[str, Any],
) -> dict[str, Any]:
    row_id = row["row_id"]
    process_path = files[f"evidence/{row_id}/process.json"]
    process = load_json(process_path)["data"]
    return {
        "row_id": row_id,
        "execution_row_sha256": row["execution_row_sha256"],
        "case_contract_sha256": row["case_contract_sha256"],
        "source_sha256": row["source_sha256"],
        "aex_sha256": row["aex_sha256"],
        "project_sha256": sha256(files[f"projects/{row_id}.aep"]),
        "effect_on_sha256": sha256(files[f"outputs/{row_id}/effect_on.exr"]),
        "process_attestation_sha256": sha256(process_path),
        "render_queue_item_id": process["outputs"]["effect_on"][
            "render_queue_item_id"
        ],
    }


def verify_targeted_diagnostics(
    files: dict[str, Path],
    rows_by_id: dict[str, dict[str, Any]],
    status_by_id: dict[str, dict[str, Any]],
    batch_sha: str,
) -> None:
    radial = resolve_unique_row(
        rows_by_id,
        "OLMRadialBlur",
        "olmradialblur__canonical_20260604_case_0010_tiny_rotation",
        8,
        "RadialBlur targeted witness",
    )
    if status_by_id[radial["row_id"]]["terminal_status"] == "pass":
        base = "diagnostics/OLMRadialBlur/8bpc/canonical_20260604_case0010"
        png = files.get(f"{base}/effect_on.png")
        witness = files.get(f"{base}/witness_1614_6.json")
        if png is None or witness is None:
            fail("RadialBlur pass row lacks its targeted PNG/witness")
        _, _, png_pixels = read_rgba8_png(
            png,
            (radial["comp"]["width"], radial["comp"]["height"]),
        )
        value = load_json(witness)
        require_exact_keys(
            value,
            {
                "schema_version",
                "kind",
                "binding",
                "effect_on_exr",
                "effect_on_png",
                "probe",
                "output_module_settings_sha256",
                "diagnostic_output_module_settings_sha256",
                "process_attestation_sha256",
                "render_queue_item_id",
            },
            str(witness),
        )
        binding = value.get("binding")
        if not isinstance(binding, dict):
            fail("RadialBlur witness binding missing")
        effect_on_exr = value.get("effect_on_exr")
        effect_on_png = value.get("effect_on_png")
        probe = value.get("probe")
        if not all(
            isinstance(record, dict)
            for record in (effect_on_exr, effect_on_png, probe)
        ):
            fail("RadialBlur witness nested record missing")
        require_exact_keys(
            effect_on_exr,
            {"path", "sha256"},
            "RadialBlur witness effect_on_exr",
        )
        require_exact_keys(
            effect_on_png,
            {
                "path",
                "sha256",
                "same_effect_on_render_queue_item",
                "same_process",
            },
            "RadialBlur witness effect_on_png",
        )
        require_exact_keys(
            probe,
            {
                "x",
                "y",
                "physical_channel_order",
                "exr_float32",
                "exr_raw_u32",
                "logical_rgba_float32",
                "png_rgba8",
            },
            "RadialBlur witness probe",
        )
        expected_binding = {
            "campaign_id": CAMPAIGN_ID,
            "row_id": radial["row_id"],
            "batch_manifest_sha256": batch_sha,
            "execution_row_sha256": radial["execution_row_sha256"],
            "case_contract_sha256": radial["case_contract_sha256"],
        }
        if binding != expected_binding:
            fail("RadialBlur witness binding mismatch")
        probe_x, probe_y = 1614, 6
        planes, exr_width, exr_height, _ = read_planes_with_layout(
            files[f"outputs/{radial['row_id']}/effect_on.exr"]
        )
        if (
            exr_width != radial["comp"]["width"]
            or exr_height != radial["comp"]["height"]
        ):
            fail("RadialBlur witness EXR dimensions drifted")
        exr_offset = (probe_y * exr_width + probe_x) * 4
        physical_names = ("A", "B", "G", "R")
        exr_bytes = [
            planes[name][exr_offset : exr_offset + 4]
            for name in physical_names
        ]
        exr_u32 = [struct.unpack("<I", sample)[0] for sample in exr_bytes]
        exr_float = [struct.unpack("<f", sample)[0] for sample in exr_bytes]
        logical_rgba = [exr_float[index] for index in (3, 2, 1, 0)]
        png_offset = (probe_y * exr_width + probe_x) * 4
        png_rgba = list(png_pixels[png_offset : png_offset + 4])
        if (
            not is_exact_int(value.get("schema_version"), 1)
            or value.get("kind") != "olmradialblur_tiny_rotation_png_probe_v1"
            or probe["x"] != 1614
            or probe["y"] != 6
            or probe["physical_channel_order"] != list(physical_names)
            or not json_number_equal(probe["exr_float32"], exr_float)
            or not strict_equal(probe["exr_raw_u32"], exr_u32)
            or not json_number_equal(
                probe["logical_rgba_float32"],
                logical_rgba,
            )
            or not strict_equal(probe["png_rgba8"], png_rgba)
            or any(
                not is_finite_float32_json(component)
                for field in ("exr_float32", "logical_rgba_float32")
                for component in probe[field]
            )
            or any(
                type(component) is not int or not 0 <= component <= 0xFFFFFFFF
                for component in probe["exr_raw_u32"]
            )
            or any(
                type(component) is not int or not 0 <= component <= 255
                for component in probe["png_rgba8"]
            )
            or effect_on_png["path"] != f"{base}/effect_on.png"
            or effect_on_png["sha256"] != sha256(png)
            or effect_on_exr["path"]
            != f"outputs/{radial['row_id']}/effect_on.exr"
            or effect_on_exr["sha256"]
            != sha256(files[f"outputs/{radial['row_id']}/effect_on.exr"])
            or effect_on_png["same_process"] is not True
            or effect_on_png["same_effect_on_render_queue_item"] is not True
            or value.get("output_module_settings_sha256")
            != load_json(
                files[
                    f"evidence/{radial['row_id']}/output_module_after.json"
                ]
            )["data"]["branches"]["effect_on"]["settings_serialization_sha256"]
            or value.get("diagnostic_output_module_settings_sha256")
            != load_json(files[f"evidence/{radial['row_id']}/process.json"])[
                "data"
            ]["diagnostic_outputs"]["effect_on_png"][
                "settings_serialization_sha256"
            ]
            or value.get("process_attestation_sha256")
            != sha256(files[f"evidence/{radial['row_id']}/process.json"])
            or value.get("render_queue_item_id")
            != load_json(files[f"evidence/{radial['row_id']}/process.json"])[
                "data"
            ]["outputs"]["effect_on"]["render_queue_item_id"]
        ):
            fail("RadialBlur witness payload mismatch")
    kira_targets = (
        (
            "kk_mapped_bm2_mm1_ray_f0_a0_opaque",
            "0x18114e3e9",
        ),
        (
            "kk_mapped_bm2_mm2_ray_f0_a0_opaque",
            "0x18114e287",
        ),
    )
    for case_id, rva in kira_targets:
        row = resolve_unique_row(
            rows_by_id,
            "OLMKiraKira",
            case_id,
            8,
            f"{case_id} targeted writer trace",
        )
        if status_by_id[row["row_id"]]["terminal_status"] != "pass":
            continue
        base = f"diagnostics/OLMKiraKira/8bpc/{case_id}"
        png = files.get(f"{base}/effect_on.png")
        trace_path = files.get(f"{base}/writer_trace.json")
        if png is None or trace_path is None:
            fail(f"{case_id}: targeted Kira PNG/trace missing")
        _, _, png_pixels = read_rgba8_png(
            png,
            (row["comp"]["width"], row["comp"]["height"]),
        )
        trace = load_json(trace_path)
        require_exact_keys(
            trace,
            {
                "schema_version",
                "kind",
                "binding",
                "writer_call_rva",
                "xy",
                "mxcsr_raw_u32",
                "loaded_aex_sha256",
                "source_sha256",
                "effect_on_exr_sha256",
                "effect_on_png_sha256",
                "same_effect_on_render_queue_item",
                "same_process",
                "output_module_settings_sha256",
                "diagnostic_output_module_settings_sha256",
                "process_attestation_sha256",
                "render_queue_item_id",
                "records",
            },
            str(trace_path),
        )
        binding = trace.get("binding")
        expected_binding = {
            "campaign_id": CAMPAIGN_ID,
            "row_id": row["row_id"],
            "batch_manifest_sha256": batch_sha,
            "execution_row_sha256": row["execution_row_sha256"],
            "case_contract_sha256": row["case_contract_sha256"],
        }
        records = trace.get("records")
        record_fields = {
            "owner_plus_0x44",
            "owner_plus_0x128_pointer",
            "owner_plus_0x190_pointer",
            "source_rgba_f32",
            "glow_rgba_f32",
            "xmm0_3",
            "destination_rsp_plus_0x20",
            "post_writer_argb8",
            "exported_rgba8",
        }
        xy_offset = (118 * row["comp"]["width"] + 934) * 4
        exported_rgba8 = list(png_pixels[xy_offset : xy_offset + 4])
        four_component_fields = (
            "source_rgba_f32",
            "glow_rgba_f32",
            "xmm0_3",
            "post_writer_argb8",
            "exported_rgba8",
        )
        expected_owner_mode = 1 if rva == "0x18114e3e9" else 2
        if (
            not is_exact_int(trace.get("schema_version"), 1)
            or binding != expected_binding
            or trace.get("kind") != "olmkirakira_pf8_outer_writer_trace_v1"
            or trace.get("writer_call_rva") != rva
            or trace.get("xy") != [934, 118]
            or type(trace.get("mxcsr_raw_u32")) is not int
            or not 0 <= trace["mxcsr_raw_u32"] <= 0xFFFFFFFF
            or trace["mxcsr_raw_u32"] & 0xE040
            or trace["mxcsr_raw_u32"] & 0x1F80 != 0x1F80
            or trace.get("loaded_aex_sha256") != row["aex_sha256"]
            or trace.get("source_sha256") != row["source_sha256"]
            or trace.get("effect_on_exr_sha256")
            != sha256(files[f"outputs/{row['row_id']}/effect_on.exr"])
            or trace.get("effect_on_png_sha256") != sha256(png)
            or trace.get("same_process") is not True
            or trace.get("same_effect_on_render_queue_item") is not True
            or trace.get("output_module_settings_sha256")
            != load_json(
                files[f"evidence/{row['row_id']}/output_module_after.json"]
            )["data"]["branches"]["effect_on"]["settings_serialization_sha256"]
            or trace.get("diagnostic_output_module_settings_sha256")
            != load_json(files[f"evidence/{row['row_id']}/process.json"])[
                "data"
            ]["diagnostic_outputs"]["effect_on_png"][
                "settings_serialization_sha256"
            ]
            or trace.get("process_attestation_sha256")
            != sha256(files[f"evidence/{row['row_id']}/process.json"])
            or trace.get("render_queue_item_id")
            != load_json(files[f"evidence/{row['row_id']}/process.json"])[
                "data"
            ]["outputs"]["effect_on"]["render_queue_item_id"]
            or not isinstance(records, dict)
            or set(records) != record_fields
            or any(
                not isinstance(records[field], list)
                or len(records[field]) != 4
                for field in four_component_fields
            )
            or type(records["owner_plus_0x44"]) is not int
            or records["owner_plus_0x44"] != expected_owner_mode
            or not pointer_json_value(records["owner_plus_0x128_pointer"])
            or not pointer_json_value(records["owner_plus_0x190_pointer"])
            or not pointer_json_value(records["destination_rsp_plus_0x20"])
            or any(
                not is_finite_float32_json(component)
                for field in ("source_rgba_f32", "glow_rgba_f32", "xmm0_3")
                for component in records[field]
            )
            or any(
                not 0.0 <= f32_round(component) <= 1.0
                for component in records["xmm0_3"]
            )
            or any(
                type(component) is not int or not 0 <= component <= 255
                for field in (
                    "post_writer_argb8",
                    "exported_rgba8",
                )
                for component in records[field]
            )
        ):
            fail(f"{case_id}: targeted Kira trace binding mismatch")
        writer_rgba = [
            math.trunc(
                f32_round(f32_round(component) * f32_round(255.0))
            )
            for component in records["xmm0_3"]
        ]
        writer_argb = [
            writer_rgba[3],
            writer_rgba[0],
            writer_rgba[1],
            writer_rgba[2],
        ]
        if (
            not strict_equal(records["post_writer_argb8"], writer_argb)
            or not strict_equal(records["exported_rgba8"], writer_rgba)
            or not strict_equal(records["exported_rgba8"], exported_rgba8)
        ):
            fail(f"{case_id}: PF8 ARGB writer/export byte mismatch")
        expected_xmm = expected_kira_pf8_xmm(
            records["source_rgba_f32"],
            records["glow_rgba_f32"],
            expected_owner_mode,
        )
        if not strict_equal(
            float32_words(records["xmm0_3"], f"{case_id}.xmm0_3"),
            float32_words(expected_xmm, f"{case_id}.expected_xmm0_3"),
        ):
            fail(f"{case_id}: PF8 source/glow compose does not produce XMM")
    pf32_root = "diagnostics/OLMKiraKira/32bpc/controlled_matrix"
    for name, contract in PF32_DIAGNOSTICS.items():
        expected_rows = [
            row
            for case_id in contract["case_ids"]
            for row in rows_by_id.values()
            if row["plugin"] == "OLMKiraKira"
            and row["depth"] == 32
            and row["case_id"] == case_id
        ]
        if len(expected_rows) != 2:
            fail(f"Kira PF32 diagnostic row binding drift: {name}")
        if not all(
            status_by_id[row["row_id"]]["terminal_status"] == "pass"
            for row in expected_rows
        ):
            continue
        relative = f"{pf32_root}/{name}"
        path = files.get(relative)
        if path is None or path.stat().st_size <= 0:
            fail(f"Kira PF32 controlled diagnostic missing: {relative}")
        value = load_json(path)
        require_exact_keys(
            value,
            {
                "schema_version",
                "kind",
                "campaign_id",
                "batch_manifest_sha256",
                "rows",
                "data",
            },
            str(path),
        )
        expected_bindings = [
            diagnostic_row_binding(files, row) for row in expected_rows
        ]
        expected_rows_by_id = {row["row_id"]: row for row in expected_rows}
        action_maps = [
            {
                action["match_name"]: action
                for action in row["parameter_writes"]
                if action["action"] == "set"
            }
            for row in expected_rows
        ]
        differing_controls = [
            match_name
            for match_name in set(action_maps[0]) | set(action_maps[1])
            if match_name not in action_maps[0]
            or match_name not in action_maps[1]
            or not parameter_action_values_equal(
                action_maps[0][match_name],
                action_maps[1][match_name],
            )
        ]
        if len(differing_controls) != 1:
            fail(f"Kira PF32 diagnostic is not a one-control pair: {name}")
        differing_control = differing_controls[0]
        data = value["data"]
        if not isinstance(data, dict):
            fail(f"Kira PF32 controlled diagnostic data is not an object: {name}")
        require_exact_keys(
            data,
            {"instrumentation", "trace_records"},
            f"{name}.data",
        )
        instrumentation = data["instrumentation"]
        trace_records = data["trace_records"]
        if not isinstance(instrumentation, dict):
            fail(f"Kira PF32 instrumentation is not an object: {name}")
        require_exact_keys(
            instrumentation,
            {
                "capture_method",
                "trace_tool",
                "trace_session_id",
                "declared_only_different_match_name",
                "trace_point_contract",
                "process_attestation_sha256_by_row",
            },
            f"{name}.instrumentation",
        )
        expected_process_hashes = {
            binding["row_id"]: binding["process_attestation_sha256"]
            for binding in expected_bindings
        }
        record_keys = {"row_id", "record_index", "event", "payload"}
        payload_keys = {
            "x",
            "y",
            "control_match_name",
            "control_value",
            "input_rgba_f32",
            "stage_rgba_f32",
        }
        if (
            not is_exact_int(value["schema_version"], 1)
            or value["kind"] != contract["kind"]
            or value["campaign_id"] != CAMPAIGN_ID
            or value["batch_manifest_sha256"] != batch_sha
            or not strict_equal(value["rows"], expected_bindings)
            or any(
                not isinstance(instrumentation[field], str)
                or not instrumentation[field]
                for field in ("capture_method", "trace_tool", "trace_session_id")
            )
            or instrumentation["declared_only_different_match_name"]
            != differing_control
            or instrumentation["trace_point_contract"]
            != "same_xy_same_input_one_control_delta_with_different_stage"
            or not strict_equal(
                instrumentation["process_attestation_sha256_by_row"],
                expected_process_hashes,
            )
            or not isinstance(trace_records, list)
            or len(trace_records) < len(expected_rows)
            or any(
                not isinstance(record, dict)
                or set(record) != record_keys
                or record["row_id"] not in expected_process_hashes
                or type(record["record_index"]) is not int
                or record["record_index"] < 0
                or record["event"] != contract["event"]
                or not isinstance(record["payload"], dict)
                or set(record["payload"]) != payload_keys
                or type(record["payload"]["x"]) is not int
                or record["payload"]["x"] < 0
                or record["payload"]["x"]
                >= expected_rows_by_id[record["row_id"]]["comp"]["width"]
                or type(record["payload"]["y"]) is not int
                or record["payload"]["y"] < 0
                or record["payload"]["y"]
                >= expected_rows_by_id[record["row_id"]]["comp"]["height"]
                or record["payload"]["control_match_name"] != differing_control
                or not trace_control_value_matches(
                    record["payload"]["control_value"],
                    action_maps[
                        0
                        if record["row_id"] == expected_rows[0]["row_id"]
                        else 1
                    ][differing_control],
                    f"{name}.{record['row_id']}.control_value",
                )
                or any(
                    not isinstance(record["payload"][field], list)
                    or len(record["payload"][field]) != 4
                    or any(
                        not is_finite_float32_json(component)
                        for component in record["payload"][field]
                    )
                    for field in ("input_rgba_f32", "stage_rgba_f32")
                )
                for record in trace_records
            )
            or {
                record["row_id"]
                for record in trace_records
                if isinstance(record, dict) and isinstance(record.get("row_id"), str)
            }
            != set(expected_process_hashes)
            or len(
                {
                    (record["row_id"], record["record_index"])
                    for record in trace_records
                }
            )
            != len(trace_records)
        ):
            fail(f"Kira PF32 controlled diagnostic binding mismatch: {name}")
        records_by_row = {
            row["row_id"]: sorted(
                (
                    record
                    for record in trace_records
                    if record["row_id"] == row["row_id"]
                ),
                key=lambda record: record["record_index"],
            )
            for row in expected_rows
        }
        left_records = records_by_row[expected_rows[0]["row_id"]]
        right_records = records_by_row[expected_rows[1]["row_id"]]
        if (
            len(left_records) != len(right_records)
            or not left_records
            or any(
                left["record_index"] != right["record_index"]
                or left["payload"]["x"] != right["payload"]["x"]
                or left["payload"]["y"] != right["payload"]["y"]
                or not strict_equal(
                    float32_words(
                        left["payload"]["input_rgba_f32"],
                        f"{name}.left.input_rgba_f32",
                    ),
                    float32_words(
                        right["payload"]["input_rgba_f32"],
                        f"{name}.right.input_rgba_f32",
                    ),
                )
                for left, right in zip(left_records, right_records, strict=True)
            )
            or not any(
                not strict_equal(
                    float32_words(
                        left["payload"]["stage_rgba_f32"],
                        f"{name}.left.stage_rgba_f32",
                    ),
                    float32_words(
                        right["payload"]["stage_rgba_f32"],
                        f"{name}.right.stage_rgba_f32",
                    ),
                )
                for left, right in zip(left_records, right_records, strict=True)
            )
        ):
            fail(f"Kira PF32 differential trace predicate failed: {name}")
    kernel_rows = [
        row
        for row in rows_by_id.values()
        if row["plugin"] == "OLMKiraKira"
        and row["depth"] == 32
        and row["case_id"]
        in {
            "kk_mapped_bm3_mm1_hi_r5_white_opaque",
            "kk_mapped_bm3_mm1_hi_r5_orange_opaque",
            "kk_mapped_bm4_mm1_hi_r5_orange_opaque",
        }
    ]
    if len(kernel_rows) != 3:
        fail("Kira Gaussian kernel row binding drift")
    if all(
        status_by_id[row["row_id"]]["terminal_status"] == "pass"
        for row in kernel_rows
    ):
        binary_relative = f"{pf32_root}/gaussian_kernel_21_f32_le.bin"
        json_relative = f"{pf32_root}/gaussian_kernel_21_f32_le.json"
        kernel = files.get(binary_relative)
        kernel_json_path = files.get(json_relative)
        if (
            kernel is None
            or kernel_json_path is None
            or kernel.stat().st_size != 84
        ):
            fail("Kira Gaussian kernel dump/JSON missing or not exactly 84 bytes")
        kernel_json = load_json(kernel_json_path)
        require_exact_keys(
            kernel_json,
            {
                "schema_version",
                "kind",
                "campaign_id",
                "batch_manifest_sha256",
                "rows",
                "binary_member",
                "binary_sha256",
                "byte_count",
                "element_count",
                "encoding",
                "float32_u32_le",
            },
            str(kernel_json_path),
        )
        expected_kernel_bindings = [
            diagnostic_row_binding(files, row) for row in kernel_rows
        ]
        kernel_words = list(struct.unpack("<21I", kernel.read_bytes()))
        if (
            not is_exact_int(kernel_json["schema_version"], 1)
            or kernel_json["kind"]
            != "olmkirakira_gaussian_kernel_21_f32_le_v1"
            or kernel_json["campaign_id"] != CAMPAIGN_ID
            or kernel_json["batch_manifest_sha256"] != batch_sha
            or not strict_equal(kernel_json["rows"], expected_kernel_bindings)
            or kernel_json["binary_member"] != binary_relative
            or kernel_json["binary_sha256"] != sha256(kernel)
            or not is_exact_int(kernel_json["byte_count"], 84)
            or not is_exact_int(kernel_json["element_count"], 21)
            or kernel_json["encoding"] != "IEEE-754 binary32 little-endian"
            or not strict_equal(kernel_json["float32_u32_le"], kernel_words)
            or any(
                type(word) is not int or not 0 <= word <= 0xFFFFFFFF
                for word in kernel_json["float32_u32_le"]
            )
        ):
            fail("Kira Gaussian kernel JSON/binary binding mismatch")


def conditional_diagnostic_members(
    rows_by_id: dict[str, dict[str, Any]],
    status_by_id: dict[str, dict[str, Any]],
) -> set[str]:
    members: set[str] = set()
    radial = resolve_unique_row(
        rows_by_id,
        "OLMRadialBlur",
        "olmradialblur__canonical_20260604_case_0010_tiny_rotation",
        8,
        "RadialBlur allowlist",
    )
    if status_by_id[radial["row_id"]]["terminal_status"] == "pass":
        base = "diagnostics/OLMRadialBlur/8bpc/canonical_20260604_case0010"
        members.update({f"{base}/effect_on.png", f"{base}/witness_1614_6.json"})
    for case_id in (
        "kk_mapped_bm2_mm1_ray_f0_a0_opaque",
        "kk_mapped_bm2_mm2_ray_f0_a0_opaque",
    ):
        row = resolve_unique_row(
            rows_by_id,
            "OLMKiraKira",
            case_id,
            8,
            f"{case_id} allowlist",
        )
        if status_by_id[row["row_id"]]["terminal_status"] == "pass":
            base = f"diagnostics/OLMKiraKira/8bpc/{case_id}"
            members.update({f"{base}/effect_on.png", f"{base}/writer_trace.json"})
    pf32_root = "diagnostics/OLMKiraKira/32bpc/controlled_matrix"
    for name, contract in PF32_DIAGNOSTICS.items():
        bound_rows = [
            resolve_unique_row(
                rows_by_id,
                "OLMKiraKira",
                case_id,
                32,
                f"{name} allowlist",
            )
            for case_id in contract["case_ids"]
        ]
        if all(
            status_by_id[row["row_id"]]["terminal_status"] == "pass"
            for row in bound_rows
        ):
            members.add(f"{pf32_root}/{name}")
    kernel_rows = [
        resolve_unique_row(
            rows_by_id,
            "OLMKiraKira",
            case_id,
            32,
            "Gaussian kernel allowlist",
        )
        for case_id in (
            "kk_mapped_bm3_mm1_hi_r5_white_opaque",
            "kk_mapped_bm3_mm1_hi_r5_orange_opaque",
            "kk_mapped_bm4_mm1_hi_r5_orange_opaque",
        )
    ]
    if all(
        status_by_id[row["row_id"]]["terminal_status"] == "pass"
        for row in kernel_rows
    ):
        members.update(
            {
                f"{pf32_root}/gaussian_kernel_21_f32_le.bin",
                f"{pf32_root}/gaussian_kernel_21_f32_le.json",
            }
        )
    return members


def expected_return_members(
    request_files: dict[str, Path],
    execution_rows: list[dict[str, Any]],
    status_by_id: dict[str, dict[str, Any]],
    fail_diagnostics: dict[str, list[str]],
) -> set[str]:
    allowed = set(request_files) - {"CHECKSUMS.sha256"}
    allowed.update(
        {
            "CHECKSUMS.sha256",
            "BATCH_MANIFEST.json",
            "RETURN_STATUS.json",
            "cross_row/olmkirakira_controlled_matrix.json",
        }
    )
    rows_by_id = {row["row_id"]: row for row in execution_rows}
    for row in execution_rows:
        row_id = row["row_id"]
        if status_by_id[row_id]["terminal_status"] == "pass":
            allowed.update(
                {
                    f"projects/{row_id}.aep",
                    f"outputs/{row_id}/no_effect.exr",
                    f"outputs/{row_id}/effect_on.exr",
                    *(
                        f"evidence/{row_id}/{filename}"
                        for filename in PASS_JSON_FILES
                    ),
                    *(
                        f"evidence/{row_id}/{filename}"
                        for filename in PASS_OTHER_FILES
                    ),
                }
            )
            if is_kira_authoritative_row(row):
                evidence_root = f"evidence/{row_id}"
                allowed.update(
                    {
                        f"{evidence_root}/{KIRA_PROPERTY_READBACK_FILE}",
                        f"{evidence_root}/{KIRA_LINEAGE_FILE}",
                    }
                )
                case = authoritative_kira_case(request_files, row)
                if case["mode"] == 4:
                    allowed.add(f"{evidence_root}/{KIRA_MODE4_FILE}")
        else:
            allowed.add(f"evidence/{row_id}/failure.json")
            allowed.update(fail_diagnostics[row_id])
    allowed.update(conditional_diagnostic_members(rows_by_id, status_by_id))
    return allowed


def verify_return(request_root: Path, return_root: Path) -> dict[str, Any]:
    request_files, campaign, _, execution = request_contract(request_root)
    return_files = regular_files(return_root)
    verify_checksums(return_root, return_files)
    for relative, source in request_files.items():
        if relative == "CHECKSUMS.sha256":
            continue
        returned = return_files.get(relative)
        if (
            returned is None
            or returned.stat().st_size != source.stat().st_size
            or sha256(returned) != sha256(source)
        ):
            fail(f"return altered/omitted outbound member: {relative}")
    batch_path = return_files.get("BATCH_MANIFEST.json")
    status_path = return_files.get("RETURN_STATUS.json")
    if batch_path is None or status_path is None:
        fail("BATCH_MANIFEST.json or RETURN_STATUS.json missing")
    batch = load_json(batch_path)
    require_exact_keys(
        batch,
        {
            "schema_version",
            "campaign_id",
            "execution_rows_sha256",
            "row_inventory_sha256",
            "campaign_manifest_sha256",
            "row_count",
            "rows",
        },
        "BATCH_MANIFEST.json",
    )
    execution_rows = execution["rows"]
    if (
        not is_exact_int(batch["schema_version"], 1)
        or batch["campaign_id"] != CAMPAIGN_ID
        or batch["execution_rows_sha256"]
        != sha256(request_files["EXECUTION_ROWS.json"])
        or batch["row_inventory_sha256"] != sha256(request_files["ROW_INVENTORY.json"])
        or batch["campaign_manifest_sha256"]
        != sha256(request_files["CAMPAIGN_MANIFEST.json"])
        or not is_exact_int(batch["row_count"], len(execution_rows))
        or not strict_equal(batch["rows"], execution_rows)
    ):
        fail("BATCH_MANIFEST is not an exact outbound execution-row binding")
    batch_sha = canonical_json_sha256(batch)
    status = load_json(status_path)
    require_exact_keys(
        status,
        {
            "schema_version",
            "campaign_id",
            "batch_manifest_sha256",
            "row_count",
            "rows",
        },
        "RETURN_STATUS.json",
    )
    status_rows = status["rows"]
    if (
        not is_exact_int(status["schema_version"], 1)
        or status["campaign_id"] != CAMPAIGN_ID
        or status["batch_manifest_sha256"] != batch_sha
        or not is_exact_int(status["row_count"], len(execution_rows))
        or not isinstance(status_rows, list)
        or len(status_rows) != len(execution_rows)
    ):
        fail("RETURN_STATUS header/cardinality mismatch")
    rows_by_id = {row["row_id"]: row for row in execution_rows}
    status_by_id: dict[str, dict[str, Any]] = {}
    for index, (row, record) in enumerate(zip(execution_rows, status_rows, strict=True)):
        if not isinstance(record, dict):
            fail(f"RETURN_STATUS row {index} is not an object")
        require_exact_keys(
            record,
            {
                "row_id",
                "terminal_status",
                "execution_row_sha256",
                "evidence_complete",
                "outputs_complete",
                "failure_codes",
            },
            f"RETURN_STATUS.rows[{index}]",
        )
        if (
            record["row_id"] != row["row_id"]
            or record["execution_row_sha256"] != row["execution_row_sha256"]
            or record["terminal_status"] not in ("pass", "fail")
            or not isinstance(record["failure_codes"], list)
        ):
            fail(f"RETURN_STATUS row binding mismatch: {row['row_id']}")
        if record["terminal_status"] == "pass":
            if (
                record["evidence_complete"] is not True
                or record["outputs_complete"] is not True
                or not strict_equal(record["failure_codes"], [])
            ):
                fail(f"PASS status booleans/codes invalid: {row['row_id']}")
        else:
            if (
                record["evidence_complete"] is not False
                or record["outputs_complete"] is not False
            ):
                fail(f"FAIL status booleans invalid: {row['row_id']}")
            require_unique_nonempty_strings(
                record["failure_codes"],
                f"RETURN_STATUS {row['row_id']} failure_codes",
            )
        status_by_id[row["row_id"]] = record
    fail_diagnostics: dict[str, list[str]] = {}
    for row in execution_rows:
        record = status_by_id[row["row_id"]]
        if record["terminal_status"] == "fail":
            fail_diagnostics[row["row_id"]] = verify_fail_row(
                return_files,
                row,
                batch_sha,
                record,
            )
    allowed_members = expected_return_members(
        request_files,
        execution_rows,
        status_by_id,
        fail_diagnostics,
    )
    actual_members = set(return_files)
    if actual_members != allowed_members:
        fail(
            "return member allowlist mismatch "
            f"missing={sorted(allowed_members - actual_members)[:10]} "
            f"extra={sorted(actual_members - allowed_members)[:10]}"
        )
    pass_processes: list[dict[str, Any]] = []
    for row in execution_rows:
        record = status_by_id[row["row_id"]]
        if record["terminal_status"] == "pass":
            pass_processes.append(verify_pass_row(return_files, row, batch_sha))
    nonces = [process["run_nonce"] for process in pass_processes]
    process_identities = [
        (
            process["aerender"]["pid"],
            process["aerender"]["start_time_utc"],
        )
        for process in pass_processes
    ]
    if len(nonces) != len(set(nonces)):
        fail("passing rows reuse a run_nonce")
    if len(process_identities) != len(set(process_identities)):
        fail("passing rows reuse an aerender process identity")
    for noop in (row for row in execution_rows if row["intentional_noop"]):
        if status_by_id[noop["row_id"]]["terminal_status"] != "pass":
            continue
        siblings = [
            row
            for row in execution_rows
            if row["plugin"] == noop["plugin"]
            and row["depth"] == noop["depth"]
            and row["source_sha256"] == noop["source_sha256"]
            and not row["intentional_noop"]
            and status_by_id[row["row_id"]]["terminal_status"] == "pass"
        ]
        if not siblings:
            fail(f"intentional no-op lacks a passing positive sibling: {noop['row_id']}")
    verify_cross_row(return_files, rows_by_id, status_by_id, batch_sha)
    verify_targeted_diagnostics(return_files, rows_by_id, status_by_id, batch_sha)
    return {
        "status": "PASS",
        "campaign_id": CAMPAIGN_ID,
        "rows": len(execution_rows),
        "pass_rows": sum(
            record["terminal_status"] == "pass" for record in status_rows
        ),
        "fail_rows": sum(
            record["terminal_status"] == "fail" for record in status_rows
        ),
        "batch_manifest_sha256": batch_sha,
        "return_file_count": len(return_files),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--request-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--return-root", type=Path)
    parser.add_argument(
        "--self-test-request",
        action="store_true",
        help="verify only the outbound request package",
    )
    args = parser.parse_args()
    try:
        if args.self_test_request:
            files, campaign, _, execution = request_contract(
                args.request_root.resolve(strict=True)
            )
            result = {
                "status": "PASS",
                "kind": "request_self_test",
                "campaign_id": campaign["campaign_id"],
                "rows": execution["row_count"],
                "files": len(files),
            }
        else:
            if args.return_root is None:
                fail("--return-root is required unless --self-test-request is used")
            result = verify_return(
                args.request_root.resolve(strict=True),
                args.return_root.resolve(strict=True),
            )
    except (
        OSError,
        ValueError,
        OverflowError,
        RecursionError,
        TypeError,
        KeyError,
        AttributeError,
        StopIteration,
        csv.Error,
        struct.error,
        zlib.error,
        ExrVerificationError,
        VerificationError,
    ) as exc:
        print(f"[FAIL_CLOSED] {exc}")
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
