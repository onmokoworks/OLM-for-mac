#!/usr/bin/env python3
"""Smoke-test the 2026-07-15 OLMBlur residual-locus analysis."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts/analyze_olmblur_residual_locus_20260715.py"
    with tempfile.TemporaryDirectory(prefix="olmblur_residual_locus_") as tmp:
        out = Path(tmp)
        cmd = [sys.executable, str(script), "--output-json", str(out / "report.json"), "--output-md", str(out / "report.md")]
        subprocess.run(cmd, cwd=root, check=True)
        report = json.loads((out / "report.json").read_text(encoding="utf-8"))
        assert report["verdict"] == "separate-lanes"
        assert report["identity"]["windows_export_equals_canonical"] is True
        assert report["residuals"] == [{"xy": [601, 598], "windows": [18, 18, 18, 255], "mac_single": [17, 17, 18, 255], "delta": [1, 1, 0, 0]}]
        assert report["mapping"]["status"] == "not-proven"
        assert report["actual_aex"]["portable_trace_self_check"] is True
        assert report["gates"]["cdb_attach_used"] is False
        assert report["gates"]["windows_return_classification"] is True
        assert report["host_contracts_compatible"] is True
        text = (out / "report.md").read_text(encoding="utf-8")
        for needle in ("601,598", "separate-lanes", "FACT", "INFERENCE", "CDB attach"):
            assert needle in text, needle

        exact_observation = out / "exact_observation.json"
        exact_sha = report["files"]["windows_export"]["sha256"]
        exact_observation.write_text(
            json.dumps(
                {
                    "status": "answered_observation",
                    "claim": "observation_only_not_exact",
                    "case_id": "olmblur__case_0006",
                    "point": [601, 598],
                    "mac_plugin_binary_sha256": "c6de66dab49a6a96852d6158780bfd8c52767cc699e2cef1fa2206e0fbadf206",
                    "output": {"sha256": exact_sha},
                    "ae_result": {"project_bits_per_channel": 16},
                    "diagnostic_log": {"record": {"fields": {
                        "plugin_sha256": "c6de66dab49a6a96852d6158780bfd8c52767cc699e2cef1fa2206e0fbadf206",
                        "project_bpc": "16", "renderer": "Software", "x": "601", "y": "598"
                    }}},
                }
            ) + "\n",
            encoding="utf-8",
        )
        exact_cmd = [
            sys.executable,
            str(script),
            "--mac-single-export",
            report["files"]["windows_export"]["path"],
            "--mac-observation-report",
            str(exact_observation),
            "--output-json",
            str(out / "exact.json"),
            "--output-md",
            str(out / "exact.md"),
        ]
        subprocess.run(exact_cmd, cwd=root, check=True)
        exact = json.loads((out / "exact.json").read_text(encoding="utf-8"))
        assert exact["verdict"] == "ae-exact-observed"
        assert exact["residuals"] == []
        assert exact["gates"]["mac_observation_bound"] is True

        missing = out / "missing.png"
        fail = subprocess.run(cmd[:1] + [str(script), "--windows-export", str(missing), "--output-json", str(out / "bad.json"), "--output-md", str(out / "bad.md")], cwd=root, text=True, capture_output=True)
        assert fail.returncode != 0
        assert "FAIL-CLOSED" in fail.stderr
    print("[OK] OLMBlur residual-locus smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
