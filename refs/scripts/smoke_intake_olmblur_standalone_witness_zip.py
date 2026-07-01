#!/usr/bin/env python3
"""Smoke-test scripts/intake_olmblur_standalone_witness_zip.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    root = repo_root()
    script = root / "scripts" / "intake_olmblur_standalone_witness_zip.py"
    source_zip = Path("/Volumes/onmk/olm_pr/new/olmblur_case0007_16bpc_345_672_b_witness_windows_20260630.zip")
    with tempfile.TemporaryDirectory(prefix="olmblur_standalone_witness_") as td:
        out_json = Path(td) / "intake.json"
        out_md = Path(td) / "intake.md"
        proc = subprocess.run(
            [sys.executable, str(script), str(source_zip), "--output-json", str(out_json), "--output-md", str(out_md)],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="")
        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert payload["kind"] == "olmblur_standalone_witness_intake"
        assert payload["case_id"] == "olmblur__case_0007"
        assert payload["target"]["x"] == 345
        assert payload["target"]["y"] == 672
        assert payload["target_channel_pre_store_float"] == 12544.498046875
        assert payload["final_word"]["decimal"] == 12544
        md = out_md.read_text(encoding="utf-8")
        for needle in ("Standalone Witness Intake", "12544.498046875", "12544", "case_0007"):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle!r}")
    print("[OK] OLMBlur standalone witness intake smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
