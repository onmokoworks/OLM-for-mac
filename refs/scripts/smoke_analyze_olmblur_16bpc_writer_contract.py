#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmblur_16bpc_writer_contract.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmblur_writer_contract_") as tmp:
        out_json = Path(tmp) / "writer_contract.json"
        out_md = Path(tmp) / "writer_contract.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_olmblur_16bpc_writer_contract.py"),
                "--summary-json",
                str(out_json),
                "--summary-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmblur_16bpc_writer_contract_audit"
        assert report["decision"] == "source-writer-mismatch-real-but-not-yet-sufficient-for-global-swap"
        assert report["mac_source_writer"]["nonlegacy_round_expr"] == "nearbyintf(v)"
        assert report["mac_source_writer"]["legacy_round_expr"] == "floorf(v + 0.5f)"
        assert report["windows_standard_writer"]["classification"] == "round-add-helper-truncate-word-store"
        assert report["mac_vs_windows_standard"]["nonlegacy_rounding_expression_matches_standard_16bpc"] is False
        assert report["residual_context"]["nonlegacy_sign_mixed_one_word_cases"] == 6
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "Current Mac source non-legacy store16 path",
            "Windows standard 16bpc writer asm",
            "source-writer-mismatch-real-but-not-yet-sufficient-for-global-swap",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] OLMBlur 16bpc writer contract smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
