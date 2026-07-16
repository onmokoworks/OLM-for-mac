#!/usr/bin/env python3
"""Smoke test for the case0012 natural-caller contract oracle."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tools/emulation/test_olmsmoother2_case0012_natural_contract_followup_20260717.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmsmoother2_contract_") as temp:
        output_json = Path(temp) / "result.json"
        output_md = Path(temp) / "result.md"
        run = subprocess.run([sys.executable, str(PROBE), "--output-json", str(output_json), "--output-md", str(output_md)], cwd=ROOT, text=True, capture_output=True)
        assert run.returncode == 0, run.stdout + run.stderr
        result = json.loads(output_json.read_text(encoding="utf-8"))
        markdown = output_md.read_text(encoding="utf-8")
    assert result["verdict"] == "PASS_FAIL_CLOSED_FUN_18000ADA0_ENTRY_CONTRACT_ORACLE"
    assert result["contract"]["fplane"]["size_bytes"] == 24
    assert result["contract"]["rect"]["order"] == ["left", "top", "right", "bottom"]
    assert result["oracle"]["exclusive_endpoints_proved"] is True
    assert "+0x74" in markdown
    print("PASS: fail-closed FUN_18000ada0 contract and padded-stride oracle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
