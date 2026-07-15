#!/usr/bin/env python3
"""Smoke-test the local KiraKira aggregation/quantization invariant."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmkirakira_quantization_invariant_") as tmp:
        out_json = Path(tmp) / "report.json"
        out_md = Path(tmp) / "report.md"
        subprocess.run(
            [sys.executable, str(root / "scripts/analyze_olmkirakira_aggregation_quantization_invariant_20260715.py"), "--output-json", str(out_json), "--output-md", str(out_md)],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmkirakira_aggregation_quantization_invariant"
        assert report["status"] == "local-invariant-proven"
        assert report["summary"] == {"complete_count": 1, "incomplete_count": 3, "passed_count": 1, "point_count": 4}
        check = next(item for item in report["checks"] if item["status"] == "pass")
        assert check["predicted_u8"] == [144, 144, 144, 255]
        assert check["max_abs_error"] <= 1e-6
        md = out_md.read_text(encoding="utf-8")
        for needle in ("local-invariant-proven", "Witness checks", "144, 144, 144, 255", "does not claim AE exactness"):
            assert needle in md, needle
    print("[OK] OLMKiraKira aggregation/quantization invariant smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
