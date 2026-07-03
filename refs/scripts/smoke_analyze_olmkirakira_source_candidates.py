#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmkirakira_source_candidates.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmkirakira_source_candidates_") as tmp:
        out_json = Path(tmp) / "report.json"
        out_md = Path(tmp) / "report.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_olmkirakira_source_candidates.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmkirakira_source_candidates_audit"
        assert report["lane_summary"]["canonical_reference_rgba"] == [131, 131, 131, 255]
        assert report["lane_summary"]["windows_traced_rgba"] == [144, 144, 144, 255]
        assert report["lane_summary"]["current_mac_witness_rgba"] == [144, 144, 144, 255]
        assert report["source_candidates"][0]["site"] == "render_typed_merge_mode_1_screen_compose"
        assert report["source_candidates"][1]["site"] == "add_colored_union_glow_aggregation"
        assert report["source_candidates"][2]["site"] == "params_setup_highlight_ramp_control_surface"
        assert report["source_candidates"][0]["line"] == 456
        assert report["source_candidates"][1]["line"] == 366
        assert report["source_candidates"][2]["line"] == 615
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "OLMKiraKira Source-Candidates Audit",
            "render_typed_merge_mode_1_screen_compose",
            "add_colored_union_glow_aggregation",
            "params_setup_highlight_ramp_control_surface",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] OLMKiraKira source-candidates smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
