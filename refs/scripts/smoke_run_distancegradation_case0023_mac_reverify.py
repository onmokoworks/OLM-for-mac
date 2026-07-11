#!/usr/bin/env python3
"""Smoke-test the DG case_0023 request/readiness runner without AE GUI."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="dg_case0023_reverify_") as tmp:
        work = Path(tmp) / "work"
        subprocess.run([sys.executable, str(root / "scripts/run_distancegradation_case0023_mac_reverify.py"), "--work-dir", str(work), "--dry-run"], cwd=root, check=True)
        readiness = json.loads((work / "MAC_AE_READINESS.json").read_text())
        request = work / "request"
        manifest = json.loads((request / "request_manifest.json").read_text())
        reference = json.loads((request / "reference_manifest.json").read_text())
        assert readiness["status"] == "dry_run_ready_for_mac_ae_gui"
        assert readiness["profile"] == {"bits_per_channel": 16, "gpu_accel_type": "SOFTWARE", "software_equivalent_profile": "software_16bpc", "max_diff": 0}
        assert manifest["threshold_groups"][0]["max_diff"] == 0
        assert [case["id"] for case in manifest["cases"]] == ["olmdistancegradation_extended__case_0023__bg_on", "olmdistancegradation_extended__case_0023__bg_off"]
        assert reference["project"]["bits_per_channel"] == 16
        assert reference["project"]["gpu_accel_type"] == "SOFTWARE"
        assert reference["project"]["software_equivalent_profile"] == "software_16bpc"
    print("[OK] DG case_0023 Mac reverify smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
