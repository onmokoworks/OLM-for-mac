#!/usr/bin/env python3
"""Smoke-test OLMBlur 16bpc word-delta audit generation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmblur_word_delta_smoke_") as tmp:
        tmp_path = Path(tmp)
        out_json = tmp_path / "audit.json"
        out_md = tmp_path / "audit.md"
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "analyze_olmblur_16bpc_word_delta.py"),
                "--summary-json",
                str(out_json),
                "--summary-md",
                str(out_md),
            ],
            cwd=ROOT,
            check=True,
        )
        data = json.loads(out_json.read_text(encoding="utf-8"))
        if data.get("kind") != "olmblur_16bpc_word_delta_audit":
            raise AssertionError("unexpected audit kind")
        cases = data.get("cases")
        if not isinstance(cases, list) or len(cases) != 7:
            raise AssertionError("expected seven OLMBlur 16bpc cases")
        classes = {row.get("case_id"): row.get("classification") for row in cases if isinstance(row, dict)}
        for case_num in range(1, 7):
            case_id = f"case_{case_num:04d}"
            if classes.get(case_id) != "sign-mixed-one-word":
                raise AssertionError(f"unexpected class for {case_id}: {classes.get(case_id)}")
        if classes.get("case_0007") != "legacy-border-plus-one-word":
            raise AssertionError(f"unexpected class for case_0007: {classes.get('case_0007')}")
        max_values = {row.get("case_id"): row.get("max_exported_delta") for row in cases if isinstance(row, dict)}
        if max_values.get("case_0007") != 383:
            raise AssertionError("expected case_0007 max_exported_delta=383")
        if not out_md.read_text(encoding="utf-8").startswith("# OLMBlur 16bpc Word-Delta Audit"):
            raise AssertionError("markdown output missing expected title")
    print("[OK] OLMBlur 16bpc word-delta audit smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
