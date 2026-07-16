#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/emulation/test_olmsmoother2_case0012_c280_weight42_oracle_20260717.py"


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        out = Path(directory)
        result = subprocess.run([sys.executable, str(SCRIPT), "--output-json", str(out / "r.json"), "--output-md", str(out / "r.md")], cwd=ROOT, check=True, capture_output=True, text=True)
        report = json.loads(result.stdout)
    assert report["verdict"] == "PASS_EXACT_C280_0X42_WEIGHT_ORACLE_STOPPED_AT_0X5A_OWNER"
    assert len(report["cases_0x42"]) == 2
    assert all(item["status"] == "exact" for item in report["comparisons_0x42"])
    assert report["next_family"]["owner"] == "FUN_18000ec40@0x18000ec40"
    print("PASS 0x42 weight oracle smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
