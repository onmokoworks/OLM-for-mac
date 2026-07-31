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


CAMPAIGN_ID = "olm_windows_all_plugins_reference_campaign_20260731_r4"
EXPECTED_LANE_ROWS = {
    "OLMDistanceGradation": 99,
    "OLMDirectionalBlur": 54,
    "OLMRadialBlur": 18,
    "OLMKiraKira": 30,
    "OLMSmoother v1": 19,
    "ColorKeep": 9,
}
EXPECTED_TOTAL_ROWS = sum(EXPECTED_LANE_ROWS.values())
EXPECTED_SCHEMA_FILES = {
    "BATCH_MANIFEST.schema.json",
    "EVIDENCE_BINDING.schema.json",
    "RETURN_STATUS.schema.json",
    "OLMKIRAKIRA_CROSS_ROW.schema.json",
    "OLMRADIALBLUR_WITNESS.schema.json",
    "OLMKIRAKIRA_WRITER_TRACE.schema.json",
    "OLMKIRAKIRA_PF32_TRACE.schema.json",
    "OLMKIRAKIRA_GAUSSIAN_KERNEL.schema.json",
}
EXPECTED_SCHEMA_SHA256 = {
    "BATCH_MANIFEST.schema.json": "e1c1c0da472de21687db303ce8aa17b7c4382754e276e95f771955b8f71c4e50",
    "EVIDENCE_BINDING.schema.json": "8d74613b654ba22d764ef0bd19ee0364559e0ba86aeaf7f14516f3a41436a1ed",
    "OLMKIRAKIRA_CROSS_ROW.schema.json": "23853809ad2075cceb7bf81f1a72c481b8ccab9815da6f71cddc9466edc96595",
    "OLMKIRAKIRA_GAUSSIAN_KERNEL.schema.json": "37b1a6628f7a3b594d588d36fa3c48a6c2c775a8ed97cb838d2f98bf806979e0",
    "OLMKIRAKIRA_PF32_TRACE.schema.json": "f68aa194232473dc1561bab11f40a5d651d81aa2af19f9cfb301d053ed12427b",
    "OLMKIRAKIRA_WRITER_TRACE.schema.json": "1768bdc167b40949bce93d6ec2dcded3978334bfffe5eb5fa7fee8ec1816eb20",
    "OLMRADIALBLUR_WITNESS.schema.json": "2687d2054e9dabf77f3a2066129505d2ffb514c8a6845089da1fc039996ee4aa",
    "RETURN_STATUS.schema.json": "a51f97277ccf2792b9b86e03f7cdfd87de78f46c34f2632097890f9b967de57d",
}
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
        require_exact_keys(
            project_contract,
            {
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
            },
            f"{row_id}.project_contract",
        )
        require_exact_keys(
            comp,
            {
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
            },
            f"{row_id}.comp",
        )
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
            or comp["frame"] != 24
            or type(comp["time_seconds"]) is not float
            or comp["time_seconds"] != 1.0
            or type(comp["duration_seconds"]) is not float
            or comp["duration_seconds"] != 2.0
            or type(comp["render_time_span_start_seconds"]) is not float
            or comp["render_time_span_start_seconds"] != 1.0
            or type(comp["render_time_span_duration_seconds"]) is not float
            or comp["render_time_span_duration_seconds"] != 1.0 / 24.0
            or not strict_equal(comp["resolution_factor"], [1, 1])
            or not strict_equal(comp["source_layer_scale"], [100.0, 100.0])
            or comp["source_layer_centered"] is not True
            or type(comp["source_layer_index"]) is not int
            or comp["source_layer_index"] != 1
            or type(comp["num_layers"]) is not int
            or comp["num_layers"] != 1
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
        require_exact_keys(
            interpretation,
            {
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
            },
            f"{row_id}.input_interpretation",
        )
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
    require_exact_keys(
        observed,
        {
            "project_return_member",
            "project_sha256",
            "run_nonce",
            "source",
            "comp",
            "source_layer",
            "effect",
            "render_queue_items",
        },
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
    require_exact_keys(
        source_layer,
        {
            "index",
            "source_item_id",
            "scale",
            "centered",
            "effect_parade_count_before_add",
            "effect_parade_count_after_add",
        },
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
        require_exact_keys(
            record,
            {
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
            },
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
        ):
            fail(f"{label}: {branch} render-queue observation mismatch")
    if (
        material_settings_sha256_by_branch["no_effect"]
        != material_settings_sha256_by_branch["effect_on"]
    ):
        fail(f"{label}: RQ material settings differ beyond Effects mode")
    interpretation = row["project_contract"]["input_interpretation"]
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
