#!/usr/bin/env python3
"""Require semantic default ramp fields to survive different host bases."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tools/emulation/test_olmkirakira_ramp_default_handle_actual_aex_20260805.py"
REPORT = ROOT / "refs/conformance/olmkirakira_ramp_default_handle_actual_aex_20260805.json"


def run(preallocate: int) -> dict:
    env = dict(os.environ, OLM_KK_RAMP_PREALLOCATE=str(preallocate))
    subprocess.run(["python3", str(PROBE)], cwd=ROOT, env=env, check=True,
                   stdout=subprocess.DEVNULL)
    return json.loads(REPORT.read_text(encoding="utf-8"))


def main() -> int:
    first = run(0)
    second = run(0x3000)
    assert first["events"][1]["handle"] != second["events"][1]["handle"]
    assert first["layout"] == second["layout"]
    assert first["handle_data_sha256"] == second["handle_data_sha256"]
    assert first["layout"]["stop_count"] == 3
    assert first["layout"]["stops_position_alpha_red_green_blue"] == [
        [0.0, 1.0, 1.0, 0.0, 0.0],
        [0.7799999713897705, 1.0, 1.0, 0.6510000228881836, 0.0],
        [1.0, 1.0, 1.0, 1.0, 1.0],
    ]
    run(0)  # leave the canonical report at the baseline allocation.
    print("PASS_OLMKIRAKIRA_RAMP_DEFAULT_HANDLE_RELOCATION_20260805 bases=2 semantic_exact=true stops=3")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
