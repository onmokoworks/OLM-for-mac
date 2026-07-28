#!/usr/bin/env python3
"""Focused regression for the fail-closed DG non-identity host probe."""

from __future__ import annotations

import importlib.util
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools/emulation/probe_olmdistancegradation_nonidentity_host_adapter_20260728.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("dg_nonidentity_host_probe_20260728", PROBE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_nonidentity_worlds_fail_closed_before_host_operations() -> None:
    report = _load_probe().run()
    fixtures = {fixture["name"]: fixture for fixture in report["fixtures"]}

    assert fixtures["identity_padded_pf8"]["operation_order"] == ["RenderBits"]
    rejected = [fixture for fixture in fixtures.values()
                if fixture["status"] == "unknown_host_behavior_rejected"]
    assert len(rejected) == 4
    for fixture in rejected:
        assert fixture["operation_order"] == []
        assert fixture["allocation_count"] == 0
        assert fixture["copy_count"] == 0
        assert fixture["conversion_count"] == 0
        assert fixture["resize_count"] == 0

    contract = report["contract"]
    assert contract["fact"] == "RenderBits uses output dimensions to index both input and output"
    assert all(not hits for hits in contract["host_operations_observed_in_renderbits"].values())
