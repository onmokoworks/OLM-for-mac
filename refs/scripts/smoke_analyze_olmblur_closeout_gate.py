#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmblur_closeout_gate.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmblur_closeout_gate_") as tmp:
        out_json = Path(tmp) / "report.json"
        out_md = Path(tmp) / "report.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_olmblur_closeout_gate.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmblur_closeout_gate_audit"
        assert report["decision"]["status"] == "do-not-reopen-source-without-two-specific-external-proofs"
        lanes = {row["lane"]: row for row in report["lanes"]}
        assert lanes["case_0006_nonlegacy_16bpc"]["status"] == "outcome-a-current-aex-matches-canonical"
        assert lanes["case_0007_legacy_16bpc"]["status"] == "resolved-as-pre-store-float-delta"
        assert lanes["case_0007_legacy_8bpc_old_normalized"]["status"] == "still-needs-windows-pre-store-float"
        assert lanes["case_0006_nonlegacy_16bpc"]["key_points"][0]["xy"] == [314, 14]
        assert lanes["case_0007_legacy_8bpc_old_normalized"]["key_points"][0]["xy"] == [488, 941]
        assert report["supporting_evidence"]["case0006_contract_status"] == "outcome-a-current-aex-matches-canonical"
        assert report["supporting_evidence"]["case0006_provenance_status"] == "current-aex-export-missing"
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "OLMBlur Closeout Gate Audit",
            "case_0006_nonlegacy_16bpc",
            "case_0007_legacy_16bpc",
            "case_0007_legacy_8bpc_old_normalized",
            "outcome-a-current-aex-matches-canonical",
            "do-not-reopen-source-without-two-specific-external-proofs",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] OLMBlur closeout gate smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
