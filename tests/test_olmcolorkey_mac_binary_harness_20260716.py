#!/usr/bin/env python3
"""Regression test for the bounded Mac-local OLMColorKey binary lane."""

import json
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from exercise_olmcolorkey_mac_binary_harness_20260716 import run  # noqa: E402


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmcolorkey_mac_binary_test_") as raw:
        report = Path(raw) / "report.json"
        result = run(report)
        assert result["status"] == "pass_mac_binary_fixture"
        assert result["raw_output_matches_expected"] is True
        assert result["fixture"] == {"width": 2, "height": 2, "raw_rgba_bytes": 16}
        assert result["plugin_boundary"]["standalone_worker_export"] is False
        assert any("_EffectMain" in line for line in result["plugin_boundary"]["exported_host_symbols"])
        json.loads(report.read_text(encoding="utf-8"))
    print("[OK] OLMColorKey Mac binary fixture harness")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
