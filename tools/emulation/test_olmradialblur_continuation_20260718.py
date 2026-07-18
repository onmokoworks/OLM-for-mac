#!/usr/bin/env python3
"""Structural tests for the RadialBlur continuation probe.

These tests intentionally never load an AEX, open a checkpoint, launch AE, or
start the expensive continuation.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "tools/emulation/run_olmradialblur_continuation_20260718.py"
SPEC = importlib.util.spec_from_file_location("radial_continuation", RUNNER_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class ContinuationStructureTests(unittest.TestCase):
    def test_default_and_stops_are_pinned(self) -> None:
        self.assertEqual(runner.DEFAULT_CHECKPOINT.name, "full_merged_at_normalization_20260718.aexcp")
        self.assertEqual(
            runner.STOPS,
            (
                ("normalized_polar_plane", 0x180005D96),
                ("complete_pf32_frame", 0x180005E8E),
                ("pre_return", 0x1800063A1),
            ),
        )
        self.assertEqual(runner.RETURN_TRAMPOLINE, 0x90000000)

    def test_parser_does_not_execute(self) -> None:
        parser = argparse.ArgumentParser()
        runner.checkpoint_args(parser)
        args = parser.parse_args([])
        self.assertEqual(args.checkpoint, runner.DEFAULT_CHECKPOINT)
        self.assertEqual(args.pixel, [(0, 0), (6, 0), (7, 0), (8, 0), (24, 0)])

    def test_metadata_gate_rejects_synthetic_paths(self) -> None:
        header = {
            "aex": {"sha256": "wrong"},
            "metadata": {
                "harness": "test_zoom_case0009",
                "harness_checkpoint_version": 1,
                "config": {
                    "case_id": "case_0009",
                    "input_sha256": "x",
                    "manifest_sha256": "y",
                    "direct_python_prefill": True,
                },
                "captured": {"zoom_param1": 1, "zoom_param2": 2},
            },
        }
        with self.assertRaises(ValueError):
            runner.checkpoint_metadata_gate(
                header, Path("/tmp/checkpoint.aexcp"),
                Path("/tmp/aex"), Path("/tmp/manifest"), Path("/tmp/input"), "case_0009",
            )

    def test_portable_removes_repo_path_recursively(self) -> None:
        value = {"a": str(ROOT / "refs/conformance/evidence.json"), "b": [str(ROOT)]}
        result = runner.portable(value)
        self.assertEqual(result, {"a": "<repo>/refs/conformance/evidence.json", "b": ["<repo>"]})

    def test_report_schema_is_json_safe(self) -> None:
        report = {
            "kind": "olmradialblur_continuation_20260718",
            "status": "pass_internal_continuation_only",
            "gates": {"normal_return": True},
            "sequential_stops": [],
        }
        encoded = json.dumps(report, sort_keys=True)
        self.assertIn("pass_internal_continuation_only", encoded)


if __name__ == "__main__":
    unittest.main()
