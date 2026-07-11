#!/usr/bin/env python3
"""Smoke test for analyze_distancegradation_0010_0011_field_pack_read.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/analyze_distancegradation_0010_0011_field_pack_read.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmdg_0010_field_pack_") as tmp:
        tmp_path = Path(tmp)
        out_json = tmp_path / "audit.json"
        out_md = tmp_path / "audit.md"
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=ROOT,
            check=True,
        )
        data = json.loads(out_json.read_text(encoding="utf-8"))
        assert data["kind"] == "olmdistancegradation_0010_0011_field_pack_read_audit"
        assert data["decision"] == "field-pack-alone-insufficient-sign-flipped-boundary"
        assert len(data["witnesses"]) == 3
        by_xy = {tuple(row["xy"]): row for row in data["witnesses"]}
        assert by_xy[(6, 40)]["windows_field_word_required"] == 29500
        assert by_xy[(901, 394)]["windows_field_word_required"] == 22892
        assert by_xy[(915, 392)]["windows_field_word_required"] == 4409
        assert by_xy[(6, 40)]["models"]["floor_mac_field_word"]["matches_windows_store"]
        assert by_xy[(901, 394)]["models"]["ceil_mac_field_word"]["matches_windows_store"]
        text = out_md.read_text(encoding="utf-8")
        assert "field-pack/read audit" in text
        assert "Do not change global output rounding" in text
    print("[OK] DistanceGradation 0010/0011 field-pack/read smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
