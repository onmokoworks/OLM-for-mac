#!/usr/bin/env python3
"""Static regression for the audited OLMColorKey parameter registration surface."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HEADER = ROOT / "mac" / "OLMColorKey" / "OLMColorKey.h"
SOURCE = ROOT / "mac" / "OLMColorKey" / "OLMColorKey.cpp"

EXPECTED_FIXED_REGISTRATIONS = [
    ("COLOR_KEEP_DISK_ID", 1, "leaf"),
    ("THRESHOLD_DISK_ID", 2, "leaf"),
    ("THRESHOLD_GROUP_START_DISK_ID", 3, "structural"),
    ("PREMULTIPLIED_DISK_ID", 4, "leaf"),
    ("COLOR_SPACE_DISK_ID", 5, "leaf"),
    ("FORCE_LOWER_PRECISION_DISK_ID", 0x20A, "leaf"),
    ("PER_COLOR_DISK_ID", 6, "leaf"),
    ("PER_COMPONENT_DISK_ID", 7, "leaf"),
    ("THRESHOLD_R_DISK_ID", 8, "leaf"),
    ("THRESHOLD_G_DISK_ID", 9, "leaf"),
    ("THRESHOLD_B_DISK_ID", 10, "leaf"),
    ("THRESHOLD_GROUP_END_DISK_ID", 11, "structural"),
    ("EDGE_THIN_GROUP_START_DISK_ID", 12, "structural"),
    ("EDGE_THIN_AMOUNT_DISK_ID", 0x0D, "leaf"),
    ("EDGE_THIN_DISTANCE_TYPE_DISK_ID", 0x0E, "leaf"),
    ("EDGE_THIN_GROUP_END_DISK_ID", 20, "structural"),
    ("EDGE_BLUR_GROUP_START_DISK_ID", 16, "structural"),
    ("EDGE_BLUR_AMOUNT_DISK_ID", 0x11, "leaf"),
    ("EDGE_BLUR_DISTANCE_TYPE_DISK_ID", 0x12, "leaf"),
    ("EDGE_BLUR_DIRECTION_DISK_ID", 0x13, "leaf"),
    ("EDGE_BLUR_GROUP_END_DISK_ID", 1016, "structural"),
    ("NUMBER_OF_COLORS_DISK_ID", 0x15, "leaf"),
    ("ENABLE_REPLACE_DISK_ID", 0x20B, "leaf"),
]

EXPECTED_LEAF_IDENTITIES = {
    name: disk_id
    for name, disk_id, kind in EXPECTED_FIXED_REGISTRATIONS
    if kind == "leaf"
}

EXPECTED_INDEXED_LEAF_IDENTITIES = {
    "COLOR_DISK_ID_FIRST": 0x16,
    "THRESHOLD_DISK_ID_FIRST": 0x17,
    "THRESHOLD_R_DISK_ID_FIRST": 0x18,
    "THRESHOLD_G_DISK_ID_FIRST": 0x19,
    "THRESHOLD_B_DISK_ID_FIRST": 0x1A,
    "USE_COLOR_DISK_ID_FIRST": 0x20C,
    "USE_REPLACE_DISK_ID_FIRST": 0x20D,
    "REPLACE_COLOR_DISK_ID_FIRST": 0x20E,
}


def enum_constants(header: str) -> dict[str, int]:
    constants: dict[str, int] = {}
    for name, literal in re.findall(
        r"^\s*([A-Z][A-Z0-9_]*_DISK_ID(?:_FIRST)?)\s*=\s*(0x[0-9a-fA-F]+|\d+)\s*,?$",
        header,
        re.MULTILINE,
    ):
        constants[name] = int(literal, 0)
    return constants


def params_setup_body(source: str) -> str:
    match = re.search(
        r"ParamsSetup\(.*?\)\s*\{(?P<body>.*?)\n\}\n\nstatic A_long ColorParamIndex",
        source,
        re.DOTALL,
    )
    if not match:
        raise AssertionError("ParamsSetup body not found")
    return match.group("body")


def fixed_registration_ids(body: str) -> list[str]:
    fixed = body.split("for (int i = 0;", 1)[0]
    return re.findall(
        r"\b(?:PF_ADD_CHECKBOX|PF_ADD_FLOAT_SLIDERX|PF_ADD_POPUP|PF_ADD_TOPIC|"
        r"PF_ADD_SLIDER|PF_END_TOPIC)\s*\(.*?\b([A-Z][A-Z0-9_]*_DISK_ID)\s*\);",
        fixed,
        re.DOTALL,
    )


class OLMColorKeyParameterOrderStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.body = params_setup_body(SOURCE.read_text(encoding="utf-8"))
        cls.constants = enum_constants(cls.header)

    def test_exact_first_23_registration_disk_id_and_kind_sequence(self) -> None:
        names = fixed_registration_ids(self.body)
        self.assertEqual(names, [row[0] for row in EXPECTED_FIXED_REGISTRATIONS])
        self.assertEqual(
            [(name, self.constants[name], kind) for name, _, kind in EXPECTED_FIXED_REGISTRATIONS],
            EXPECTED_FIXED_REGISTRATIONS,
        )

    def test_symbolic_enum_order_matches_registration_order(self) -> None:
        enum_match = re.search(
            r"enum\s*\{\s*OLMCOLORKEY_INPUT\s*=\s*0,(.*?)OLMCOLORKEY_NUM_PARAMS",
            self.header,
            re.DOTALL,
        )
        self.assertIsNotNone(enum_match)
        symbols = re.findall(r"\b(OLMCOLORKEY_[A-Z0-9_]+)\s*,", enum_match.group(1))
        expected = ["OLMCOLORKEY_" + name.removesuffix("_DISK_ID") for name, _, _ in EXPECTED_FIXED_REGISTRATIONS]
        self.assertEqual(symbols[:23], expected)

    def test_all_leaf_disk_identities_are_unchanged(self) -> None:
        self.assertEqual(
            {name: self.constants[name] for name in EXPECTED_LEAF_IDENTITIES},
            EXPECTED_LEAF_IDENTITIES,
        )
        self.assertEqual(
            {name: self.constants[name] for name in EXPECTED_INDEXED_LEAF_IDENTITIES},
            EXPECTED_INDEXED_LEAF_IDENTITIES,
        )

    def test_indexed_payload_registration_id_expressions_are_unchanged(self) -> None:
        expected_expressions = [
            "USE_COLOR_DISK_ID_FIRST + i * 3",
            "USE_REPLACE_DISK_ID_FIRST + i * 3",
            "COLOR_DISK_ID_FIRST + i * 5",
            "REPLACE_COLOR_DISK_ID_FIRST + i * 3",
            "THRESHOLD_DISK_ID_FIRST + i * 5",
            "THRESHOLD_R_DISK_ID_FIRST + i * 5",
            "THRESHOLD_G_DISK_ID_FIRST + i * 5",
            "THRESHOLD_B_DISK_ID_FIRST + i * 5",
        ]
        positions = [self.body.find(expression) for expression in expected_expressions]
        self.assertTrue(all(position >= 0 for position in positions))
        self.assertEqual(positions, sorted(positions))


if __name__ == "__main__":
    unittest.main()
