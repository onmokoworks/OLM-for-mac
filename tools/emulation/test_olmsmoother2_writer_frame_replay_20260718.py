#!/usr/bin/env python3
"""Regression gate for the observed Smoother2 writer-frame replay."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "tools/emulation/audit_olmsmoother2_writer_frame_replay_20260718.py"


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        out = Path(directory)
        result = subprocess.run(
            [sys.executable, str(AUDIT), "--output-json", str(out / "report.json"), "--output-md", str(out / "report.md")],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        report = json.loads((out / "report.json").read_text(encoding="utf-8"))
        assert report["verdict"] == "PARTIAL_SMOOTHER2_OBSERVED_WRITER_FRAME_REPLAY"
        assert len(report["cases"]) == 2
        assert report["cases"][0]["writer_replay_classification"] == "not_reproduced_from_supplied_float_tuple"
        assert report["cases"][1]["writer_replay_classification"] == "reproduced"
        assert "No production plugin source was changed." in report["facts"]
        assert "Upstream config/crop/classifier/c280/cce0 semantics remain unresolved." in report["inferences"]
        assert "PARTIAL_SMOOTHER2_OBSERVED_WRITER_FRAME_REPLAY" in result.stdout
    print("PASS_SMOOTHER2_WRITER_FRAME_REPLAY_AUDIT_CLASSIFICATION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
