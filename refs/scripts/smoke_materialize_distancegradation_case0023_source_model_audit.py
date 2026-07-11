#!/usr/bin/env python3
"""Smoke test for materialize_distancegradation_case0023_source_model_audit.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "materialize_distancegradation_case0023_source_model_audit.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmdg_case0023_source_model_") as tmp:
        tmp_path = Path(tmp)
        out_json = tmp_path / "source_model.json"
        out_md = tmp_path / "source_model.md"
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
        assert data["kind"] == "olmdistancegradation_case0023_source_model_audit"
        assert data["status"] == "source-model-matches-aex-helper-samples"
        assert len(data["samples"]) == 10
        assert all(row["match"] for row in data["samples"])
        assert any(
            row["xy"] == [1699, 7]
            and row["mac_source_model"]["both_add_saturate_field"] == 0.0
            and row["aex_cpu_helper"]["both_add_saturate_field"] == 0.0
            for row in data["samples"]
        )
        text = out_md.read_text(encoding="utf-8")
        assert "Source Model Audit" in text
        assert "Mac inside" in text
    print("[OK] materialize_distancegradation_case0023_source_model_audit smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
