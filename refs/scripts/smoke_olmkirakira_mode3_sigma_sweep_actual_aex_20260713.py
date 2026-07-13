#!/usr/bin/env python3
"""Static smoke for the OLMKiraKira Mode 3 sigma sweep evidence bundle."""

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tools/emulation/probe_olmkirakira_mode3_sigma_sweep_actual_aex_20260713.py"
EVIDENCE = ROOT / "refs/conformance/olmkirakira_mode3_sigma_sweep_actual_aex_20260713.json"


def main() -> int:
    source = PROBE.read_text(encoding="utf-8")
    ast.parse(source)
    for token in (
        "DAT_18148D670",
        "capture_disasm",
        "capture_data_constant",
        "sigma_matches_length_times_dat",
        "observed_size_set",
    ):
        assert token in source, token

    if EVIDENCE.exists():
        report = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        assert report["schema"] == "olmkirakira-mode3-sigma-sweep-actual-aex/1"
        assert report["dat_18148d670"]["data"]["f64"] == 0.5
        summary = report["summary"]
        assert summary["dat_18148d670_f64"] == 0.5
        assert summary["observed_size_set"] == [[0, 1]]
        expected = {1: 0.5, 2: 1.0, 5: 2.5, 9: 4.5}
        seen = {case["length"]: case for case in report["cases"]}
        for length, sigma in expected.items():
            case = seen[length]
            assert case["status"] == "captured"
            assert case["size"] == [0, 1]
            assert case["sigma_x_f64"] == sigma
            assert case["expected_sigma_x_f64"] == sigma
            assert case["sigma_matches_expected"] is True
    print("smoke_olmkirakira_mode3_sigma_sweep_actual_aex_20260713=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
