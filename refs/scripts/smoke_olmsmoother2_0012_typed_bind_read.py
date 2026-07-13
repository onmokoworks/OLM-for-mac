#!/usr/bin/env python3
"""Smoke the Smoother2 0012 audit against the current pending package."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = Path(__file__).with_name("analyze_olmsmoother2_0012_typed_bind_read.py")
PACKAGE = ROOT / "refs/runtime_trace_packages/olm_smoother2_current_aex_0012_typed_bind_read_20260710.zip"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="smoother2_smoke_") as directory:
        output = Path(directory) / "audit.json"
        proc = subprocess.run([sys.executable, str(AUDIT), "--package", str(PACKAGE), "--json-output", str(output)], text=True, capture_output=True)
        if proc.returncode != 2:
            print(proc.stdout, end="")
            print(proc.stderr, end="", file=sys.stderr)
            return 1
        report = json.loads(output.read_text(encoding="utf-8"))
        expected = {"request_manifest_scope", "request_contract_present", "local_c280_cce0_replay"}
        labels = {item["label"] for item in report["checks"]}
        if report["verdict"] != "BLOCKED_MISSING_LIVE_TYPED_BINDING" or not expected <= labels:
            print(json.dumps(report, indent=2), file=sys.stderr)
            return 1
    print("PASS Smoother2 0012 typed bind/read audit fails closed on pending request package")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
