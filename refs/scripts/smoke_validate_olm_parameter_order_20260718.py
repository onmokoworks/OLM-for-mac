#!/usr/bin/env python3
"""Regression test for the Windows/Mac parameter-order contract.

This intentionally checks the three places that must move together when a
PARAMS_SETUP order is corrected: the Windows fresh-instance property order,
the Mac enum/render indices, and the disk IDs passed by ParamsSetup.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULTS = ROOT / "refs/win_references/olm_fresh_instance_defaults_20260629/OLMmulti-effectdefaultcapture/reference_manifest.json"
RANGES = ROOT / "refs/win_references/olm_fresh_instance_ranges_20260629/OLMmulti-effectrangecapture/reference_manifest.json"


def manifest_effect(path: Path, effect_name: str) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    for case in data["cases"]:
        for effect in case.get("effects", []):
            if effect.get("name") == effect_name:
                return effect
    raise AssertionError(f"missing {effect_name} in {path}")


def manifest_rows(effect: dict) -> list[dict]:
    return [row for row in effect["params"] if row.get("property_index", 0) >= 1]


def suffix(match_name: str) -> int:
    return int(match_name.rsplit("-", 1)[1], 10)


def first_enum_values(header: Path) -> dict[str, int]:
    text = header.read_text(encoding="utf-8")
    block = re.search(r"enum\s*\{(.*?)\n\};", text, re.S)
    assert block, f"first enum missing in {header}"
    values: dict[str, int] = {}
    current = -1
    for raw in block.group(1).split(","):
        item = raw.strip()
        item = re.sub(r"/\*.*?\*/", "", item, flags=re.S).strip()
        if not item or item.startswith("//"):
            continue
        match = re.match(r"([A-Z0-9_]+)(?:\s*=\s*(\d+))?", item)
        if not match:
            continue
        name, explicit = match.groups()
        if "=" in item and explicit is None:
            continue
        current = int(explicit) if explicit is not None else current + 1
        values[name] = current
    return values


def header_constants(header: Path, names: list[str]) -> dict[str, int]:
    text = header.read_text(encoding="utf-8")
    values = {}
    for name in names:
        match = re.search(rf"\b{name}\s*=\s*(0x[0-9a-fA-F]+|\d+)", text)
        assert match, f"missing disk constant {name}"
        values[name] = int(match.group(1), 0)
    return values


def registration_body(source: Path) -> str:
    text = source.read_text(encoding="utf-8")
    start = text.index("ParamsSetup(")
    end = text.index("out_data->num_params", start)
    return text[start:end]


def assert_registration_order(source: Path, tokens: list[str]) -> None:
    body = registration_body(source)
    positions = []
    for token in tokens:
        match = re.search(rf"(?<![A-Z0-9_]){re.escape(token)}(?![A-Z0-9_])", body)
        position = match.start() if match else -1
        assert position >= 0, f"{source.name}: registration token missing: {token}"
        positions.append(position)
    assert positions == sorted(positions), f"{source.name}: registration order changed"


def assert_reference_symbols(source: Path, enum_values: dict[str, int], required: set[str], allowed_missing: set[str] = set()) -> None:
    text = source.read_text(encoding="utf-8")
    referenced = set(re.findall(r"params\[([A-Z0-9_]+)\]", text))
    unknown = referenced - set(enum_values)
    assert not unknown, f"{source.name}: unknown render index symbols: {sorted(unknown)}"
    missing = required - referenced
    assert not missing, f"{source.name}: render references missing: {sorted(missing)}"
    assert allowed_missing <= set(enum_values), f"invalid allowlist: {allowed_missing - set(enum_values)}"


def check_colorkey() -> dict:
    header = ROOT / "mac/OLMColorKey/OLMColorKey.h"
    source = ROOT / "mac/OLMColorKey/OLMColorKey.cpp"
    effect = manifest_effect(DEFAULTS, "OLM Color Key")
    range_effect = manifest_effect(RANGES, "OLM Color Key")
    assert [(r["match_name"], r["property_index"]) for r in manifest_rows(effect)] == [
        (r["match_name"], r["property_index"]) for r in manifest_rows(range_effect)
    ], "default/range manifest property order differs"

    enum_names = [
        "OLMCOLORKEY_INPUT", "OLMCOLORKEY_COLOR_KEEP", "OLMCOLORKEY_THRESHOLD",
        "OLMCOLORKEY_THRESHOLD_GROUP_START",
        "OLMCOLORKEY_PREMULTIPLIED", "OLMCOLORKEY_COLOR_SPACE",
        "OLMCOLORKEY_FORCE_LOWER_PRECISION", "OLMCOLORKEY_PER_COLOR",
        "OLMCOLORKEY_PER_COMPONENT",
        "OLMCOLORKEY_THRESHOLD_R", "OLMCOLORKEY_THRESHOLD_G",
        "OLMCOLORKEY_THRESHOLD_B", "OLMCOLORKEY_THRESHOLD_GROUP_END",
        "OLMCOLORKEY_EDGE_THIN_GROUP_START", "OLMCOLORKEY_EDGE_THIN_AMOUNT",
        "OLMCOLORKEY_EDGE_THIN_DISTANCE_TYPE", "OLMCOLORKEY_EDGE_THIN_GROUP_END",
        "OLMCOLORKEY_EDGE_BLUR_GROUP_START", "OLMCOLORKEY_EDGE_BLUR_AMOUNT",
        "OLMCOLORKEY_EDGE_BLUR_DISTANCE_TYPE", "OLMCOLORKEY_EDGE_BLUR_DIRECTION",
        "OLMCOLORKEY_EDGE_BLUR_GROUP_END", "OLMCOLORKEY_NUMBER_OF_COLORS",
        "OLMCOLORKEY_ENABLE_REPLACE", "OLMCOLORKEY_COLOR_FIRST",
    ]
    values = first_enum_values(header)
    assert [values[name] for name in enum_names] == list(range(len(enum_names))), "ColorKey enum/render indices drifted"

    rows = [row for row in manifest_rows(effect) if row["match_name"].startswith("OLM Color Key-")]
    structural_labels = {"Threshold Parameters", "Edge Thin", "Edge Blur", ""}
    leaf_rows = [row for row in rows if row.get("name") not in structural_labels]
    fixed_leaf_suffixes = [1, 2, 4, 5, 0x20A, 6, 7, 8, 9, 10, 0x0D, 0x0E, 0x11, 0x12, 0x13, 0x15, 0x20B]
    assert [suffix(row["match_name"]) for row in leaf_rows[:17]] == fixed_leaf_suffixes, "ColorKey Windows leaf order drifted"
    assert len(rows) == 23 + 25 * 8, "ColorKey manifest surface changed unexpectedly"
    for i in range(25):
        actual = [suffix(row["match_name"]) for row in leaf_rows[17 + i * 8:17 + (i + 1) * 8]]
        assert actual == [0x20C + i * 3, 0x20D + i * 3, 0x16 + i * 5, 0x20E + i * 3, 0x17 + i * 5, 0x18 + i * 5, 0x19 + i * 5, 0x1A + i * 5]
    assert len(leaf_rows) == 17 + 25 * 8

    registration = [
        "THRESHOLD_GROUP_START_DISK_ID",
        "PREMULTIPLIED_DISK_ID", "COLOR_SPACE_DISK_ID", "FORCE_LOWER_PRECISION_DISK_ID", "PER_COLOR_DISK_ID", "PER_COMPONENT_DISK_ID",
        "THRESHOLD_R_DISK_ID", "THRESHOLD_G_DISK_ID", "THRESHOLD_B_DISK_ID", "THRESHOLD_GROUP_END_DISK_ID",
        "EDGE_THIN_GROUP_START_DISK_ID", "EDGE_THIN_AMOUNT_DISK_ID", "EDGE_THIN_DISTANCE_TYPE_DISK_ID", "EDGE_THIN_GROUP_END_DISK_ID",
        "EDGE_BLUR_GROUP_START_DISK_ID", "EDGE_BLUR_AMOUNT_DISK_ID", "EDGE_BLUR_DISTANCE_TYPE_DISK_ID", "EDGE_BLUR_DIRECTION_DISK_ID", "EDGE_BLUR_GROUP_END_DISK_ID",
        "NUMBER_OF_COLORS_DISK_ID", "ENABLE_REPLACE_DISK_ID", "USE_COLOR_DISK_ID_FIRST", "USE_REPLACE_DISK_ID_FIRST", "COLOR_DISK_ID_FIRST", "REPLACE_COLOR_DISK_ID_FIRST",
        "THRESHOLD_DISK_ID_FIRST", "THRESHOLD_R_DISK_ID_FIRST", "THRESHOLD_G_DISK_ID_FIRST", "THRESHOLD_B_DISK_ID_FIRST",
    ]
    assert_registration_order(source, registration)
    constants = header_constants(header, [
        "COLOR_KEEP_DISK_ID", "THRESHOLD_DISK_ID", "PREMULTIPLIED_DISK_ID", "COLOR_SPACE_DISK_ID",
        "FORCE_LOWER_PRECISION_DISK_ID", "PER_COLOR_DISK_ID", "PER_COMPONENT_DISK_ID",
        "THRESHOLD_R_DISK_ID", "THRESHOLD_G_DISK_ID", "THRESHOLD_B_DISK_ID",
        "EDGE_THIN_AMOUNT_DISK_ID", "EDGE_THIN_DISTANCE_TYPE_DISK_ID", "EDGE_BLUR_AMOUNT_DISK_ID",
        "EDGE_BLUR_DISTANCE_TYPE_DISK_ID", "EDGE_BLUR_DIRECTION_DISK_ID", "NUMBER_OF_COLORS_DISK_ID",
        "ENABLE_REPLACE_DISK_ID",
    ])
    assert list(constants.values()) == [1, 2, 4, 5, 0x20A, 6, 7, 8, 9, 10, 0x0D, 0x0E, 0x11, 0x12, 0x13, 0x15, 0x20B]
    assert_reference_symbols(source, values, {"OLMCOLORKEY_COLOR_KEEP", "OLMCOLORKEY_THRESHOLD", "OLMCOLORKEY_PREMULTIPLIED", "OLMCOLORKEY_COLOR_SPACE", "OLMCOLORKEY_FORCE_LOWER_PRECISION", "OLMCOLORKEY_PER_COLOR", "OLMCOLORKEY_PER_COMPONENT", "OLMCOLORKEY_THRESHOLD_R", "OLMCOLORKEY_THRESHOLD_G", "OLMCOLORKEY_THRESHOLD_B", "OLMCOLORKEY_EDGE_THIN_AMOUNT", "OLMCOLORKEY_EDGE_THIN_DISTANCE_TYPE", "OLMCOLORKEY_EDGE_BLUR_AMOUNT", "OLMCOLORKEY_EDGE_BLUR_DISTANCE_TYPE", "OLMCOLORKEY_EDGE_BLUR_DIRECTION", "OLMCOLORKEY_NUMBER_OF_COLORS", "OLMCOLORKEY_ENABLE_REPLACE", "OLMCOLORKEY_INPUT"})
    return {"windows_rows": len(rows), "mac_enum_slots": values["OLMCOLORKEY_NUM_PARAMS"] if "OLMCOLORKEY_NUM_PARAMS" in values else values["OLMCOLORKEY_COLOR_FIRST"]}


def check_kirakira() -> dict:
    header = ROOT / "mac/OLMKiraKira/OLMKiraKira.h"
    source = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
    effect = manifest_effect(DEFAULTS, "OLM Kira Kira")
    range_effect = manifest_effect(RANGES, "OLM Kira Kira")
    rows = [row for row in manifest_rows(effect) if row["match_name"].startswith("OLM OLM Kira Kira-")]
    range_rows = [row for row in manifest_rows(range_effect) if row["match_name"].startswith("OLM OLM Kira Kira-")]
    assert [(r["match_name"], r["property_index"]) for r in rows] == [(r["match_name"], r["property_index"]) for r in range_rows], "KiraKira default/range order differs"
    expected_suffixes = [8, 9, 0x11, 0x0A, 2, 0x0B, 0x1B, 7, 0x0C, 3, 0x0D, 0x12, 4, 0x0E, 0x14, 5, 0x0F, 0x16, 0x1A, 0x1C, 0x23, 6, 0x10, 0x18, 0x01]
    mapped = [suffix(row["match_name"]) for row in rows if suffix(row["match_name"]) in expected_suffixes]
    assert mapped == expected_suffixes, "KiraKira Windows mapped property order drifted"

    enum_names = [
        "OLMKIRAKIRA_INPUT", "OLMKIRAKIRA_CHANNEL", "OLMKIRAKIRA_BLUR_MODE", "OLMKIRAKIRA_MERGE_MODE", "OLMKIRAKIRA_APPROX_INPUT",
        "OLMKIRAKIRA_BRIGHTNESS_GAIN", "OLMKIRAKIRA_STRENGTH_MULTIPLIER", "OLMKIRAKIRA_FADE_OUT", "OLMKIRAKIRA_GLOW_OPACITY", "OLMKIRAKIRA_SOURCE_OPACITY",
        "OLMKIRAKIRA_VERTICAL_LENGTH", "OLMKIRAKIRA_VERTICAL_COLOR", "OLMKIRAKIRA_VERTICAL_USE_RAMP", "OLMKIRAKIRA_HORIZONTAL_LENGTH", "OLMKIRAKIRA_HORIZONTAL_COLOR",
        "OLMKIRAKIRA_HORIZONTAL_USE_RAMP", "OLMKIRAKIRA_DIAGONAL_LENGTH", "OLMKIRAKIRA_DIAGONAL_COLOR", "OLMKIRAKIRA_DIAGONAL_USE_RAMP", "OLMKIRAKIRA_DIAGONAL2_LENGTH",
        "OLMKIRAKIRA_DIAGONAL2_COLOR", "OLMKIRAKIRA_DIAGONAL2_USE_RAMP", "OLMKIRAKIRA_HIGHLIGHT_RADIUS", "OLMKIRAKIRA_HIGHLIGHT_COLOR", "OLMKIRAKIRA_HIGHLIGHT_USE_RAMP", "OLMKIRAKIRA_GLOW_ROTATION",
    ]
    values = first_enum_values(header)
    assert [values[name] for name in enum_names] == list(range(len(enum_names))), "KiraKira enum/render indices drifted"
    registration = [
        "CHANNEL_DISK_ID", "BLUR_MODE_DISK_ID", "MERGE_MODE_DISK_ID", "APPROX_INPUT_DISK_ID", "BRIGHTNESS_GAIN_DISK_ID", "STRENGTH_MULTIPLIER_DISK_ID", "FADE_OUT_DISK_ID", "GLOW_OPACITY_DISK_ID", "SOURCE_OPACITY_DISK_ID",
        "VERTICAL_LENGTH_DISK_ID", "VERTICAL_COLOR_DISK_ID", "VERTICAL_USE_RAMP_DISK_ID", "HORIZONTAL_LENGTH_DISK_ID", "HORIZONTAL_COLOR_DISK_ID", "HORIZONTAL_USE_RAMP_DISK_ID",
        "DIAGONAL_LENGTH_DISK_ID", "DIAGONAL_COLOR_DISK_ID", "DIAGONAL_USE_RAMP_DISK_ID", "DIAGONAL2_LENGTH_DISK_ID", "DIAGONAL2_COLOR_DISK_ID", "DIAGONAL2_USE_RAMP_DISK_ID",
        "HIGHLIGHT_RADIUS_DISK_ID", "HIGHLIGHT_COLOR_DISK_ID", "HIGHLIGHT_USE_RAMP_DISK_ID", "GLOW_ROTATION_DISK_ID",
    ]
    assert_registration_order(source, registration)
    constants = header_constants(header, [
        "CHANNEL_DISK_ID", "BLUR_MODE_DISK_ID", "MERGE_MODE_DISK_ID", "APPROX_INPUT_DISK_ID",
        "BRIGHTNESS_GAIN_DISK_ID", "STRENGTH_MULTIPLIER_DISK_ID", "FADE_OUT_DISK_ID", "GLOW_OPACITY_DISK_ID",
        "SOURCE_OPACITY_DISK_ID", "VERTICAL_LENGTH_DISK_ID", "VERTICAL_COLOR_DISK_ID", "VERTICAL_USE_RAMP_DISK_ID",
        "HORIZONTAL_LENGTH_DISK_ID", "HORIZONTAL_COLOR_DISK_ID", "HORIZONTAL_USE_RAMP_DISK_ID", "DIAGONAL_LENGTH_DISK_ID",
        "DIAGONAL_COLOR_DISK_ID", "DIAGONAL_USE_RAMP_DISK_ID", "DIAGONAL2_LENGTH_DISK_ID", "DIAGONAL2_COLOR_DISK_ID",
        "DIAGONAL2_USE_RAMP_DISK_ID", "HIGHLIGHT_RADIUS_DISK_ID", "HIGHLIGHT_COLOR_DISK_ID", "HIGHLIGHT_USE_RAMP_DISK_ID",
        "GLOW_ROTATION_DISK_ID",
    ])
    assert list(constants.values()) == expected_suffixes
    required = set(enum_names)
    assert_reference_symbols(source, values, required)
    source_text = source.read_text(encoding="utf-8")
    referenced = set(re.findall(r"params\[([A-Z0-9_]+)\]", source_text))
    assert set(enum_names) - referenced == set(), "KiraKira standard-render checkout surface changed"
    for symbol in ("OLMKIRAKIRA_APPROX_INPUT", "OLMKIRAKIRA_FADE_OUT", "OLMKIRAKIRA_HIGHLIGHT_RADIUS"):
        assert f"checkout({symbol}, &p)" in source_text, f"KiraKira SmartRender misses {symbol}"
    assert "info.approximated_input" not in source_text, "Approximated Input must remain fail-closed until non-identity resize is grounded"
    return {
        "windows_rows": len(rows),
        "mapped_rows": len(expected_suffixes),
        "unmapped_ramp_and_separator_rows": len(rows) - len(expected_suffixes),
        "registered_but_unchecked_out": [],
        "checked_out_but_algorithm_blocked": ["OLMKIRAKIRA_APPROX_INPUT"],
    }


def main() -> int:
    result = {"OLMColorKey": check_colorkey(), "OLMKiraKira": check_kirakira()}
    print(json.dumps({"status": "pass", "result": result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
