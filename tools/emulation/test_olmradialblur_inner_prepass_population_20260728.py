#!/usr/bin/env python3
"""Focused regression for the bounded Inner B150/A9D0 proof fixture."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = HERE / "probe_olmradialblur_inner_prepass_population_20260728.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm-rb-inner-population-") as directory:
        output = Path(directory) / "result.json"
        run = subprocess.run(
            [sys.executable, str(PROBE), "--output-json", str(output)],
            check=False, capture_output=True, text=True,
        )
        assert run.returncode == 0, run.stdout + run.stderr
        report = json.loads(output.read_text(encoding="utf-8"))
        assert report["status"] == "pass"
        assert report["scatter_tail"]["status"] == "out_of_scope_already_closed"
        assert [x["name"] for x in report["scenarios"]] == [
            "rb_inner_only_strength_large_low_span", "rb_inner_quality_1"
        ]
        for index, scenario in enumerate(report["scenarios"]):
            assert scenario["status"] == "pass"
            assert all(scenario["gates"].values())
            assert scenario["population"]["prepass_nonzero_words_after_b150"] > 0
            assert scenario["population"]["a9d0_changed_population"] is (index == 1)
            assert scenario["population"]["expected_a9d0_changed_population"] is (index == 1)
            assert scenario["population"]["zero_vs_populated_prepass_diverged"] is (index == 1)
            assert scenario["population"]["expected_zero_vs_populated_prepass_diverged"] is (index == 1)
    print("[OK] actual-AEX Inner B150 population and A9D0 prepass counterfactual")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
