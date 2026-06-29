#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmblur_16bpc_proof_plan.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmblur16_proof_plan_") as tmp:
        out_dir = Path(tmp) / "report"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_olmblur_16bpc_proof_plan.py"),
                "--output-dir",
                str(out_dir),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads((out_dir / "proof_plan.json").read_text(encoding="utf-8"))
        assert report["kind"] == "olmblur_16bpc_proof_plan"
        assert report["decision"] == "prewriteback-helper-proof-before-writer-swap"
        assert report["nonlegacy_case_0006"]["witness_positive_word"]["xy"] == [314, 14]
        assert report["nonlegacy_case_0006"]["witness_negative_word"]["xy"] == [29, 71]
        assert report["legacy_case_0007"]["witness_major_border_seed"]["xy"] == [0, 0]
        assert report["writer_contract"]["blind_global_swap_allowed"] is False
        md = (out_dir / "proof_plan.md").read_text(encoding="utf-8")
        for needle in ("case_0006", "case_0007", "Blind global swap allowed: `False`"):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] OLMBlur 16bpc proof plan smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
