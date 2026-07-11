#!/usr/bin/env python3
"""Smoke test for materialize_distancegradation_case0023_lane_state.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "materialize_distancegradation_case0023_lane_state.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmdg_case0023_lane_state_") as tmp:
        tmp_path = Path(tmp)
        out_json = tmp_path / "out.json"
        out_md = tmp_path / "out.md"
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--stamp",
                "20990101",
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=ROOT,
            check=True,
        )
        data = json.loads(out_json.read_text(encoding="utf-8"))
        assert data["kind"] == "olmdistancegradation_case0023_lane_state"
        assert data["threshold_family"]["status"] == "reference-export-exact-mac-source-output-live"
        assert data["edge_family"]["status"] == "upstream-field-ownership-still-live"
        assert data["threshold_family"]["reference_export_audit"]["reference_exact"] is True
        assert "(1699,7)" in data["edge_family"]["live_bg_off_mismatches"]
        assert data["edge_family"]["aex_cpu_simu"]["status"] == "diagnostic_binary_grounded_field_witness"
        assert any(
            sample.get("xy") == [1699, 7] and sample.get("both_add_saturate_field") == 0.0
            for sample in data["edge_family"]["aex_cpu_simu"]["samples"]
        )
        compose = data["edge_family"].get("compose_witness")
        if compose is not None:
            assert compose["status"] == "compose-writeback-triplet-binary-grounded"
            assert all(row["match_promoted"] for row in compose["triplet"])
        source_model = data["edge_family"].get("source_model_audit")
        if source_model is not None:
            assert source_model["status"] == "source-model-matches-aex-helper-samples"
            assert all(row["match"] for row in source_model["samples"])
        text = out_md.read_text(encoding="utf-8")
        assert "OLMDistanceGradation case_0023 Lane State" in text
        assert "Threshold-family" in text
        assert "Reference Export Audit" in text
        assert "packaged/current Windows exact" in text
        assert "Edge-family" in text
        assert "AEX CPU Simu Reading" in text
        if compose is not None:
            assert "Compose/Writeback Witness" in text
        if source_model is not None:
            assert "Mac Source Model Audit" in text
    print("[OK] materialize_distancegradation_case0023_lane_state smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
