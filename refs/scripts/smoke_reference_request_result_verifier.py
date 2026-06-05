#!/usr/bin/env python3
"""Smoke-test verify_reference_request_result.py with a synthetic returned manifest."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def write_synthetic_result(root: Path, request: dict) -> tuple[Path, Path]:
    good_dir = root / "good"
    good_dir.mkdir()
    cases = []
    for case in request["cases"]:
        if case.get("optional"):
            continue
        frame = f"SOFTWARE_{case['id']}.png"
        before = f"SOFTWARE_{case['id']}_before_effects.png"
        (good_dir / frame).write_bytes(b"png")
        (good_dir / before).write_bytes(b"png")
        cases.append(
            {
                "id": f"SOFTWARE_{case['id']}",
                "request_case_id": case["id"],
                "render_set": "SOFTWARE",
                "project_gpu_accel_type": {"current_name": "SOFTWARE", "raw": 1816},
                "frame": frame,
                "before_effects_frame": before,
                "selected_layer_effects": [
                    {"name": "OLM Kira Kira", "match_name": "OLM OLM Kira Kira"}
                ],
            }
        )

    manifest = {
        "kind": "ae_effect_reference_manifest",
        "effect": {"name": "OLM Kira Kira", "match_name": "OLM OLM Kira Kira"},
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
    repo = Path(__file__).resolve().parents[2]
    request = repo / "refs/reference_requests/kirakira_single_ray_20260606.json"
    verifier = repo / "refs/scripts/verify_reference_request_result.py"
    data = json.loads(request.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory(prefix="olm_ref_verify_smoke_") as tmp:
        good_manifest, bad_manifest = write_synthetic_result(Path(tmp), data)
        base_cmd = [
            sys.executable,
            str(verifier),
            "--allow-missing-optional-render-sets",
            str(request),
        ]
        good = run(base_cmd + [str(good_manifest)])
        print(good.stdout, end="")
        if good.returncode != 0:
            return good.returncode

        bad = run(base_cmd + [str(bad_manifest)])
        print(bad.stdout, end="")
        if bad.returncode == 0:
            print("[FAIL] missing-case negative test unexpectedly passed")
            return 1

    print("[OK] reference request result verifier smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
