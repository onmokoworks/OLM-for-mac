#!/usr/bin/env python3
"""Regression test for the KiraKira evidence rejection matrix."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/audit_olmkirakira_rejection_matrix_20260716.py"


def load_module():
    spec = importlib.util.spec_from_file_location("kirakira_rejection_matrix", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_matrix_is_fail_closed_and_grounded():
    report = load_module().build_report(ROOT)
    assert report["status"] == "pass"
    by_name = {item["name"]: item for item in report["checks"]}
    assert by_name["mode-1-dispatch-preserved"]["status"] == "PASS"
    assert by_name["mode-2-dispatch-preserved"]["status"] == "PASS"
    assert by_name["mode-3-aex-to-portable-replay"]["status"] == "PASS"
    assert by_name["mode-3-live-gaussian-promotion"]["status"] == "REJECT"
    assert by_name["mode-4-implementation"]["status"] == "REJECT"
    assert by_name["merge-mode-2-compose"]["status"] == "REJECT"
    assert by_name["final-quantization-scope"]["status"] == "REJECT"
