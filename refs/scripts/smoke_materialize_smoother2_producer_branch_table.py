#!/usr/bin/env python3
"""Smoke test for materialize_smoother2_producer_branch_table.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "materialize_smoother2_producer_branch_table.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmsm2_producer_branch_") as tmp:
        tmp_path = Path(tmp)
        out_json = tmp_path / "branch_table.json"
        out_md = tmp_path / "branch_table.md"
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--stamp",
                "20990101",
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=ROOT,
            check=True,
        )
        data = json.loads(out_json.read_text(encoding="utf-8"))
        assert data["kind"] == "olmsmoother2_producer_branch_table"
        assert data["leaf_check"]["all_match"] is True
        rows = {row["scenario"]: row for row in data["case_0004"]["rows"]}
        assert rows["force-passthrough"]["vcount"] == 0
        assert rows["force-passthrough"]["emit_guard"] is False
        assert rows["empty-around-cur"]["vcount"] == 3
        assert data["case_0012"]["result"]["e170_c"] == 2
        assert data["case_0012"]["result"]["f270"]["count"] == 1
        text = out_md.read_text(encoding="utf-8")
        assert "OLMSmoother2 Producer Branch Table" in text
        assert "Do not request final writer bytes again" in text
    print("[OK] materialize_smoother2_producer_branch_table smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
