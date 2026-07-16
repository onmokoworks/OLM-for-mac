#!/usr/bin/env python3
"""Smoke test for the unique-family c280 oracle evidence."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/emulation/test_olmsmoother2_case0012_c280_unique_family_oracle_20260717.py"


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory)
        result = subprocess.run([sys.executable, str(SCRIPT), "--output-json", str(output / "report.json"), "--output-md", str(output / "report.md")], cwd=ROOT, check=True, capture_output=True, text=True)
        report = json.loads(result.stdout)
    assert report["unique_classifier_indices"] == ["0x00", "0x42", "0x5a", "0xff"]
    assert report["family_counts"] == {"0x00": 8, "0x42": 2, "0x5a": 2, "0xff": 18}
    assert len(report["portable_checks"]) == 8
    assert all(item["status"] == "exact" for item in report["portable_checks"])
    assert report["first_missing_semantic"]["helper"] == "FUN_180013630@0x180013630"
    print("PASS unique-family c280 oracle smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
