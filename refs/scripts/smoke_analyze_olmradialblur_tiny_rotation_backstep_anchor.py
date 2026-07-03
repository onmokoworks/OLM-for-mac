#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmradialblur_tiny_rotation_backstep_anchor.py."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmrb_tiny_rotation_backstep_anchor_") as tmp:
        out_json = Path(tmp) / "report.json"
        out_md = Path(tmp) / "report.md"
        subprocess.run(
            [
                "python3",
                str(root / "scripts" / "analyze_olmradialblur_tiny_rotation_backstep_anchor.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            check=True,
        )
        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert payload["kind"] == "olmradialblur_tiny_rotation_backstep_anchor_audit"
        assert payload["witness_xy"] == [1614, 6]
        assert payload["inverse_sampler_anchor"]["indices"] == [1603, 1604, 844, 845]
        assert payload["direct_support"]["same_row_direct_source_cells_all_black"] is True
        assert payload["upstream_candidate_family"]["dominant_cluster_rows"] == [843]
        assert payload["wanted_chain"] == ["+0xf252", "+0xf250", "+0xe"]
        assert payload["active_contract_path"].endswith("olmradialblur_tiny_rotation_anchor_watch_followup_contract_20260701.md")
        assert payload["historical_predecessor_contract_path"].endswith("olmradialblur_tiny_rotation_backstep_followup_contract_20260701.md")
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "Backstep Anchor Audit",
            "Active contract",
            "Inverse-Sampler Anchor",
            "Nearest Upstream Positive Family",
            "Windows Anchor-Watch Ask",
            "Preferred retained caller-side chain",
        ):
            assert needle in md, needle
    print("[OK] OLMRadialBlur tiny Rotation backstep-anchor smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
