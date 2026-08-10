#!/usr/bin/env python3
"""Capture non-square Mode-3 complete chains for geometry generalization."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / "tools/emulation/probe_olmkirakira_mode3_default50_canonical_actual_aex_20260810.py"
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
REPORT = ROOT / "refs/conformance/olmkirakira_mode3_geometry_generalization_actual_aex_20260810.json"
GEOMETRY_ANGLES = (
    (36, 22, 0), (39, 39, 45), (39, 30, 17),
    (68, 40, 0), (74, 74, 45), (75, 57, 17),
)
GENERAL_LENGTHS = (3, 5, 7, 9, 11, 25, 50, 100, 200, 300)
CASES = tuple((width, height, angle, length)
              for width, height, angle in GEOMETRY_ANGLES
              for length in GENERAL_LENGTHS) + (
    (39, 39, -45, 3), (39, 39, -45, 50),
    (36, 22, 0, 1), (36, 22, 0, 2),
    (36, 22, 0, 301), (36, 22, 0, 1000),
)


def load_base():
    spec = importlib.util.spec_from_file_location("kira_mode3_default50_base", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Mode-3 complete-chain probe")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    os.environ["OLM_KK_PROCESS_ATTACH_DIAGNOSTIC"] = "1"
    os.environ["OLM_KK_MANUAL_CRT_INITIALIZERS_DIAGNOSTIC"] = "1"
    helper = load_base()
    output = helper.load_output_base()
    cases = [helper.run_case(output, width, height, angle, length)
             for width, height, angle, length in CASES]
    report = {
        "schema": "olmkirakira.mode3-geometry-generalization-actual-aex/1",
        "status": "captured",
        "source_work_geometry": [32, 18],
        "additional_source_work_geometry": [64, 36],
        "aex_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
        "cases": cases,
        "boundary": "Hostless checked-in Windows AEX complete helper chains; no native-AE claim.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "cases": len(cases)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
