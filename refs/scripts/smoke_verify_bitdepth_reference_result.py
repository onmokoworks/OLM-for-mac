#!/usr/bin/env python3
"""Smoke-test verifier support for the mixed-effect 16bpc reference request."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REQUEST = ROOT / "refs" / "reference_requests" / "olm_bitdepth_16bpc_normalized_exact_20260625.json"


def write_result(root: Path, request: dict) -> tuple[Path, Path]:
    good_dir = root / "bitdepth_16bpc_return"
    good_dir.mkdir()
    cases = []
    request_id = request["request_id"]
    for case in request["cases"]:
        frame = f"{request_id}__software_16bpc__{case['id']}.png"
        before = f"{request_id}__software_16bpc__{case['id']}_before_effects.png"
        (good_dir / frame).write_bytes(b"png")
        (good_dir / before).write_bytes(b"png")
        cases.append(
            {
                "id": f"software_16bpc__{case['id']}",
                "request_id": request_id,
                "request_case_id": case["id"],
                "source_case_id": case.get("source_case_id"),
                "render_set_id": "software_16bpc",
                "bit_depth": "16bpc",
                "bits_per_channel": 16,
                "project_gpu_accel_type": {"current_name": "SOFTWARE", "raw": 1816},
                "frame": frame,
                "before_effects_frame": before,
                "selected_layer_effects": [case["effect"]],
            }
        )
    manifest = {
        "kind": "ae_effect_reference_manifest",
        "request_id": request_id,
        "requests": [{"request_id": request_id, "effect": request["effect"]}],
        "project_gpu_accel_type": {"current_name": "SOFTWARE", "raw": 1816},
        "cases": cases,
    }
    good_manifest = good_dir / "reference_manifest.json"
    good_manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    bad_manifest = good_dir / "reference_manifest_missing.json"
    bad = dict(manifest)
    bad["cases"] = cases[:-1]
    bad_manifest.write_text(json.dumps(bad, indent=2), encoding="utf-8")
    return good_manifest, bad_manifest


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def main() -> int:
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    verifier = ROOT / "refs" / "scripts" / "verify_reference_request_result.py"
    with tempfile.TemporaryDirectory(prefix="olm_bitdepth_result_smoke_") as tmp:
        tmp_path = Path(tmp)
        good_manifest, bad_manifest = write_result(tmp_path, request)
        good = run([sys.executable, str(verifier), str(REQUEST), str(good_manifest)])
        print(good.stdout, end="" if good.stdout.endswith("\n") else "\n")
        if good.returncode != 0:
            return good.returncode
        bad = run([sys.executable, str(verifier), str(REQUEST), str(bad_manifest)])
        print(bad.stdout, end="" if bad.stdout.endswith("\n") else "\n")
        if bad.returncode == 0:
            print("[FAIL] missing 16bpc case negative test unexpectedly passed")
            return 1

        requests_dir = tmp_path / "requests"
        requests_dir.mkdir()
        request_copy = requests_dir / REQUEST.name
        shutil.copy2(REQUEST, request_copy)
        intake = run(
            [
                sys.executable,
                str(ROOT / "scripts" / "intake_olm_return.py"),
                str(good_manifest.parent),
                "--kind",
                "win-reference",
                "--dest-root",
                str(tmp_path / "win_references"),
                "--requests-dir",
                str(requests_dir),
                "--request",
                str(request_copy),
                "--set-id",
                "synthetic_16bpc_return",
                "--no-next-actions",
            ]
        )
        print(intake.stdout, end="" if intake.stdout.endswith("\n") else "\n")
        if intake.returncode != 0:
            return intake.returncode
        imported_manifest = (
            tmp_path
            / "win_references"
            / "synthetic_16bpc_return"
            / "OLMbit-depthconformancebatch"
            / "reference_manifest.json"
        )
        if not imported_manifest.exists():
            print("[FAIL] bit-depth intake did not import the synthetic reference manifest")
            return 1
    print("[OK] bit-depth reference result verifier smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
