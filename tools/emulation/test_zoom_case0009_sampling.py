#!/usr/bin/env python3
"""Lightweight tests for case_0009 post-core point sampling helpers."""

from __future__ import annotations

import struct
import json
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

import test_zoom_case0009 as zoom

ROOT = Path(__file__).resolve().parents[2]


class MemoryLoader:
    def __init__(self, payload: bytes):
        self.payload = payload

    def read_bytes(self, address: int, size: int) -> bytes:
        return self.payload[address : address + size]


class ZoomSamplingTests(unittest.TestCase):
    def test_parse_point_is_repeatable_and_keeps_legacy_coordinates(self) -> None:
        with patch.object(
            sys,
            "argv",
            ["test_zoom_case0009.py", "--x", "6", "--y", "0", "--point", "7,0", "--point", "8,0"],
        ):
            args = zoom.parse_args()
        self.assertEqual((args.x, args.y), (6, 0))
        self.assertEqual(args.point, [(7, 0), (8, 0)])
        self.assertEqual(zoom.parse_point("24, 0"), (24, 0))

    def test_sample_final_plane_reports_four_cells_and_float_u8_values(self) -> None:
        # Two angle rows by two radius columns, with distinct RGBA cells.
        cells = [
            (0.0, 0.1, 0.2, 1.0),
            (0.1, 0.2, 0.3, 1.0),
            (0.2, 0.3, 0.4, 1.0),
            (0.3, 0.4, 0.5, 1.0),
        ]
        payload = b"".join(struct.pack("<4f", *cell) for cell in cells)
        sample = zoom.sample_final_plane(MemoryLoader(payload), 0, 2, 2, 0.25, 0.5)
        self.assertEqual(sample["angle_indices"], [0, 1])
        self.assertEqual(sample["radius_indices"], [0, 1])
        self.assertEqual(len(sample["weights"]), 4)
        self.assertEqual(set(sample["cells"]), {"a0_r0", "a0_r1", "a1_r0", "a1_r1"})
        self.assertEqual(len(sample["sample_float"]), 4)
        self.assertEqual(len(sample["trunc_u8"]), 4)

    def test_sample_zoom_point_shapes_one_post_core_record(self) -> None:
        final_cells = [(0.0, 0.0, 0.0, 1.0)] * 4
        rgba_plane = b"".join(struct.pack("<4f", *cell) for cell in final_cells)
        scalar_plane = struct.pack("<f", 1.0) * 4
        loader = MemoryLoader(rgba_plane + rgba_plane + scalar_plane)
        with patch.object(zoom, "call_zoom_inverse", return_value=(0.25, 0.5)), patch.object(
            zoom, "read_world_pixel_argb", return_value=(4, 3, 2, 1)
        ):
            point = zoom.sample_zoom_point(loader, 0, 64, 128, 2, 2, 0, 1.0, 0, 256, 7, 0)
        self.assertEqual(point["xy"], [7, 0])
        self.assertEqual(set(point), {
            "xy", "inverse_coords", "indices", "weights", "four_cells", "final_float",
            "final_u8", "final_sample", "witness_cells", "output_world_rgba",
        })
        self.assertEqual(point["output_world_rgba"], [3, 2, 1, 4])

    def test_markdown_lists_same_run_point_samples(self) -> None:
        report = {
            "case_id": "case_0009", "xy": [6, 0], "aex": "test.aex",
            "entry_reached": True, "classification": "test", "geometry": {},
            "pointers": {}, "final_sample": {"sample_float": [0, 0, 0, 1], "trunc_u8": [0, 0, 0, 255]},
            "output_world_rgba": [0, 0, 0, 0], "windows_trace": {},
            "witness_cells": {"denom_0x843": {}, "final_7": {}, "accum_0x842": {}},
            "reading": "test",
            "point_samples": [{
                "xy": [7, 0], "indices": {"radius": 1.25, "angle": 2.5},
                "final_float": [0, 0, 0, 1], "final_u8": [0, 0, 0, 255],
                "output_world_rgba": [0, 0, 0, 0],
            }],
        }
        markdown = zoom.build_markdown(report)
        self.assertIn("## Same-run point samples", markdown)
        self.assertIn("`[7, 0]`", markdown)

    def test_checked_in_same_run_witness_is_bound_and_complete(self) -> None:
        path = ROOT / "refs/conformance/olmradialblur_case0009_fullframe_same_run_points_20260716.json"
        report = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(report["render_stop_rip"], "0x90000000")
        self.assertEqual((report["prepass_calls"], report["scatter_calls"]), (1, 1))
        self.assertEqual((report["prepass_detour_calls"], report["scatter_detour_calls"]), (0, 0))
        self.assertEqual({tuple(point["xy"]) for point in report["point_samples"]}, {(7, 0), (8, 0), (24, 0)})
        for digest in report["provenance"].values():
            self.assertEqual(len(digest), 64)


if __name__ == "__main__":
    unittest.main()
