#!/usr/bin/env python3
"""Smoke test for materialize_16bpc_exact_manifest.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "materialize_16bpc_exact_manifest.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_16bpc_manifest_smoke_") as tmp:
        tmp_path = Path(tmp)
        out_json = tmp_path / "out.json"
        out_md = tmp_path / "out.md"
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--manifest-json",
                str(out_json),
                "--summary-md",
                str(out_md),
                "--stamp",
                "20990101",
            ],
            check=True,
        )
        data = json.loads(out_json.read_text(encoding="utf-8"))
        assert data["scope"] == "covered 16bpc AE-host exact slices"
        assert data["summary"]["counts"].get("AE exact") == 12
        text = out_md.read_text(encoding="utf-8")
        assert "OLMColorKey" in text
        assert "OLMToonDilate" in text
    print("[OK] materialize_16bpc_exact_manifest smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
