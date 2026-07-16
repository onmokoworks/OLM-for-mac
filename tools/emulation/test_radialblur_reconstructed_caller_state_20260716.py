#!/usr/bin/env python3
"""Direct checks for the bounded reconstructed OLMRadialBlur caller witness."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import probe_radialblur_reconstructed_caller_state_20260716 as probe  # noqa: E402


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="radialblur_reconstructed_test_") as directory:
        output_json = Path(directory) / "witness.json"
        output_md = Path(directory) / "witness.md"
        completed = subprocess.run([
            sys.executable, str(probe.__file__), "--output-json", str(output_json),
            "--output-md", str(output_md),
        ], check=False, capture_output=True, text=True)
        assert completed.returncode == 0, completed.stdout + completed.stderr
        report = json.loads(output_json.read_text(encoding="utf-8"))
        assert report["status"] == "pass", report["issues"]
        assert report["geometry"] == {"width": 32, "height": 1, "row_start": 0, "row_end": 1}
        assert all(run["instructions"]["total"] <= 2_000_000 for run in report["runs"])
        assert all(run["sample"]["exact_float32_words"] for run in report["runs"])

        broken = copy.deepcopy(report)
        broken["runs"][1]["initial_state_sha256"] = "0" * 64
        assert "initial_state_not_byte_identical" in probe.evaluate(broken)
        broken = copy.deepcopy(report)
        broken["runs"][0]["sample"]["exact_float32_words"] = False
        assert "live:portable_sampler_word_mismatch" in probe.evaluate(broken)
        broken = copy.deepcopy(report)
        broken["runs"][0]["instructions"]["total"] = 2_000_001
        assert "live:instruction_budget_exceeded" in probe.evaluate(broken)
        broken = copy.deepcopy(report)
        broken["runs"][0]["entry_captures"]["worker"][0]["stack_args"][2] = 1
        assert "live:worker_abi_state_mismatch" in probe.evaluate(broken)

    print("[OK] reconstructed caller-state actual-AEX witness gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
