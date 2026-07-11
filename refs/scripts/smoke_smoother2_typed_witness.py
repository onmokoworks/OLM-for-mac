#!/usr/bin/env python3
"""Smoke test the bounded OLMSmoother2 typed witness."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tools" / "emulation" / "test_smoother2_typed_witness.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmsm2_typed_witness_") as tmp:
        tmp_path = Path(tmp)
        out_json = tmp_path / "typed_witness.json"
        out_md = tmp_path / "typed_witness.md"
        subprocess.run(
            [sys.executable, str(PROBE), "--output-json", str(out_json), "--output-md", str(out_md)],
            cwd=ROOT,
            check=True,
        )
        result = json.loads(out_json.read_text(encoding="utf-8"))
        assert result["kind"] == "olmsmoother2_typed_witness"
        assert result["status"] == "local-aex-cpu-execution"
        assert result["claim_boundary"].startswith("This is not Windows truth")
        assert result["assertions"]["expected_shape_matches"] is True
        rows = {row["name"]: row for row in result["cases"]}
        assert rows["legacy_current_aex"]["descriptor"] == [91, 841, 1, 91, 843, 5]
        assert rows["legacy_current_aex"]["e170"]["c"] == 2
        assert rows["legacy_current_aex"]["f270"]["append"] is True
        assert rows["legacy_current_aex"]["e3a0"]["append"] is True
        assert rows["legacy_current_aex"]["append"] is True
        assert rows["control_suppressing"]["e170"]["c"] == 4
        assert rows["control_suppressing"]["f270"]["append"] is False
        assert rows["control_suppressing"]["e3a0"]["append"] is True
        assert rows["control_suppressing"]["append"] is False
        assert "not Windows truth" in out_md.read_text(encoding="utf-8")
    print("[OK] OLMSmoother2 typed witness smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
