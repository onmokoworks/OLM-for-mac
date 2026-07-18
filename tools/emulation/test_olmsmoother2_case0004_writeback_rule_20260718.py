#!/usr/bin/env python3
"""Regression gate for the bounded case_0004 writeback audit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "tools/emulation/audit_olmsmoother2_case0004_writeback_rule_20260718.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmsmoother2-case0004-writeback-") as directory:
        out = Path(directory)
        result = subprocess.run(
            [sys.executable, str(AUDIT), "--output-json", str(out / "report.json"), "--output-md", str(out / "report.md")],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        report = json.loads((out / "report.json").read_text(encoding="utf-8"))
        assert report["verdict"] == "PASS_BOUNDED_WRITER_RULE_NEXT_SAME_RUN_FLOAT_WITNESS"
        assert report["straight_case"]["aex_memory_hex"] == "71cecece"
        assert report["case0012"]["matches_retained_windows_record"] is True
        assert report["retained_case0004"]["straight_replay_matches"] is False
        assert report["candidate_replays"]["premultiplied_rgb"]["aex_memory_hex"] == "715b5b5b"
        assert report["candidate_replays"]["unpremultiplied_rgb_clamped"]["aex_memory_hex"] == "71ffffff"
        assert "same-run case_0004 typed PF8 worker-entry float4 bits" in report["next_missing_witness"]
        assert "PASS_BOUNDED_WRITER_RULE_NEXT_SAME_RUN_FLOAT_WITNESS" in result.stdout
    print("PASS_SMOOTHER2_CASE0004_BOUNDED_WRITEBACK_RULE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
