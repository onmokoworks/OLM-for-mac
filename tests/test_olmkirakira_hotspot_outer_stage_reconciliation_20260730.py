#!/usr/bin/env python3
"""Fail-closed static reconciliation of KiraKira's PF8 outer compose path."""

from __future__ import annotations

import importlib.util
import json
import unittest
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ASM_PATH = ROOT / "disasm/OLMKiraKira.aex.asm.txt"
ORACLE_PATH = ROOT / "tools/emulation/olmkirakira_outer_compose_oracle_20260728.py"
OLD_WITNESS = ROOT / "refs/conformance/olmkirakira_hotspot_lane_audit_20260701.md"
OLD_WITNESS_JSON = ROOT / "refs/conformance/olmkirakira_hotspot_lane_audit_20260701.json"
OLD_COMPARISON_JSON = (
    ROOT
    / "refs/reports/runtime_trace_comparisons/"
    / "olmkirakira_hotspot_compose_writeback_witness_20260701.json"
)


def load_oracle():
    spec = importlib.util.spec_from_file_location("olmkirakira_outer_oracle", ORACLE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load oracle: {ORACLE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ORACLE = load_oracle()


def function_body(asm: str, name: str, next_name: str) -> str | None:
    start = f"; === {name} @"
    end = f"; === {next_name} @"
    if asm.count(start) != 1 or asm.count(end) != 1:
        return None
    left = asm.index(start)
    right = asm.index(end, left)
    return asm[left:right]


def ordered_once(body: str | None, anchors: tuple[str, ...]) -> bool:
    if body is None or any(body.count(anchor) != 1 for anchor in anchors):
        return False
    positions = [body.index(anchor) for anchor in anchors]
    return positions == sorted(positions)


def separate_static_facts(asm: str) -> dict[str, bool]:
    owner = function_body(asm, "FUN_18114d220", "FUN_18114d7f0")
    driver = function_body(asm, "FUN_18114f4a0", "FUN_18114fd90")
    outer = function_body(asm, "FUN_18114e110", "FUN_18114e460")
    return {
        "owner_order": ordered_once(
            owner,
            (
                "18114d62c  CALL 0x18114f4a0",
                "18114d71e  MOV RAX,qword ptr [RDI + 0x78]",
                "18114d722  MOV qword ptr [RDI + 0x128],RAX",
                "18114d729  MOV RAX,qword ptr [RDI + 0x140]",
                "18114d730  MOV qword ptr [RDI + 0x190],RAX",
                "18114d73d  CALL 0x18114e110",
            ),
        ),
        "inner_selector": ordered_once(
            driver,
            (
                "18114fbbb  MOV ECX,dword ptr [RBP + 0x600]",
                "18114fbc4  JZ 0x18114fc2d",
                "18114fc28  CALL qword ptr [RAX + 0x10]",
                "18114fc86  CALL qword ptr [RAX + 0x8]",
            ),
        ),
        "outer_mode2_loads_and_writer": ordered_once(
            outer,
            (
                "18114e158  JZ 0x18114e2b7",
                "18114e161  JNZ 0x18114e414",
                "18114e191  MOV RAX,qword ptr [R15 + 0x190]",
                "18114e19c  MOV RAX,qword ptr [R15 + 0x128]",
                "18114e287  CALL 0x181230b90",
            ),
        ),
        "outer_mode1_loads_divide_and_writer": ordered_once(
            outer,
            (
                "18114e2e2  MOV RAX,qword ptr [R15 + 0x190]",
                "18114e2ed  MOV RAX,qword ptr [R15 + 0x128]",
                "18114e374  DIVSS XMM2,XMM9",
                "18114e3e9  CALL 0x181230b90",
            ),
        ),
        "no_screen_subtract": outer is not None and "SUBSS" not in outer,
    }


def _numeric(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    return float(value)


def _numeric_vector(value: Any, length: int, label: str) -> tuple[float, ...]:
    if not isinstance(value, list) or len(value) != length:
        raise ValueError(f"{label} must be a {length}-element list")
    return tuple(_numeric(item, f"{label}[{index}]") for index, item in enumerate(value))


def _byte_vector(value: Any, label: str) -> tuple[int, ...]:
    if (
        not isinstance(value, list)
        or len(value) != 4
        or any(isinstance(item, bool) or not isinstance(item, int) for item in value)
        or any(not 0 <= item <= 255 for item in value)
    ):
        raise ValueError(f"{label} must be a four-byte integer list")
    return tuple(value)


def parse_artifact_fixture(lane: Any, comparison: Any) -> dict[str, Any]:
    """Strictly bind the hypothetical oracle fixture to checked-in artifacts."""

    if not isinstance(lane, dict) or lane.get("schema") != 1:
        raise ValueError("lane must be schema 1 object")
    case_id = lane.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        raise ValueError("case_id must be a non-empty string")
    xy_raw = lane.get("witness_xy")
    if (
        not isinstance(xy_raw, list)
        or len(xy_raw) != 2
        or any(isinstance(value, bool) or not isinstance(value, int) for value in xy_raw)
    ):
        raise ValueError("witness_xy must be two integers")
    mac = lane.get("mac_compose_boundary")
    if not isinstance(mac, dict):
        raise ValueError("mac_compose_boundary must be an object")
    source = _numeric_vector(mac.get("src_rgba_float"), 4, "src_rgba_float")
    glow = _numeric_vector(mac.get("glow_rgba_float"), 4, "glow_rgba_float")
    out_u8 = _byte_vector(mac.get("out_u8"), "out_u8")
    reference_u8 = _byte_vector(mac.get("windows_reference_u8"), "windows_reference_u8")

    if not isinstance(comparison, dict) or comparison.get("schema") != 1:
        raise ValueError("comparison must be schema 1 object")
    windows = comparison.get("windows")
    if not isinstance(windows, dict) or windows.get("case_id") != case_id:
        raise ValueError("comparison case must match lane case")
    aggregation = windows.get("fun_18114fd90_aggregation")
    entry = aggregation.get("entry") if isinstance(aggregation, dict) else None
    if not isinstance(entry, dict):
        raise ValueError("aggregation entry must be an object")
    source_opacity = _numeric(entry.get("source_opacity"), "source_opacity")
    glow_opacity = _numeric(entry.get("glow_opacity"), "glow_opacity")
    if source_opacity != 1.0 or glow_opacity != 1.0:
        raise ValueError("this hypothetical fixture requires declared unit opacities")
    return {
        "case_id": case_id,
        "witness_xy": tuple(xy_raw),
        "source": source,
        "glow_after_opacity": glow,
        "out_u8": out_u8,
        "reference_u8": reference_u8,
        "source_opacity": source_opacity,
        "glow_opacity": glow_opacity,
        "classification": "hypothetical_unit_opacity_outer_prediction",
    }


class HotspotOuterStageReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.asm = ASM_PATH.read_text(encoding="utf-8")
        cls.lane = json.loads(OLD_WITNESS_JSON.read_text(encoding="utf-8"))
        cls.comparison = json.loads(OLD_COMPARISON_JSON.read_text(encoding="utf-8"))

    def test_checked_in_pf8_separate_static_facts_are_present(self) -> None:
        facts = separate_static_facts(self.asm)
        self.assertTrue(all(facts.values()), facts)

    def test_artifact_bound_hypothetical_outputs_are_three_distinct_classes(self) -> None:
        fixture = parse_artifact_fixture(self.lane, self.comparison)
        self.assertEqual(fixture["case_id"], "kk_vertical_len50_brightness1_strength100")
        self.assertEqual(fixture["witness_xy"], (934, 118))
        self.assertEqual(fixture["classification"], "hypothetical_unit_opacity_outer_prediction")
        mode1 = ORACLE.compose_pixel(
            fixture["glow_after_opacity"],
            fixture["source"],
            glow_opacity=fixture["glow_opacity"],
            source_opacity=fixture["source_opacity"],
            merge_mode=1,
        )
        mode2 = ORACLE.compose_pixel(
            fixture["glow_after_opacity"],
            fixture["source"],
            glow_opacity=fixture["glow_opacity"],
            source_opacity=fixture["source_opacity"],
            merge_mode=2,
        )
        mode1_argb = list(ORACLE.stage_typed_writer(mode1, depth="PF8"))
        mode2_argb = list(ORACLE.stage_typed_writer(mode2, depth="PF8"))
        mode1_rgba = mode1_argb[1:] + mode1_argb[:1]
        mode2_rgba = mode2_argb[1:] + mode2_argb[:1]
        self.assertEqual(mode1_rgba, [105, 105, 105, 255])
        self.assertEqual(mode2_rgba, [159, 159, 159, 255])
        self.assertEqual(fixture["out_u8"], (144, 144, 144, 255))
        self.assertEqual(fixture["reference_u8"], (131, 131, 131, 255))
        self.assertEqual(len({tuple(mode1_rgba), tuple(mode2_rgba), fixture["out_u8"]}), 3)

    def test_old_witness_is_not_address_bound_to_outer_writer(self) -> None:
        old = OLD_WITNESS.read_text(encoding="utf-8")
        self.assertIn("final_writeback_or_png_rgba: `[144, 144, 144, 255]`", old)
        for required_binding in (
            "18114e110",
            "18114e287",
            "18114e3e9",
            "181230b90",
            "+0x128",
            "+0x190",
        ):
            self.assertNotIn(required_binding, old)

    def test_missing_owner_pointer_anchor_fails_closed(self) -> None:
        mutated = self.asm.replace(
            "18114d730  MOV qword ptr [RDI + 0x190],RAX",
            "18114d730  MOV qword ptr [RDI + 0x198],RAX",
            1,
        )
        self.assertFalse(separate_static_facts(mutated)["owner_order"])

    def test_swapped_outer_source_glow_loads_fail_closed(self) -> None:
        mutated = self.asm.replace(
            "18114e2e2  MOV RAX,qword ptr [R15 + 0x190]",
            "18114e2e2  MOV RAX,qword ptr [R15 + 0x128]",
            1,
        )
        self.assertFalse(separate_static_facts(mutated)["outer_mode1_loads_divide_and_writer"])

    def test_added_screen_instruction_fails_closed(self) -> None:
        marker = "18114e374  DIVSS XMM2,XMM9"
        mutated = self.asm.replace(marker, marker + "\n18114e378  SUBSS XMM2,XMM0", 1)
        self.assertFalse(separate_static_facts(mutated)["no_screen_subtract"])

    def test_adversarial_json_shape_and_case_mutations_fail_closed(self) -> None:
        bad_shape = deepcopy(self.lane)
        bad_shape["mac_compose_boundary"]["src_rgba_float"] = [0.1, 0.2, 0.3]
        with self.assertRaises(ValueError):
            parse_artifact_fixture(bad_shape, self.comparison)

        bad_type = deepcopy(self.lane)
        bad_type["witness_xy"] = [934, True]
        with self.assertRaises(ValueError):
            parse_artifact_fixture(bad_type, self.comparison)

        bad_case = deepcopy(self.comparison)
        bad_case["windows"]["case_id"] = "different_case"
        with self.assertRaises(ValueError):
            parse_artifact_fixture(self.lane, bad_case)

        bad_opacity = deepcopy(self.comparison)
        bad_opacity["windows"]["fun_18114fd90_aggregation"]["entry"]["glow_opacity"] = 0.5
        with self.assertRaises(ValueError):
            parse_artifact_fixture(self.lane, bad_opacity)


if __name__ == "__main__":
    unittest.main()
