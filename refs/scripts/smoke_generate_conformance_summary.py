#!/usr/bin/env python3
"""Smoke-test the packaged 8bpc conformance summary generator."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_conformance_summary_smoke_") as tmp:
        tmp_path = Path(tmp)
        manifest_json = tmp_path / "manifest.json"
        summary_json = tmp_path / "summary.json"
        summary_md = tmp_path / "summary.md"
        subprocess.run(
            [
                sys.executable,
                "scripts/generate_conformance_summary.py",
                "--manifest-json",
                str(manifest_json),
                "--summary-json",
                str(summary_json),
                "--summary-md",
                str(summary_md),
            ],
            cwd=ROOT,
            check=True,
        )
        manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
        summary = manifest["summary"]
        assert manifest["kind"] == "olm_conformance_manifest"
        assert summary["total_cases"] == 70
        assert summary["counts"]["AE exact"] == 62
        assert summary["counts"].get("AE residual", 0) == 0
        assert summary["counts"]["reference-generation split"] == 1
        assert summary["counts"]["known-red"] == 7
        assert summary["by_plugin"]["OLMBlur"]["AE exact"] == 7
        blur_suite = next(row for row in manifest["suites"] if row["plugin"] == "OLMBlur")
        assert blur_suite["evidence_status"] == "AE exact but CLI unexplained"
        assert summary["by_plugin"]["OLMColorKey"]["AE exact"] == 8
        assert summary["by_plugin"]["OLMColorKey"]["reference-generation split"] == 1
        assert summary["by_plugin"]["OLMSmoother2"]["AE exact"] == 12
        assert summary["by_plugin"]["OLMSmoother2"]["known-red"] == 7
        assert all(row["reference_kind"] for row in manifest["cases"])
        assert all(row["runner_kind"] for row in manifest["cases"])
        assert summary_md.read_text(encoding="utf-8").startswith("# Packaged 8bpc")
    print("[OK] conformance summary smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
