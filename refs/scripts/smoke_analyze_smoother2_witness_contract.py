#!/usr/bin/env python3
"""Smoke-test scripts/analyze_smoother2_witness_contract.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmsmoother2_witness_contract_") as tmp:
        tmp_path = Path(tmp)
        output_json = tmp_path / "witness_contract.json"
        output_md = tmp_path / "witness_contract.md"
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/analyze_smoother2_witness_contract.py",
                "--output-json",
                str(output_json),
                "--output-md",
                str(output_md),
            ],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="")
        if proc.returncode != 0:
            return proc.returncode
        report = json.loads(output_json.read_text(encoding="utf-8"))
        if report.get("kind") != "olmsmoother2_current_aex_witness_contract":
            raise AssertionError(report.get("kind"))
        classes = {row["case_id"]: row["local_classification"] for row in report["witnesses"]}
        if classes.get("legacy_case_0004_current_aex") != "local-transparent-center-no-polygon-passthrough":
            raise AssertionError(classes)
        if classes.get("legacy_case_0012_gamma5_red_blue_current_aex") != "local-cardinal6-f270-e3a0-append":
            raise AssertionError(classes)
        if report["rejected_global_toggles"].get("curve_idx") != "rejected-inert":
            raise AssertionError(report["rejected_global_toggles"])
        if report["rejected_global_toggles"].get("f270_suppression") != "rejected-worse":
            raise AssertionError(report["rejected_global_toggles"])
        md = output_md.read_text(encoding="utf-8")
        if "blocked-narrow-proof-only" not in md or "cardinal6" not in md:
            raise AssertionError("markdown missing witness classification")
    print("[OK] Smoother2 witness contract smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
