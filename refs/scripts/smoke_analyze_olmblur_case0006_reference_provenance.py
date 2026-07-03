#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmblur_case0006_reference_provenance.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmblur_case0006_provenance_") as tmp:
        out_json = Path(tmp) / "report.json"
        out_md = Path(tmp) / "report.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_olmblur_case0006_reference_provenance.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmblur_case0006_reference_provenance_audit"
        assert report["canonical_vs_handoff_identical"] is True
        assert report["outcome"]["status"] == "current-aex-export-missing"
        files = report["files"]
        assert files["canonical_ref"]["sha256"] == files["handoff_expected"]["sha256"]
        assert files["handoff_results_export"]["sha256"] == files["mac_single_export"]["sha256"]
        assert files["archive_results_export"]["sha256"] == files["mac_batch_export"]["sha256"]
        alias_roles = [tuple(group["roles"]) for group in report["alias_groups"]]
        assert ("handoff_results_export", "mac_single_export") in alias_roles
        assert ("archive_results_export", "mac_batch_export") in alias_roles
        assert report["result_metadata"]["handoff_result_json"]["request_id"] == "ae_pixel_bitdepth16_olmblur_exact_20260625"
        pts = report["point_values"]
        assert pts["canonical_ref"]["314,14"] == [2201, 2201, 2201, 65535]
        assert pts["mac_single_export"]["314,14"] == [2199, 2199, 2199, 65535]
        assert pts["mac_batch_export"]["314,14"] == [2201, 2201, 2201, 65535]
        assert report["point_role_matrix"]["314,14"]["match_roles"] == ["mac_batch_matches_canonical"]
        assert report["point_role_matrix"]["29,71"]["match_roles"] == ["mac_single_matches_mac_batch"]
        assert report["overall_point_pattern"]["counts"]["mac_batch_matches_canonical"] == 2
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "OLMBlur case_0006 Reference Provenance Audit",
            "current-aex-export-missing",
            "Alias Groups",
            "(314,14)",
            "Point-Role Matrix",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] OLMBlur case_0006 provenance smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
