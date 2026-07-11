#!/usr/bin/env python3
"""Smoke-test the bounded DirectionalBlur rowdriver typed classifier."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    probe = repo / "tools/emulation/probe_dblur_case0001_row169_typed_classifier.py"
    with tempfile.TemporaryDirectory(prefix="dblur-row169-smoke-") as tmp:
        out = Path(tmp)
        proc = subprocess.run([sys.executable, str(probe), "--output-json", str(out / "result.json"),
                               "--output-md", str(out / "result.md")], cwd=repo,
                              text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(proc.stdout, end="")
        if proc.returncode not in (0, 2):
            return proc.returncode
        data = json.loads((out / "result.json").read_text(encoding="utf-8"))
        if data.get("status") == "ok":
            records = data.get("records", [])
            if [row.get("xy") for row in records] != [[x, 169] for x in range(487, 495)] + [[579, 169]]:
                print("[FAIL] row169 strip/witness records are incomplete")
                return 1
            required = {"valid", "component", "param_11", "span", "reach", "outside_valid_source_range", "span_le_1", "classification"}
            if any(not required.issubset(row) for row in records):
                print("[FAIL] typed classifier fields are incomplete")
                return 1
        else:
            blocked = data.get("blocked")
            if not isinstance(blocked, dict) or not blocked.get("reason") or not isinstance(blocked.get("missing"), list):
                print("[FAIL] blocked result is not machine-readable")
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
