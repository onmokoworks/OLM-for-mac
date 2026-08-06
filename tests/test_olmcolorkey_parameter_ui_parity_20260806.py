#!/usr/bin/env python3
"""Fail-closed source contract for the proven OLMColorKey Windows UI surface."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "mac/OLMColorKey/OLMColorKey.cpp").read_text(encoding="utf-8")
STRINGS = (ROOT / "mac/OLMColorKey/OLMColorKey_Strings.cpp").read_text(encoding="utf-8")


def test_number_of_colors_keeps_abi_but_matches_windows_zero_minimum() -> None:
    assert re.search(
        r"PF_ADD_SLIDER\(GetStringPtr\(StrID_NumberOfColors_Param_Name\),\s*"
        r"0, OLMCOLORKEY_MAX_COLORS, 0, OLMCOLORKEY_MAX_COLORS, 1,\s*"
        r"NUMBER_OF_COLORS_DISK_ID\)",
        SOURCE,
    )


def test_fixed_group_and_control_types_remain_windows_shaped() -> None:
    assert SOURCE.count("PF_ADD_TOPIC(") == 3
    assert SOURCE.count("PF_END_TOPIC(") == 3
    assert SOURCE.count("PF_ADD_POPUP(") == 5
    assert "PF_ADD_SLIDER(GetStringPtr(StrID_Amount_Param_Name),\n\t              -4000, 4000, -4000, 4000, 0," in SOURCE
    assert re.search(
        r"PF_ADD_FLOAT_SLIDERX\(GetStringPtr\(StrID_Amount_Param_Name\),\s*"
        r"0\.0, 4000\.0, 0\.0, 4000\.0, 0\.0,\s*PF_Precision_TENTHS",
        SOURCE,
    )


def test_proven_popup_names_choices_and_defaults_remain_exact() -> None:
    for literal in (
        '"RGB|HSV|Lab76|Lab94|YUV|YCrCb"',
        '"Full|16bit|8bit"',
        '"Box|Approximate|Euclidean"',
        '"Inside|Around|Outside"',
        '"Threshold Parameters"',
        '"Edge Thin"',
        '"Edge Blur"',
    ):
        assert literal in STRINGS
    assert "6, 1, GetStringPtr(StrID_ColorSpace_Choices)" in SOURCE
    assert "3, 1, GetStringPtr(StrID_ForceLowerPrecision_Choices)" in SOURCE
    assert SOURCE.count("3, 1, GetStringPtr(StrID_DistanceType_Choices)") == 2
    assert "3, 2, GetStringPtr(StrID_EdgeBlurDirection_Choices)" in SOURCE


if __name__ == "__main__":
    test_number_of_colors_keeps_abi_but_matches_windows_zero_minimum()
    test_fixed_group_and_control_types_remain_windows_shaped()
    test_proven_popup_names_choices_and_defaults_remain_exact()
    print("[OK] OLMColorKey parameter UI parity")
