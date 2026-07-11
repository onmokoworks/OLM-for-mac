#!/usr/bin/env python3
"""Prepare and optionally run the canonical Mac AE DG case_0023 reverify.

The request contains separate bg_on/bg_off cases so each output is compared
with its matching Windows AE Software 16bpc reference.  This wrapper keeps the
8bpc project-depth carry-over trap out of the run by forcing a fresh project.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASE_ID = "olmdistancegradation_extended__case_0023"
ON_ID = CASE_ID + "__bg_on"
OFF_ID = CASE_ID + "__bg_off"
NORMALIZED = ROOT / "refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch"
VARIANTS = ROOT / "refs/win_references/olmdistancegradation_16bpc_bg_compose_variants_20260626/DistanceGradation"


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--work-dir", type=Path, default=Path("/tmp/olmdg_case0023_mac_reverify"))
    p.add_argument("--app-name", default="Adobe After Effects 2026")
    p.add_argument("--timeout", type=int, default=1200)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--keep-open", action="store_true")
    return p.parse_args()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def find_case(manifest: dict, case_id: str) -> dict:
    return next(case for case in manifest["cases"] if case["id"] == case_id)


def materialize(work: Path) -> tuple[Path, Path, list[dict]]:
    request = work / "request"
    input_dir = request / "input"
    expected_dir = request / "expected"
    input_dir.mkdir(parents=True, exist_ok=True)
    expected_dir.mkdir(parents=True, exist_ok=True)
    normalized_case = find_case(load(NORMALIZED / "reference_manifest.json"), CASE_ID)
    variant_manifest = load(VARIANTS / "reference_manifest.json")
    on_case = find_case(variant_manifest, "olmdistancegradation_case_0023_bg_on_control")
    off_case = find_case(variant_manifest, "olmdistancegradation_case_0023_bg_off_variant")

    rows = []
    for case_id, source_root, source_case, use_bg in (
        (ON_ID, NORMALIZED, normalized_case, 1),
        (OFF_ID, VARIANTS / "renders", off_case, 0),
    ):
        input_name = source_case["before_effects_frame"]
        frame_name = source_case["frame"]
        shutil.copy2(source_root / input_name, input_dir / input_name)
        shutil.copy2(source_root / frame_name, expected_dir / frame_name)
        copied = dict(source_case)
        copied["id"] = case_id
        copied["case_id"] = CASE_ID
        copied["use_background_color"] = use_bg
        rows.append({"id": case_id, "before_effects_frame": input_name, "frame": frame_name})
        if case_id == ON_ID:
            on_full = copied
        else:
            off_full = copied

    reference = {
        "kind": "olm_ae_pixel_validation_reference_manifest",
        "project": {"bits_per_channel": 16, "gpu_accel_type": "SOFTWARE", "profile": "software_16bpc", "software_equivalent_profile": "software_16bpc"},
        "comp": {"width": 1920, "height": 1080, "duration": 1, "frame_rate": 24},
        "cases": [on_full, off_full],
    }
    request_manifest = {
        "kind": "olm_ae_pixel_validation_request",
        "request_id": "olmdistancegradation_case0023_mac_reverify_20260710",
        "reference_manifest": "reference_manifest.json",
        "input_dir": "input",
        "expected_dir": "expected",
        "effect_name": "Distance Gradation",
        "effect_match_name": "OLM Distance Gradation",
        "reference_profile": "windows-software-16bpc",
        "execution_profile": {"bits_per_channel": 16, "gpu_accel_type": "SOFTWARE", "software_equivalent_profile": "software_16bpc", "fresh_project": True},
        "threshold_groups": [{"name": "case0023_exact", "case_ids": [ON_ID, OFF_ID], "max_diff": 0, "mean_diff": 0.0, "nonzero_px_percent": 0.0}],
        "cases": rows,
        "notes": ["Canonical DG case_0023 bg_on/bg_off Mac AE reverify.", "Do not run this request through an inherited 8bpc AE project."],
    }
    (request / "reference_manifest.json").write_text(json.dumps(reference, indent=2) + "\n", encoding="utf-8")
    (request / "request_manifest.json").write_text(json.dumps(request_manifest, indent=2) + "\n", encoding="utf-8")
    return request, work / "candidate", rows


def main() -> int:
    a = args()
    work = a.work_dir.resolve()
    request, candidate, rows = materialize(work)
    candidate.mkdir(parents=True, exist_ok=True)
    common = ["--app-name", a.app_name, "--timeout", str(a.timeout), "--ae-env", "OLM_AE_FORCE_NEW_PROJECT=1", "--ae-env", "OLM_AE_FORCE_SOFTWARE=1"]
    on_cmd = [sys.executable, str(ROOT / "scripts/run_ae_single_case.py"), "--request-dir", str(request), "--case-id", ON_ID, "--output-dir", str(work / "bg_on"), "--param-override", "Use Background Color=1", *common]
    off_cmd = [sys.executable, str(ROOT / "scripts/run_ae_single_case.py"), "--request-dir", str(request), "--case-id", OFF_ID, "--output-dir", str(work / "bg_off"), "--param-override", "Use Background Color=0", *common]
    commands = [on_cmd, off_cmd]
    gui_ready = platform.system() == "Darwin" and shutil.which("osascript") is not None
    readiness = {
        "kind": "olm_distancegradation_case0023_mac_reverify_readiness",
        "status": "ready_for_mac_ae_gui" if gui_ready and not a.dry_run else "dry_run_ready_for_mac_ae_gui",
        "executed": False,
        "validated": False,
        "case_ids": [row["id"] for row in rows],
        "request_dir": str(request),
        "profile": {"bits_per_channel": 16, "gpu_accel_type": "SOFTWARE", "software_equivalent_profile": "software_16bpc", "max_diff": 0},
        "commands": [subprocess.list2cmdline(cmd) for cmd in commands],
        "blocked_reason": None if gui_ready else "AE GUI execution requires macOS with osascript; no GUI run performed.",
    }
    readiness_path = work / "MAC_AE_READINESS.json"
    readiness_path.write_text(json.dumps(readiness, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] request: {request}")
    print(f"[OK] readiness: {readiness_path}")
    if a.dry_run or not gui_ready:
        print("[READY] AE GUI not executed; use the recorded commands on the Mac AE host.")
        return 0

    for cmd in commands:
        if a.keep_open:
            cmd.append("--keep-open")
        subprocess.run(cmd, cwd=ROOT, check=True)
        output_dir = Path(cmd[cmd.index("--output-dir") + 1])
        frame = next(row["frame"] for row in rows if row["id"] == cmd[cmd.index("--case-id") + 1])
        shutil.copy2(output_dir / frame, candidate / frame)
    verify = [sys.executable, str(ROOT / "refs/scripts/verify_manifest.py"), str(request / "reference_manifest.json"), "--reference-dir", str(request / "expected"), "--candidate-dir", str(candidate), "--diff-dir", str(work / "diff"), "--report-dir", str(work / "report"), "--report-name", "case0023_mac_reverify", "--max-diff", "0", "--mean-diff", "0", "--nonzero-px-percent", "0"]
    rc = subprocess.run(verify, cwd=ROOT).returncode
    readiness["executed"] = True
    readiness["validated"] = rc == 0
    readiness["status"] = "validated_exact" if rc == 0 else "executed_not_exact"
    readiness_path.write_text(json.dumps(readiness, indent=2) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
