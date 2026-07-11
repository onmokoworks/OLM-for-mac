#!/usr/bin/env python3
"""Smoke test for materialize_32bpc_probe_status.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "materialize_32bpc_probe_status.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_32bpc_probe_status_smoke_") as tmp:
        tmp_path = Path(tmp)
        out_json = tmp_path / "out.json"
        out_md = tmp_path / "out.md"
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
                "--stamp",
                "20990101",
            ],
            check=True,
        )
        data = json.loads(out_json.read_text(encoding="utf-8"))
        assert data["kind"] == "olm_32bpc_probe_status"
        assert len(data["suites"]) == 3
        by_scope = {(row["plugin"], row["scope"]): row for row in data["suites"]}
        assert by_scope[("OLMColorKey", "focused 32bpc probe")]["classification"] == "probe-only-png-return"
        assert by_scope[("OLMColorKey", "focused 32bpc probe")]["float_preserving_present"] is False
        assert by_scope[("Cross-plugin batch", "broad 32bpc full probe")]["classification"] == "probe-only-png-return"
        assert "PNG-only/non-float-preserving" in by_scope[("Cross-plugin batch", "broad 32bpc full probe")]["reference_quality_reason"]
        assert by_scope[("Cross-plugin batch", "broad 32bpc EXR-first rerun")]["classification"] == "probe-only-png-return"
        assert "PNG-only/non-float-preserving" in by_scope[("Cross-plugin batch", "broad 32bpc EXR-first rerun")]["reference_quality_reason"]
        text = out_md.read_text(encoding="utf-8")
        assert "probe-only" in text
        assert "float-preserving" in text
    print("[OK] materialize_32bpc_probe_status smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
