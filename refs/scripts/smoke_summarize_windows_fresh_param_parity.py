#!/usr/bin/env python3
"""Smoke-test scripts/summarize_windows_fresh_param_parity.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run(cmd: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def main() -> int:
    root = repo_root()
    script = root / "scripts" / "summarize_windows_fresh_param_parity.py"
    with tempfile.TemporaryDirectory(prefix="olm_param_parity_smoke_") as tmp:
        out_json = Path(tmp) / "summary.json"
        out_md = Path(tmp) / "summary.md"
        run(
            [
                sys.executable,
                str(script),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            root,
        )
        data = json.loads(out_json.read_text(encoding="utf-8"))
        assert data["kind"] == "windows_fresh_param_parity_summary"
        by_plugin = {row["plugin"]: row for row in data["plugins"]}
        assert by_plugin["OLMBlur"]["defaults_status"] == "fixed"
        assert by_plugin["OLMKiraKira"]["ranges_status"] == "needs-followup"
        assert by_plugin["OLMRadialBlur"]["ranges_status"] == "mostly-fixed"
        assert by_plugin["OLMRadialBlur"]["overall_status"] == "mostly-fixed"
        assert by_plugin["OLMDirectionalBlur"]["overall_status"] == "mostly-fixed"
        text = out_md.read_text(encoding="utf-8")
        assert "Windows Fresh Parameter Parity Summary" in text
        assert "`OLMKiraKira`" in text
    print("[OK] summarize Windows fresh param parity smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
