#!/usr/bin/env python3
"""Smoke test for the DG 0010/0011 AEX fieldgen materializer."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmdg_0010_0011_fieldgen_") as td:
        out = Path(td)
        json_path = out / "fieldgen.json"
        md_path = out / "fieldgen.md"
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/materialize_distancegradation_0010_0011_aex_fieldgen_probe.py"),
                "--output-json",
                str(json_path),
                "--output-md",
                str(md_path),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        print(proc.stdout, end="")
        if proc.returncode != 0:
            return proc.returncode
        report = json.loads(json_path.read_text(encoding="utf-8"))
        assert report["decision"] == "fieldgen-floats-match-current-mac-but-pack-rule-sign-flips"
        assert len(report["probes"]) == 3
        assert any(row["windows_required_matches_floor"] for row in report["probes"])
        assert any(row["windows_required_matches_ceil"] for row in report["probes"])
        md = md_path.read_text(encoding="utf-8")
        assert "field-world pack/consume" in md
    print("smoke_materialize_distancegradation_0010_0011_aex_fieldgen_probe OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
