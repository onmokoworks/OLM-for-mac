#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/emulation/test_olmsmoother2_case0012_c280_5a_oracle_20260717.py"


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        out = Path(directory)
        result = subprocess.run([sys.executable, str(SCRIPT), "--output-json", str(out / "r.json"), "--output-md", str(out / "r.md")], cwd=ROOT, check=True, capture_output=True, text=True)
        report = json.loads(result.stdout)
    assert report["verdict"] == "PASS_EXACT_C280_0X5A_EMPTY_PATH_ORACLE"
    assert len(report["cases_0x5a"]) == 2
    assert all(item["status"] == "exact_empty" for item in report["comparisons_0x5a"])
    assert report["first_new_owner"] is None
    print("PASS 0x5a oracle smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
