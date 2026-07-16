#!/usr/bin/env python3
"""Differential for DG FUN_181174760 with embedded versus detoured OpenCV."""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from aex_loader import AexLoader  # noqa: E402
import cv_bridge as cvb  # noqa: E402
import opencv_impls as ocv  # noqa: E402
from test_dg_fieldgen_p1b import build_context, build_host_suites, setup_tls  # noqa: E402
from windows_runtime import WindowsOpenCVRuntime  # noqa: E402


AEX = ROOT / "plugins_2025/DistanceGradation.aex"
EXPECTED_AEX_SHA256 = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
FUN_FIELDGEN = 0x181174760


def _run(mask: np.ndarray, threshold: int, param8: int, *, embedded: bool):
    height, width = mask.shape
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    if embedded:
        WindowsOpenCVRuntime(loader).install()
    else:
        setup_tls(loader)
        ocv.register_opencv_impls(
            loader,
            "DistanceGradation",
            ops=["threshold", "dist_transform", "resize_same_shape", "normalize_minmax"],
        )

    spbasic = build_host_suites(loader)
    context = build_context(loader, spbasic)
    source = cvb.build_ipl(loader, mask, align_step=4)
    destination = cvb.build_ipl(
        loader,
        np.full((height, width), np.float32(-777.0), dtype=np.float32),
        align_step=16,
    )
    registers = loader.call_function(
        FUN_FIELDGEN,
        int_args=[context, source, destination, threshold, 0, width, height, param8],
        max_instructions=100_000_000,
    )
    return cvb.read_ipl(loader, destination).copy(), registers, loader


class EmbeddedFieldgenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        actual = hashlib.sha256(AEX.read_bytes()).hexdigest()
        if actual != EXPECTED_AEX_SHA256:
            raise AssertionError(f"DistanceGradation AEX hash mismatch: {actual}")

    def assert_embedded_matches_detour(self, mask: np.ndarray, threshold: int, param8: int):
        embedded, embedded_registers, embedded_loader = _run(
            mask, threshold, param8, embedded=True
        )
        detoured, detoured_registers, detoured_loader = _run(
            mask, threshold, param8, embedded=False
        )

        self.assertEqual(embedded.tobytes(), detoured.tobytes())
        self.assertGreater(embedded_registers["instructions"], detoured_registers["instructions"])
        self.assertGreater(embedded_registers["instructions"], 10_000)
        self.assertTrue(
            any(call.name == "FlsSetValue" and call.ret == 1 for call in embedded_loader.import_log)
        )
        self.assertFalse(
            any(label.startswith("cv::") for label, _args, _ret in embedded_loader.callback_log)
        )
        self.assertEqual(
            [
                label
                for label, _args, _ret in detoured_loader.callback_log
                if label.startswith("cv::")
            ],
            [
                "cv::resize_same_shape",
                "cv::dist_transform",
                "cv::resize_same_shape",
                "cv::threshold",
                "cv::normalize_minmax",
            ],
        )

    def test_single_source_constant_threshold(self):
        mask = np.full((11, 17), 255, dtype=np.uint8)
        mask[5, 8] = 0
        self.assert_embedded_matches_detour(mask, threshold=3, param8=1)

    def test_three_stripes_truncated_ramp(self):
        mask = np.full((11, 17), 255, dtype=np.uint8)
        mask[:, (0, 8, 16)] = 0
        self.assert_embedded_matches_detour(mask, threshold=4, param8=0)

    def test_all_foreground_normalizes_constant_field(self):
        mask = np.full((3, 4), 255, dtype=np.uint8)
        self.assert_embedded_matches_detour(mask, threshold=4, param8=0)


if __name__ == "__main__":
    unittest.main()
