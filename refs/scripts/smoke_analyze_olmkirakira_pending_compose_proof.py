#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmkirakira_pending_compose_proof.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmkirakira_pending_compose_") as tmp:
        out_json = Path(tmp) / "pending_compose.json"
        out_md = Path(tmp) / "pending_compose.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_olmkirakira_pending_compose_proof.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmkirakira_pending_compose_proof"
        assert report["status"] == "historical-superseded-by-hotspot-provenance-lane"
        assert report["superseded_by"]["report"].endswith("refs/conformance/olmkirakira_hotspot_export_contract_audit_20260701.md")
        assert "runtime_trace_summary_kirakira_aggregation_compose_bt709_20260629_235638.json" in report["latest_runtime_summary"]
        assert report["hotspot_targets"]["primary_vertical_case"]["xy"] == [934, 118]
        assert report["windows_trace_gap"]["residual_hotspot_xy"] == [934, 118]
        assert report["windows_trace_gap"]["latest_runtime_note"]["merge_mode_1_compose"]["internal_compose_float_status"] == "not isolated by this breakpoint set"
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "Historical status",
            "Superseded by",
            "Latest runtime summary",
            "Residual Hotspot Targets",
            "934, 118",
            "compose_internal_float",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] OLMKiraKira pending compose proof smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
