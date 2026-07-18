#!/usr/bin/env python3
"""Bounded differential check for the 2026-07-18 ADA0 input witness.

The comparison is deliberately ordered at the ADA0 boundary: source
neighborhood, generated class window, rectangle, strides, config, then the
serial VCOMP schedule.  It compares values, not process-local addresses.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WITNESS = ROOT / "refs/conformance/olmsmoother2_case0012_ada0_input_before_vcomp_20260718.json"
SOURCE = ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"


def _load_case():
    import sys

    sys.path.insert(0, str(ROOT / "tools" / "emulation"))
    from probe_olmsmoother2_case0012_ada0_input_before_vcomp_20260718 import run
    from test_smoother2_case0012_local_tuple import LOG_PATH, parse_log

    return run(parse_log(LOG_PATH))


def _assert_first_equal(test: unittest.TestCase, expected, actual, label: str) -> None:
    if expected != actual:
        test.fail(f"first exact divergence: {label}\nexpected={expected!r}\nactual={actual!r}")


class Ada0InputDifferentialTests(unittest.TestCase):
    def test_ada0_input_matches_mac_port_and_serial_harness(self):
        witness = json.loads(WITNESS.read_text(encoding="utf-8"))
        actual = _load_case()

    # 1. Source neighborhood: the AEX input capture must equal the f32 bytes
    # installed by the retained Mac-local source harness.
        expected_source = []
        for item in actual["input_checkpoint"]["source_window_5x5"]:
            expected_source.append({"offset": item["offset"], "rgba": item["rgba"]})
        witness_source = [
            {"offset": item["offset"], "rgba": item["rgba"]}
            for item in witness["input_checkpoint"]["source_window_5x5"]
        ]
        _assert_first_equal(self, witness_source, expected_source, "source neighborhood")

    # 2. Class window: the natural actual-AEX class generation remains the
    # retained translated tuple, including the central 3x4 dependency window.
        _assert_first_equal(self, True, actual["execution"]["generated_window_exact"], "class window")

    # 3. Rectangle and 4. descriptor geometry.
        _assert_first_equal(self, actual["input_checkpoint"]["rectangle"], witness["input_checkpoint"]["rectangle"], "rectangle")
        witness_source_desc = witness["input_checkpoint"]["source_descriptor"]
        witness_class_desc = witness["input_checkpoint"]["class_descriptor"]
        _assert_first_equal(self,
            {"width": actual["input_checkpoint"]["source_descriptor"]["width"], "height": actual["input_checkpoint"]["source_descriptor"]["height"], "stride_bytes": actual["input_checkpoint"]["source_descriptor"]["stride_bytes"]},
            {"width": witness_source_desc["width"], "height": witness_source_desc["height"], "stride_bytes": witness_source_desc["stride_bytes"]},
            "source descriptor strides",
        )
        _assert_first_equal(self,
            {"width": actual["input_checkpoint"]["class_descriptor"]["width"], "height": actual["input_checkpoint"]["class_descriptor"]["height"], "stride_bytes": actual["input_checkpoint"]["class_descriptor"]["stride_bytes"]},
            {"width": witness_class_desc["width"], "height": witness_class_desc["height"], "stride_bytes": witness_class_desc["stride_bytes"]},
            "class descriptor stride",
        )

    # 5. Config bytes and interpreted fields.
        config = witness["input_checkpoint"]["config"]
        _assert_first_equal(self, actual["input_checkpoint"]["config"]["bytes_hex"], config["bytes_hex"], "config bytes")
        _assert_first_equal(self, 88, config["offset_0x1c_i32"], "config +0x1c")
        _assert_first_equal(self, 0, config["offset_0x70_i32"], "config +0x70")
        _assert_first_equal(self, 0.0, config["offset_0x74_f32"], "config +0x74")
        _assert_first_equal(self, 128, config["length"], "config length")

    # 6. Worker schedule.  The checked-in harness must observe the same
    # compiler-generated VCOMP boundary and one serial worker invocation.
        _assert_first_equal(self,
            witness["execution"]["vcomp"], actual["execution"]["vcomp"], "worker schedule"
        )

    # Finally pin the relevant current Mac implementation assumptions.  These
    # are source-level ABI checks, not a production behavior claim.
        port = SOURCE.read_text(encoding="utf-8")
        for text, label in (
            ("(size_t)w * sizeof(FPix)", "Mac source pixel stride"),
            ("poly.cplane_stride = p.w * 4", "Mac class stride"),
            ("const float threshold = (float)class_threshold_field / 100.0f + WIN_THRESH_BIAS;", "Mac class threshold"),
        ):
            if text not in port:
                self.fail(f"first exact divergence: {label}\nmissing={text!r}")


if __name__ == "__main__":
    unittest.main()
