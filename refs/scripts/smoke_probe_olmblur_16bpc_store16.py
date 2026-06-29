#!/usr/bin/env python3
"""Smoke test for the bounded OLMBlur 16bpc store16 probe driver."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmblur_store16_probe_smoke_") as tmp:
        out_dir = Path(tmp) / "probe"
        proc = subprocess.run(
            [
                sys.executable,
                "scripts/probe_olmblur_16bpc_store16.py",
                "--dry-run",
                "--output-dir",
                str(out_dir),
            ],
            cwd=repo,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="")
        report = json.loads((out_dir / "probe_report.json").read_text(encoding="utf-8"))
        assert report["dry_run"] is True
        assert report["case_ids"] == ["olmblur__case_0006", "olmblur__case_0007"]
        assert report["points"] == "314,14;29,71;0,0;951,7"
        commands = report["cases"]
        assert len(commands) == 2
        assert "OLMBLUR_DEBUG_DUMP_PATH" in " ".join(commands[0]["command"])
        assert "OLMBLUR_DEBUG_POINTS=314,14;29,71;0,0;951,7" in " ".join(commands[0]["command"])
    print("[OK] OLMBlur 16bpc store16 probe smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
