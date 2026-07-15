#!/usr/bin/env python3
"""Focused local regression for the case_0012 differential boundary."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/analyze_smoother2_case0012_differential.py"
SPEC = importlib.util.spec_from_file_location("smoother2_case0012_differential", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_fixture_has_requested_typed_boundaries() -> None:
    path = ROOT / "refs/windows_witness_specs/olmsmoother2_case0012_current_aex_20260713/fixtures/complete_cdb_trace.txt"
    observed, kind = MODULE.normalize(path)
    report = MODULE.analyze(observed, kind)
    assert report["verdict"] == "READY_TYPED_FIELDS_ONLY"
    assert report["FACT"]["completeness"] == {"events": True, "producer": True, "config": True, "writer": True}


def test_explicit_reference_attributes_config_difference() -> None:
    fixture = ROOT / "refs/windows_witness_specs/olmsmoother2_case0012_current_aex_20260713/fixtures/complete_cdb_trace.txt"
    observed, kind = MODULE.normalize(fixture)
    baseline = MODULE.stage_snapshot(observed["events"])
    changed = baseline | {"config": {**baseline["config"], "cce0": {**baseline["config"]["cce0"], "mode_byte": 0}}}
    report = MODULE.analyze(observed, kind, changed)
    assert report["verdict"] == "DIFF_AT_CONFIG"
    assert report["INFERENCE"]["first_divergence"] == "config"
