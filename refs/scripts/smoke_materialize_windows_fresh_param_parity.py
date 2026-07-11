#!/usr/bin/env python3
"""Smoke test for materialize_windows_fresh_param_parity.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "materialize_windows_fresh_param_parity.py"
DEFAULTS_MANIFEST = (
    ROOT
    / "refs"
    / "win_references"
    / "olm_fresh_instance_defaults_20260629"
    / "OLMmulti-effectdefaultcapture"
    / "reference_manifest.json"
)
RANGES_MANIFEST = (
    ROOT
    / "refs"
    / "win_references"
    / "olm_fresh_instance_ranges_20260629"
    / "OLMmulti-effectrangecapture"
    / "reference_manifest.json"
)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_fresh_param_parity_smoke_") as tmp:
        tmp_path = Path(tmp)
        out_json = tmp_path / "out.json"
        out_md = tmp_path / "out.md"
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--defaults-manifest",
                str(DEFAULTS_MANIFEST),
                "--ranges-manifest",
                str(RANGES_MANIFEST),
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
        assert data["kind"] == "windows_fresh_param_parity_summary"
        assert any(row["plugin"] == "OLMColorKey" for row in data["plugins"])
        text = out_md.read_text(encoding="utf-8")
        assert "Windows Fresh Parameter Parity Audit" in text
        assert "`OLMColorKey`" in text
    print("[OK] materialize_windows_fresh_param_parity smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
