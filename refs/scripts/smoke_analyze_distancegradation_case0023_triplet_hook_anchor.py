#!/usr/bin/env python3
"""Smoke-test scripts/analyze_distancegradation_case0023_triplet_hook_anchor.py."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmdg_case0023_triplet_hook_anchor_") as tmp:
        out_json = Path(tmp) / "report.json"
        out_md = Path(tmp) / "report.md"
        subprocess.run(
            [
                "python3",
                str(root / "scripts" / "analyze_distancegradation_case0023_triplet_hook_anchor.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            check=True,
        )
        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert payload["kind"] == "olmdistancegradation_case0023_triplet_hook_anchor_audit"
        assert payload["triplet_xy"] == [[414, 393], [415, 393], [416, 393]]
        assert payload["current_local_field_boundary"]["first_above_xy"] == [415, 393]
        assert payload["current_local_field_boundary"]["first_above_field_x"] == 1.0
        assert "FUN_181170480 consumed value" in payload["wanted_fields"]
        assert payload["contract_path"].endswith("olmdistancegradation_case0023_output_word_triplet_followup_contract_20260701.md")
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "Triplet Hook Anchor Audit",
            "Same-Row Triplet",
            "Windows Hook Ask",
            "first above-threshold point",
            "output-word address",
        ):
            assert needle in md, needle
    print("[OK] OLMDistanceGradation case_0023 triplet-hook-anchor smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
