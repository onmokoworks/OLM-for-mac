#!/usr/bin/env python3
"""Smoke test for analyze_distancegradation_both_add_overlap.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/analyze_distancegradation_both_add_overlap.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmdg_both_add_overlap_") as tmp:
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
        assert data["kind"] == "olmdistancegradation_both_add_overlap_audit"
        assert data["both_case_count"] >= 1
        assert data["decision"] == "no-current-fullres-add-vs-max-lever"
        assert data["divergent_case_count"] == 0
        assert data["total_divergent_px"] == 0
        text = out_md.read_text(encoding="utf-8")
        assert "BOTH add-vs-max overlap audit" in text
        assert "no-current-fullres-add-vs-max-lever" in text
    print("[OK] DistanceGradation BOTH add-vs-max overlap smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
