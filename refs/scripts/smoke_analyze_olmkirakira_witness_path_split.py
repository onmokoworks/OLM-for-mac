#!/usr/bin/env python3
"""Smoke-test the KiraKira witness-path split analyzer."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    historical_output = Path("/tmp/kirakira_compose_debug_20260703_8bpc_rerun/kirakira_single_ray_20260606__software__fr24__kk_vertical_len50_brightness1_strength100.png")
    live_output = Path("/tmp/olm_ae_single_case_20260703_141656/kirakira_single_ray_20260606__software__fr24__kk_vertical_len50_brightness1_strength100.png")
    if not historical_output.exists() or not live_output.exists():
        print("skipping smoke: required live outputs missing", file=sys.stderr)
        return 0
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        out_json = tmp / "split.json"
        out_md = tmp / "split.md"
        proc = subprocess.run(
            [
                "python3",
                "scripts/analyze_olmkirakira_witness_path_split.py",
                "--reference-png",
                str(ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_single_kirakira_hotspot_probe_20260703_r3/expected/kirakira_single_ray_20260606__software__fr24__kk_vertical_len50_brightness1_strength100.png"),
                "--historical-output-png",
                str(historical_output),
                "--live-output-png",
                str(live_output),
                "--historical-debug-json",
                str(ROOT / "refs/conformance/olmkirakira_compose_boundary_mac_witness_20260630.json"),
                "--live-debug-json",
                str(ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_single_kirakira_hotspot_probe_20260703_r3/kirakira_neighborhood.json"),
                "--historical-request-reference-manifest",
                "/tmp/ae_kirakira_single_ray_request_20260630/reference_manifest.json",
                "--live-request-reference-manifest",
                str(ROOT / "handoff/ae_pixel_validation_20260618/requests/ae_single_kirakira_hotspot_probe_20260703_r3/reference_manifest.json"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if proc.returncode != 0:
            print(proc.stdout, file=sys.stderr, end="")
            return proc.returncode
        data = json.loads(out_json.read_text(encoding="utf-8"))
        if data.get("kind") != "olmkirakira_witness_path_split":
            print("unexpected kind", file=sys.stderr)
            return 1
        if data.get("historical_8bpc_lane", {}).get("project_bits_per_channel") != 8:
            print("historical bitsPerChannel mismatch", file=sys.stderr)
            return 1
    print("[OK] OLMKiraKira witness-path split smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
