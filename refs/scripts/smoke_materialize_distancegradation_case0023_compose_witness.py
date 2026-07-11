#!/usr/bin/env python3
"""Smoke test for materialize_distancegradation_case0023_compose_witness.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "materialize_distancegradation_case0023_compose_witness.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmdg_case0023_compose_") as tmp:
        tmp_path = Path(tmp)
        out_json = tmp_path / "compose.json"
        out_md = tmp_path / "compose.md"
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
        assert data["kind"] == "olmdistancegradation_case0023_compose_witness"
        assert data["status"] == "compose-writeback-triplet-binary-grounded"
        assert data["leaf_check"]["use_bg_on"]["match"] is True
        assert data["leaf_check"]["use_bg_off"]["match"] is True
        assert len(data["triplet"]) == 3
        assert all(row["match_promoted"] for row in data["triplet"])
        assert any(row["xy"] == [414, 393] and row["promoted_rgba"] == [7195, 0, 61165, 65535] for row in data["triplet"])
        text = out_md.read_text(encoding="utf-8")
        assert "Compose Witness" in text
        assert "compose/writeback" in text
    print("[OK] materialize_distancegradation_case0023_compose_witness smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
